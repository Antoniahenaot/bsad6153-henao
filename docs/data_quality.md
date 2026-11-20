# Milestone 3 Part E: Data Quality Report

## Scope and measurement method

Codex executed the approved checks as `app_reader` in a read-only, repeatable-read transaction, then rolled it back. All quality measurements in the tables below come from **2026-11-20 at 03:46:01.984637 UTC**. Every measurement-date entry refers to that exact timestamp. All sixteen result queries succeeded. [SQL checks](../db/quality_checks.sql)

This report updates the earlier saved-file analysis with database measurements. The stored source run is `20261109T062536Z-9fp_q80e`, for the IGAC August 31, 2026 release. Database counts agree with the earlier parcel-building findings. Database checks cannot establish whether an API field was absent or explicitly null before loading. [Snapshot metadata query](../db/quality_checks.sql#L23) · [Data dictionary](data_dictionary.md)

## Row counts and historical scope

| Table | Measured rows | Measurement date (UTC) | SQL reference |
|---|---:|---|---|
| `igac.cadastral_snapshots` | 1 | 2026-11-20 | [Table counts](../db/quality_checks.sql#L12) |
| `igac.parcels` | 500 | 2026-11-20 | [Table counts](../db/quality_checks.sql#L12) |
| `igac.buildings` | 1,218 | 2026-11-20 | [Table counts](../db/quality_checks.sql#L12) |
| `igac.sync_runs` | 3 | 2026-11-20 | [Table counts](../db/quality_checks.sql#L12) |

The per-snapshot query returned snapshot `1`, containing the parcel and building counts above (measured 2026-11-20). [Snapshot counts](../db/quality_checks.sql#L23)

The sync preserves historical content versions. Repeated source IDs across different snapshots are therefore not automatically duplicate records. Source duplicate checks below are scoped within each snapshot; total physical row counts must not be presented as unique geographic coverage.

## Null and blank rates

| Field scope | Measured result | Measurement date (UTC) | SQL reference |
|---|---|---|---|
| Parcel `department_code` | 500/500 null; 100.00% | 2026-11-20 | [Field rates](../db/quality_checks.sql#L33) |
| Other parcel and building fields checked | 0 null values and 0 blank strings; 0.00% for each field | 2026-11-20 | [Field rates](../db/quality_checks.sql#L33) |
| Snapshot fields checked | 0 null values and 0 blank strings; 0.00% for each field | 2026-11-20 | [Field rates](../db/quality_checks.sql#L33) |
| All checked fields, including run logs | 0 blank strings | 2026-11-20 | [Field rates](../db/quality_checks.sql#L33) |
| Failed-run `snapshot_id`, content hash, GitHub run ID, and attempt | Each null in 1/1 failed run; 100.00% | 2026-11-20 | [Field rates](../db/quality_checks.sql#L33) |
| Successful-run `error_category` | Null in 2/2 successful runs; 100.00% | 2026-11-20 | [Field rates](../db/quality_checks.sql#L33) |
| Successful-run GitHub run ID and attempt | Each null in 1/2 successful runs; 50.00% | 2026-11-20 | [Field rates](../db/quality_checks.sql#L33) |

The missing department code limits analyses that need that field. It remains nullable rather than being invented from another field. Run-log nulls have different meanings: successful runs have no error category, locally executed runs have no GitHub identifiers, and a failed import may have no completed snapshot or hash. These nulls are not automatically data-quality defects.

## Duplicates and preservation

| Check | Measured result | Measurement date (UTC) | SQL reference |
|---|---|---|---|
| Parcel `OBJECTID` and parcel `CODIGO`, within snapshot | 0 duplicate groups and 0 excess rows | 2026-11-20 | [Natural-ID checks](../db/quality_checks.sql#L62) |
| Building `OBJECTID`, within snapshot | 0 duplicate groups and 0 excess rows | 2026-11-20 | [Natural-ID checks](../db/quality_checks.sql#L62) |
| Snapshot `source_run_id` and operational `run_id` | 0 duplicate groups and 0 excess rows | 2026-11-20 | [ID checks](../db/quality_checks.sql#L62) |
| Building `CODIGO` | 422 distinct codes; 325 codes associated with multiple source IDs | 2026-11-20 | [Repeated-code check](../db/quality_checks.sql#L91) |
| Keeping only one row per building code | Would omit 796 stored records | 2026-11-20 | [Repeated-code check](../db/quality_checks.sql#L91) |
| Different-ID, identical stored-payload candidates | 0 groups and 0 excess rows in each source table | 2026-11-20 | [Payload check](../db/quality_checks.sql#L107) |

Building codes are not unique record identifiers. Multiple building records can belong to a parcel, and records sharing codes can differ in construction category or geometry. Preserve their distinct source `OBJECTID` values. Repeated codes alone do not justify removing records.

The different-ID check compares all stored source fields and exact geometry, excluding source/internal IDs, snapshot linkage, and audit timestamps. It cannot detect all spatially similar duplicates, and attributes not stored in the database could distinguish candidate records. Any future candidates require review before deletion.

## Invalid values, measurements, and geometry

| Check | Measured result | Measurement date (UTC) | SQL reference |
|---|---|---|---|
| Invalid source IDs, cadastral codes, or building parent codes | 0 in each applicable source table | 2026-11-20 | [Identifier checks](../db/quality_checks.sql#L139) |
| Missing construction categories | 0 building records | 2026-11-20 | [Category check](../db/quality_checks.sql#L139) |
| Missing geometry or malformed/empty ring containers | 0 in each source table | 2026-11-20 | [Geometry-container check](../db/quality_checks.sql#L139) |
| Missing, nonfinite, or nonpositive finite area/perimeter values | 0 for each measurement in each source table | 2026-11-20 | [Measurement checks](../db/quality_checks.sql#L167) |
| Missing, reversed, or future audit timestamps | 0 in every table | 2026-11-20 | [Audit checks](../db/quality_checks.sql#L190) |
| Invalid SRID, malformed municipality code, future source/fetch dates, or release after fetch | 0 for each check | 2026-11-20 | [Snapshot checks](../db/quality_checks.sql#L210) |

Observed ranges below are rounded to six decimal places. They are descriptive ranges, not verified accuracy limits or grounds for automatic rejection.

| Stored measurement | Minimum | Maximum | Measurement date (UTC) | SQL reference |
|---|---:|---:|---|---|
| Parcel area | 0.934204 | 25,910.875610 | 2026-11-20 | [Ranges](../db/quality_checks.sql#L167) |
| Parcel perimeter | 4.688048 | 1,357.695290 | 2026-11-20 | [Ranges](../db/quality_checks.sql#L167) |
| Building area | 0.172607 | 1,630.558228 | 2026-11-20 | [Ranges](../db/quality_checks.sql#L167) |
| Building perimeter | 2.009926 | 346.900394 | 2026-11-20 | [Ranges](../db/quality_checks.sql#L167) |

The coordinate reference is documented as EPSG:3857. The reported area/perimeter units, ground accuracy, and suitability for machinery access or site planning remain unverified. These SQL checks inspect ring containers, not polygon topology, ring closure, self-intersection, or real-world location. No spatial-validity claim is made.

## Relationships and construction categories

| Check | Measured result | Measurement date (UTC) | SQL reference |
|---|---|---|---|
| Parcels without a snapshot | 0 | 2026-11-20 | [Orphan checks](../db/quality_checks.sql#L220) |
| Buildings without a matching parcel or snapshot | 0 for each check | 2026-11-20 | [Orphan checks](../db/quality_checks.sql#L220) |
| Non-null run snapshot references without a snapshot | 0 | 2026-11-20 | [Orphan checks](../db/quality_checks.sql#L220) |
| Parcels with returned building matches | 422 | 2026-11-20 | [Match counts](../db/quality_checks.sql#L241) |
| Parcels without returned building matches | 78/500; 15.60% | 2026-11-20 | [Match counts](../db/quality_checks.sql#L241) |
| Returned buildings | 1,218 | 2026-11-20 | [Match counts](../db/quality_checks.sql#L241) |
| `CONVENCIONAL` | 995 buildings; 81.69% | 2026-11-20 | [Category distribution](../db/quality_checks.sql#L260) |
| `NO CONVENCIONAL` | 223 buildings; 18.31% | 2026-11-20 | [Category distribution](../db/quality_checks.sql#L260) |

The unmatched parcels cannot be classified as vacant. The result means only that the query returned no associated building record for those parcels in this release and selected sample. It does not establish current occupancy, land use, complete source coverage, or suitability for construction machinery. The foreign key and unique parcel key enforce a single valid parent match for each stored building.

## Geographic fairness and representation

| Check | Measured result | Measurement date (UTC) | SQL reference |
|---|---|---|---|
| Snapshot geography | Pasto (`52001`); 500 parcels and 1,218 buildings; 100.00% Pasto share for each layer | 2026-11-20 | [Geographic coverage](../db/quality_checks.sql#L268) |
| Represented block codes | 134 | 2026-11-20 | [Block-level result rows](../db/quality_checks.sql#L290) |
| Blocks containing unmatched parcels | 33 | 2026-11-20 | [Block rows with unmatched count above zero](../db/quality_checks.sql#L290) |
| Missing block codes | 0 | 2026-11-20 | [Block-level checks](../db/quality_checks.sql#L290) |
| Block `52001010300000150` | 8/35 parcels unmatched; 22.86% | 2026-11-20 | [Block-level checks](../db/quality_checks.sql#L290) |
| Block `52001010400000544` | 16/18 parcels unmatched; 88.89% | 2026-11-20 | [Block-level checks](../db/quality_checks.sql#L290) |

The block totals are derived by counting the returned block groups and groups with unmatched parcels. The examples show different returned-match rates within the selected pilot; they do not prove that a block is less developed or that IGAC treats residents unfairly. Small group sizes and incomplete source coverage limit comparisons.

Municipality coverage here comes from snapshot metadata; ingestion separately checked the source municipality field. This SQL does not independently locate the polygons. Selection uses the first valid Pasto parcels in source-ID order, not a random or representative sample. It therefore cannot support conclusions about all of Pasto, Manizales, or Colombia.

The business operates in Manizales. A feature that appears useful on the Pasto pilot may exclude or mislead its actual users if Manizales coverage is assumed. Recommended action: label the pilot geography, release date, and unknown coverage clearly; verify relevant Manizales job-site coverage before operational use. This recommendation has not been validated through a cross-city accuracy study. Maintenance decisions still require the business's readings and service records.

## Sync history and operational interpretation

| Check | Measured result | Measurement date (UTC) | SQL reference |
|---|---|---|---|
| Successful manual syncs | 2 | 2026-11-20 | [Run summary](../db/quality_checks.sql#L311) |
| Failed manual syncs | 1 | 2026-11-20 | [Run summary](../db/quality_checks.sql#L311) |
| Scheduled sync entries returned | 0; no scheduled group returned | 2026-11-20 | [Run summary](../db/quality_checks.sql#L311) |
| Reversed run times, inconsistent states, or negative counters | 0 for each check | 2026-11-20 | [Run consistency](../db/quality_checks.sql#L311) |

This history is a measurement-time snapshot, not a claim about later executions. A failed run's zero counters do not measure partial downloads. Successful checks against a dated release do not prove current cadastral conditions. Scheduled-run evidence must be assessed separately from these quality findings.

## Cleaning, rejection, and preservation decisions

**Implemented behavior:**

- The loader validates required source IDs and codes, municipality, coordinate reference, polygon-ring presence, finite measurements, and parcel-building relationships. The sync rejects invalid/skipped-record summaries or inconsistent counts rather than silently importing a partial sample.
- Database keys and constraints reject conflicting identities and broken relationships. These stored-data checks do not measure how many source records were rejected before loading.
- Department-code nulls remain null. The pipeline does not invent department values or automatically impute missing source information.
- Distinct building source IDs, unmatched parcels, source geometry, and historical content versions are preserved. No quality-check query cleans or deletes data.
- Content comparison excludes download/audit metadata and normalizes integral numeric representations for comparison. Binary database reads preserve numeric precision; they do not round or change stored source values.
- Identical content reuses its snapshot; a changed version is stored separately. Validation and verification protect the transaction from a partial source import.

**Recommendations, not completed cleaning:** review future duplicate candidates, nonpositive measurements, unusual observed values, or questionable geometry with the source before changing records. The loader checks finite measurements but does not currently reject every nonpositive value. Do not invent a size threshold or infer vacancy from a missing match. Validate geometry and measurement meaning before relying on the map for operational decisions.

IGAC reuse terms remain unresolved. Confirm the applicable terms before public map display or data redistribution. Keep private machinery, worker, and customer information separate from the public mapping pilot. [Source and licensing references](data_dictionary.md#ethical-use-and-attribution)

## Freshness, monitoring, and ownership

### Source age versus pipeline activity

The source release is **August 31, 2026**, as recorded in snapshot metadata measured on November 20, 2026. Its download timestamp is not its release date. Rechecking that endpoint cannot establish current site conditions or confirm a newer release. The earlier quality tables are fixed measurement-time evidence, not continuously updated totals. [Snapshot query](../db/quality_checks.sql#L23)

The implemented [workflow](../.github/workflows/sync.yml) requests synchronization every six hours at **00:23, 06:23, 12:23, and 18:23 UTC**, with cron `23 */6 * * *`, on `main`. It also supports manual execution, queues overlapping workflow executions, and has a 35-minute job timeout. This is the configured cadence, not a guaranteed service level; API failures, runner delays, connection problems, or timeouts can prevent a check from completing.

A live GitHub manual execution was verified successful on **November 20, 2026**, with database completion time **03:33:58.839213 UTC**. [Verified Actions run](https://github.com/Antoniahenaot/bsad6153-henao/actions/runs/44668476841)

Later controlled tests replayed saved data rather than fetching the API. Their successful log timestamps must not be presented as evidence of a fresh IGAC download. `trigger_type` distinguishes local, manual, and scheduled executions, but it does not independently identify every replay: consult the test evidence as well. The follow-up golden-question evaluation completed successfully after three successful scheduled syncs on November 20, 2026: 12 SQL references passed, none failed, and four decline questions were skipped. The recorded scheduled starts span 11 hours, 44 minutes, 25 seconds; evidence spanning at least 48 hours remains pending. [Test procedures and pending work](sync_tests.md)

### Implemented monitoring and known gaps

`igac.sync_runs` records execution status, timestamps, trigger, source release, snapshot reference, content fingerprint, record counts, safe error category, and GitHub identifiers when available. This allows the project maintainer to trace successes and failures and distinguish a new historical snapshot from reuse of unchanged content. The sync commits source changes and its success update together; failed imports roll back before separate failure logging is attempted. [Run-log definition](../db/migrations/003_sync_runs.sql) · [Lineage](data_dictionary.md#lineage-and-database-mapping)

The interrupted test entry `254f3825-7f3d-4e8a-8f77-13ab2ded58ae` remained `running` after its child process stopped on November 20, 2026. Recovery succeeded under a separate run ID without repairing that entry. It must not be counted as an active process merely because its status is `running`. A database outage can also prevent failure logging. The current implementation has no automatic abandoned-run reconciliation or project-specific alerting service. [Observed interruption and recovery](sync_tests.md#test-2-controlled-interruption-and-recovery)

The freshness banner now queries `igac.sync_runs` and snapshot release metadata through a verified `app_reader` connection in a read-only transaction. It distinguishes the latest successful GitHub sync check from the IGAC source release and excludes local test replays from live-check freshness. Ten mocked checks and a live Streamlit AppTest passed, including stale/error handling and separate check-time and source-release messages. These tests do not establish that the dated source reflects current site conditions.

### Supabase Data API verification

On November 20, 2026, Antonia manually verified Supabase project `bsad6153-milestone-2` under Integrations → Data API. `Enable Data API` was OFF, and the Dashboard displayed "No schemas can be queried." This is Antonia's Dashboard verification, not an inference from a successful database connection.

### Ownership and response decisions

| Responsibility | Accountable person or organization | Current boundary |
|---|---|---|
| Published cadastral records and release metadata | IGAC, as source publisher | The project cannot correct IGAC's upstream records or promise their completeness. |
| Pilot ingestion, quality evidence, and operational review | Antonia, as project maintainer | Antonia reviews results and authorizes corrections. Codex helps implement and verify approved steps; it is not the accountable data owner. |
| Project access and spending | Antonia during the pilot | Keep credentials private and use the approved limited roles. |
| Machinery readings, service evidence, and maintenance decisions | Antonia's dad, with operators supplying records | Business records are separate from IGAC; maintenance conclusions require his review and approval. |

**Recommended operating procedure, not verified ongoing practice:** Antonia should review scheduled outcomes and source age, investigate failures or unexpectedly old successful checks, and compare material count or coverage changes before accepting them for operational use. Preserve the previous verified snapshot when an import fails. Do not impute source values, remove repeated codes, or reconcile abandoned log entries without review. Confirm a suitable freshness threshold with the intended user; no tested freshness guarantee or response-time commitment is established here.

**Planned improvements:** complete scheduled-run evidence spanning at least 48 hours; define and test abandoned-run detection, alerting, and reconciliation; and validate new-release discovery before changing source endpoints. These remain pending controls; the follow-up reference evaluation and freshness-display implementation and testing are complete. Missing department codes, limited coverage, geometry validity, measurement meaning, and reuse terms remain the limitations described above.
