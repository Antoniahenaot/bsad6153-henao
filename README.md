# BSAD 6153 Project: Construction Equipment Management System

**Student:** Antonia Henao  
**My decision:** Which construction machines need maintenance this week based on their operating hours?  
**Website:** [Pasto Property-Data Pilot](https://bsad6153-henao.onrender.com) — deployed from `milestone-4`, not yet the final `main` deployment.

This repository is one complete AI system, built over eight weeks: a real API, synced on a schedule into a
PostgreSQL database, shown on a public website, with a chatbot and an agent that answer and act from your
own data. You build it with an AI coding agent, and you read and verify everything it writes.

---

## Setting up your computer (Week 1 Setup)

You need a **Windows 10/11 or macOS computer where you can install software**, Git, Python 3.12, and your AI
coding agent (Claude Code, Codex, Antigravity, or Copilot). Let your agent help with the installs, but read
every command before you approve it, and keep auto-approve off.

1. **Clone this repository** into a short folder path that isn't synced by OneDrive or Dropbox, for example
   `C:\dev\bsad6153` on Windows or `~/dev/bsad6153` on macOS.
2. **Create and activate a virtual environment** from the project folder:

   | | Windows (PowerShell) | macOS (Terminal) |
   |---|---|---|
   | Create | `py -3.12 -m venv .venv` | `python3.12 -m venv .venv` |
   | Activate | `.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |

   You'll see `(.venv)` at the start of your prompt when it's active. Activate it every time you open a new terminal.
3. **Install the packages:** `pip install -r requirements.txt`
4. **Create your secrets file:** copy `.env.example` to `.env`, and put a fake value on the `TEST_SECRET=` line.
5. **Check everything:** `python scripts/check_setup.py` should end with `Setup OK`.
6. **Try the website:** `streamlit run app/streamlit_app.py` opens it in your browser. Press Ctrl+C to stop it.

### Working with your AI agent

- **You approve every command.** Read it first, and if you don't understand it, ask the agent what it does.
- **Ask for a plan before code:** "Before writing anything, tell me your plan."
- **Never paste a real key into the chat,** and never ask the agent to print your `.env` file.
- **The agent never gets the owner database password or deploy tokens.** That's how agents delete databases.
- **Record what you directed, read, verified, and decided** in each pull request's AI review log.

---

## Project layout

| Folder | What goes there | When |
|---|---|---|
| `ingest/` | Fetch, load, and sync code | Weeks 1&ndash;3 |
| `db/` | `schema.sql`, `roles.sql`, `queries.sql` | Weeks 2&ndash;6 |
| `docs/` | Data dictionary, logs, reports (see `docs/README.md`) | Every week |
| `evals/` | Golden questions and evaluation runs | Weeks 3&ndash;7 |
| `app/` | Your website (Streamlit) | Weeks 4&ndash;6 |
| `examples/` | A reference tool-using chatbot loop | Week 5 |
| `scripts/` | Setup and database checks | Weeks 0&ndash;2 |
| `data/sample/` | A small sample of raw API data (large downloads go in `data/raw/`, which Git ignores) | Week 1 |

## Secrets: where each one lives

| Secret | On your computer | On Render (website) | In GitHub Actions (sync) |
|---|---|---|---|
| `DATABASE_URL` (setup) | `.env` | **never** | **never** |
| `IGAC_LOADER_DATABASE_URL` (limited loader/sync) | `.env` | no | Actions secret |
| `APP_DATABASE_URL` (read-only) | `.env` | environment setting | if your checks need it |
| `AGENT_DATABASE_URL` | `.env` | environment setting | no |
| LLM key, `APP_PASSWORD` | `.env` | environment setting | no |
| Data API key | `.env` | no | Actions secret |

`.env.example` lists the names only. If a secret ever leaks, revoke or rotate it first, then tell the instructor.

---

## Deploying on Render (Week 4)

1. Claim your free domain through the GitHub Student Developer Pack.
2. In Render, choose **New &gt; Blueprint**, pick this repository, and enter each secret when asked.
   (`render.yaml` describes the service.) Or create a **Web Service** by hand with:
   - Build command: `pip install -r requirements.txt`
   - Start command: `streamlit run app/streamlit_app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
   - Environment variables: `PYTHON_VERSION=3.12.10`, `FRESHNESS_HOURS=24`, and private `APP_DATABASE_URL` for `app_reader`. No AI key, owner/loader URL, or password feature is needed for this milestone.
3. Under **Settings &gt; Custom Domains**, add your domain, then add the DNS records Render shows you at your
   registrar. Ask your agent to explain each record before you add it. HTTPS turns on automatically.
4. Free services sleep when idle and take about a minute to wake. Say so on your site.

---

## Troubleshooting

- **`pip install` fails with "No such file or directory" on Windows:** the folder path is too long. Move the
  project to a short path such as `C:\dev\bsad6153` and recreate `.venv`.
- **PowerShell says running scripts is disabled when you activate:** use Command Prompt instead and run
  `.venv\Scripts\activate.bat`, or ask the instructor. Don't change system security settings without asking.
- **`python` opens the Microsoft Store or isn't found:** use `py -3.12` on Windows or `python3.12` on macOS.
- **The database check can't connect:** use Supabase's Session pooler string, check the password, and check
  that your Supabase project isn't paused.

---

## Project proposal (Week 1)

I want to build a website to help my dad manage his construction machinery business in Manizales, Colombia. He has six machines and six operators. The operators send photos of the hour meters or write down the readings. My dad uses a notebook and Excel to track machine hours. He spends about eight hours a week recording and reviewing this information, and sometimes an oil change is missed.

The website would let operators submit readings directly. My dad could see each machine’s operating hours, who is assigned to it, and which machines may need maintenance this week. A future agent would prepare a weekly oil change review list. For each machine on the list, it would show the latest reading and the maintenance record behind the reminder. I would measure success by tracking time spent on recordkeeping and how often oil changes are overdue.

My provisional primary API for the map is [IGAC’s public cadastral service](https://services2.arcgis.com/RVvWzU3lgJISqdke/ArcGIS/rest/services/CATASTRO_PUBLICO_31082026/FeatureServer), using Pasto as a pilot pending instructor approval. The pilot would show how parcel boundaries and existing building footprints could help my dad understand a job site. The business operates in Manizales, and operators would still supply the machine hours. The [Manizales municipal cadastral API](https://sig.manizales.gov.co/wadmzl/rest/services/2022_WEB/2022_consulta_catas_urbano_web_NEW/MapServer) is an unverified backup. Its count requests timed out, so I would test access and confirm reuse terms before relying on it.

Late or incorrect readings could lead to unreliable reminders. The website should flag missing readings and ask before changing records, deleting information, or marking maintenance complete. Map records can also be outdated or incomplete. I would confirm the license before public display and keep worker and job information private. Later, I’d like to add machine availability, expected job completion dates, and job progress.

## How to run this project

After completing the setup steps above, activate your virtual environment
and run this from the repository root to fetch the Milestone 1 data:

```sh
python ingest/fetch.py
```

The script downloads land and related building records for Pasto, Colombia.
It saves the original API responses and a summary in a new run folder under
`data/raw/2026-08-31/`. Git ignores that folder.

To inspect a few records without making an API request, open the local
[Milestone 1 sample](data/sample/README.md).

### Milestone 2 database setup

Complete the Python environment setup above and install `requirements.txt`.
Copy `.env.example` to `.env` only if `.env` does not already exist. Enter
connection strings directly in your local editor, with percent-encoded passwords.
Use Supabase Session pooler connections on port 5432.

| Variable | Database role |
|---|---|
| `DATABASE_URL` | Setup role for schema creation and checks |
| `IGAC_LOADER_DATABASE_URL` | `igac_loader` for the import |
| `APP_DATABASE_URL` | `app_reader` for read-only application access |

In a fresh database, review and run `db/schema.sql` in the Supabase SQL editor
as the setup role, followed by `db/roles.sql`. Each script uses a transaction.
They expect unused schema and role names. If those objects exist, review their
configuration first. Our current database already has these objects.

Set the role passwords separately through a trusted PostgreSQL client's private
password prompts. For example, in an authenticated setup session in the optional
PostgreSQL `psql` client, run:

```text
\password igac_loader
\password app_reader
```

For each custom role's Session pooler URL, replace the database-role portion
of the pooler username while keeping the project reference, and use that role's
own password. Save the connection strings in the ignored local `.env` file.
Review shared `PUBLIC` permissions in a fresh database. Our verified setup
permits temporary tables but restricts permanent object creation and unrelated
application data access. The Supabase Data API is disabled for this project.

### Load the saved IGAC run

From the repository root with the virtual environment activated, replace the
path below with the folder containing `complete.json` and the saved JSON pages:

```sh
python ingest/load.py --validate-only /absolute/path/to/saved-run
python ingest/load.py /absolute/path/to/saved-run
```

The first command checks local files. The second uses `IGAC_LOADER_DATABASE_URL`
and loads all three tables in one transaction. Repeat the second command with
the same folder to check idempotency. Our saved run is in the original checkout
under `data/raw/2026-08-31/20261109T062536Z-9fp_q80e/`. A fresh checkout needs a
completed saved run, or a new download using the fetch command above. Verify
counts separately for any new download.

### Check the reader and execute the SQL questions

```sh
python scripts/check_db.py --app
```

This checks the `APP_DATABASE_URL` connection. It prints the database username
and server version, and may print connection details on failure. Keep its output
private when recording a demonstration.

Open `db/queries.sql` in the Supabase SQL editor and run its five queries inside
`BEGIN READ ONLY;` and `ROLLBACK;`. The editor uses its selected database role.
The queries filter our verified saved run. For a different run, adjust the run ID
and the November 2026 time filter. A separate direct `app_reader` connection was
verified to read all three tables.

Our load produced 1 snapshot, 500 parcels, and 1,218 buildings. Repeating it
preserved row IDs and audit timestamps. A full clean-start reproduction has
**not been performed**. The implemented database and scheduled pipeline passed
their documented checks; that is distinct from testing this entire setup in
an empty database. [Implementation brief](docs/implementation_brief.md)

### Milestone 3 clean-checkout guide

**Status:** these instructions have been reviewed against the project files.
A full clean-start reproduction has **not been performed**. Do not mark the
PR's clean-start item complete based on this documentation review.

#### Branch and Python environment

Until PR #5 merges, use `milestone-3` to obtain Parts E–H. `main` currently
contains the merged Parts A–D pipeline. For a new macOS checkout:

```sh
git clone --branch milestone-3 https://github.com/Antoniahenaot/bsad6153-henao.git bsad6153-henao
cd bsad6153-henao
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

After PR #5 merges, use `main` for the complete milestone instead. Windows
environment commands appear in the setup table above. These are instructions
for a new checkout, not a request to switch or overwrite an existing worktree.

Create `.env` from `.env.example` only if `.env` does not already exist.
Enter authorized connection values privately in your editor. A fresh checkout
intentionally has no usable credentials, raw downloads, or local evaluation
evidence. Use the Session pooler format described above.

| Task | Configuration and role |
|---|---|
| Quality checks, golden references, and freshness display | `APP_DATABASE_URL` for `app_reader` |
| Import/sync and run logging | `IGAC_LOADER_DATABASE_URL` for `igac_loader` |
| Schema, role, and migration setup | Authorized setup role; never the scheduled application connection |

No LLM key or agent connection is needed for Milestone 3 SQL verification.

#### Existing versus completely new database

**Existing course database:** schema, roles, and the migration are already
applied. Configure the authorized reader connection to run read-only checks.
Do not rerun fresh-setup SQL, reset passwords, or import data merely because
you cloned the repository.

**Completely new database:** after review, the setup role runs these files in
order. Each file uses its own transaction:

1. `db/schema.sql` creates `igac` and the source tables.
2. `db/roles.sql` creates the limited loader and reader roles.
3. `db/migrations/003_sync_runs.sql` creates the run log and its permissions.

The scripts expect unused names. Inspect conflicts rather than dropping
existing objects. Set role passwords through private prompts as described
above, review shared/default privileges, and verify Enable Data API is OFF in
the Supabase Dashboard. The scheduled workflow never applies migrations.

Populate a new database only with approval, using the saved-run validation
and import commands above or a separately approved download. Raw files are
not included in a clone. Any separately approved publication must preserve
the source/data-adaptation CC BY-SA 4.0 conditions; see [data licensing](docs/data_license.md). The live sync command is `python ingest/sync.py`; it makes API
requests and writes source data and operational logs.

#### Read-only quality checks and golden references

With the environment activated and `APP_DATABASE_URL` privately configured,
the following example executes the existing quality SQL as `app_reader`.
It needs only the pinned psycopg and python-dotenv packages. Run it only when
database access is approved; this example has not been executed as part of
the documentation update.

```sh
python - <<'PY'
import logging
import os
import sys
from pathlib import Path
import psycopg
from dotenv import dotenv_values

logging.getLogger("dotenv.main").disabled = True
try:
    url = os.environ.get("APP_DATABASE_URL") or dotenv_values(
        Path(".env"), interpolate=False
    ).get("APP_DATABASE_URL")
    if not url:
        raise RuntimeError("Reader connection missing")
    with psycopg.connect(url, connect_timeout=10, autocommit=True) as connection:
        with connection.transaction():
            connection.execute("SET TRANSACTION READ ONLY")
            connection.execute("SET LOCAL statement_timeout = '10s'")
            if not connection.execute(
                "SELECT current_user = 'app_reader'"
            ).fetchone()[0]:
                raise RuntimeError("Expected app_reader")
        with connection.cursor() as cursor:
            cursor.execute(Path("db/quality_checks.sql").read_text(), prepare=False)
            while True:
                if cursor.description:
                    print([column.name for column in cursor.description])
                    for row in cursor.fetchall():
                        print(row)
                if not cursor.nextset():
                    break
except Exception:
    print("Quality checks failed; connection and error details withheld.")
    sys.exit(1)
PY
```

The SQL file starts a read-only, repeatable-read transaction, sets a statement
timeout, and ends with `ROLLBACK`. Do not substitute an owner connection.
Installing the optional `psql` client is not necessary for this example.

Run the golden reference checker with:

```sh
python evals/check_reference.py --max-rows 10000
```

The checker validates the CSV and `app_reader`, then executes the twelve
answerable references in read-only transactions. Four `should_decline`
questions have empty SQL and are skipped, not tested against an LLM. Empty
results or SQL errors cause a nonzero exit. Check for a preview-truncation
notice before describing saved output as complete.

**Original-snapshot dependency:** Q01–Q05 (CSV IDs 1–5) intentionally select
`source_run_id = '20261109T062536Z-9fp_q80e'`. They answer historical questions
about that original saved pilot, which the existing course database contains.
A completely new database populated by a new download may lack that run;
the reference queries can then return empty results and fail the checker.
Either obtain approved access to the original completed saved run, preserving
its metadata and folder identity, or review and adjust the questions and
reference scope/provenance to an available run. Do not relabel a new download
as the original or copy old answer counts.

Q10–Q12 use the snapshot linked to the latest successful sync; loading raw
data without a successful sync entry does not satisfy that scope. Operational
questions depend on actual history: a new database may have no failed run for
Q15. Do not invent log entries to make references pass.

The freshness display opens with `streamlit run app/streamlit_app.py` and
performs read-only database queries. It separates the successful GitHub check
from the IGAC release. Without a GitHub-backed successful run it correctly
shows no qualifying check; a local replay is not treated as fresh API access.
To reproduce scheduling in another repository, configure its limited loader
repository secret and put the reviewed workflow on its default `main` branch.
Manual/local tests do not substitute for elapsed scheduled-run evidence.

See [data quality](docs/data_quality.md), [test evidence](docs/sync_tests.md),
and [lineage](docs/data_dictionary.md) for verified results and limitations.
Those results do not establish a full new-database reproduction.

## Credits

Cadastral data provided by Instituto Geográfico Agustín Codazzi (IGAC),
August 31, 2026 release. This project uses a subset for Pasto, Colombia,
from `U_TERRENO` (urban land, layer 7) and `U_CONSTRUCCION` (urban buildings,
layer 3). [IGAC service directory](https://services2.arcgis.com/RVvWzU3lgJISqdke/ArcGIS/rest/services/CATASTRO_PUBLICO_31082026/FeatureServer)

The exact source service item explicitly states **CC BY-SA 4.0**, independently supported by IGAC release metadata, verified November 25, 2026. Antonia approved applying it to the source data and project data-derived presentations/adaptations. Filtering, relationships, counts, and charts are project changes; credit IGAC, link the source/license, indicate changes, preserve applicable notices, and do not imply endorsement. The national portal's previously reported CC BY 4.0 label remains an unexplained discrepancy, not a confirmed replacement license. This notice does not relicense independent application code or dependencies. [Evidence, attribution, and scope](docs/data_license.md).


## Milestone 4 operating expectations

The original Pasto snapshot remains historical. A **600-second (10-minute) cache TTL** reduces repeated database reads; snapshot/block arguments separate view entries. Expired results refresh on a later interaction or reload, not continuously in an idle browser. GitHub Actions on main schedules sync every **six hours** (`23 */6 * * *`); delays or failures are possible. `FRESHNESS_HOURS` controls the warning threshold with a safe default of **24 hours**, measuring the last qualifying GitHub-backed check rather than current source conditions.

Render Free web services spin down after **15 minutes without inbound traffic** and normally take **about one minute** to wake on the next request. This is an expected cold start, not a guaranteed recovery time. Process-local caches do not survive restarts; persistent source records remain in Supabase. Free usage limits can suspend service, and free hosting is not a production availability guarantee. [Render Free documentation](https://render.com/docs/free), checked November 25, 2026.

The blueprint uses Python 3.12.10, pinned dependencies, `$PORT`, and `0.0.0.0`. Render documents fully qualified released Python versions through `PYTHON_VERSION` ([runtime documentation](https://render.com/docs/python-version)). Antonia reported a successful Render deployment from `milestone-4` on November 25, 2026, and personally checked the HTTPS website in Safari. Both views and the block filter displayed the verified totals; attribution/license information and an approximately 3.1-hour-old sync check were visible. See [browser evidence](docs/app_verification.md#antonia-safari-verification-and-local-display-corrections--november-25-2026). This is not the final `main`-branch deployment or a full clean-start reproduction. The zero-baseline chart and shorter metric-label corrections made after that review are local only until approved commit/push/redeployment. Do not expose setup or loader credentials to the website.
