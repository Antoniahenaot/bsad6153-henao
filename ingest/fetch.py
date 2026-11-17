"""Fetch a Milestone 1 sample from the provisional IGAC source in Pasto."""

import json
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from tempfile import mkdtemp

import requests


# Keep the release and layer settings together so a newer release can be verified first.
RELEASE = "2026-08-31"
BASE_URL = (
    "https://services2.arcgis.com/RVvWzU3lgJISqdke/arcgis/rest/services/"
    "CATASTRO_PUBLICO_31082026/FeatureServer"
)
MUNICIPALITY = "52001"  # Pasto
LAND_LAYER = 7
BUILDING_LAYER = 3
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

LAND_TARGET = 500
PAGE_SIZE = 100
CODE_BATCH_SIZE = 20
REQUEST_DELAY = 0.5
TIMEOUT = 20
MAX_ATTEMPTS = 4
MAX_RETRY_WAIT = 120


class FetchError(Exception):
    """A fetch could not be completed safely."""


def retry_delay(retry_after, attempt):
    """Return a wait in seconds, accepting either form of Retry-After."""
    if retry_after:
        try:
            return max(0, int(retry_after))
        except ValueError:
            try:
                date = parsedate_to_datetime(retry_after)
                if date.tzinfo is not None:
                    return max(0, (date - datetime.now(timezone.utc)).total_seconds())
            except (ValueError, TypeError, OverflowError):
                pass
    return 2 ** (attempt - 1)


def request_page(session, layer, params):
    """Request one page and retry temporary failures a limited number of times."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        time.sleep(REQUEST_DELAY)
        retry_after = None
        try:
            response = session.get(
                f"{BASE_URL}/{layer}/query",
                params=params,
                timeout=TIMEOUT,
            )
        except (requests.Timeout, requests.ConnectionError) as error:
            if isinstance(error, requests.exceptions.SSLError):
                raise FetchError(f"HTTPS certificate verification failed: {error}") from error
            problem = f"{type(error).__name__}: {error}"
        else:
            status = response.status_code
            if status == 429 or 500 <= status < 600:
                problem = f"HTTP {status}"
                retry_after = response.headers.get("Retry-After")
            else:
                response.raise_for_status()
                try:
                    payload = response.json()
                except ValueError as error:
                    raise FetchError("Expected JSON but received an unreadable response.") from error
                if not isinstance(payload, dict):
                    raise FetchError("Expected a JSON object from ArcGIS.")
                if "error" not in payload:
                    return response.content, payload
                details = payload["error"]
                code = details.get("code") if isinstance(details, dict) else None
                problem = f"ArcGIS error: {details}"
                if type(code) is not int or (code != 429 and not 500 <= code < 600):
                    raise FetchError(problem)
                retry_after = response.headers.get("Retry-After")

        if attempt == MAX_ATTEMPTS:
            raise FetchError(f"{problem} after {attempt} attempts.")
        wait = retry_delay(retry_after, attempt)
        if wait > MAX_RETRY_WAIT:
            raise FetchError(f"{problem}. Server requested a {wait:.0f}s wait. Try again later.")
        print(f"Layer {layer}: {problem}. Retrying in {wait:g}s.")
        time.sleep(wait)


def pages(session, run_dir, label, layer, where, fields):
    """Yield pages in OBJECTID order and save each original JSON response."""
    offset = 0
    last_id = None
    while True:
        params = {
            "where": where,
            "outFields": fields,
            "returnGeometry": "true",
            "orderByFields": "OBJECTID ASC",
            "resultRecordCount": PAGE_SIZE,
            "resultOffset": offset,
            "f": "json",
        }
        try:
            raw, payload = request_page(session, layer, params)
        except (FetchError, requests.RequestException) as error:
            raise FetchError(f"{label}, offset {offset}: {error}") from error

        features = payload.get("features")
        if not isinstance(features, list) or len(features) > PAGE_SIZE:
            raise FetchError(f"{label}, offset {offset}: expected a bounded list of features.")
        more = payload.get("exceededTransferLimit")
        if more is True and not features:
            raise FetchError(f"{label}, offset {offset}: empty page reports more records.")

        page_path = run_dir / f"{label}-{offset:06d}.json"
        page_path.write_bytes(raw)
        print(f"{label}, offset {offset}: received {len(features)} records.")

        rows = []
        for feature in features:
            attributes = feature.get("attributes") if isinstance(feature, dict) else None
            attributes = attributes if isinstance(attributes, dict) else {}
            object_id = attributes.get("OBJECTID")
            if type(object_id) is int:
                if last_id is not None and object_id <= last_id:
                    raise FetchError(f"{label}, offset {offset}: duplicate or out-of-order OBJECTID.")
                last_id = object_id
            rows.append(attributes)
        yield rows

        if more is False or (more is not True and len(features) < PAGE_SIZE):
            return
        offset += PAGE_SIZE


def valid_code(value):
    """Cadastral codes are 30 digits stored as text."""
    return isinstance(value, str) and len(value) == 30 and value.isascii() and value.isdigit()


def fetch(session, run_dir):
    city_filter = f"codigo_municipio = '{MUNICIPALITY}'"
    land_codes = set()
    invalid_land = 0
    duplicate_land = 0
    land_pages = pages(
        session, run_dir, "land", LAND_LAYER, city_filter,
        "OBJECTID,CODIGO,MANZANA_CODIGO,CODIGO_ANTERIOR,codigo_municipio,"
        "CODIGO_DEPARTAMENTO,Shape__Area,Shape__Length",
    )
    for page in land_pages:
        for row in page:
            code = row.get("CODIGO")
            if type(row.get("OBJECTID")) is not int or not valid_code(code):
                invalid_land += 1
            elif code in land_codes:
                duplicate_land += 1
            else:
                land_codes.add(code)
        if len(land_codes) >= LAND_TARGET:
            break

    if len(land_codes) < LAND_TARGET:
        raise FetchError(
            f"Found only {len(land_codes)} distinct valid parcels. "
            f"Skipped {invalid_land} invalid rows and {duplicate_land} duplicate codes."
        )

    selected_codes = sorted(land_codes)
    matched_codes = set()
    building_count = 0
    invalid_buildings = 0
    for start in range(0, len(selected_codes), CODE_BATCH_SIZE):
        batch = set(selected_codes[start:start + CODE_BATCH_SIZE])
        # The codes were validated as ASCII digits before they enter the query.
        quoted_codes = ", ".join(f"'{code}'" for code in sorted(batch))
        building_filter = f"{city_filter} AND TERRENO_CODIGO IN ({quoted_codes})"
        for page in pages(
            session, run_dir, f"buildings-{start // CODE_BATCH_SIZE + 1:03d}",
            BUILDING_LAYER, building_filter,
            "OBJECTID,CODIGO,TERRENO_CODIGO,TIPO_CONSTRUCCION,codigo_municipio,"
            "Shape__Area,Shape__Length",
        ):
            for row in page:
                code = row.get("TERRENO_CODIGO")
                if type(row.get("OBJECTID")) is not int or not valid_code(code) or code not in batch:
                    invalid_buildings += 1
                    continue
                matched_codes.add(code)
                building_count += 1

    return {
        "distinct_valid_land": len(land_codes),
        "related_buildings": building_count,
        "parcels_with_buildings": len(matched_codes),
        "parcels_without_building_matches": len(land_codes - matched_codes),
        "invalid_land_rows": invalid_land,
        "duplicate_land_codes": duplicate_land,
        "invalid_building_rows": invalid_buildings,
    }


def main():
    started = datetime.now(timezone.utc)
    print(f"Provisional source: IGAC, Pasto ({MUNICIPALITY}), release {RELEASE}.")
    run_dir = None
    try:
        release_dir = RAW_DIR / RELEASE
        release_dir.mkdir(parents=True, exist_ok=True)
        run_dir = Path(mkdtemp(prefix=started.strftime("%Y%m%dT%H%M%SZ-"), dir=release_dir))
        with requests.Session() as session:
            # Avoid sending credentials from the user's local .netrc configuration.
            session.trust_env = False
            counts = fetch(session, run_dir)
        print(f"Distinct valid parcels: {counts['distinct_valid_land']}")
        print(f"Related buildings: {counts['related_buildings']}")
        print(f"Parcels with building matches: {counts['parcels_with_buildings']}")
        print(f"Parcels without building matches: {counts['parcels_without_building_matches']}")
        print(
            f"Skipped {counts['invalid_land_rows']} invalid land rows, "
            f"{counts['duplicate_land_codes']} duplicate land codes, "
            f"and {counts['invalid_building_rows']} invalid building rows."
        )
        if not counts["related_buildings"]:
            raise FetchError("No related building records found in the selected parcel sample.")
        summary = {
            "source": "IGAC (provisional)",
            "municipality": "Pasto (provisional)",
            "municipality_code": MUNICIPALITY,
            "release_date": RELEASE,
            "fetched_at_utc": started.isoformat(),
            "land_layer_url": f"{BASE_URL}/{LAND_LAYER}",
            "building_layer_url": f"{BASE_URL}/{BUILDING_LAYER}",
            **counts,
        }
        summary_tmp = run_dir / "complete.json.tmp"
        summary_tmp.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        summary_tmp.rename(run_dir / "complete.json")
        print(f"Raw JSON and completion summary saved in {run_dir}")
    except (FetchError, OSError) as error:
        if run_dir is not None:
            print(f"Incomplete run: raw responses received so far are in {run_dir}")
        raise SystemExit(f"Fetch failed: {error}") from error


if __name__ == "__main__":
    main()
