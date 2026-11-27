# Milestone 4 App Verification

**Current status, November 27, 2026:** the milestone-4 pilot automatically deployed commit `b12f9da`; Antonia personally verified the corrected website in Safari at approximately 04:52 EST (09:52 UTC). See the dated evidence below. Earlier no-deployment/local-only statements are historical. Final main-branch deployment remains pending.

## Scope and status

Local offline verification performed by Codex with Antonia's approval on November 23, 2026, on `milestone-4`. The website implements the approved [app specification](app_spec.md): original saved Pasto snapshot, parcel–building coverage, construction categories, shared parameterized block filter, and read-only access. Public chatbot and sign-in placeholders are removed; no AI API or database write feature was added.

**The initial offline stage made no live database connection. The separately approved live read-only verification is recorded below. No ingestion, deployment, or database change was performed. The November 25 exact-source licensing finding and approved notice scope are recorded below; deployment still requires separate approval.**

## Environment and commands actually run

Used the existing Milestone 2 virtual environment, Python **3.12.10**, without installing packages or copying credentials:

```sh
/Users/antoniahenao/BSAD6153/bsad6153-milestone-2/.venv/bin/python -B -m unittest discover -s tests -v
```

The initial implementation's final run completed **26 tests: 26 passed, 0 failures, 0 errors**. This comprises 16 app tests and the 10 existing sync tests. All database connections were mocked or blocked. The app's dotenv loading was mocked in UI tests so tests did not read local credentials. Sync HTTP calls were mocked; the printed retry messages are simulated, not live API activity.

AST syntax checks passed for `app/streamlit_app.py`, `tests/test_app.py`, and `tests/test_sync.py`. Whitespace checks covered the tracked diff and new documentation/test files.

## Offline checks and evidence boundaries

| Area | Verified offline behavior |
|---|---|
| Database safeguards | Reader-only configuration; wrong role rejected before source queries; repeatable-read, read-only transaction and statement timeout requested; connection context closes. |
| Snapshot | Exact original source-run ID bound as a parameter; unexpected municipality rejected; missing original snapshot displays an explanation rather than substituting a new run. |
| Filter and queries | Both queries use the same snapshot/block parameters; SQL-like block text remains a bound value; invalid filter mode rejected. UI tests exercise a selected block and missing-block option. |
| Coverage and categories | Mocked UI renders four coverage metrics and two tables; category totals must equal returned building totals. Empty parcel results and parcels with zero returned buildings have different messages. |
| Freshness | Exactly 24 hours is not overdue; more than 24 hours warns. Missing sync, future timestamp, and different checked/displayed snapshot produce warnings. Only GitHub-backed manual/scheduled successes qualify in the query. |
| Caching | Repeated identical inputs reuse results; changed snapshot/block inputs use separate entries; failed calls are not cached. TTL is configured as 600 seconds. Actual wall-clock expiry was not waited out. |
| Safe errors | Missing configuration, wrong role, and simulated connection failure produce friendly UI states without the synthetic private error detail. No chatbot password field is rendered. |
| Existing sync | All 10 prior offline sync regression tests still pass; sync source was not changed. |

Mock rows are test fixtures, not new measurements or claims about current stored data. Offline tests do not execute PostgreSQL, prove production query plans, or independently establish reference-answer accuracy.

## Failures encountered and resolved

The first run had three failed assertions and one error in UI tests. Streamlit caches were shared between mocked fixtures, causing stale test results. Tests now clear the cache between independent fixtures. A subsequent run encountered one AppTest timeout with its three-second default; the UI harness now allows ten seconds. The final 26-test run passed after these corrections. The app also normalizes the displayed sync timestamp to UTC and suppresses dotenv parse warnings to avoid exposing local configuration details.

## Render configuration review

`render.yaml` retains `APP_DATABASE_URL` as a private environment value and the 24-hour setting, removes the unused AI-key/password prompts, and selects Python 3.12.10, matching the local environment. Existing build/start commands remain unchanged. No Render service was contacted or deployed; runtime availability and a clean Render build remain unverified. This is not a full clean-start reproduction test.

## Pending before public release

- [x] Compared live read-only app results with golden Q02, Q03, and Q05 and equivalent SQL for one selected block; see measured evidence below.
- [x] Verified live `app_reader` identity, read-only transaction mode, original snapshot identity, and latest qualifying sync metadata. Permission-denied tests were not repeated in this step; existing Milestone 3 permission evidence remains separate.
- [x] Exact-source CC BY-SA 4.0 evidence reviewed and Antonia approved licensing source data and data-derived presentations/adaptations accordingly; see data_license.md. The national-portal discrepancy remains unexplained.
- [x] Antonia reported visible attribution/license information in Safari on November 25; exhaustive source-link/legal-notice inspection is not claimed.
- [x] Antonia reported a successful milestone-4 Render deployment and working Safari views/filter; this confirms the reported deployment, not a full clean-start test.
- [x] Antonia verified the deployed display corrections in Safari on November 27; see follow-up below.
- [ ] Remaining error/configuration cases and final main-branch deployment.
- [ ] Complete personal browser review, peer code review, and remaining assignment evidence. AppTest is not a visual browser or accessibility audit.

The 24-hour threshold concerns pipeline activity, not current source conditions. Missing building matches do not establish vacancy. The historical Pasto sample does not establish Manizales coverage or machinery maintenance improvements. Private business records are outside this public pilot.


## Live read-only verification — November 23, 2026

With Antonia's separate approval, Codex used only `APP_DATABASE_URL` from the authorized environment/local configuration. No owner or loader connection was used. The app's actual `reader()`, `context_data()`, and `view_data()` functions ran; cached wrappers were bypassed to force fresh database reads. This verifies the query/data functions, not a live browser session or deployed website.

The comparison transaction timestamp was **2026-11-23 21:00:09.424811 UTC**. The role query returned `app_reader`, and `current_setting('transaction_read_only')` returned `on`. All connections used the app's repeatable-read, read-only transactions, 10-second connection/statement timeouts, and 3-second lock timeout. Connections closed normally. No data-changing statements were issued.

The original run `20261109T062536Z-9fp_q80e` exists as **snapshot 1**, municipality **52001 (Pasto)**, source release **2026-08-31**. Every measurement below was collected during this verification session; separate read-only transactions were used for app and reference results. This is not a single transaction spanning every comparison.

| Measurement | App result | Reference result | Reference SQL | Comparison |
|---|---:|---:|---|---|
| Parcel rows | 500 | 500 | Q02: number of returned parcel groups | Exact complete ordered row comparison passed |
| Returned building records | 1,218 | 1,218 | Q02: sum of per-parcel building counts | Passed |
| Parcels with building matches | 422 | 422 | Q03: `matched_parcels` | Passed |
| Parcels without returned matches | 78 | 78 | Q03: `parcels_without_returned_matches` | Passed |
| CONVENCIONAL records | 995 | 995 | Q05: category group | Exact complete ordered category comparison passed |
| NO CONVENCIONAL records | 223 | 223 | Q05: category group | Passed |

Reference SQL was read directly from [golden_questions.csv](../evals/golden_questions.csv), IDs **2, 3, and 5**, without changing the queries. These correspond to [db/queries.sql](../db/queries.sql), queries 2, 3, and 5. Q02 uses a left join and per-parcel grouping; Q03 counts matched/unmatched parcels; Q05 groups source building records by category. The app and references selected the same original snapshot.

Internal consistency passed: **422 + 78 = 500 parcels**, and **995 + 223 = 1,218 building records**, matching the sum of all per-parcel returned-building counts. Repeated building codes were not deduplicated.

### Parameterized block comparison

Block **52001010300000150** was present in the original snapshot. App calls used `view_data(1, 'code', '52001010300000150')`. Independent reference queries used bound parameters `(1, '52001010300000150')`:

```sql
SELECT p.codigo, count(b.building_id)
FROM igac.parcels p
LEFT JOIN igac.buildings b
  ON b.snapshot_id = p.snapshot_id AND b.terreno_codigo = p.codigo
WHERE p.snapshot_id = %s AND p.manzana_codigo = %s
GROUP BY p.codigo
ORDER BY count(b.building_id) DESC, p.codigo;
```

```sql
SELECT b.construction_type, count(*)
FROM igac.buildings b
JOIN igac.parcels p
  ON p.snapshot_id = b.snapshot_id AND p.codigo = b.terreno_codigo
WHERE p.snapshot_id = %s AND p.manzana_codigo = %s
GROUP BY b.construction_type
ORDER BY count(*) DESC, b.construction_type;
```

| Block measurement | App | Reference | Result |
|---|---:|---:|---|
| Parcels | 35 | 35 | Passed; all ordered parcel rows equal |
| With building matches | 27 | 27 | Passed; derived from per-parcel counts |
| Without returned matches | 8 | 8 | Passed; derived from per-parcel counts |
| Building records | 68 | 68 | Passed |
| CONVENCIONAL | 62 | 62 | Passed; all ordered category rows equal |
| NO CONVENCIONAL | 6 | 6 | Passed |

Block consistency passed: **27 + 8 = 35** and **62 + 6 = 68**. Neither unmatched count establishes vacancy.

### Freshness metadata and remaining boundaries

The context query returned the latest qualifying successful GitHub-backed check at **2026-11-23 19:28:23.581218 UTC**, linked to snapshot **1** and source release **2026-08-31**. It was approximately **1.53 hours old** at the comparison timestamp, below the 24-hour operational threshold. This is stored sync metadata, not an independent recheck of GitHub history or current property conditions. No displayed/checked snapshot mismatch was present.

No discrepancies or connection/query failures occurred. Streamlit emitted its normal no-runtime cache warning because query functions were invoked outside the interactive UI. Credentials and raw connection errors were not displayed or saved in the evidence. A credential-free local result summary is retained at `/tmp/bsad_m4_verified_results.json`; it is outside the repository and may be removed by the operating system.

Live UI behavior, deployed Render compatibility, full clean-start reproduction, peer review, remain unverified or pending. This historical statement predates the November 25 exact-source license verification below. No additional scheduled runs, ingestion, or write-permission tests were triggered.


## Freshness configuration correction and latest offline tests

The initial configuration claim that changing Render's FRESHNESS_HOURS would change the application threshold was incorrect at commit `990f0c2`: Render declared the variable, but the app hardcoded 24. With Antonia's approval, Codex changed the app to read the environment at runtime after dotenv loading. Positive finite numeric values are accepted; absent, blank, invalid, nonpositive, or nonfinite values fall back to 24 hours. The banner warning and page explanation both use the effective threshold. Render configuration was not changed by this correction.

On **November 23, 2026**, Codex ran the same offline unittest-discovery command shown above using Python 3.12.10. The latest completed suite reported **28 passed, 0 failures, 0 errors**: 18 app tests and 10 existing sync tests. New tests verify that a six-hour configuration permits a check exactly six hours old, warns one second beyond it, and displays the configured value. They also verify missing/invalid settings, positive fractional values, and the 24-hour fallback. The existing 24-hour boundary tests passed. Python AST syntax checks and whitespace checks passed. These results were not rerun during the documentation-only update on November 25, 2026.

Database connections and HTTP calls were mocked/blocked; UI dotenv loading was mocked. No live database, Render, or browser verification was performed for this correction. The earlier 26-test result and live Q02/Q03/Q05/block comparisons remain historical evidence above; the live SQL checks were not repeated and are not replaced by the 28-test result.

On **November 25, 2026**, Antonia confirmed reviewing the provided Code Tour, supporting excerpts, configuration comparison, and reported results. The checked items in [code_tour.md](code_tour.md) record that excerpt-based review only. They do not claim she independently inspected every complete file or personally executed Codex's tests. Full-file personal review, actual browser/configuration verification, Render behavior, peer review, clean-start reproduction, remain pending or unverified. Exact-source license evidence and the separately approved data-license scope are documented below; the portal discrepancy remains unexplained.

## November 25 licensing and deployment-readiness review

Antonia approved CC BY-SA 4.0 for IGAC source data and project data-derived adaptations/presentations. [data_license.md](data_license.md) records the exact service-to-item link, publisher licenseInfo, independent IGAC release metadata, attribution, and the unexplained national-portal label discrepancy. The app About section now displays source/evidence/license links, project changes, no-endorsement/warranty language, and the separate scope of independent application code. This is not a claim that the national portal discrepancy has been resolved. Existing personal-review checkboxes do not certify the newer notice or its browser appearance.

Codex reran the offline suite on **November 25, 2026** with the existing Python 3.12.10 environment: **28 passed, 0 failures, 0 errors** (18 app tests, 10 sync tests). No database or HTTP ingestion calls were made; connections/calls were mocked or blocked as before. AST syntax checks passed for app and both test files. The prior live SQL evidence remains unchanged; no live database comparison was repeated. Whitespace checks passed for the changed/new files.

`render.yaml` was reviewed but not changed: Python 3.12.10, Free web service, pinned requirements build, Streamlit binding to `$PORT`/`0.0.0.0`, private APP_DATABASE_URL, and FRESHNESS_HOURS=24. No owner/loader credentials, AI keys, or password feature are configured. Render's [Python-version documentation](https://render.com/docs/python-version), checked November 25, supports fully qualified released versions through PYTHON_VERSION. This is documentary compatibility evidence, not an actual successful build. A YAML parser was unavailable in the existing environment; no parser validation or new installation is claimed.

Render's [Free documentation](https://render.com/docs/free), checked November 25, describes spin-down after 15 minutes without inbound traffic and approximately one minute to wake. Free usage limits and ephemeral local storage remain constraints. These are platform expectations, not measurements from this app. Caches are process-local; durable source records remain in Supabase.

**Readiness:** suitable for a separately approved deployment attempt after branch/service selection, secure app_reader environment entry, free-plan limit/spending review, and personal review of the updated notices. No service was created or deployed. Actual dependency installation on Render, HTTPS/WebSocket operation, database connectivity from Render, browser display/filters/errors, and cold-start behavior remain unverified. Do not mark the public website, browser review, peer review, usage log, ungrounded evaluation, or clean-start reproduction complete based on this review.

## Pre-deployment reader permission and TLS verification — November 25, 2026

With Antonia's explicit approval, Codex used **only APP_DATABASE_URL** and confirmed both `current_user` and `session_user` were `app_reader`. The final diagnostic began at **2026-11-25 22:20:19.445000 UTC**. Short connection/statement timeouts (10 seconds) and lock timeout (3 seconds) were applied. Credentials, database addresses, and raw errors were not displayed or saved in this document.

### TLS and Render connection configuration

An earlier configuration check stopped before connecting because the URL did not explicitly require TLS. With separate approval, only the existing local reader URL's TLS option was corrected to `sslmode=require`; other credentials/connection details were preserved, with no downgrade of stronger settings. The local `.env` was verified ignored and untracked by Git. This does not prove earlier connections were unencrypted; it fixes the absence of an explicit requirement.

The final check confirmed PostgreSQL URL format, the custom reader Session-pooler username format, Supabase Session-pooler port, IPv4 DNS resolution, explicit `sslmode=require`, and client-side TLS actually in use. No local certificate-file dependency was present. This connection approach is suitable for a Render deployment attempt, but it does not verify the URL has been entered correctly in Render or that Render's network can connect. `sslmode=require` enforces encryption; it is not a claim of full hostname/certificate verification equivalent to a correctly configured `verify-full` connection. No Render environment settings were inspected or changed.

### Effective role and object privileges

Metadata inspection found no superuser, CREATEDB, CREATEROLE, replication, or BYPASSRLS attributes; no memberships in other roles; no owned relations, schemas, or routines; no database CREATE or non-system schema CREATE privileges. The four approved IGAC relations are ordinary tables, not views providing indirect access.

SELECT succeeded on all four approved tables. Observed counts during this session were **1 cadastral snapshot, 500 parcels, 1,218 buildings, and 30 sync_runs entries**. These are session-time observations, not replacements for earlier historical measurements.

For each IGAC table, effective table-level INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, and TRIGGER privileges were absent. Column-level INSERT, UPDATE, and REFERENCES privileges were also absent. Checks included privileges inherited through PUBLIC rather than only direct grants.

No usable non-system table/view privileges outside the four approved IGAC tables were found after accounting for schema USAGE. No non-system sequence privileges, accessible non-system executable routines (including SECURITY DEFINER routines), foreign-server USAGE, or foreign-data-wrapper USAGE were found. These checks address the inspected SQL access paths; they are not a claim of a comprehensive platform vulnerability audit.

### Platform monitoring grants and corrected diagnostic

The first broad diagnostic stopped because it counted object-level SELECT grants without considering schema access. A separately approved metadata-only investigation and corrected verification established:

| Object | Extension | Grant source | Object privilege | app_reader schema USAGE |
|---|---|---|---|---|
| `extensions.pg_stat_statements` | `pg_stat_statements` | PUBLIC | SELECT only | Denied |
| `extensions.pg_stat_statements_info` | `pg_stat_statements` | PUBLIC | SELECT only | Denied |

These are extension-owned query-monitoring views, not unrelated business tables. No records from either view were read. The object ACLs remain in place, but ordinary named access through the extensions schema is blocked for this role. No grants were revoked and no platform settings were changed. `igac` USAGE is granted directly to app_reader; `public` USAGE is available through PUBLIC; both schemas deny CREATE. The metadata investigation also found no USAGE on auth, storage, realtime, vault, graphql, graphql_public, or pgbouncer.

### Non-executing write-authorization evidence

The diagnostic used an **ordinary transaction**, verified `transaction_read_only = off`, so write authorization was not merely denied by a read-only transaction setting. Only `EXPLAIN (ANALYZE FALSE)` was sent for the proposed data-changing statements. INSERT plans omitted generated identity columns; all test statements used `WHERE FALSE`. No INSERT, UPDATE, or DELETE statement was actually executed, no sequence function was called, and no TRUNCATE or DDL operation was attempted.

Each check ran inside a savepoint and rolled back to it. The outer transaction was unconditionally rolled back in the cleanup path; its final state was verified IDLE before closing the connection.

| Table | INSERT authorization SQLSTATE | UPDATE authorization SQLSTATE | DELETE authorization SQLSTATE |
|---|---|---|---|
| `igac.cadastral_snapshots` | 42501 | 42501 | 42501 |
| `igac.parcels` | 42501 | 42501 | 42501 |
| `igac.buildings` | 42501 | 42501 | 42501 |
| `igac.sync_runs` | 42501 | 42501 | 42501 |

**Outcome: all 12 authorization checks returned insufficient privilege (42501); final rollback succeeded.** No application records, permissions, or schema objects were changed. A credential-free local diagnostic summary is at `/tmp/bsad_reader_permission_results.json`, outside the repository; it is not a durable or committed evidence artifact.

### Remaining limitations and deployment decision

The shared PUBLIC TEMPORARY database privilege remains available, allowing temporary objects; this is not permission to write persistent IGAC tables. Standard system-catalog access remains available. No attempt was made to remove shared platform privileges. Permissions can change and should be reviewed again after role/grant changes. These checks establish current inspected privileges and authorization failures without executing actual writes; they do not test application behavior from Render, browser display, certificate hostname verification, or every possible extension/system-function behavior.

The safe URL transfer to Render, an actual build/deployment, network connectivity from Render, updated-notice browser review, full clean-start reproduction, complete-file personal review, peer review, usage observations, and ungrounded baseline evaluation remain pending as previously documented. The national licensing-portal discrepancy remains unexplained. No deployment, Git commit/push, or merge was performed during these checks.


## Antonia Safari verification and local display corrections — November 25, 2026

**Source of evidence:** Antonia personally opened [the public website](https://bsad6153-henao.onrender.com) in Safari and reported the following. Codex is documenting her observations, not claiming an independent browser inspection, a new live database query, or access to Render logs. The deployment was from **milestone-4**, not the final main branch. The exact deployed commit/build ID and browser-check time were not supplied and are not invented.

- Freshness banner showed the latest successful sync at approximately **3.1 hours old** at her review; this is a historical observation, not the current age or proof of current source conditions.
- IGAC attribution and license information were visible.
- Both views, tables, charts, and the shared block filter worked in her review.

| Observed metric | All blocks | Block 52001010300000150 |
|---|---:|---:|
| Parcels | 500 | 35 |
| Returned building records | 1,218 | 68 |
| Parcels with matches | 422 | 27 |
| Parcels without returned matches | 78 | 8 |
| Conventional building records | 995 | 62 |
| Nonconventional building records | 223 | 6 |

These user-observed totals agree with the earlier approved live SQL evidence. No database measurements were rerun in this step. Unmatched parcels are not proven vacant; category counts are source records and do not establish occupancy, safety, or machinery maintenance needs.

### Review findings and local corrections

Antonia identified chart-baseline and metric-label presentation issues and an obsolete deployment-approval statement. Codex made these approved local fixes:

1. Replaced the category chart call with an explicit Vega-Lite specification: quantitative y-scale `zero: true` and `domainMin: 0`. This fixes the zero baseline without changing category counts or requiring another package.
2. Shortened the fourth metric to **No building match**, with help text: “Parcels without returned building matches; vacancy is unknown.”
3. Replaced the obsolete deployment-approval caption with milestone-4 pilot deployment status, preserving IGAC attribution, license scope, source links, national-portal discrepancy, and data limitations.

On **November 25, 2026**, Codex ran the existing offline unittest-discovery command again: **29 passed, 0 failures, 0 errors** (19 app tests and 10 sync tests). The added test checks the actual chart specification for a zero baseline, the shorter metric label/help, and removal of the old approval caption. Connections and HTTP calls were mocked/blocked; UI dotenv loading was mocked. Python AST syntax checks and whitespace checks passed. Earlier test results remain historical evidence, not failures or replacements of live comparisons.

### What is and is not complete

- [x] Antonia reported successful milestone-4 Render deployment and personally verified the listed Safari interactions, numbers, freshness display, and visible attribution/license information.
- [x] README now identifies the public URL and milestone-4 deployment scope.
- [x] Local chart/label/status corrections passed offline regression tests.
- [x] Approved display corrections committed/pushed as b12f9da; Render automatic deployment succeeded November 27 (see follow-up).
- [x] Antonia verified the zero chart baseline, untruncated metric label, and removed approval statement in Safari after deployment, November 27 at approximately 04:52 EST. Broader viewport testing is not claimed.
- [ ] Verify final main-branch deployment after an approved merge; milestone-4 remains the deployed pilot branch.
- [ ] Remaining error/configuration cases, full clean-start reproduction, full-file review, peer review, and screencast/submission evidence. Parts E/F documentation is now recorded with limitations in the current checklist below.

No database access, permission changes, commit, push, redeployment, or merge was performed in this correction step. The national licensing-portal discrepancy remains unexplained; CC BY-SA 4.0 applies to the approved IGAC data/adaptation/presentation scope, not automatically to independent application source code.


## Antonia Safari follow-up — November 27, 2026

**Browser verification reported by Antonia:** approximately **04:52 AM EST (09:52 UTC)** at [the public milestone-4 pilot](https://bsad6153-henao.onrender.com). Codex records her actual observations; no independent browser inspection, database query, or new test execution was performed in this documentation step.

- The fourth metric displayed **No building match** without truncation.
- The construction-category chart started at **zero**.
- The outdated deployment-approval statement was absent.
- IGAC attribution and licensing remained visible.
- All six unfiltered counts remained correct: **500 parcels, 1,218 building records, 422 parcels with matches, 78 without returned matches, 995 conventional records, and 223 nonconventional records**.
- The freshness banner showed the successful **November 27 check at 07:49 UTC**, approximately **two hours old** at review. The minute-level timestamp and age are reported as observed, not as a newly queried precise completion time or current age. This does not establish current source conditions.

Codex's earlier read-only Render dashboard observation confirmed automatic deployment of `b12f9dac3b284a8271975df293c84623943dabd1`, displayed time November 27 at 04:48:49 EST, trigger Auto-Deploy, duration 55.1 seconds. Antonia's subsequent review establishes the three corrections were visible on the website. It does not independently associate a browser-exposed build identifier with the page, which does not display one.

- [x] Antonia personally verified the three deployed display/status corrections and listed unfiltered values in Safari.
- [ ] Final main-branch deployment after approved merge.
- [ ] Broader viewport/accessibility tests, all error/configuration scenarios, full clean-start reproduction, complete-file review, peer review, and remaining submission evidence. Parts E/F evidence and missing measurements/settings are separated below.

No new block-filtered observation, task duration, confidence score, business improvement, or time saving was supplied for this follow-up, so none is inferred. This browser verification is functional evidence, not automatically a Real Usage Log entry. Earlier dated SQL results and the 29-test offline result remain intact. The national-portal licensing discrepancy remains documented.


## Current Milestone 4 evidence checklist — November 27, 2026

This checklist supersedes pending statements in earlier dated sections without changing their historical measurements.

- [x] Approved app specification, two views, parameterized block filter, read-only safeguards, caching, freshness, attribution, and documented limitations implemented.
- [x] 29 offline tests passed; syntax and whitespace checks passed. Codex reran the offline suite during the November 27 documentation review; no live database connection was used for that run.
- [x] Prior live SQL comparisons and reader permission/TLS evidence documented with their original timestamps and limits.
- [x] Public milestone-4 pilot deployment, automatic deployment of b12f9da, and Antonia's November 25/27 Safari observations documented.
- [x] Code Tour prepared; Antonia's supplied-excerpt review and specific Safari checks recorded without claiming complete-file inspection.
- [x] Part E: two actual website uses recorded in [usage_log.md](usage_log.md), including the chart improvement identified through use. Antonia approved their accurate documentation.
- [ ] Part E measurement fields: task durations and confidence ratings remain unrecorded; wished-for information was not supplied. If mandatory, obtain additional genuine timed observations or instructor guidance. Do not backfill invented measurements. No machinery-maintenance time saving is established.
- [x] Part F: five exact user-supplied responses, IDs 1/3/5/6/9, four measured read-only SQL references, verdicts, and web-status fields recorded in [ungrounded_baseline.md](../evals/ungrounded_baseline.md). ChatGPT Temporary Chat confirmed; Antonia agreed with the verdicts.
- [ ] Part F metadata: exact model version, experiment time, and web activity remain unrecorded; other context/prompt-order details and original export are not supplied. If required by the rubric, these remain incomplete. No settings or tool usage were inferred.
- [ ] Peer code review and docs/peer_review.md, including feedback and responses.
- [ ] Remaining complete-file personal review, broader browser/accessibility/error/configuration checks, and full clean-start reproduction. Do not confuse these with the completed excerpt/specific-browser checks.
- [ ] Approved merge and final main-branch deployment/verification; currently the deployed pilot branch is milestone-4.
- [ ] Milestone 4 screencast link and remaining Canvas submission requirements, including any applicable domain requirement not verified in this review.

The national licensing-portal discrepancy remains unexplained. The exact publisher's CC BY-SA 4.0 statement and approved data/output scope remain documented. Earlier live measurements and user responses are preserved; no new SQL or usage measurements were generated while reconciling these checklists.
