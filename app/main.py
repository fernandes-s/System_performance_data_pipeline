import streamlit as st
import pandas as pd

from utils.queries import (
    load_metrics,
    load_anomaly_results,
    load_recent_metrics,
)
from utils.metrics import (
    get_summary_metrics,
    get_recent_window,
)
from utils.anomaly import (
    get_anomaly_count,
    get_anomaly_rate,
    get_anomaly_rows,
    get_top_anomaly_drivers,
)
from utils.charts import make_metric_line_chart
from utils.formatters import (
    format_timestamp,
    format_large_number,
    format_percentage,
)
from utils.ui_helpers import (
    section_header,
    show_empty_state,
    show_chart_or_empty,
    show_dataframe_preview,
    four_column_kpis,
)
from utils.db import database_exists

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="System Metrics Dashboard",
    page_icon="📊",
    layout="wide",
)


st.title("System Metrics Dashboard")
st.caption("A concise overview of system activity and anomaly detection results.")


# =========================
# LOAD DATA
# =========================
def normalize_anomaly_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardise anomaly result columns so the page works with both
    older and newer saved outputs.
    """
    if df.empty:
        return df.copy()

    df = df.copy()

    column_map = {
        "is_anomaly": "anomaly_flag",
        "anomaly_strength": "severity",
        "top_driver": "dominant_driver",
    }

    rename_dict = {
        old: new for old, new in column_map.items()
        if old in df.columns and new not in df.columns
    }

    if rename_dict:
        df = df.rename(columns=rename_dict)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    if "anomaly_score" in df.columns:
        df["anomaly_score"] = pd.to_numeric(df["anomaly_score"], errors="coerce")

    return df

if not database_exists():
    st.error("Database not found. Please check that data/raw/system_metrics.db exists.")
    st.stop()

metrics_df = load_metrics()
anomaly_df = normalize_anomaly_columns(load_anomaly_results())

if metrics_df.empty:
    st.warning("No data found in the metrics table yet.")
    st.stop()


# =========================
# PREP DATA
# =========================
summary = get_summary_metrics(metrics_df)
chart_df = get_recent_window(metrics_df, days=7)

anomaly_count = get_anomaly_count(anomaly_df)
anomaly_rate = get_anomaly_rate(anomaly_df)

driver_df = get_top_anomaly_drivers(anomaly_df)
top_driver = "N/A"
if not driver_df.empty and "feature" in driver_df.columns:
    top_driver = driver_df.iloc[0]["feature"]

preview_df = get_anomaly_rows(anomaly_df, n=5)


# =========================
# SYSTEM SNAPSHOT
# =========================
section_header("System Snapshot")

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
        "label": "Average CPU",
        "value": format_percentage(summary.get("avg_cpu")),
    },
    {
        "label": "Average Memory",
        "value": format_percentage(summary.get("avg_memory")),
    },
])


# =========================
# ANOMALY SNAPSHOT
# =========================
section_header("Anomaly Snapshot")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Detected Anomalies", f"{anomaly_count:,}")

with col2:
    st.metric(
        "Anomaly Rate",
        format_percentage(anomaly_rate, decimals=2) if anomaly_rate is not None else "N/A",
    )

with col3:
    st.metric("Top Driver", str(top_driver).replace("_", " ").title())


# =========================
# RECENT SYSTEM BEHAVIOUR
# =========================
section_header("Recent System Behaviour", "Last 7 days")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    cpu_fig = make_metric_line_chart(
        chart_df,
        metric="cpu_percent",
        title="CPU Usage",
    )
    show_chart_or_empty(cpu_fig, "No CPU chart data available.")

with chart_col2:
    memory_fig = make_metric_line_chart(
        chart_df,
        metric="memory_percent",
        title="Memory Usage",
    )
    show_chart_or_empty(memory_fig, "No memory chart data available.")


# =========================
# RECENT ANOMALY PREVIEW
# =========================
section_header("Recent Anomaly Preview")

if preview_df.empty:
    show_empty_state("No anomaly preview is available yet.")
else:
    preview_columns = [
        "timestamp",
        "anomaly_score",
        "severity",
        "dominant_driver",
        "cpu_percent",
        "memory_percent",
        "disk_percent",
    ]
    available_columns = [col for col in preview_columns if col in preview_df.columns]

    preview_display = preview_df[available_columns].copy()
    show_dataframe_preview(
        preview_display,
        max_rows=5,
        use_container_width=True,
    )


# =========================
# QUICK LINKS
# =========================
section_header("Explore More")

link_col1, link_col2, link_col3 = st.columns(3)

with link_col1:
    st.page_link("pages/anomalies.py", label="Open Anomalies", icon="🚨")

with link_col2:
    st.page_link("pages/model_diagnostics.py", label="Open Model Diagnostics", icon="📈")

with link_col3:
    st.page_link("pages/system_info.py", label="Open System Info", icon="🖥️")
