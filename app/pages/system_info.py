import socket
import platform

import pandas as pd
import streamlit as st

from utils.db import database_exists
from utils.queries import load_metrics
from utils.metrics import (
    get_summary_metrics,
    get_recent_window,
    get_recent_rows,
    calculate_collection_gaps,
    calculate_system_health,
)
from utils.charts import make_metric_line_chart
from utils.formatters import (
    format_timestamp,
    format_percentage,
    format_large_number,
    format_duration,
)
from utils.ui_helpers import (
    section_header,
    show_empty_state,
    show_chart_or_empty,
    show_dataframe_preview,
    four_column_kpis,
    show_status_badge,
)


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="System Info",
    page_icon="🖥️",
    layout="wide",
)

st.title("System Information")
st.caption("A concise view of current system health, recent collection coverage, and core machine details.")


# =========================
# HELPERS
# =========================
import os
import socket
import platform


def get_machine_info() -> dict:
    return {
        "hostname": socket.gethostname(),

        # Better OS naming
        "operating_system": f"{platform.system()} {platform.release()}",

        # Clean version
        "os_version": platform.version(),

        # Cleaner architecture
        "architecture": platform.architecture()[0].replace("bit", "-bit"),

        # Better processor (Windows env variable)
        "processor": os.environ.get("PROCESSOR_IDENTIFIER", "Not available"),
    }

# =========================
# LOAD DATA
# =========================
if not database_exists():
    st.error("Database not found. Please check that data/raw/system_metrics.db exists.")
    st.stop()

df = load_metrics()

if df.empty:
    st.warning("No data found in the metrics table yet.")
    st.stop()

if "timestamp" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

df = df.dropna(subset=["timestamp"]).copy()

if df.empty:
    st.warning("No valid timestamps are available in the metrics table.")
    st.stop()


# =========================
# PREP DATA
# =========================
summary = get_summary_metrics(df)
recent_df = get_recent_window(df, days=7)
latest_rows = get_recent_rows(df, n=10)
gap_df = calculate_collection_gaps(df)
health = calculate_system_health(df)
machine_info = get_machine_info()

latest_row = df.sort_values("timestamp").iloc[-1]

current_cpu = latest_row["cpu_percent"] if "cpu_percent" in latest_row else None
current_memory = latest_row["memory_percent"] if "memory_percent" in latest_row else None
current_disk = latest_row["disk_percent"] if "disk_percent" in latest_row else None
latest_uptime = latest_row["uptime_seconds"] if "uptime_seconds" in latest_row else None


# =========================
# KPI SNAPSHOT
# =========================
four_column_kpis([
    {
        "label": "Latest Timestamp",
        "value": format_timestamp(summary.get("latest_timestamp")),
    },
    {
        "label": "Total Records",
        "value": format_large_number(summary.get("row_count")),
    },
    {
        "label": "Current CPU",
        "value": format_percentage(current_cpu),
    },
    {
        "label": "Current Memory",
        "value": format_percentage(current_memory),
    },
])


# =========================
# HEALTH STATUS
# =========================
section_header("Current Health")

left_col, right_col = st.columns([1, 2])

with left_col:
    show_status_badge(health.get("status", "Unknown"))

with right_col:
    info_lines = []

    if current_disk is not None:
        info_lines.append(f"Disk usage is currently {format_percentage(current_disk)}.")
    if latest_uptime is not None:
        info_lines.append(f"Recorded uptime is {format_duration(latest_uptime)}.")
    info_lines.append(f"Detected collection gaps: {len(gap_df):,}.")

    st.info(" ".join(info_lines))


# =========================
# RECENT TRENDS
# =========================
section_header("Recent System Behaviour", "Last 7 days")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    cpu_fig = make_metric_line_chart(
        recent_df,
        metric="cpu_percent",
        title="CPU Usage",
    )
    show_chart_or_empty(cpu_fig, "No CPU trend is available.")

with chart_col2:
    memory_fig = make_metric_line_chart(
        recent_df,
        metric="memory_percent",
        title="Memory Usage",
    )
    show_chart_or_empty(memory_fig, "No memory trend is available.")


# =========================
# MACHINE DETAILS
# =========================
section_header("Machine Details")

info_col1, info_col2 = st.columns(2)

with info_col1:
    st.write(f"**Hostname:** {machine_info['hostname']}")
    st.write(f"**Operating System:** {machine_info['operating_system']}")
    st.write(f"**Version:** {machine_info['os_version']}")

with info_col2:
    st.write(f"**Architecture:** {machine_info['architecture']}")
    st.write(f"**Processor:** {machine_info['processor']}")

# =========================
# RECENT DATA PREVIEW
# =========================
section_header("Recent Records")

preview_columns = [
    "timestamp",
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "net_sent_delta_mb",
    "net_recv_delta_mb",
    "uptime_seconds",
]
available_columns = [col for col in preview_columns if col in latest_rows.columns]

if latest_rows.empty or not available_columns:
    show_empty_state("No recent records are available.")
else:
    preview_df = latest_rows[available_columns].sort_values("timestamp", ascending=False)
    show_dataframe_preview(preview_df, max_rows=10)


# =========================
# OPTIONAL ADVANCED DETAILS
# =========================
with st.expander("Advanced details"):
    st.markdown("**Collection coverage**")
    st.write(f"First timestamp: {format_timestamp(df['timestamp'].min())}")
    st.write(f"Latest timestamp: {format_timestamp(df['timestamp'].max())}")
    st.write(f"Collection gaps detected: {len(gap_df):,}")

    if not gap_df.empty:
        gap_preview_cols = ["timestamp", "gap_minutes"]
        available_gap_cols = [col for col in gap_preview_cols if col in gap_df.columns]
        if available_gap_cols:
            st.dataframe(
                gap_df[available_gap_cols].sort_values("timestamp", ascending=False),
                use_container_width=True,
                hide_index=True,
            )

    st.markdown(f"**Available columns** - {', '.join(df.columns.tolist())}")
