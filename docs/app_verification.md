# Milestone 4 App Verification

## Scope and status

Local offline verification performed by Codex with Antonia's approval on November 23, 2026, on `milestone-4`. The website implements the approved [app specification](app_spec.md): original saved Pasto snapshot, parcel–building coverage, construction categories, shared parameterized block filter, and read-only access. Public chatbot and sign-in placeholders are removed; no AI API or database write feature was added.

**The initial offline stage made no live database connection. The separately approved live read-only verification is recorded below. No ingestion, deployment, or database change was performed. Public deployment remains blocked until IGAC reuse and attribution terms are verified.**

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
- [ ] Resolve applicable IGAC terms: release metadata lists CC BY-SA 4.0 while the national listing lists CC BY 4.0. Confirm required attribution, links, and any ShareAlike obligations. Attribution text alone does not resolve this discrepancy.
- [ ] Verify Render runtime/build compatibility and deployed behavior after deployment approval.
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

Live UI behavior, deployed Render compatibility, full clean-start reproduction, peer review, and IGAC reuse/attribution resolution remain unverified or pending. No additional scheduled runs, ingestion, or write-permission tests were triggered.


## Freshness configuration correction and latest offline tests

The initial configuration claim that changing Render's FRESHNESS_HOURS would change the application threshold was incorrect at commit `990f0c2`: Render declared the variable, but the app hardcoded 24. With Antonia's approval, Codex changed the app to read the environment at runtime after dotenv loading. Positive finite numeric values are accepted; absent, blank, invalid, nonpositive, or nonfinite values fall back to 24 hours. The banner warning and page explanation both use the effective threshold. Render configuration was not changed by this correction.

On **November 23, 2026**, Codex ran the same offline unittest-discovery command shown above using Python 3.12.10. The latest completed suite reported **28 passed, 0 failures, 0 errors**: 18 app tests and 10 existing sync tests. New tests verify that a six-hour configuration permits a check exactly six hours old, warns one second beyond it, and displays the configured value. They also verify missing/invalid settings, positive fractional values, and the 24-hour fallback. The existing 24-hour boundary tests passed. Python AST syntax checks and whitespace checks passed. These results were not rerun during the documentation-only update on November 25, 2026.

Database connections and HTTP calls were mocked/blocked; UI dotenv loading was mocked. No live database, Render, or browser verification was performed for this correction. The earlier 26-test result and live Q02/Q03/Q05/block comparisons remain historical evidence above; the live SQL checks were not repeated and are not replaced by the 28-test result.

On **November 25, 2026**, Antonia confirmed reviewing the provided Code Tour, supporting excerpts, configuration comparison, and reported results. The checked items in [code_tour.md](code_tour.md) record that excerpt-based review only. They do not claim she independently inspected every complete file or personally executed Codex's tests. Full-file personal review, actual browser/configuration verification, Render behavior, peer review, clean-start reproduction, and IGAC reuse resolution remain pending or unverified.
