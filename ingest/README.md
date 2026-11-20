# ingest/

Code that moves data from your API into your database. You build it with your AI agent, one piece per week:

| Week | File | What it does |
|---|---|---|
| 1 | `fetch.py` | Calls your API: authentication, pagination, rate limits, retries. Saves raw JSON to `data/raw/`. |
| 2 | `load.py` | Turns the raw JSON into rows in your tables, using parameterized queries. Running it twice must not create duplicates. |
| 3 | `sync.py` | Combines fetch and load into one incremental, idempotent sync that GitHub Actions runs on a schedule and records in `sync_runs`. |

The loader and proposed sync use the limited `igac_loader` login through
`IGAC_LOADER_DATABASE_URL`. Schema setup and migrations require the setup role;
the scheduled job must not run migrations or use owner credentials.

## Milestone 3 sync (live manual test verified; GitHub execution pending)

After separately reviewing and applying `db/migrations/003_sync_runs.sql` to the
existing Milestone 2 database, run from the project root:

```sh
python ingest/sync.py
```

This command makes public API requests and writes to the database. It requires
explicit approval during development. It reads `IGAC_LOADER_DATABASE_URL` from
the environment or this worktree's ignored `.env`; it does not automatically
read secrets from another worktree. No existing credentials were copied.

### Source and comparison policy

Public metadata inspection on November 19, 2026 found no per-record edit-date
fields or advertised change tracking on either layer. The service reports
`syncEnabled: false` and editor tracking disabled. Layer-level edit timestamps
cannot identify individual inserts, changes, or deletions. Consequently this is
a bounded re-fetch with content comparison, not record-level incremental fetching.
[Land metadata](https://services2.arcgis.com/RVvWzU3lgJISqdke/ArcGIS/rest/services/CATASTRO_PUBLICO_31082026/FeatureServer/7?f=pjson)
· [Building metadata](https://services2.arcgis.com/RVvWzU3lgJISqdke/ArcGIS/rest/services/CATASTRO_PUBLICO_31082026/FeatureServer/3?f=pjson)
· [Service metadata](https://services2.arcgis.com/RVvWzU3lgJISqdke/ArcGIS/rest/services/CATASTRO_PUBLICO_31082026/FeatureServer?f=pjson)

The sync uses the existing selection: the first 500 valid Pasto parcels in
OBJECTID order and their returned related buildings. Membership can change;
this is not full-city coverage. A successful run must validate exactly 500
parcels, but building counts may change. Incomplete requests or invalid records
fail the run instead of being interpreted as source deletions.

Both layers' metadata is compared before and after downloading. Reported
changes cause failure. This is a useful safeguard, not a guarantee of an atomic
source snapshot. Retrieval has a 250-request budget, a 20-minute deadline
checked before each request, per-request timeouts, and bounded retry waits.
The final request or wait can extend beyond that deadline, so Actions also
needs an overall job timeout. Temporary raw files are removed after processing.

A SHA-256 comparison includes release, source URLs, municipality, SRID, and
all attributes and geometry that the existing loader stores. Other API fields
are outside this comparison. Record order and download timestamps are excluded;
integral float/int representations are normalized. Geometry coordinate ordering
is preserved, so reordered rings can create a distinct content version.

The sync compares against compatible existing snapshots, including the original
Milestone 2 snapshot. Matching content reuses its snapshot without touching its
rows or audit timestamps. Distinct content creates a new historical snapshot
with a deterministic content-version run ID. No historical rows are deleted.
An unexpected mismatch under an existing content-version ID fails for review.

The existing parameterized UPSERT helper loads new versions. Normal sync does
not overwrite historical versions: changed source records are stored in a new
snapshot, so run counts report inserted rows, zero in-place updates, and
unchanged rows for reused snapshots. These are database write counts, not counts
of source edits between versions. Snapshot creation is recorded separately.
The Milestone 2 loader's changed-row UPDATE behavior remains unchanged.

### Transactions, logging, and automation

`igac.sync_runs` starts with a committed `running` entry. A transaction-level
advisory lock serializes this sync's comparison and import. The import, final
content/relationship verification, and success log commit together. Failures
roll back the import, then attempt to log only a fixed error category in a
separate transaction. No raw errors, credentials, or records are printed.
If the database is unavailable, logging may fail; a killed job can leave a
`running` entry. Reconcile these cases before retrying, especially after an
uncertain commit acknowledgement. Other writers must respect this sync's
immutability policy; the advisory lock does not lock out unrelated tools.

`records_fetched` counts validated parcel and building records on successful
runs. Failed runs currently leave record counters at zero, meaning no committed
source-row writes; they do not measure partial downloads. Trigger types are
`local`, `manual` (`workflow_dispatch`), and `scheduled` (`schedule`). GitHub run
ID and attempt are recorded when provided. Success exits 0; failures exit 1.

The migration grants SELECT on the run table to `app_reader`, and SELECT,
INSERT, and limited status/count UPDATE permissions to `igac_loader`. It adds
no DELETE, TRUNCATE, schema-creation, or sequence grants. Apply it once after
the Milestone 2 roles exist; do not rerun the fresh-setup schema or role scripts.
The runtime does not apply migrations.

The GitHub Actions workflow has been created locally in
`.github/workflows/sync.yml`. It schedules a run every six hours, supports a
manual trigger, and includes Python 3.12, pinned dependencies, concurrency
control, and a 35-minute job timeout. It uses only the
`IGAC_LOADER_DATABASE_URL` Actions secret and runs only on `main`. It has not
yet run on GitHub. Antonia has configured the `IGAC_LOADER_DATABASE_URL`
repository secret in GitHub. GitHub execution and successful scheduled runs
spanning at least 48 hours remain pending.

### Verified live manual test

An initial live test failed with the safe category `validation`. Read-only
investigation reproduced numeric precision loss when PostgreSQL returned
area and perimeter values in text format with `extra_float_digits = 0`.
Binary reads exactly matched the saved originals. The storage transaction now
uses `connection.cursor(binary=True)` to preserve numeric precision without
rounding values or changing database settings. A regression test checks this
cursor configuration; all ten offline tests passed.

The corrected live sync then succeeded in one approved manual attempt. The
`sync_runs` entry recorded **1,718 fetched, 0 inserted, 0 updated, and 1,718
unchanged**. Existing snapshot 1 was reused, and the database still contained
1 snapshot, 500 parcels, and 1,218 buildings. Before-and-after comparisons
confirmed that all existing source records and audit timestamps were unchanged.
The data/success-log transaction committed, and the read-only verification
transactions rolled back safely. This local manual test does not count toward
the scheduled GitHub Actions evidence.

The source release remains August 31, 2026. A successful scheduled run means
"checked successfully," not "source data is current." New release endpoints
require separate validation. Manizales coverage and IGAC reuse terms remain
unresolved; raw data must not be published as Actions artifacts.
