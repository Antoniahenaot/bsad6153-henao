# App Specification: Pasto Property-Data Pilot

**Purpose and audience**
This read-only website helps the instructor, peer reviewers, and interested visitors explore a limited IGAC property-data sample from Pasto, Colombia. It supports reviewing parcel–building coverage and construction categories, not machinery maintenance decisions.

**Questions and views**

| View | Question answered | Existing references |
|---|---|---|
| Parcel–Building Coverage | How many returned building records belong to each parcel? | [SQL query 2](../db/queries.sql); [golden Q02](../evals/golden_questions.csv) |
| Parcel–Building Coverage | How many parcels have building matches, and how many have no returned match? | SQL query 3; golden Q03 |
| Construction Categories | Which construction categories appear, and how many records belong to each? | SQL query 5; golden Q05 |

Coverage will show summary counts and a parcel-level table. Categories will show a count table and bar chart. Counts represent source records; repeated building codes will not be automatically removed.

**Snapshot and filter behavior**
Both views will use the same explicitly identified snapshot. Initially, this will be the original saved pilot, matching Q02, Q03, and Q05. Historical snapshots will never be combined into one coverage total.

A block selector will offer “All blocks” and available block codes. Its value and the snapshot identifier will be passed as SQL parameters, never inserted into SQL text. Both views will update consistently and label filtered totals. A category count means building records associated with parcels in the selected block.

**Freshness and caching**
The banner will show the latest successful GitHub-backed sync recorded in `igac.sync_runs`, its UTC completion time, and its age. Local saved-payload replays will not count as live checks.

The documented operational threshold will be **24 hours**: warn when the latest qualifying check exceeds it. This is a pipeline freshness threshold, not a guarantee that property conditions are current. The IGAC source release date will appear separately. If the displayed historical snapshot differs from the latest checked snapshot, the website will say so.

Database results will use a **600-second cache TTL**, shorter than the six-hour sync interval. Cache keys will include snapshot and filter values. Refresh occurs when the app reruns after expiry; caching does not provide continuous background refresh.

**Data and security boundaries**
Data comes from IGAC’s August 31, 2026 release: Pasto urban land and building layers, stored in `igac.cadastral_snapshots`, `igac.parcels`, and `igac.buildings`. Operational freshness comes from `igac.sync_runs`.

The app will connect only through private `APP_DATABASE_URL` configuration, verify `app_reader`, and use read-only transactions and query timeouts. Owner and loader credentials, private business information, and raw errors will never be displayed. No AI API or database-writing feature is required.

**Limitations and friendly states**
The sample is not representative of all Pasto or Manizales. Missing building matches do not establish vacancy. Construction categories do not establish safety, occupancy, or machinery requirements.

Missing snapshots, unavailable connections, and filters returning no records will produce clear messages rather than misleading zeros or technical tracebacks.

**Definition of done**
Both views and the parameterized filter work; results match reference SQL for the same snapshot and filter; freshness, empty, error, and wrong-role cases are tested; attribution and limitations are visible; no credentials are exposed. Public deployment follows separate approval and verification that the approved data-license notices are present.

**Connection to the baseline**
This pilot supports the baseline questions about whether downloaded property data is useful as mapping context. It does not contain machine readings, service history, or maintenance intervals and cannot demonstrate maintenance improvements.

**Data reuse and attribution**
The exact IGAC service item's licenseInfo and corresponding release metadata identify CC BY-SA 4.0, verified November 25, 2026. Antonia approved this license for source data and project data-derived presentations/adaptations. Show source/creator credit, license/evidence links, project changes, and no-endorsement/warranty notices. This does not relicense independent application code or dependencies. The previously reported national-portal CC BY 4.0 discrepancy remains unexplained; it is not treated as an override. See [data-license evidence and attribution](data_license.md). No deployment has occurred or been authorized by this specification update.
