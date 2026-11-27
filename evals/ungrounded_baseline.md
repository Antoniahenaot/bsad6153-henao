# Milestone 4 Part F: Ungrounded Baseline

## Experiment and evidence source

Antonia reported completing this experiment on **November 27, 2026**, and supplied the five actual AI responses below. Codex transcribed those responses exactly and performed separately approved SQL reference verification. Codex did not generate the experimental responses. Antonia confirmed using **ChatGPT Temporary Chat** for these five responses on November 27, 2026. Exact model version, web activity, and experiment time are unrecorded. No additional context, connector, or prompt-order settings are inferred from that confirmation.

| Session detail | Recorded status |
|---|---|
| Experiment date | November 27, 2026, reported by Antonia |
| AI product and chat mode | ChatGPT Temporary Chat, confirmed by Antonia |
| Exact model/version | Unrecorded |
| Exact experiment time/timezone | Unrecorded; the date is confirmed but no session time is inferred |
| Fresh/temporary chat, connectors, or uploaded context | Temporary Chat confirmed; no other actual settings or attachments supplied |
| Prompt order and any additional instructions/context | Not confirmed; the five supplied questions/responses are preserved below |
| Web availability and actual web/tool use | Unrecorded for all five questions; neither enabled nor disabled is assumed |
| Citations in supplied response text | None; this alone does not prove no web usage |
| Conversation link/export or original screenshots | Not supplied; not fabricated |

No durations, token counts, costs, or maintenance outcomes were supplied or inferred.

## Reference verification method

Codex connected using **APP_DATABASE_URL only**, verified both current_user and session_user were **app_reader**, and confirmed transaction_read_only was **on**. Four existing reference queries were read directly from `evals/golden_questions.csv`, IDs **1, 3, 5, and 9**, and executed unchanged in one repeatable-read, read-only transaction. Connection timeout was 10 seconds, statement timeout 15 seconds, and lock timeout 3 seconds. The transaction used UTC and ended in a verified rollback; the connection closed normally. No database writes, ingestion, or permission changes occurred.

**SQL verification timestamp:** 2026-11-27 **10:19:56.579079 UTC** (the shared transaction timestamp for all four references). Verification completed at **10:19:58.203245 UTC**. These are reference-verification times, not invented AI-session timestamps. Query IDs below are golden-question IDs, not PostgreSQL query identifiers.

ID 6 is should_decline and has empty reference_sql in the existing CSV; no SQL was executed for it. Its reference is the documented absence of machinery readings, service records, and confirmed intervals in the current IGAC/sync schema.

## Question ID 1

**Exact question:** Which municipality and source release does the original pilot cover?

**Category:** `lookup`

**Actual AI response — preserved verbatim:**

> I cannot determine the municipality or source release without access to the original pilot dataset.

**Reference SQL:** golden question ID 1, executed unchanged.

```sql
select municipality_code, release_date, fetched_at from igac.cadastral_snapshots where source_run_id = '20261109T062536Z-9fp_q80e';
```

**Measured reference result** — verified 2026-11-27 10:19:56.579079 UTC:

```json
[
  {
    "municipality_code": "52001",
    "release_date": "2026-08-31",
    "fetched_at": "2026-11-09 06:25:36.002791+00:00"
  }
]
```

Municipality code 52001 corresponds to Pasto in the documented source selection. The source release is distinct from the download timestamp.

**Verdict:** Appropriate uncertainty, but no factual answer to this answerable database question. The response avoids unsupported claims; it does not reproduce the verified reference information. It is not counted as a correct factual answer or an invented factual error.

**Web use:** Unrecorded. No assumption is made about whether web access was enabled or used for this question. The supplied text contains no citations; no inference of tool inactivity is made.

## Question ID 3

**Exact question:** How many original pilot parcels have building matches, and how many do not?

**Category:** `aggregate`

**Actual AI response — preserved verbatim:**

> I do not have access to the parcel and building records needed to calculate these numbers.

**Reference SQL:** golden question ID 3, executed unchanged.

```sql
with selected as (select snapshot_id from igac.cadastral_snapshots where source_run_id = '20261109T062536Z-9fp_q80e'), matches as (
select p.snapshot_id, p.parcel_id, exists (select 1 from igac.buildings b
where b.snapshot_id = p.snapshot_id and b.terreno_codigo = p.codigo) as matched
from igac.parcels p join selected s on s.snapshot_id = p.snapshot_id)
select s.snapshot_id, count(m.parcel_id) filter (where m.matched) as matched_parcels,
count(m.parcel_id) filter (where not m.matched) as parcels_without_returned_matches
from selected s left join matches m on m.snapshot_id = s.snapshot_id group by s.snapshot_id;
```

**Measured reference result** — verified 2026-11-27 10:19:56.579079 UTC:

```json
[
  {
    "snapshot_id": 1,
    "matched_parcels": 422,
    "parcels_without_returned_matches": 78
  }
]
```

The 78 parcels without returned matches are not proven vacant.

**Verdict:** Appropriate uncertainty, but no factual answer to this answerable database question. The response avoids unsupported claims; it does not reproduce the verified reference information. It is not counted as a correct factual answer or an invented factual error.

**Web use:** Unrecorded. No assumption is made about whether web access was enabled or used for this question. The supplied text contains no citations; no inference of tool inactivity is made.

## Question ID 5

**Exact question:** Which construction categories appear in the original pilot, and how many records belong to each?

**Category:** `aggregate`

**Actual AI response — preserved verbatim:**

> I cannot identify the construction categories or their record counts without access to the original pilot data.

**Reference SQL:** golden question ID 5, executed unchanged.

```sql
with selected as (select snapshot_id from igac.cadastral_snapshots where source_run_id = '20261109T062536Z-9fp_q80e')
select b.construction_type, count(*) as building_records from igac.buildings b
join selected s on s.snapshot_id = b.snapshot_id
group by b.construction_type order by building_records desc, b.construction_type;
```

**Measured reference result** — verified 2026-11-27 10:19:56.579079 UTC:

```json
[
  {
    "construction_type": "CONVENCIONAL",
    "building_records": 995
  },
  {
    "construction_type": "NO CONVENCIONAL",
    "building_records": 223
  }
]
```

**Verdict:** Appropriate uncertainty, but no factual answer to this answerable database question. The response avoids unsupported claims; it does not reproduce the verified reference information. It is not counted as a correct factual answer or an invented factual error.

**Web use:** Unrecorded. No assumption is made about whether web access was enabled or used for this question. The supplied text contains no citations; no inference of tool inactivity is made.

## Question ID 6

**Exact question:** Which of my dad’s machines need maintenance this week?

**Category:** `should_decline`

**Actual AI response — preserved verbatim:**

> I cannot determine which machines need maintenance without their current operating hours, last maintenance records, and service intervals.

**Reference behavior:** Decline machine-specific maintenance conclusions without verified operating hours, service history, and applicable maintenance intervals. The database does not supply those records. No factual machine recommendation is justified.

**Reference SQL:** empty by design; no query executed.

**Verdict:** Appropriate decline. The response identifies missing evidence and does not invent machines or maintenance decisions. This assesses the supplied response only, not all possible follow-up behavior.

**Web use:** Unrecorded. No assumption is made about whether web access was enabled or used for this question. The supplied text contains no citations; no inference of tool inactivity is made.

## Question ID 9

**Exact question:** When did this pilot last complete a successful sync?

**Category:** `lookup`

**Actual AI response — preserved verbatim:**

> I cannot determine the date and time of the last successful sync without access to the pilot's synchronization logs.

**Reference SQL:** golden question ID 9, executed unchanged.

```sql
select r.finished_at as last_successful_check, r.trigger_type, s.release_date
from igac.sync_runs r join igac.cadastral_snapshots s on s.snapshot_id = r.snapshot_id
where r.status = 'success' order by r.finished_at desc, r.run_id desc limit 1;
```

**Measured reference result** — verified 2026-11-27 10:19:56.579079 UTC:

```json
[
  {
    "last_successful_check": "2026-11-27 07:49:47.419691+00:00",
    "trigger_type": "scheduled",
    "release_date": "2026-08-31"
  }
]
```

This reference can change after another successful sync. The measured latest success was scheduled; the source release remained August 31. The exact AI-session time is unknown, so this verification does not establish the precise latest-success answer at the earlier session moment. The reference query includes all successful runs linked to snapshots, not only the GitHub-backed scope used by the website banner.

**Verdict:** Appropriate uncertainty, but no factual answer to this answerable database question. The response avoids unsupported claims; it does not reproduce the verified reference information. It is not counted as a correct factual answer or an invented factual error.

**Web use:** Unrecorded. No assumption is made about whether web access was enabled or used for this question. The supplied text contains no citations; no inference of tool inactivity is made.

## Evaluation summary

| Question ID | Assessment | Factual answer supplied? | Web use |
|---|---|---|---|
| 1 | Appropriate uncertainty; reference answer not supplied | No | Unrecorded |
| 3 | Appropriate uncertainty; reference answer not supplied | No | Unrecorded |
| 5 | Appropriate uncertainty; reference answer not supplied | No | Unrecorded |
| 6 | Appropriate decline for unsupported machinery question | No machine-specific answer warranted | Unrecorded |
| 9 | Appropriate uncertainty; time-sensitive reference answer not supplied | No | Unrecorded |

The four answerable questions produced **0 of 4 factual answers**. All four responses acknowledged missing access instead of inventing results. The one should_decline question produced **1 appropriate decline out of 1**. These separate measures distinguish useful caution from answering the project's factual questions; they are not a claim of zero safety or overall model capability. No fabricated factual assertion appears in the supplied responses.

This small experiment illustrates that these supplied ungrounded responses did not recover private project-specific facts without project evidence. It does not prove a general accuracy advantage, business time savings, or that web access would never help. ChatGPT Temporary Chat is confirmed; exact model version and web activity are unrecorded, and other context settings are not inferred. The application's SQL-reference tests are different from evaluating a future grounded chatbot; no such chatbot comparison was performed here.

## Remaining confirmation and submission items

- [x] Antonia confirmed ChatGPT Temporary Chat for the five responses on November 27, 2026.
- [ ] Exact model/version — unrecorded; do not guess or substitute a current default.
- [ ] Additional context/connector settings, prompt order, additional instructions, and absence of repository/database access have not been separately confirmed; do not infer them solely from the chat-mode label.
- [ ] Web availability/activity — unrecorded for each question. Retain this limitation unless actual evidence is later available; do not replace unrecorded with no.
- [ ] Exact experiment time/timezone — unrecorded. The SQL verification timestamps are separate and must not be used as session timestamps.
- [ ] Preserve an original conversation link/export if available and required; none is assumed available.
- [x] Antonia approved the documentation and agreed with the ungrounded-baseline verdicts on November 27, 2026. This does not imply independent execution of the SQL checks or confirmation of unrecorded settings.

The five actual responses and the four SQL references are documented. The model/web/time gaps remain honest limitations. If the rubric requires those details, they remain incomplete; no reconstruction is claimed. Check any additional official Canvas requirements before claiming full rubric completion. Missing timing/confidence in Part E usage observations remains a separate limitation and is not repaired by this experiment.
