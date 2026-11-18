# Milestone 2 Implementation Brief

## Purpose

The database supports the Pasto mapping pilot for the construction machinery project. It uses a saved download of IGAC's August 31, 2026 release to show how parcel records and building records connect. The SQL questions build on the baseline decisions about whether to use the Pasto data and what the download can show on a map. [Baseline log](baseline_log.md)

## Database design

Supabase contains three related tables in the dedicated `igac` schema. `cadastral_snapshots` records the source and date of each saved download. `parcels` stores the land records for a snapshot. `buildings` links each building to a parcel in the same snapshot using the parcel code. A parcel can have several building records or have no building match returned.

Each table has a generated primary key. Source `OBJECTID` values are unique within each layer and snapshot. Building cadastral codes can repeat, so separate records with the same code are kept. Polygon geometry is stored as ArcGIS JSON, and the snapshot records EPSG:3857. Each table records when a row was first inserted and when it was last updated. [Schema and ER diagram](schema.md)

## Ingestion and repeat-load test

The loader reads the saved JSON pages and checks their counts, source IDs, cadastral codes, municipality, parcel links, and coordinate system before connecting to the database. It recognizes the saved ArcGIS spatial reference of `wkid` 102100 with `latestWkid` 3857 as EPSG:3857.

The loader uses parameterized SQL and writes the snapshot, parcels, and buildings in that order in one transaction. It checks the database counts and relationships before committing. The first load produced **1 snapshot, 500 parcels, and 1,218 buildings**. All 1,218 buildings linked to a parcel in the same snapshot.

I verified idempotency by running the loader again with the same files. It reported every row unchanged. There were zero new or updated rows, and the before-and-after comparison showed identical record IDs and identical `first_seen_at` and `last_updated_at` timestamps. [Loader](../ingest/load.py)

## Fresh-environment local validation

A new `.venv` in the Milestone 2 worktree uses Python 3.12.10, and the installed package versions match `requirements.txt`. Running the loader with `--validate-only` in that environment successfully checked the existing saved files as read-only input. It verified 500 parcels and 1,218 buildings, valid required identifiers, unique source `OBJECTID`s within each layer, and valid parcel-building relationships. There were 422 parcels with building matches and 78 without returned building matches. Every page passed the EPSG:3857 check, including the saved `wkid` 102100 with `latestWkid` 3857. This local test made no database connection.

A full clean-start database test remains pending. In a separate empty test environment, that test would apply the schema and role scripts, configure private credentials, verify both role connections and effective permissions, run the first import and an identical repeat import, compare record IDs and audit timestamps, and run the five SQL queries as `app_reader`. The existing Supabase installation has already passed schema and permission verification, both role connection checks, the import and idempotency checks, and execution of the five queries. The remaining test checks whether the documented setup can reproduce those results from an empty database.

## Five SQL questions and verified results

All five queries ran successfully in a read-only Supabase transaction.

| Question | Verified result |
|---|---|
| Which municipality and release did the November 2026 download cover? | The time filter returned Pasto (`52001`), using the August 31, 2026 release downloaded on November 9, 2026. |
| How many building records did IGAC return for each parcel? | The query returned all 500 parcels and counted 1,218 building records across them. The highest count for one parcel was 21. |
| How many parcels had a returned building match? | 422 parcels had at least one returned match, and 78 had none. The vacancy status of those 78 parcels is unknown. |
| How many building records would the map omit if it kept one row per building code? | The surprising result was that 325 building codes repeated. Keeping one row per code would omit 796 records with distinct source IDs. |
| Which construction categories can the pilot display for matched Pasto parcels? | The records included 995 marked `CONVENCIONAL` and 223 marked `NO CONVENCIONAL`. |

[SQL queries](../db/queries.sql) · [Data quality findings](data_quality.md)

## Access permissions

The setup role owns the schema. The dedicated `igac_loader` role connects directly to PostgreSQL and can read and insert rows in the three tables and update selected columns. Permission checks confirmed that it cannot delete or truncate rows or create permanent tables. The checks found no access to unrelated application tables, views, sequences, or routines. The shared `PUBLIC TEMPORARY` grant still permits temporary tables. The Supabase Data API is disabled. [Verified access roles](schema.md#access-roles)

The separate `app_reader` login has `USAGE` on `igac` and `SELECT` on the three tables. Effective permission checks confirmed it cannot insert, update, delete, truncate, or create permanent database objects, and found no access to unrelated application data, application sequences, or routines. A direct connection using `APP_DATABASE_URL` succeeded. In a read-only transaction, it counted 1 snapshot, 500 parcels, and 1,218 buildings. Its connection string is stored in the ignored local `.env` file.

## Remaining limits

- **Manizales coverage.** The saved run covers Pasto. Map coverage and current site conditions for Manizales job sites remain unverified. The equipment maintenance decision requires the business's own hour-meter readings, service history, and maintenance intervals.
- **IGAC reuse terms.** The release metadata and national open-data listing show different license terms. Which terms apply to these layers remains unresolved. [Data dictionary and source references](data_dictionary.md#ethical-use-and-attribution)
