"""Recheck a bounded Pasto sample and preserve distinct content snapshots.

Requires db/migrations/003_sync_runs.sql. No DDL or credential output.
"""

import argparse
import contextlib
import hashlib
import io
import json
import os
import time
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
import requests
from dotenv import dotenv_values

import fetch
import load


class BoundedSession(requests.Session):
    """Bound the complete download, including retries and metadata calls."""

    def __init__(self):
        super().__init__()
        self.trust_env = False
        self.deadline = time.monotonic() + 1200
        self.requests_left = 250

    def get(self, *args, **kwargs):
        if self.requests_left <= 0 or time.monotonic() >= self.deadline:
            raise fetch.FetchError("Download budget exhausted.")
        self.requests_left -= 1
        return super().get(*args, **kwargs)


def metadata(session, layer):
    for attempt in range(1, fetch.MAX_ATTEMPTS + 1):
        time.sleep(fetch.REQUEST_DELAY)
        retry_after = None
        try:
            response = session.get(
                f"{fetch.BASE_URL}/{layer}", params={"f": "json"}, timeout=fetch.TIMEOUT
            )
            if response.status_code == 429 or 500 <= response.status_code < 600:
                retry_after = response.headers.get("Retry-After")
            else:
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict) or "error" in payload:
                    raise fetch.FetchError("Invalid layer metadata.")
                if payload.get("id") != layer or not payload.get("editingInfo"):
                    raise fetch.FetchError("Required layer metadata missing.")
                return {key: payload.get(key) for key in (
                    "id", "fields", "editingInfo", "spatialReference", "capabilities"
                )}
        except (requests.Timeout, requests.ConnectionError) as error:
            if isinstance(error, requests.exceptions.SSLError):
                raise fetch.FetchError("TLS verification failed.") from None
        if attempt == fetch.MAX_ATTEMPTS:
            raise fetch.FetchError("Metadata retries exhausted.")
        wait = fetch.retry_delay(retry_after, attempt)
        if wait > fetch.MAX_RETRY_WAIT:
            raise fetch.FetchError("Requested retry wait exceeds budget.")
        time.sleep(wait)


def download():
    with TemporaryDirectory(prefix="igac-sync-") as folder, BoundedSession() as session:
        directory = Path(folder)
        before = [metadata(session, layer) for layer in (fetch.LAND_LAYER, fetch.BUILDING_LAYER)]
        fetched_at = datetime.now(timezone.utc)
        # Existing fetch diagnostics may include remote error details. Keep them private.
        with contextlib.redirect_stdout(io.StringIO()):
            summary = fetch.fetch(session, directory)
        after = [metadata(session, layer) for layer in (fetch.LAND_LAYER, fetch.BUILDING_LAYER)]
        if before != after:
            raise fetch.FetchError("Source changed during download.")
        parcels = load.read_layer(directory, "land", load.PARCEL_FIELDS, fetch.MUNICIPALITY)
        buildings = load.read_layer(directory, "buildings", load.BUILDING_FIELDS, fetch.MUNICIPALITY)
        counts = load.relationship_counts(parcels, buildings)
        expected = tuple(summary[key] for key in (
            "distinct_valid_land", "related_buildings", "parcels_with_buildings",
            "parcels_without_building_matches",
        ))
        if counts != expected or counts[0] != fetch.LAND_TARGET or any(
            summary[key] for key in ("invalid_land_rows", "duplicate_land_codes", "invalid_building_rows")
        ):
            raise ValueError("Download validation failed.")
        return fetched_at, parcels, buildings, counts


def normalized(value):
    # PostgreSQL jsonb may return integral geometry coordinates as ints.
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, dict):
        return {key: normalized(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalized(item) for item in value]
    return value


def fingerprint(parcels, buildings):
    content = {
        "release": fetch.RELEASE, "municipality": fetch.MUNICIPALITY,
        "land_url": f"{fetch.BASE_URL}/{fetch.LAND_LAYER}".lower(),
        "building_url": f"{fetch.BASE_URL}/{fetch.BUILDING_LAYER}".lower(),
        "srid": 3857,
        "parcels": sorted(parcels, key=lambda row: row["object_id"]),
        "buildings": sorted(buildings, key=lambda row: row["object_id"]),
    }
    encoded = json.dumps(normalized(content), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode()).hexdigest()


def read_rows(cursor, table, fields, snapshot_id):
    columns = list(fields) + ["geometry"]
    cursor.execute(sql.SQL("SELECT {} FROM {} WHERE snapshot_id = %s ORDER BY object_id").format(
        sql.SQL(", ").join(map(sql.Identifier, columns)), sql.Identifier("igac", table)
    ), (snapshot_id,))
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def store(connection, run_id, fetched_at, parcels, buildings, counts):
    digest = fingerprint(parcels, buildings)
    with connection.transaction(), connection.cursor(binary=True) as cursor:
        cursor.execute("SET LOCAL statement_timeout = '60s'")
        cursor.execute("SET LOCAL lock_timeout = '10s'")
        # Shared by all instances of this sync; avoids simultaneous content versions.
        cursor.execute("SELECT pg_advisory_xact_lock(6153, 3)")
        cursor.execute("""
            SELECT snapshot_id FROM igac.cadastral_snapshots
            WHERE release_date = %s AND municipality_code = %s AND geometry_srid = 3857
              AND lower(land_layer_url) = lower(%s) AND lower(building_layer_url) = lower(%s)
            ORDER BY snapshot_id
        """, (date.fromisoformat(fetch.RELEASE), fetch.MUNICIPALITY,
              f"{fetch.BASE_URL}/{fetch.LAND_LAYER}", f"{fetch.BASE_URL}/{fetch.BUILDING_LAYER}"))
        candidates = cursor.fetchall()
        snapshot_id = None
        for (candidate,) in candidates:
            old_parcels = read_rows(cursor, "parcels", load.PARCEL_FIELDS, candidate)
            old_buildings = read_rows(cursor, "buildings", load.BUILDING_FIELDS, candidate)
            if fingerprint(old_parcels, old_buildings) == digest:
                snapshot_id = candidate
                break
        created = snapshot_id is None
        if created:
            snapshot = {
                "source_run_id": f"sync-v1-{digest}",
                "release_date": date.fromisoformat(fetch.RELEASE), "fetched_at": fetched_at,
                "municipality_code": fetch.MUNICIPALITY,
                "land_layer_url": f"{fetch.BASE_URL}/{fetch.LAND_LAYER}",
                "building_layer_url": f"{fetch.BASE_URL}/{fetch.BUILDING_LAYER}",
                "geometry_srid": 3857,
            }
            cursor.execute("SELECT snapshot_id FROM igac.cadastral_snapshots WHERE source_run_id = %s",
                           (snapshot["source_run_id"],))
            if cursor.fetchone() is not None:
                raise ValueError("Existing content-version ID has different stored content.")
            load.upsert(cursor, "cadastral_snapshots", ("source_run_id",), [snapshot])
            cursor.execute("SELECT snapshot_id FROM igac.cadastral_snapshots WHERE source_run_id = %s",
                           (snapshot["source_run_id"],))
            snapshot_id = cursor.fetchone()[0]
            for table, rows in (("parcels", parcels), ("buildings", buildings)):
                incoming = [{**row, "snapshot_id": snapshot_id, "geometry": Jsonb(row["geometry"])}
                            for row in rows]
                load.upsert(cursor, table, ("snapshot_id", "object_id"), incoming)
        saved_parcels = read_rows(cursor, "parcels", load.PARCEL_FIELDS, snapshot_id)
        saved_buildings = read_rows(cursor, "buildings", load.BUILDING_FIELDS, snapshot_id)
        if (load.relationship_counts(saved_parcels, saved_buildings) != counts
                or fingerprint(saved_parcels, saved_buildings) != digest):
            raise ValueError("Post-load verification failed.")
        total = len(parcels) + len(buildings)
        cursor.execute("""
            UPDATE igac.sync_runs SET status = 'success', finished_at = clock_timestamp(),
                snapshot_id = %s, content_sha256 = %s, records_fetched = %s,
                records_inserted = %s, records_updated = 0, records_unchanged = %s,
                snapshot_created = %s, last_updated_at = clock_timestamp()
            WHERE run_id = %s AND status = 'running'
        """, (snapshot_id, digest, total, total if created else 0,
              0 if created else total, created, run_id))
        if cursor.rowcount != 1:
            raise RuntimeError("Run finalization failed.")
    return total, created


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    connection = None
    run_id = uuid.uuid4()
    stage = "database"
    try:
        settings = dotenv_values(Path(__file__).resolve().parents[1] / ".env", interpolate=False)
        url = os.environ.get("IGAC_LOADER_DATABASE_URL") or settings.get("IGAC_LOADER_DATABASE_URL")
        if not url:
            raise RuntimeError("Loader connection missing.")
        event = os.environ.get("GITHUB_EVENT_NAME", "")
        if event and event not in ("schedule", "workflow_dispatch"):
            raise RuntimeError("Unsupported workflow event.")
        trigger = {"schedule": "scheduled", "workflow_dispatch": "manual"}.get(event, "local")
        connection = psycopg.connect(url, connect_timeout=10, autocommit=True)
        connection.execute("""
            INSERT INTO igac.sync_runs
                (run_id, status, trigger_type, github_run_id, github_run_attempt, source_release)
            VALUES (%s, 'running', %s, %s, %s, %s)
        """, (run_id, trigger, os.environ.get("GITHUB_RUN_ID"),
              int(os.environ["GITHUB_RUN_ATTEMPT"]) if os.environ.get("GITHUB_RUN_ATTEMPT") else None,
              date.fromisoformat(fetch.RELEASE)))
        stage = "fetch"
        fetched_at, parcels, buildings, counts = download()
        stage = "database"
        total, created = store(connection, run_id, fetched_at, parcels, buildings, counts)
        print(f"Sync success: {total} source records; "
              f"{total if created else 0} inserted, 0 updated, {0 if created else total} unchanged; "
              f"snapshot {'created' if created else 'reused'}.")
        return 0
    except Exception as error:
        category = "validation" if isinstance(error, (ValueError, KeyError, TypeError)) else stage
        try:
            if connection is not None:
                # Separate from the rolled-back import. Do not overwrite a committed success
                # if the server committed but its acknowledgement was lost.
                with connection.transaction():
                    result = connection.execute("""
                        UPDATE igac.sync_runs SET status = 'failed', finished_at = clock_timestamp(),
                            error_category = %s, last_updated_at = clock_timestamp()
                        WHERE run_id = %s AND status = 'running'
                    """, (category, run_id))
                if result.rowcount == 0:
                    print("Run status requires reconciliation; do not blindly retry.")
        except Exception:
            print("Database run logging unavailable; reconcile run history before retrying.")
        print(f"Sync failed ({category}); details withheld. Run ID: {run_id}")
        return 1
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
