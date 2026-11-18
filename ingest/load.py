"""Validate or load one completed IGAC run from a local folder."""

import argparse
import json
import math
import os
import re
from datetime import date, datetime
from pathlib import Path


PARCEL_FIELDS = {
    "object_id": "OBJECTID",
    "codigo": "CODIGO",
    "manzana_codigo": "MANZANA_CODIGO",
    "codigo_anterior": "CODIGO_ANTERIOR",
    "department_code": "CODIGO_DEPARTAMENTO",
    "shape_area": "Shape__Area",
    "shape_length": "Shape__Length",
}
BUILDING_FIELDS = {
    "object_id": "OBJECTID",
    "codigo": "CODIGO",
    "terreno_codigo": "TERRENO_CODIGO",
    "construction_type": "TIPO_CONSTRUCCION",
    "shape_area": "Shape__Area",
    "shape_length": "Shape__Length",
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def valid_code(value, length):
    return isinstance(value, str) and re.fullmatch(r"[0-9]{" + str(length) + "}", value)


def read_layer(run_dir, layer, fields, municipality):
    paths = sorted(run_dir.glob(f"{layer}-*.json"))
    if not paths:
        raise ValueError(f"No saved {layer} pages.")
    rows = []
    identities = set()
    for path in paths:
        page = read_json(path)
        reference = page["spatialReference"]
        wkid = reference.get("wkid")
        latest = reference.get("latestWkid")
        if (wkid, latest) not in {(3857, None), (3857, 3857), (102100, 3857)}:
            raise ValueError(f"A {layer} page does not report EPSG:3857.")
        if page.get("geometryType") != "esriGeometryPolygon":
            raise ValueError(f"A {layer} page is not a polygon layer.")
        for feature in page["features"]:
            attributes = feature["attributes"]
            row = {column: attributes.get(field) for column, field in fields.items()}
            object_id = row["object_id"]
            if type(object_id) is not int or not 0 < object_id < 2**63 or object_id in identities:
                raise ValueError(f"Invalid or repeated source OBJECTID in {layer}.")
            identities.add(object_id)
            if attributes.get("codigo_municipio") != municipality:
                raise ValueError(f"Municipality mismatch in {layer}.")
            for column, value in row.items():
                if column in ("codigo", "terreno_codigo") and not valid_code(value, 30):
                    raise ValueError(f"Invalid cadastral code in {layer}.")
                if column == "construction_type" and (not isinstance(value, str) or not value.strip()):
                    raise ValueError("Missing building construction type.")
                if column in ("shape_area", "shape_length") and value is not None and (
                    type(value) not in (int, float) or not math.isfinite(value)
                ):
                    raise ValueError(f"Invalid measurement in {layer}.")
            geometry = feature.get("geometry")
            if not isinstance(geometry, dict) or not isinstance(geometry.get("rings"), list) or not geometry["rings"]:
                raise ValueError(f"Missing polygon rings in {layer}.")
            json.dumps(geometry, allow_nan=False)
            row["geometry"] = geometry
            rows.append(row)
    return rows


def relationship_counts(parcels, buildings):
    codes = {row["codigo"] for row in parcels}
    parents = {row["terreno_codigo"] for row in buildings}
    if len(codes) != len(parcels) or not parents <= codes:
        raise ValueError("Duplicate parcel code or building without a parent parcel.")
    return len(parcels), len(buildings), len(parents), len(codes - parents)


def validate_run(run_dir):
    summary = read_json(run_dir / "complete.json")
    snapshot = {
        "source_run_id": run_dir.name,
        "release_date": date.fromisoformat(summary["release_date"]),
        "fetched_at": datetime.fromisoformat(summary["fetched_at_utc"]),
        "municipality_code": summary["municipality_code"],
        "land_layer_url": summary["land_layer_url"],
        "building_layer_url": summary["building_layer_url"],
        "geometry_srid": 3857,
    }
    if not (
        valid_code(snapshot["municipality_code"], 5)
        and snapshot["fetched_at"].utcoffset() is not None
        and snapshot["source_run_id"].strip()
        and all(isinstance(snapshot[key], str) and snapshot[key].strip()
                for key in ("land_layer_url", "building_layer_url"))
    ):
        raise ValueError("Invalid snapshot metadata.")
    parcels = read_layer(run_dir, "land", PARCEL_FIELDS, snapshot["municipality_code"])
    buildings = read_layer(run_dir, "buildings", BUILDING_FIELDS, snapshot["municipality_code"])
    counts = relationship_counts(parcels, buildings)
    expected = tuple(summary[key] for key in (
        "distinct_valid_land", "related_buildings", "parcels_with_buildings",
        "parcels_without_building_matches",
    ))
    if counts != expected:
        raise ValueError("Saved record or relationship counts differ from complete.json.")
    return snapshot, parcels, buildings, counts


def upsert(cursor, table, keys, rows):
    from psycopg import sql

    if not rows:
        return 0
    columns = tuple(rows[0])
    changed = [sql.Identifier(column) for column in columns if column not in keys]
    join = sql.SQL(", ").join
    statement = sql.SQL("""
        INSERT INTO {} AS existing ({}) VALUES ({})
        ON CONFLICT ({}) DO UPDATE SET {}, last_updated_at = now()
        WHERE ROW({}) IS DISTINCT FROM ROW({})
    """).format(
        sql.Identifier("igac", table),
        join(map(sql.Identifier, columns)),
        join(sql.Placeholder() for _ in columns),
        join(map(sql.Identifier, keys)),
        join(sql.SQL("{} = excluded.{}").format(col, col) for col in changed),
        join(sql.SQL("existing.{}").format(col) for col in changed),
        join(sql.SQL("excluded.{}").format(col) for col in changed),
    )
    cursor.executemany(statement, [tuple(row[column] for column in columns) for row in rows])
    return cursor.rowcount


def load(snapshot, parcels, buildings, counts):
    import psycopg
    from dotenv import dotenv_values
    from psycopg.types.json import Jsonb

    settings = dotenv_values(Path(__file__).resolve().parents[1] / ".env", interpolate=False)
    url = os.environ.get("IGAC_LOADER_DATABASE_URL") or settings.get("IGAC_LOADER_DATABASE_URL")
    if not url:
        raise RuntimeError("Set IGAC_LOADER_DATABASE_URL for the dedicated loader login.")

    with psycopg.connect(url, connect_timeout=10) as connection, connection.cursor() as cursor:
        snapshot_changes = upsert(cursor, "cadastral_snapshots", ("source_run_id",), [snapshot])
        # Serialize imports of the same run until this transaction finishes.
        cursor.execute(
            "SELECT snapshot_id FROM igac.cadastral_snapshots WHERE source_run_id = %s FOR UPDATE",
            (snapshot["source_run_id"],),
        )
        snapshot_id = cursor.fetchone()[0]
        upsert_key = ("snapshot_id", "object_id")
        changes = [snapshot_changes]
        for table, rows in (("parcels", parcels), ("buildings", buildings)):
            incoming = [
                {**row, "snapshot_id": snapshot_id, "geometry": Jsonb(row["geometry"])}
                for row in rows
            ]
            changes.append(upsert(cursor, table, upsert_key, incoming))

        cursor.execute("""
            SELECT count(*), coalesce(sum(building_count), 0),
                   count(*) FILTER (WHERE building_count > 0),
                   count(*) FILTER (WHERE building_count = 0)
            FROM (
                SELECT p.parcel_id, count(b.building_id) AS building_count
                FROM igac.parcels AS p
                LEFT JOIN igac.buildings AS b
                    ON b.snapshot_id = p.snapshot_id AND b.terreno_codigo = p.codigo
                WHERE p.snapshot_id = %s
                GROUP BY p.parcel_id
            ) AS per_parcel
        """, (snapshot_id,))
        if cursor.fetchone() != counts:
            raise RuntimeError("Database counts differ from the saved run.")
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="Folder containing complete.json and saved pages")
    parser.add_argument("--validate-only", action="store_true", help="Check files without connecting")
    args = parser.parse_args()
    try:
        snapshot, parcels, buildings, counts = validate_run(args.run_dir.resolve())
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        parser.exit(1, "Saved run validation failed. Check the run folder, page metadata, and records.\n")

    parcel_count, building_count, matched, unmatched = counts
    print(f"Validated {parcel_count} parcels and {building_count} buildings in EPSG:3857.")
    print(f"Parcels with building matches: {matched}. No building match returned: {unmatched}.")
    if args.validate_only:
        return
    try:
        changes = load(snapshot, parcels, buildings, counts)
    except Exception:
        parser.exit(1, "Load failed. Check the loader login, access, and the destination tables.\n")
    for label, changed, total in zip(("Snapshots", "Parcels", "Buildings"), changes, (1, *counts[:2])):
        print(f"{label}: {changed} inserted or updated, {total - changed} unchanged.")


if __name__ == "__main__":
    main()
