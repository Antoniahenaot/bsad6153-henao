# BSAD 6153 Project: Construction Equipment Management System

**Student:** Antonia Henao  
**My decision:** Which construction machines need maintenance this week based on their operating hours?  
**Website:** &lt;your domain, from Week 4&gt;

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
| `DATABASE_URL` (owner) | `.env` | **never** | Actions secret |
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
   - Environment variables: `PYTHON_VERSION=3.12.4`, `APP_DATABASE_URL`, and later your LLM key and `APP_PASSWORD`
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
preserved row IDs and audit timestamps. A complete clean-start test of these
setup instructions is still pending. [Implementation brief](docs/implementation_brief.md)

## Credits

Cadastral data provided by Instituto Geográfico Agustín Codazzi (IGAC),
August 31, 2026 release. This project uses a subset for Pasto, Colombia,
from `U_TERRENO` (urban land, layer 7) and `U_CONSTRUCCION` (urban buildings,
layer 3). [IGAC service directory](https://services2.arcgis.com/RVvWzU3lgJISqdke/ArcGIS/rest/services/CATASTRO_PUBLICO_31082026/FeatureServer)

IGAC's release metadata lists CC BY-SA 4.0, while Colombia's national
open-data listing shows CC BY 4.0. The terms for these exact layers still
need confirmation before the sample or a map is shared publicly.
[Data dictionary and source references](docs/data_dictionary.md#ethical-use-and-attribution)
