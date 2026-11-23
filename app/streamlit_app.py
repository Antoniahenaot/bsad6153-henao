"""Read-only Pasto pilot. Public deployment awaits IGAC reuse verification."""
import logging
import os
from contextlib import contextmanager
from datetime import datetime, timezone

import psycopg
import streamlit as st
from dotenv import load_dotenv

ORIGINAL_RUN = "20261109T062536Z-9fp_q80e"
CACHE_SECONDS = 600
FRESHNESS_HOURS = 24
ALL_BLOCKS = "all"
MISSING_BLOCK = "missing"


@contextmanager
def reader():
    """Never fall back to a setup/loader login or expose connection details."""
    url = os.environ.get("APP_DATABASE_URL")
    if not url:
        raise PermissionError("Reader configuration unavailable")
    with psycopg.connect(url, connect_timeout=10, autocommit=True) as conn:
        with conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            conn.execute("SET LOCAL statement_timeout = '10s'")
            conn.execute("SET LOCAL lock_timeout = '3s'")
            if not conn.execute("SELECT current_user = 'app_reader'").fetchone()[0]:
                raise PermissionError("Expected app_reader")
            yield conn


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def context_data():
    with reader() as conn:
        snapshot = conn.execute(
            "SELECT snapshot_id, municipality_code, release_date, fetched_at "
            "FROM igac.cadastral_snapshots WHERE source_run_id = %s", (ORIGINAL_RUN,)
        ).fetchone()
        if snapshot is not None and snapshot[1] != "52001":
            raise ValueError("Unexpected pilot geography")
        blocks = []
        if snapshot:
            blocks = [row[0] for row in conn.execute(
                "SELECT DISTINCT manzana_codigo FROM igac.parcels "
                "WHERE snapshot_id = %s ORDER BY manzana_codigo NULLS LAST",
                (snapshot[0],)
            ).fetchall()]
        latest = conn.execute(
            "SELECT r.finished_at, r.snapshot_id, s.release_date "
            "FROM igac.sync_runs r JOIN igac.cadastral_snapshots s "
            "ON s.snapshot_id = r.snapshot_id "
            "WHERE r.status = %s AND r.trigger_type IN ('manual', 'scheduled') "
            "AND r.github_run_id IS NOT NULL "
            "ORDER BY r.finished_at DESC, r.run_id DESC LIMIT 1", ("success",)
        ).fetchone()
    return snapshot, blocks, latest


# Fixed SQL structure; user choices are always bound parameters.
PARCEL_SCOPE = """
    p.snapshot_id = %s AND
    (%s = 'all' OR (%s = 'missing' AND p.manzana_codigo IS NULL)
     OR (%s = 'code' AND p.manzana_codigo = %s))
"""


@st.cache_data(ttl=CACHE_SECONDS, show_spinner=False)
def view_data(snapshot_id, block_mode, block_code):
    if block_mode not in {"all", "missing", "code"}:
        raise ValueError("Invalid block selection")
    params = (snapshot_id, block_mode, block_mode, block_mode, block_code)
    with reader() as conn:
        parcels = conn.execute(
            "SELECT p.codigo, count(b.building_id) AS building_records "
            "FROM igac.parcels p LEFT JOIN igac.buildings b "
            "ON b.snapshot_id = p.snapshot_id AND b.terreno_codigo = p.codigo "
            "WHERE " + PARCEL_SCOPE +
            " GROUP BY p.parcel_id, p.codigo ORDER BY building_records DESC, p.codigo",
            params
        ).fetchall()
        categories = conn.execute(
            "SELECT b.construction_type, count(*) FROM igac.parcels p "
            "JOIN igac.buildings b ON b.snapshot_id = p.snapshot_id "
            "AND b.terreno_codigo = p.codigo WHERE " + PARCEL_SCOPE +
            " GROUP BY b.construction_type ORDER BY count(*) DESC, b.construction_type",
            params
        ).fetchall()
    if sum(row[1] for row in parcels) != sum(row[1] for row in categories):
        raise ValueError("Inconsistent view totals")
    return parcels, categories


def freshness_banner(latest, displayed_snapshot, now=None):
    if latest is None:
        st.warning("No successful GitHub sync check recorded. Local replays do not count.")
        return
    finished, checked_snapshot, release = latest
    finished = finished.astimezone(timezone.utc)
    now = now or datetime.now(timezone.utc)
    age = (now - finished.astimezone(timezone.utc)).total_seconds() / 3600
    if age < 0:
        st.warning("The sync timestamp is inconsistent; freshness is unknown.")
        return
    message = f"Last successful GitHub sync check: {finished:%Y-%m-%d %H:%M} UTC ({age:.1f} hours ago)."
    if age > FRESHNESS_HOURS:
        st.warning("Sync check overdue (24-hour operational threshold). " + message)
    else:
        st.success(message)
    st.caption(f"Latest checked source release: {release}. A successful check does not establish current site conditions.")
    if displayed_snapshot is not None and checked_snapshot != displayed_snapshot:
        st.warning("The latest sync checked a different snapshot. These views retain the original historical pilot.")


def about():
    st.info("Limited Pasto sample, not representative of all Pasto or Manizales. Missing building matches do not establish vacancy. Categories do not establish occupancy, safety, or machinery requirements.")
    st.caption("This pilot explores property-data usefulness as mapping context. It contains no machine readings, service history, or maintenance intervals and demonstrates no maintenance time savings.")
    st.markdown(
        "**Source:** Instituto Geográfico Agustín Codazzi (IGAC), August 31, 2026 release; "
        "Pasto urban land (`U_TERRENO`, layer 7) and buildings (`U_CONSTRUCCION`, layer 3). "
        "[IGAC source](https://services2.arcgis.com/RVvWzU3lgJISqdke/ArcGIS/rest/services/CATASTRO_PUBLICO_31082026/FeatureServer)."
    )
    st.warning("Public deployment blocked pending verification of IGAC reuse and attribution terms: release metadata lists CC BY-SA 4.0 while the national listing lists CC BY 4.0. No license resolution is claimed.")


def main():
    # No secret values are printed. No AI clients, sign-in, or write features.
    logging.getLogger("dotenv.main").disabled = True
    load_dotenv(verbose=False, interpolate=False)
    st.set_page_config(page_title="Pasto Property-Data Pilot", page_icon=":bar_chart:")
    st.title("Pasto Property-Data Pilot")
    st.caption("Explore returned parcel–building coverage and construction categories.")
    about()
    st.caption("Results cached for up to 10 minutes; refresh occurs on a page interaction or reload after expiry. Sync checks are scheduled every six hours; the 24-hour warning does not guarantee current source data.")
    if not os.environ.get("APP_DATABASE_URL"):
        st.info("Data is unavailable: the read-only database connection is not configured.")
        return
    try:
        snapshot, blocks, latest = context_data()
        freshness_banner(latest, snapshot[0] if snapshot else None)
        if snapshot is None:
            st.info("The original saved Pasto snapshot is unavailable. Another snapshot will not be substituted.")
            return
        st.write(f"Displayed historical snapshot: {snapshot[0]} · Pasto (52001) · IGAC release: {snapshot[2]}")
        st.caption(f"Original run: {ORIGINAL_RUN}. Downloaded: {snapshot[3].astimezone(timezone.utc):%Y-%m-%d %H:%M} UTC.")
        options = [(ALL_BLOCKS, None)] + [(MISSING_BLOCK if b is None else "code", b) for b in blocks]
        mode, code = st.selectbox(
            "Block", options,
            format_func=lambda item: "All blocks" if item[0] == ALL_BLOCKS else ("Missing block code" if item[0] == MISSING_BLOCK else item[1])
        )
        parcels, categories = view_data(snapshot[0], mode, code)
        st.caption("Both views use the selected block scope within the original snapshot.")
        if not parcels:
            st.info("No parcel records match this selection. Try another block or All blocks.")
            return
        st.header("Parcel–Building Coverage")
        matched = sum(count > 0 for _, count in parcels)
        cols = st.columns(4)
        for col, label, value in zip(cols, ["Parcels", "Returned building records", "Parcels with matches", "Parcels without returned matches"], [len(parcels), sum(n for _, n in parcels), matched, len(parcels) - matched]):
            col.metric(label, value)
        st.dataframe([{"Parcel code": code, "Returned building records": count} for code, count in parcels], hide_index=True)
        st.caption("No returned building match does not mean a parcel is vacant.")
        st.header("Construction Categories")
        if categories:
            st.dataframe([{"Category": name, "Building records": count} for name, count in categories], hide_index=True)
            st.bar_chart({"Category": [r[0] for r in categories], "Building records": [r[1] for r in categories]}, x="Category", y="Building records")
            st.caption("Distinct source records are preserved even when building codes repeat.")
        else:
            st.info("These parcels have no returned building records; no construction categories are available.")
    except PermissionError:
        st.error("Data is unavailable: a read-only app_reader connection is required.")
    except (psycopg.Error, ValueError, TypeError, KeyError):
        st.error("Data is unavailable right now. Please try again later. Connection and technical details are withheld.")


if __name__ == "__main__":
    main()
