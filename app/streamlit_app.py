"""Your public website. Run it locally from the project folder:

    streamlit run app/streamlit_app.py

This starter works before anything is configured, so you can test it during Week 1 Setup.
You'll extend it with your AI agent: data views in Week 4, the chatbot in Week 5,
and the agent in Week 6. Read every change before you accept it.

Two rules this file follows, and yours must keep following:
  * It connects ONLY as the read-only role (APP_DATABASE_URL), never as the owner.
  * Anything that spends money (the chatbot) or acts (the agent) sits behind the sign-in.
"""

import hmac
import os
from datetime import datetime, timezone

import psycopg
import streamlit as st
from dotenv import load_dotenv

# Locally, secrets come from .env. On Render they come from the service's environment settings.
load_dotenv()

# Maximum age of a successful GitHub sync check before a pipeline warning.
# This threshold does not establish freshness of the source release.
FRESHNESS_HOURS = float(os.environ.get("FRESHNESS_HOURS", "24"))

st.set_page_config(page_title="My BSAD 6153 Project", page_icon=":bar_chart:")


@st.cache_data(ttl=600)  # Re-check every 10 minutes. Keep the TTL shorter than your sync interval.
def _query_latest_successful_sync():
    # Streamlit caches only successful results, never errors, so a brief database
    # outage doesn't stay on screen for the whole TTL.
    with psycopg.connect(
        os.environ["APP_DATABASE_URL"], connect_timeout=10, autocommit=True
    ) as conn, conn.transaction():
        conn.execute("SET TRANSACTION READ ONLY")
        conn.execute("SET LOCAL statement_timeout = '10s'")
        if not conn.execute("SELECT current_user = 'app_reader'").fetchone()[0]:
            raise PermissionError("Expected read-only application role.")
        # Exclude local saved-payload test replays from live workflow-check freshness.
        row = conn.execute(
            """
            SELECT r.finished_at, s.release_date
            FROM igac.sync_runs r
            JOIN igac.cadastral_snapshots s ON s.snapshot_id = r.snapshot_id
            WHERE r.status = %s AND r.trigger_type IN ('manual', 'scheduled')
              AND r.github_run_id IS NOT NULL
            ORDER BY r.finished_at DESC, r.run_id DESC
            LIMIT 1
            """, ("success",)
        ).fetchone()
        if row is None:
            release = conn.execute(
                "SELECT release_date FROM igac.cadastral_snapshots "
                "ORDER BY fetched_at DESC, snapshot_id DESC LIMIT 1"
            ).fetchone()
            return None, release[0] if release else None
        return row


def latest_successful_sync():
    """Return ((GitHub check time, source release date), state), without raw errors."""
    if not os.environ.get("APP_DATABASE_URL"):
        return None, "not_configured"
    try:
        return _query_latest_successful_sync(), "ok"
    except psycopg.errors.UndefinedTable:
        return None, "no_sync_runs"
    except PermissionError:
        return None, "wrong_role"
    except psycopg.Error:
        return None, "db_error"


def freshness_banner():
    result, state = latest_successful_sync()
    if state == "not_configured":
        st.info("Database connection is not configured.")
    elif state == "no_sync_runs":
        st.info("Sync history or source metadata is unavailable.")
    elif state in ("db_error", "wrong_role"):
        st.warning("The sync check is unavailable right now. Please try again later.")
    else:
        finished_at, release_date = result
        if finished_at is None:
            st.warning("No successful GitHub sync check is recorded. Local test replays do not count as live checks.")
        else:
            finished_at = finished_at.astimezone(timezone.utc)
            hours_old = (datetime.now(timezone.utc) - finished_at).total_seconds() / 3600
            message = (
                f"Last successful GitHub sync check: {finished_at:%Y-%m-%d %H:%M} UTC "
                f"({hours_old:.1f} hours ago)."
            )
            if hours_old > FRESHNESS_HOURS:
                st.warning("The sync check is overdue. " + message)
            else:
                st.success(message)
        if release_date is None:
            st.info("Source release date is unavailable; source freshness is unknown.")
        else:
            st.info(
                f"IGAC source release: {release_date:%Y-%m-%d}. "
                "A successful check does not mean the source was updated or reflects current site conditions."
            )


def signed_in():
    """Simple password sign-in for the parts of the site that spend money or take actions.

    The password lives in the APP_PASSWORD environment variable, never in code. Share it
    with the instructors privately. An alternative is Streamlit's built-in st.login(),
    which signs people in with an identity provider such as Google; it needs extra setup.
    """
    if st.session_state.get("signed_in"):
        return True
    expected = os.environ.get("APP_PASSWORD", "")
    if not expected:
        st.info("Sign-in isn't set up yet. Add APP_PASSWORD to your environment (Week 5).")
        return False
    with st.form("sign_in"):
        attempt = st.text_input("Password", type="password")
        if st.form_submit_button("Sign in"):
            # compare_digest avoids leaking information through timing differences.
            if hmac.compare_digest(attempt.encode(), expected.encode()):
                st.session_state["signed_in"] = True
                st.rerun()
            else:
                st.error("That password is incorrect.")
    return False


st.title("My BSAD 6153 Project")
st.caption("Replace this title and caption with what your site helps you decide.")

freshness_banner()

st.header("Data")
st.write("Your Week 4 views go here: at least two views that answer your own questions.")

st.header("Assistant")
if signed_in():
    st.write("Your Week 5 chatbot goes here, and your Week 6 agent after it.")
    if st.button("Sign out"):
        st.session_state["signed_in"] = False
        st.rerun()

with st.expander("About this site"):
    st.write(
        "A student project for BSAD 6153 AI Implementations at Newman University. "
        "Say what the data is, where it comes from (with the attribution your API requires), "
        "and how often it's updated. On Render's free tier the site sleeps when idle, "
        "so the first visit can take about a minute."
    )
