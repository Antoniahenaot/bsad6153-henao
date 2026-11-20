# Milestone 1 Data Dictionary

## Source and scope

**Provisional source:** Instituto Geográfico Agustín Codazzi (IGAC), Pasto, Colombia. Both the API and the pilot city are pending instructor approval.

The fetch used the August 31, 2026 release and filtered both layers to Pasto (`52001`). The land layer is `U_TERRENO` (layer 7), and the building layer is `U_CONSTRUCCION` (layer 3). These layers give the equipment management project map context for job sites. Machine hours, maintenance, and equipment assignments come from the business's own records.

The **full saved run** contained 500 distinct valid land records and 1,218 related building records. Of the 500 parcels, 422 had at least one building match and 78 had no match returned. The **field examples and sample observations** below come from inspecting six saved land records and six saved building records. The 12-record inspection does not establish how common a field value or missing value is across the full dataset.

Sources: [IGAC service directory](https://services2.arcgis.com/RVvWzU3lgJISqdke/ArcGIS/rest/services/CATASTRO_PUBLICO_31082026/FeatureServer) and [official layer schemas](https://services2.arcgis.com/RVvWzU3lgJISqdke/ArcGIS/rest/services/CATASTRO_PUBLICO_31082026/FeatureServer/layers).

## Fields

The tables cover 15 attributes across the two layers. “Nullable” means the published schema allows the field to have a JSON `null` value. A field can be present with a `null` value or absent from a response, so the fetch checks required identifiers before counting a record. All listed attribute keys were present in the 12 inspected records. Numeric examples are rounded for readability.

### Urban land

| Field | Type | Meaning | Saved example | Nullable? |
|---|---|---|---|---|
| `OBJECTID` | Integer ID | Identifies a row in the land layer for this release. | `3282148` | No |
| `CODIGO` | Text | Current 30-digit cadastral parcel code. | `520010103000003330005000000000` | No |
| `MANZANA_CODIGO` | Text | Code for the city block containing the parcel. | `52001010300000333` | Yes |
| `CODIGO_ANTERIOR` | Text | Previous cadastral code for the parcel. | `52001010303330005000` | Yes |
| `codigo_municipio` | Text | Municipality code. The fetch uses it to select Pasto. | `52001` | Yes |
| `CODIGO_DEPARTAMENTO` | Text | Department code. | `null` | Yes |
| `Shape__Area` | Decimal number | Area value reported for the parcel polygon. | `1392.0516` | Yes |
| `Shape__Length` | Decimal number | Boundary length reported for the parcel polygon. | `150.1138` | Yes |

### Urban buildings

| Field | Type | Meaning | Saved example | Nullable? |
|---|---|---|---|---|
| `OBJECTID` | Integer ID | Identifies a row in the building layer for this release. | `5376636` | No |
| `CODIGO` | Text | Cadastral code recorded on the building row. | `520010103000000230901901000000` | No |
| `TERRENO_CODIGO` | Text | Parcel code used to match the building to the land layer. | `520010103000000230901900000000` | Yes |
| `TIPO_CONSTRUCCION` | Text | IGAC's construction category. | `CONVENCIONAL` | No |
| `codigo_municipio` | Text | Municipality code. The fetch uses it to select Pasto. | `52001` | Yes |
| `Shape__Area` | Decimal number | Area value reported for the building footprint. | `135.6149` | Yes |
| `Shape__Length` | Decimal number | Boundary length reported for the building footprint. | `56.0482` | Yes |

The API returns `geometry` separately from the attributes. All 12 inspected records had polygon geometry, and both sample pages reported Web Mercator (EPSG:3857). The project can use the polygons to draw the parcel boundaries and building footprints. The units of the reported area and length values and the survey accuracy of the shapes have not been verified.

## Record IDs and relationships

Use `OBJECTID` to identify a row within its layer and release and to order pages during a fetch. Keep cadastral codes as text so all digits, including any leading zeros, are preserved.

Match a building's `TERRENO_CODIGO` to the land layer's `CODIGO`. One parcel can have several building rows. A building row with a missing or invalid parcel code cannot be matched by this method. Keep unmatched parcels in the land data and report the number without a building match separately.

## Verified data surprises

1. **A building can have a different code from its parcel.** In the inspected sample, building `5376636` had `CODIGO` ending in `901000000` and `TERRENO_CODIGO` ending in `900000000`. The two fields serve different purposes in the match.
2. **Two building rows can share the same cadastral codes.** In the inspected sample, buildings `5376670` and `5376714` shared both `CODIGO` and `TERRENO_CODIGO`. One was `CONVENCIONAL` and the other was `NO CONVENCIONAL`. Treating building `CODIGO` as a unique row ID would drop a record.
3. **The department field can be present but empty.** All six inspected land rows had `codigo_municipio = "52001"` and `CODIGO_DEPARTAMENTO = null`. The department field is therefore unsuitable as a required field for this sample.
4. **Some parcels had no building match.** In the full run, 78 of 500 parcels had no building match returned by the queried layer. Their vacancy status is unknown.

## Lineage and database mapping

The implemented flow is:

`IGAC layer queries → paginated responses → validation → content comparison → igac tables → read-only SQL reports`

The public source is the dated IGAC service linked above, not a machinery-maintenance API. Requests select Pasto and order parcels by `OBJECTID`; the bounded pilot selects the first valid parcels up to the configured target. Buildings are fetched in batches using the selected parcel codes. This selection is not random and does not establish complete coverage.

| Stage | Implemented behavior and lineage evidence |
|---|---|
| Source retrieval | [fetch.py](../ingest/fetch.py) requests selected attributes and geometry with pagination, delays, and bounded retries. The standalone fetch saves original responses and a completion summary under ignored `data/raw/`. |
| Scheduled retrieval | [sync.py](../ingest/sync.py) reuses the fetch helper and validates temporary response pages. Those temporary pages are removed after processing; the operational log is not a permanent raw-response archive. |
| Validation | [load.py](../ingest/load.py) checks source IDs, cadastral codes, municipality, polygon rings, finite measurements, coordinate reference, counts, and parcel-building relationships. Invalid runs are rejected rather than silently imported. |
| Mapping | Selected API names map to the database fields below. Codes remain text. Geometry remains ArcGIS JSON; no reprojection or topology repair is performed. Missing department values remain null. |
| Versioning | The sync compares stored source attributes and geometry, excluding download times and generated IDs. Matching content reuses an existing snapshot. Changed content creates a historical version in one transaction. |
| Access and outputs | The limited loader writes approved tables; `app_reader` reads them for [quality checks](../db/quality_checks.sql), [golden questions](../evals/golden_questions.csv), and reference evaluation. These are evidence queries, not completed maintenance automation. |

| Source field | Database destination | Meaning or transformation |
|---|---|---|
| Land `OBJECTID` | `igac.parcels.object_id` | Source identity within a layer and release; scoped by `snapshot_id`. |
| Land `CODIGO` | `igac.parcels.codigo` | Text parcel code, unique within a snapshot. |
| Land `MANZANA_CODIGO` | `igac.parcels.manzana_codigo` | Source block code; nullable. |
| Land `CODIGO_ANTERIOR` | `igac.parcels.codigo_anterior` | Previous source code; nullable. |
| Land `CODIGO_DEPARTAMENTO` | `igac.parcels.department_code` | Preserved source value; no imputation. |
| Building `OBJECTID` | `igac.buildings.object_id` | Source identity within a layer and release; scoped by `snapshot_id`. |
| Building `CODIGO` | `igac.buildings.codigo` | Repetition is allowed; not the building row's unique key. |
| Building `TERRENO_CODIGO` | `igac.buildings.terreno_codigo` | Links to parcel `codigo` in the same snapshot. |
| Building `TIPO_CONSTRUCCION` | `igac.buildings.construction_type` | Nonblank source category. |
| Both layers' `Shape__Area`, `Shape__Length` | `shape_area`, `shape_length` in the corresponding table | Double-precision measurements; units and ground accuracy are unverified. |
| Both layers' `geometry` | `geometry` in the corresponding table | ArcGIS polygon JSON stored as `jsonb`. |
| Both layers' `codigo_municipio` | Validated against `igac.cadastral_snapshots.municipality_code` | The record-level value is checked during ingestion but is not independently retained in each source row. |

Snapshot fields preserve the configured release date, source layer URLs, municipality, fetch time, and coordinate reference. `source_run_id` is the saved folder name for the original import and a deterministic content-version identifier for snapshots created by the sync. It is not the same as an operational sync run ID.

The database generates `snapshot_id`, `parcel_id`, and `building_id`. Foreign keys link source records through their snapshot. Every source table has `first_seen_at` and `last_updated_at`: insertion sets the timestamps, and the loader updates the latter only for changed stored values. Normal sync preserves historical snapshots and does not touch source timestamps when content matches. Binary database reads prevent text-output precision loss during comparison; numeric normalization affects comparison only, not source measurements.

Only selected source attributes are stored. Other published fields, including `GLOBALID`, are outside the current import and content comparison. For database keys, constraints, and roles, see the [schema documentation](schema.md) and [schema SQL](../db/schema.sql).

### Operational lineage through sync_runs

[The run-log migration](../db/migrations/003_sync_runs.sql) defines `igac.sync_runs`. Each execution has a UUID `run_id`, status, start and finish times, trigger type, source release, record counters, and optional GitHub run ID and attempt. Successful runs reference a source `snapshot_id` and record a content fingerprint. Several successful executions can reference the same unchanged snapshot; run count is not snapshot count.

These fields connect an execution to its stored source version and, when available, its GitHub Actions history. Counts describe committed source-row inserts, updates, or unchanged records; failed-run counters do not describe partial downloads. Sanitized error categories support investigation without storing credentials or raw errors. An abrupt interruption can leave a committed `running` entry without a finish time. The [break-it evidence](sync_tests.md) documents that limitation; automatic reconciliation is not implemented.

The log provides operational traceability, not an immutable or complete source archive. The loader can update permitted log fields, old imported snapshots do not carry the sync's content fingerprint directly, and temporary sync responses are not retained. No stronger audit guarantee is claimed.

## Update behavior

IGAC documents monthly publication for the national open cadastral dataset. The URL used for this run is for the August 31, 2026 snapshot. We have not verified that the same URL updates in place. For a newer release, check the official catalog for its endpoint, confirm that it still covers the pilot city and provides the required fields, and save it separately with its release date and fetch date.

Compare records across releases by parcel code where the code still matches. Flag codes that appear or disappear for review, since a change in code can affect a match. `OBJECTID` identifies rows within a release, and its stability across releases has not been verified.

The implemented workflow checks the same configured release every six hours. Public metadata inspection found no advertised reliable record-level change mechanism, so the sync uses bounded re-fetching and content comparison. Layer edit metadata is checked before and after retrieval, but this does not guarantee an atomic source snapshot. A successful check is not evidence that IGAC published newer cadastral data. Details and monitoring responsibilities are in the [freshness and ownership section](data_quality.md#freshness-monitoring-and-ownership).

Sources: [IGAC release metadata](https://metadatos.icde.gov.co/geonetwork/srv/api/records/0eaaf959-4229-43f9-8e9d-970a9daf43ed?language=all) and [IGAC open geospatial data catalog](https://www.igac.gov.co/datos-abiertos/datos-abiertos-geoespaciales).

## Ethical use and attribution

Credit IGAC and record the release date when using the data. The exact license for public display of the hosted layers still needs confirmation. IGAC's detailed release metadata lists **CC BY-SA 4.0**, while Colombia's national open-data portal lists **CC BY 4.0**. Both licenses require attribution, and ShareAlike adds conditions when sharing adapted data. Confirm which terms apply to the exact layers before publishing a map or a data sample.

Use the shapes as reference information for planning. Label the source and release date so readers know the map reflects a particular snapshot. Keep worker information, private job details, and equipment assignments separate from the public map.

Sources: [IGAC's release and reuse terms](https://metadatos.icde.gov.co/geonetwork/srv/api/records/0eaaf959-4229-43f9-8e9d-970a9daf43ed?language=all), [national open-data listing](https://www.datos.gov.co/en/dataset/Base-Catastral-P-blica-del-Gestor-IGAC-08-2026/ny62-ftfh), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), and [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
