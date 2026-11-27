# Milestone 4 Code Tour

Line numbers refer to the local Milestone 4 application including the November 25 display corrections; the single-line replacements did not shift the referenced locations. They may move after future edits. Codex prepared this tour and performed the technical checks below with Antonia's approval. **Personal excerpt review recorded November 25, 2026:** Antonia reviewed the provided Code Tour, selected actual code excerpts, original/corrected configuration comparison, and reported test results. Checked items below record only her understanding of that supplied evidence. They do not claim independent inspection of every complete file, personal execution of tests, a live browser check, or verified Render behavior.

## Purpose and file map

The website explores the original IGAC Pasto property sample. It does not provide machinery maintenance advice.

| File | Responsibility |
|---|---|
| `app/streamlit_app.py` | Database reads, snapshot selection, filters, views, freshness, and friendly messages. |
| `render.yaml` | Deployment build/start commands and private environment configuration. |
| `requirements.txt` | Pinned Python dependencies. |
| `tests/test_app.py` | Offline application tests with mocked connections. |
| `docs/app_spec.md` | Approved scope and acceptance criteria. |
| `docs/app_verification.md` | Earlier offline/live read-only verification evidence and remaining limitations. |
| `db/queries.sql`, `evals/golden_questions.csv` | Reference SQL used to check dashboard results. |
| `.github/workflows/sync.yml` | Separate scheduled ingestion pipeline; the website does not run ingestion. |

**Personal verification**

- [ ] Complete-file responsibility review — pending; the file map was explained, but not every complete file was independently inspected.
- [ ] Incorrect — my notes: __________

## 1. Database connection and access protection

**Location:** `app/streamlit_app.py`, lines **28–41**.

`reader()` reads only `APP_DATABASE_URL` (line 31). Line 34 creates the connection with a ten-second connection timeout. Lines 35–40 start a read-only, repeatable-read transaction, set statement/lock timeouts, and verify `current_user = 'app_reader'`. A different role is rejected before application data queries run. Connection context managers close the connection on exit.

The environment-variable name alone does not enforce security: PostgreSQL permissions, the role check, and read-only transactions are separate safeguards. Local dotenv loading is at lines **140–141**. Render declares `APP_DATABASE_URL` as a privately supplied value at `render.yaml`, lines **17–18**, without storing a real connection string.

**Personal verification**

- [x] Correct based on the reviewed connection excerpt — it uses APP_DATABASE_URL, checks app_reader, and requests read-only transactions and timeouts.
- [ ] Incorrect — my notes: __________

## 2. Original snapshot and block choices

**Location:** `app/streamlit_app.py`, lines **12**, **44–68**, and **153–157**.

The app selects original source run `20261109T062536Z-9fp_q80e` using a bound SQL parameter (lines 47–50), checks municipality 52001/Pasto (51–52), and retrieves its block choices (55–59). Missing snapshot handling does not silently substitute another historical version. The page identifies the displayed snapshot, release, and download time separately.

**Personal verification**

- [x] Correct based on the reviewed snapshot/query excerpts — both views use the original snapshot rather than combining historical versions.
- [ ] Incorrect — my notes: __________

## 3. Queries and shared parameterized filter

**Location:** `app/streamlit_app.py`, lines **72–102** and **158–163**.

`PARCEL_SCOPE` supports All blocks, a block code, or missing block codes. `view_data()` builds the parameter tuple at line 83 and passes it separately at lines 91 and 98. Fixed SQL fragments are joined together, but user-selected values are not inserted into SQL text.

Lines **85–92** use a left join to count building records per parcel, keeping parcels without matches. Lines **93–99** group buildings by category within the same snapshot/block scope. Lines **100–101** reject inconsistent building totals. Lines **168–181** display the metrics, parcel table, category table, chart, and no-building state. Distinct building records are not deduplicated by code.

**Personal verification**

- [x] Correct based on the reviewed SQL excerpts — both views share snapshot/block parameters, preserve unmatched parcels, and check their totals.
- [ ] Incorrect — my notes: __________

## 4. Errors and empty results

**Location:** `app/streamlit_app.py`, lines **147–185**.

Missing configuration (147–149), missing original snapshot (153–155), no matching parcels (165–167), and no returned buildings (180–181) have different messages. Lines **182–185** handle wrong-role and listed database/processing errors without showing raw exception details. Not every possible programming error is caught.

A genuine zero building count is different from a missing dataset or unavailable connection.

**Personal verification**

- [x] Correct based on the reviewed handling excerpts — unavailable data is distinguished from verified zero counts, and handled errors hide technical details.
- [ ] Incorrect — my notes: __________

## 5. Freshness and caching

**Location:** `app/streamlit_app.py`, lines **13–25**, **44**, **60–67**, **79**, and **105–124**.

The freshness query requires a successful manual/scheduled run with a GitHub identifier, excluding local replays. The banner calculates age in UTC, warns when age exceeds the configured threshold, and warns if the checked snapshot differs from the displayed historical snapshot.

Both cached functions use a **600-second TTL**. Snapshot and block arguments distinguish view-cache entries. Age is recalculated when the page reruns, while underlying sync metadata may remain cached for ten minutes. Cache expiry does not refresh an idle browser automatically. The separate six-hour sync schedule is in `.github/workflows/sync.yml`, lines **4–6**. Neither schedule nor cache proves current source conditions.

**Personal verification**

- [x] Correct — I understand the supplied caching/freshness excerpts and the distinction between cached results, sync-check age, and source release.
- [ ] Incorrect — my notes: __________

## 6. Attribution and public boundaries

**Location:** `app/streamlit_app.py`, lines **127–135**.

The page identifies IGAC, release, layers, and source link, and explains that unmatched parcels do not establish vacancy. Pasto data does not establish Manizales coverage or maintenance requirements.

The license notice is informational, **not a technical deployment lock**. The exact-source CC BY-SA 4.0 evidence and Antonia's November 25 licensing decision are documented in [data_license.md](data_license.md). The national-portal discrepancy remains unexplained. Antonia reported the milestone-4 deployment and Safari verification on November 25; final main-branch deployment remains pending. Render's build/start commands are at `render.yaml`, lines **9–11**; no AI key/password is requested.

**Personal verification**

- [x] Historical excerpt review — Antonia reviewed the earlier attribution/limitations excerpt and understood that its warning was not a technical deployment lock.
- [x] Antonia reported seeing IGAC attribution and license information in Safari on the milestone-4 pilot, November 25.
- [ ] Independently inspect every updated notice/source link and verify later local corrections in the redeployed website.
- [ ] Incorrect — my notes: __________

## 7. Configuration mismatch, correction, and verification

**Original incorrect configuration claim:** “Changing FRESHNESS_HOURS in Render changes the application threshold.” This was incorrect before the correction. At commit `990f0c2`, `render.yaml`, lines **15–16**, declared FRESHNESS_HOURS=24, but the app fixed the value at 24 without reading the environment. Values agreed, but changing Render alone would not change behavior. Antonia approved correcting this mismatch; this was not a previously completed correction.

**Correction:** `freshness_hours()` at app lines **19–25** reads FRESHNESS_HOURS at runtime, after local dotenv loading when called from the page. Missing, blank, nonnumeric, zero, negative, NaN, or infinite values safely fall back to 24. Positive finite values, including fractional hours, are accepted. Lines **117–119** use the configured value in the comparison and warning; line **146** displays the same effective threshold in the page explanation. Render itself was not changed in this step and remains configured for 24 hours.

**Actual offline verification:** on November 23, 2026, Codex used the existing Python 3.12.10 environment to run:

```sh
python -B -m unittest discover -s tests -v
```

**28 tests passed, 0 failures, 0 errors:** 18 app tests and the 10 existing sync tests. New tests `test_configured_freshness_threshold_controls_banner` and `test_freshness_config_defaults_and_rejects_invalid_values` verify the six-hour boundary, warning text, safe fallback cases, and fractional configuration. The existing default 24-hour boundary tests also passed. Database connections and HTTP calls were mocked/blocked, and UI dotenv loading was mocked. Syntax checks and whitespace checks passed. No live database or Render connection was used for this correction.

**Careful manual verification still deserved:** confirm that a configured threshold changes the rendered page explanation and banner consistently in an actual browser, with approved safe configuration. Offline tests establish function behavior but do not prove Render environment delivery or deployed behavior. No such deployment/browser check is claimed completed.

**Personal verification**

- [x] Correct — I reviewed the supplied original/corrected excerpts and understand the environment lookup and safe fallback. This is not a complete-file inspection.
- [ ] Incorrect — my notes: __________
- [x] Correct — I reviewed the reported offline results and test excerpts and understand their limits; Codex executed the tests.
- [ ] Incorrect — my notes: __________
- [ ] My manual browser/configuration review notes: __________

## Remaining verification limits

- [ ] Independent inspection of every complete file.
- [ ] Actual browser check of the configured threshold, page explanation, and banner.
- [ ] Render environment delivery and deployed behavior.


Earlier 26-test evidence and live Q02/Q03/Q05 comparisons remain historical evidence in docs/app_verification.md; this correction adds the 28-test offline result above. The live database comparisons were not repeated. Render deployment, full clean-start reproduction, complete browser/accessibility review, and peer review remain pending or unverified. The exact-source CC BY-SA 4.0 finding is now documented; the national-portal discrepancy remains unexplained. No machinery outcomes or time savings are claimed.


## November 25 licensing follow-up

The About text at app lines 127–135 now credits IGAC, identifies source/license evidence, explains filtering and aggregation changes, and applies CC BY-SA 4.0 to data adaptations/presentations only. Independent application code and dependencies are outside that notice. Existing code line numbers are unchanged by this text-only About update. Antonia approved the licensing approach; this does not mark her personal inspection of the new text or its browser rendering complete.


## November 25 Safari evidence and subsequent local display fixes

Antonia personally opened the milestone-4 Render pilot at https://bsad6153-henao.onrender.com and verified both views, tables, charts, the block filter, visible attribution/license information, a sync age of approximately 3.1 hours, and the reported all-block/selected-block totals recorded in app_verification.md. Codex did not perform that browser review. This does not establish every error state, different freshness settings, Render environment inspection, or final main-branch deployment.

Current app line **171** uses the shorter fourth metric label **No building match**; line **172** supplies help text explaining that it counts parcels without returned matches and vacancy remains unknown. Line **178** uses an explicit Vega-Lite quantitative scale with `zero: true` and `domainMin: 0`, so category bars start at zero. Line **135** replaces the obsolete deployment-approval statement with branch-deployment status while retaining the license discrepancy. These local changes have not been committed, pushed, or redeployed in this step.

- [x] Antonia reported successfully reviewing the previously deployed pilot in Safari.
- [ ] Browser verification of the local zero-baseline chart and shorter metric label after an approved redeployment.
- [ ] Verify final main-branch deployment after any approved merge.
