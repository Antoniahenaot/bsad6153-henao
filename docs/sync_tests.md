# Milestone 3 Part G: Break-It Tests

## Purpose and scope

Codex executed these tests with Antonia's approval on November 20, 2026. They checked deterministic reruns and recovery from an interruption before source storage. Both used the validated saved Pasto payload from `20261109T062536Z-9fp_q80e`, representing the IGAC August 31, 2026 release.

The tests used an in-memory harness around the existing sync. It supplied the saved payload instead of fetching the API and blocked unexpected source UPSERTs. No production source-code changes were made. The tests wrote real operational entries to `igac.sync_runs`, but preserved the cadastral source data.

## Common safeguards

- Privately verified that reader and loader connections targeted the same database and used `app_reader` and `igac_loader`, respectively. No credentials were printed or saved in this document.
- Compared the saved payload with the existing snapshot using binary database reads and the sync's content fingerprint before creating test log entries.
- Captured all existing source records, snapshot IDs, and audit timestamps before execution and compared them after each test execution.
- Used the limited loader role for sync logging and `app_reader` for verification. The sync's existing transaction and validation protections remained in place.
- Blocked source UPSERTs: an unexpected attempt to create or update source rows would fail the test instead of writing those rows.
- No automatic retries, database cleanup, permission changes, workflow triggers, or schema changes were performed.

## Test 1: Deterministic idempotency rerun

### Procedure

After verifying the saved payload matched the database, execute the sync twice with exactly the same validated input. Give each execution a distinct run ID and trigger `local`. After each execution, inspect its log entry and compare the source records, snapshot IDs, and audit timestamps with the captured baseline. Stop on any unexpected result.

This isolates database comparison, snapshot reuse, and logging from external API changes. It does not retest HTTP fetching or rate-limit handling.

### Prediction and observed results

Prediction for each execution: reuse snapshot 1; fetch 1,718 saved source records; insert 0 source records; update 0; report 1,718 unchanged. No new snapshot or source audit changes should occur.

| Run ID | Observed status | Trigger | Fetched | Inserted | Updated | Unchanged | Snapshot |
|---|---|---|---:|---:|---:|---:|---:|
| `bdae23ca-16c9-4698-87cf-53626b1a4385` | success | local | 1,718 | 0 | 0 | 1,718 | 1, reused |
| `737ac7c6-8d21-4d67-b086-e80d01f6641a` | success | local | 1,718 | 0 | 0 | 1,718 | 1, reused |

Both executions returned exit code 0. The actual counts matched the predictions. Full before-and-after comparisons confirmed that source records, snapshot IDs, and audit timestamps were unchanged after each execution. Each execution created its own completed success log entry with no error category.

Test date: November 20, 2026. Exact start and finish timestamps were not captured in the displayed rerun evidence and are not invented here. The run IDs identify the corresponding database entries for later inspection if needed.

**Outcome: passed for deterministic replay of unchanged content.** These fixed-payload tests do not establish behavior for a changed source version, concurrent writers, or an interrupted partial import.

## Test 2: Controlled interruption and recovery

### Procedure

1. Verify the database targets, roles, saved-payload match, and baseline source state.
2. Start one dedicated child process with a known run ID. Supply the fixed saved payload through an in-memory harness.
3. Pause the child immediately before `store()` begins, after its initial `running` entry has committed.
4. Confirm through the reader connection that the log entry exists, has trigger `local`, and is still `running` without a finish time or snapshot reference.
5. Send SIGTERM only to that child process and wait for its exit. Do not terminate a database backend.
6. Compare source records, snapshot IDs, and audit timestamps with the baseline. Verify that the interrupted log remains unchanged.
7. Execute exactly one recovery run using the same payload and blocked source UPSERTs.
8. Verify the recovery log, snapshot reuse, predicted counts, unchanged source state, and untouched interrupted entry.

### Prediction

The child should stop before source storage. Its committed log should remain `running`, with no finish time, no snapshot reference, and zero counters. Recovery should create a separate successful `local` entry, reuse snapshot 1, and report 1,718 fetched, 0 inserted, 0 updated, and 1,718 unchanged.

### Observed interruption

Run ID: `254f3825-7f3d-4e8a-8f77-13ab2ded58ae`.

| Event or field | Observed result |
|---|---|
| Started at, UTC | 2026-11-20 04:11:37.835203 |
| SIGTERM sent, UTC | 2026-11-20 04:11:38.208186 |
| Child exit code | -15, terminated by SIGTERM |
| Log status after interruption and recovery | running |
| Trigger | local |
| Finished at | null |
| Snapshot reference | null |
| Fetched / inserted / updated / unchanged | 0 / 0 / 0 / 0 |
| Snapshot created | false |
| Error category | null |
| Last updated at, UTC | 2026-11-20 04:11:37.835203 |

The committed `running` entry was confirmed before SIGTERM. Source records, IDs, and audit timestamps were unchanged after interruption. No source storage transaction began. The zero counters do not describe a completed fetch; the process stopped before run finalization.

### Observed recovery

Run ID: `d374efc8-4572-4068-9d6c-025b2d5c1155`.

| Event or field | Observed result |
|---|---|
| Started at, UTC | 2026-11-20 04:11:40.214068 |
| Finished at, UTC | 2026-11-20 04:11:41.789985 |
| Status / trigger | success / local |
| Exit code | 0 |
| Fetched / inserted / updated / unchanged | 1,718 / 0 / 0 / 1,718 |
| Snapshot | 1, reused; no new snapshot |
| Error category | null |

Recovery matched the predicted counts. Source records, snapshot IDs, and audit timestamps remained identical to the baseline. The interrupted entry was checked again and remained unchanged. Exactly one child was interrupted and one recovery execution was performed.

**Outcome: passed for resuming synchronization after interruption before source writes.**

### Limitations and abandoned log

The interrupted entry remains marked `running` even though its process has stopped. The current sync does not automatically detect or reconcile abandoned entries. A new recovery run uses a new run ID; it does not repair the old log. No cleanup or reconciliation was performed. Any later correction requires separate review and approval.

This test does **not** prove rollback after partial database writes, recovery from an uncertain commit, live API interruption, or GitHub runner cancellation. It protects production source records by stopping before storage and blocking source UPSERTs. The database was not isolated into a separate test instance; only the child execution was isolated, and the operational log entries are real.

## Follow-up reference evaluation after scheduled syncs

The first golden-question SQL baseline ran as `app_reader` on November 20, 2026, from **04:04:16.232060 to 04:04:27.557746 UTC**. Complete local output is retained in the ignored file `data/raw/evaluation_evidence/reference_baseline_20261120T040416232060Z.txt`.

### Verified scheduled executions before the follow-up

GitHub history, checked on November 20, 2026, showed these actual scheduled executions on `main`. Timestamps below are GitHub run start times, not database completion times.

| Actual start (UTC) | Status | Event | GitHub Actions evidence |
|---|---|---|---|
| 2026-11-20 07:43:53 | completed / success | schedule | [44697115181](https://github.com/Antoniahenaot/bsad6153-henao/actions/runs/44697115181) |
| 2026-11-20 13:39:45 | completed / success | schedule | [44746261611](https://github.com/Antoniahenaot/bsad6153-henao/actions/runs/44746261611) |
| 2026-11-20 19:28:18 | completed / success | schedule | [44802422249](https://github.com/Antoniahenaot/bsad6153-henao/actions/runs/44802422249) |

All three executions occurred after the baseline, satisfying the prerequisite of at least two additional scheduled syncs before repeating the reference evaluation. Local break-it runs and manual workflow runs are not counted toward that prerequisite.

### Procedure and measured outcome

With Antonia's approval, Codex executed `evals/check_reference.py --max-rows 10000` once in the `milestone-3` worktree. The checker verified `app_reader` before executing references, used read-only transactions and timeouts, and checked that decline questions had empty SQL. Complete answer output was captured without preview truncation. No database records, source code, credentials, or workflow settings were changed.

The follow-up ran on November 20, 2026, from **19:46:22.751460 to 19:46:33.845066 UTC**. Its separate ignored evidence file is `data/raw/evaluation_evidence/reference_followup_20261120T194622751460Z.txt`. The baseline file was not overwritten.

| Evaluation | SQL references passed with non-empty results | Failed | Decline questions skipped | Exit code |
|---|---:|---:|---:|---:|
| Baseline, 2026-11-20 04:04 UTC | 12 | 0 | 4 | 0 |
| Follow-up, 2026-11-20 19:46 UTC | 12 | 0 | 4 | 0 |

### Baseline comparison

Question statuses were identical. All reference answers were unchanged except the following expected operational-history changes, measured in the follow-up on November 20, 2026:

| Question | Baseline answer | Follow-up answer | Interpretation |
|---|---|---|---|
| 9: latest successful sync | Manual check finished 2026-11-20 03:33:58.839213 UTC | Scheduled check finished 2026-11-20 19:29:10.686748 UTC | A later successful scheduled check was recorded. Source release remained 2026-08-31. |
| 13: daily success/failure counts | Manual: 2 successes, 1 failure | Manual counts unchanged; local: 3 successes; scheduled: 3 successes | Controlled replay/recovery tests and the scheduled runs added legitimate history. Running entries are excluded by this question. |
| 14: successful-run durations | Manual: 2 runs, average 23.50 seconds | Manual results unchanged; local: 3 runs, average 1.57 seconds; scheduled: 3 runs, average 22.11 seconds | Additional trigger groups appeared. Local saved-payload executions are not comparable with full API retrieval for a performance-improvement claim. |

No unexpected reference-answer differences or SQL errors were found. In particular, original-pilot and latest-snapshot count answers remained unchanged. These checks establish executable SQL references, not chatbot-answer accuracy or actual refusal behavior; `should_decline` questions were skipped rather than tested against an LLM.

- [x] At least two additional scheduled executions identified after the baseline.
- [x] Follow-up reference checker completed successfully as `app_reader`.
- [x] Complete, credential-free follow-up evidence saved separately with UTC timestamps.
- [x] Reference answers compared with the baseline; expected changes explained.

## Completed: scheduled evidence spanning at least 48 hours

The earlier November 20 observation above remains historical evidence: its first three successful scheduled starts spanned only **11 hours, 44 minutes, 25 seconds**, so the requirement was pending at that time. The final read-only GitHub history review on November 22, 2026 (America/Chicago), identified the following **11 completed successful scheduled executions** on `main` between November 20 and November 22, 2026. All timestamps are actual GitHub run starts in UTC, not nominal cron slots or database completion times. Only `event=schedule` executions are included; manual and local test runs are excluded.

| Actual start (UTC) | Branch | Event | Status | GitHub Actions evidence |
|---|---|---|---|---|
| 2026-11-20 07:43:53 | main | event=schedule | completed / success | [44697115181](https://github.com/Antoniahenaot/bsad6153-henao/actions/runs/44697115181) |
| 2026-11-20 13:39:45 | main | event=schedule | completed / success | [44746261611](https://github.com/Antoniahenaot/bsad6153-henao/actions/runs/44746261611) |
| 2026-11-20 19:28:18 | main | event=schedule | completed / success | [44802422249](https://github.com/Antoniahenaot/bsad6153-henao/actions/runs/44802422249) |
| 2026-11-21 01:41:51 | main | event=schedule | completed / success | [44851693426](https://github.com/Antoniahenaot/bsad6153-henao/actions/runs/44851693426) |
| 2026-11-21 07:38:28 | main | event=schedule | completed / success | [44881178507](https://github.com/Antoniahenaot/bsad6153-henao/actions/runs/44881178507) |
| 2026-11-21 13:26:28 | main | event=schedule | completed / success | [44908865915](https://github.com/Antoniahenaot/bsad6153-henao/actions/runs/44908865915) |
| 2026-11-21 19:15:27 | main | event=schedule | completed / success | [44939946334](https://github.com/Antoniahenaot/bsad6153-henao/actions/runs/44939946334) |
| 2026-11-22 01:37:55 | main | event=schedule | completed / success | [44972352408](https://github.com/Antoniahenaot/bsad6153-henao/actions/runs/44972352408) |
| 2026-11-22 07:39:33 | main | event=schedule | completed / success | [44999226897](https://github.com/Antoniahenaot/bsad6153-henao/actions/runs/44999226897) |
| 2026-11-22 13:24:58 | main | event=schedule | completed / success | [45027363857](https://github.com/Antoniahenaot/bsad6153-henao/actions/runs/45027363857) |
| 2026-11-22 19:17:24 | main | event=schedule | completed / success | [45059899047](https://github.com/Antoniahenaot/bsad6153-henao/actions/runs/45059899047) |

The verified interval is **2026-11-22 19:17:24 UTC − 2026-11-20 07:43:53 UTC = 59 hours, 33 minutes, 31 seconds**. At least three successful scheduled executions therefore span more than 48 hours. **The 48-hour scheduled-run requirement is complete.** This is evidence for the listed observation window, not a guarantee of future execution or source-data currency.

- [x] Rechecked actual scheduled-run history after sufficient time elapsed.
- [x] Recorded successful scheduled URLs, UTC start timestamps, `main`, and `event=schedule`.
- [x] Verified at least three successful scheduled runs spanning at least 48 hours.

The interrupted test entry remains an abandoned `running` entry as documented above; the follow-up evaluation did not reconcile it or perform cleanup.
