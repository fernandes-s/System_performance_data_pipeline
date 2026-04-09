from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st

from utils.db import (
    database_exists,
    get_recent_window,
    get_summary_metrics,
    load_data,
)
from utils.charts import make_line_chart


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="System Metrics Dashboard",
    page_icon="📊",
    layout="wide"
)


# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "raw" / "system_metrics.db"
ANOMALY_TABLE = "anomaly_results"


# =========================
# DATABASE HELPERS
# =========================
def get_connection():
    return sqlite3.connect(DB_PATH)


@st.cache_data(ttl=60)
def get_table_names():
    conn = get_connection()
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = pd.read_sql_query(query, conn)
    conn.close()
    return tables["name"].tolist()


@st.cache_data(ttl=60)
def load_anomaly_results():
    if not DB_PATH.exists():
        return pd.DataFrame()

    table_names = get_table_names()
    if ANOMALY_TABLE not in table_names:
        return pd.DataFrame()

    conn = get_connection()
    query = f"""
        SELECT *
        FROM {ANOMALY_TABLE}
        ORDER BY timestamp ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty and "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    return df


def build_anomaly_summary(anomaly_df: pd.DataFrame) -> dict:
    """
    Creates homepage-friendly anomaly summary metrics.
    """
    summary = {
        "total_scored_rows": 0,
        "anomaly_count": 0,
        "anomaly_rate": 0.0,
        "strong_count": 0,
        "top_driver": "Not available",
        "latest_anomaly_timestamp": "Not available",
    }

    if anomaly_df.empty or "is_anomaly" not in anomaly_df.columns:
        return summary

    scored_rows = len(anomaly_df)
    anomaly_only = anomaly_df[anomaly_df["is_anomaly"] == 1].copy()
    anomaly_count = len(anomaly_only)
    anomaly_rate = (anomaly_count / scored_rows * 100) if scored_rows > 0 else 0.0

    summary["total_scored_rows"] = scored_rows
    summary["anomaly_count"] = anomaly_count
    summary["anomaly_rate"] = anomaly_rate

    if "anomaly_strength" in anomaly_only.columns:
        summary["strong_count"] = int((anomaly_only["anomaly_strength"] == "strong").sum())

    if not anomaly_only.empty:
        if "top_driver" in anomaly_only.columns:
            driver_counts = anomaly_only["top_driver"].dropna().value_counts()
            if not driver_counts.empty:
                summary["top_driver"] = driver_counts.index[0]

        if "timestamp" in anomaly_only.columns:
            latest_ts = anomaly_only["timestamp"].max()
            if pd.notna(latest_ts):
                summary["latest_anomaly_timestamp"] = str(latest_ts)

    return summary


# =========================
# LOAD DATA
# =========================
st.title("System Metrics Monitoring Dashboard")
st.write(
    "A lightweight overview of the system monitoring pipeline. "
    "Use the navigation cards below to explore anomaly detection, system information, and model details."
)

if not database_exists():
    st.error("Database not found. Please check that data/raw/system_metrics.db exists.")
    st.stop()

df = load_data()

if df.empty:
    st.warning("No data found in the metrics table yet.")
    st.stop()

anomaly_df = load_anomaly_results()


# =========================
# PREP DATA
# =========================
summary = get_summary_metrics(df)
chart_df = get_recent_window(df, days=7)
anomaly_summary = build_anomaly_summary(anomaly_df)


# =========================
# KPI ROW
# =========================
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    with st.container(border=True):
        st.metric("Latest Timestamp", summary["latest_timestamp_display"])

with kpi2:
    with st.container(border=True):
        st.metric("Total Records", f'{summary["total_records"]:,}')

with kpi3:
    with st.container(border=True):
        st.metric("Average CPU", f'{summary["avg_cpu"]:.1f}%')

with kpi4:
    with st.container(border=True):
        st.metric("Average Memory", f'{summary["avg_memory"]:.1f}%')


# =========================
# ANOMALY OVERVIEW
# =========================
st.subheader("Latest Model Output")

a1, a2, a3, a4 = st.columns(4)

with a1:
    with st.container(border=True):
        st.metric("Detected Anomalies", f'{anomaly_summary["anomaly_count"]:,}')

with a2:
    with st.container(border=True):
        st.metric("Anomaly Rate", f'{anomaly_summary["anomaly_rate"]:.2f}%')

with a3:
    with st.container(border=True):
        st.metric("Strong Anomalies", f'{anomaly_summary["strong_count"]:,}')

with a4:
    with st.container(border=True):
        st.metric("Top Driver", anomaly_summary["top_driver"])


with st.container(border=True):
    st.markdown("### Quick Interpretation")

    if anomaly_df.empty:
        st.info(
            "No saved anomaly results were found yet. Run the training pipeline to populate the anomaly dashboard pages."
        )
    else:
        st.write(
            f"The latest saved model run scored {anomaly_summary['total_scored_rows']:,} records "
            f"and flagged {anomaly_summary['anomaly_count']:,} anomalies "
            f"({anomaly_summary['anomaly_rate']:.2f}% of scored rows)."
        )

        if anomaly_summary["top_driver"] != "Not available":
            st.write(
                f"The most common type of flagged behaviour was **{anomaly_summary['top_driver']}**."
            )

        if anomaly_summary["latest_anomaly_timestamp"] != "Not available":
            st.write(
                f"The latest detected anomaly in the saved results occurred at "
                f"**{anomaly_summary['latest_anomaly_timestamp']}**."
            )


st.caption("Overview charts below show the most recent 7 days of data.")


# =========================
# QUICK NAVIGATION
# =========================
st.subheader("Explore the Dashboard")

nav1, nav2, nav3 = st.columns(3)

with nav1:
    with st.container(border=True):
        st.markdown("### Anomalies")
        st.write("Investigate detected anomalies and view flagged system behaviour on charts.")
        st.page_link("pages/anomalies.py", label="Open Anomalies Page", icon="🚨")

with nav2:
    with st.container(border=True):
        st.markdown("### System Info")
        st.write("Review pipeline health, database coverage, time ranges, and data quality checks.")
        st.page_link("pages/system_info.py", label="Open System Info Page", icon="🖥️")

with nav3:
    with st.container(border=True):
        st.markdown("### Model Diagnostics")
        st.write("Inspect model settings, anomaly scores, and feature-level detection details.")
        st.page_link("pages/model_diagnostics.py", label="Open Model Diagnostics", icon="📈")


# =========================
# OVERVIEW CHARTS
# =========================
st.subheader("Recent System Behaviour")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        fig_cpu = make_line_chart(
            chart_df,
            y_col="cpu_percent",
            title="CPU Usage",
            y_label="CPU %"
        )
        st.plotly_chart(fig_cpu, width="stretch")

with col2:
    with st.container(border=True):
        fig_memory = make_line_chart(
            chart_df,
            y_col="memory_percent",
            title="Memory Usage",
            y_label="Memory %"
        )
        st.plotly_chart(fig_memory, width="stretch")


# =========================
# RECENT ANOMALIES PREVIEW
# =========================
st.subheader("Recent Anomaly Preview")

if anomaly_df.empty or "is_anomaly" not in anomaly_df.columns:
    st.info("No anomaly preview is available yet.")
else:
    anomaly_only = anomaly_df[anomaly_df["is_anomaly"] == 1].copy()

    preview_cols = [
        "timestamp",
        "anomaly_score",
        "anomaly_strength",
        "top_driver",
        "explanation",
        "cpu_percent",
        "memory_percent",
        "disk_percent",
        "net_sent_delta_mb",
        "net_recv_delta_mb",
    ]
    available_preview_cols = [col for col in preview_cols if col in anomaly_only.columns]

    if anomaly_only.empty:
        st.info("No anomalies have been flagged in the latest saved model output.")
    else:
        st.dataframe(
            anomaly_only
            .sort_values("anomaly_score", ascending=False)
            .head(5)[available_preview_cols],
            use_container_width=True,
            hide_index=True
        )