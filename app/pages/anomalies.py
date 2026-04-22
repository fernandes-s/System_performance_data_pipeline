import streamlit as st
import pandas as pd

from utils.db import database_exists
from utils.queries import load_anomaly_results
from utils.anomaly import (
    get_anomaly_count,
    get_anomaly_rate,
    get_anomaly_rows,
    get_top_anomaly_drivers,
    classify_anomaly_severity,
)
from utils.charts import (
    make_anomaly_timeline_chart,
    make_score_distribution_chart,
    make_driver_bar_chart,
    make_severity_bar_chart,
)
from utils.formatters import (
    format_timestamp,
    format_percentage,
    format_large_number,
)
from utils.ui_helpers import (
    section_header,
    show_empty_state,
    show_chart_or_empty,
    show_dataframe_preview,
    four_column_kpis,
)

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Anomalies | System Metrics Dashboard",
    page_icon="🚨",
    layout="wide",
)

st.title("Anomaly Detection")
st.caption("A concise view of flagged behaviour, anomaly severity, and the main drivers over time.")


# =========================
# HELPERS
# =========================
def normalize_anomaly_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardise anomaly column names so the page works with both
    older and newer anomaly table outputs.
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

    return df


def ensure_required_columns(df: pd.DataFrame, required_columns: list[str]) -> None:
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        st.error(f"Missing required columns in anomaly table: {missing}")
        st.stop()


# =========================
# LOAD DATA
# =========================
if not database_exists():
    st.error("Database not found. Please check that data/raw/system_metrics.db exists.")
    st.stop()

df = load_anomaly_results()
df = normalize_anomaly_columns(df)

if df.empty:
    st.warning("No anomaly results found in the database yet.")
    st.stop()

ensure_required_columns(df, ["timestamp", "anomaly_score", "anomaly_flag"])

df = df.dropna(subset=["timestamp"]).copy()

if df.empty:
    st.warning("No valid anomaly timestamps are available.")
    st.stop()


# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.header("Filters")

min_date = df["timestamp"].min().date()
max_date = df["timestamp"].max().date()

selected_dates = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date, end_date = min_date, max_date

filtered_df = df[
    (df["timestamp"].dt.date >= start_date) &
    (df["timestamp"].dt.date <= end_date)
].copy()

show_only_anomalies = st.sidebar.checkbox("Show anomalies only", value=True)

if show_only_anomalies:
    filtered_df = filtered_df[filtered_df["anomaly_flag"] == 1].copy()

if "severity" in filtered_df.columns:
    severity_options = sorted(filtered_df["severity"].dropna().unique().tolist())

    if severity_options:
        selected_severity = st.sidebar.multiselect(
            "Severity",
            options=severity_options,
            default=severity_options,
        )

        if selected_severity:
            filtered_df = filtered_df[filtered_df["severity"].isin(selected_severity)].copy()

if filtered_df.empty:
    st.warning("No records found for the selected filters.")
    st.stop()

anomaly_only = filtered_df[filtered_df["anomaly_flag"] == 1].copy()


# =========================
# ADD SEVERITY IF MISSING
# =========================
if "severity" not in filtered_df.columns:
    filtered_df = classify_anomaly_severity(filtered_df)
    anomaly_only = filtered_df[filtered_df["anomaly_flag"] == 1].copy()


# =========================
# KPI SNAPSHOT
# =========================
latest_timestamp = filtered_df["timestamp"].max()
anomaly_count = get_anomaly_count(filtered_df)
anomaly_rate = get_anomaly_rate(filtered_df)

top_driver_df = get_top_anomaly_drivers(filtered_df)
top_driver = "N/A"
if not top_driver_df.empty and "feature" in top_driver_df.columns:
    top_driver = str(top_driver_df.iloc[0]["feature"]).replace("_", " ").title()

four_column_kpis([
    {
        "label": "Total Rows",
        "value": format_large_number(len(filtered_df)),
    },
    {
        "label": "Detected Anomalies",
        "value": format_large_number(anomaly_count),
    },
    {
        "label": "Anomaly Rate",
        "value": format_percentage(anomaly_rate, decimals=2) if anomaly_rate is not None else "N/A",
    },
    {
        "label": "Latest Record",
        "value": format_timestamp(latest_timestamp),
    },
])


# =========================
# SEVERITY + DRIVER SUMMARY
# =========================
section_header("Severity and Drivers")

left_col, right_col = st.columns(2)

with left_col:
    severity_fig = make_severity_bar_chart(filtered_df)
    show_chart_or_empty(severity_fig, "No severity breakdown is available.")

with right_col:
    driver_fig = make_driver_bar_chart(top_driver_df.head(6))
    show_chart_or_empty(driver_fig, "No driver summary is available.")


# =========================
# TIMELINES
# =========================
section_header("Anomaly Behaviour Over Time")

timeline_col1, timeline_col2 = st.columns(2)

with timeline_col1:
    score_fig = make_score_distribution_chart(
        filtered_df,
        score_column="anomaly_score",
        title="Anomaly Score Distribution",
    )
    show_chart_or_empty(score_fig, "No anomaly score data is available.")

with timeline_col2:
    metric_for_timeline = None
    for col in ["cpu_percent", "memory_percent", "disk_percent"]:
        if col in filtered_df.columns:
            metric_for_timeline = col
            break

    if metric_for_timeline:
        anomaly_timeline_fig = make_anomaly_timeline_chart(
            filtered_df,
            metric=metric_for_timeline,
            time_column="timestamp",
            flag_column="anomaly_flag",
            title=f"{metric_for_timeline.replace('_', ' ').title()} with Anomaly Markers",
        )
        show_chart_or_empty(anomaly_timeline_fig, "No anomaly timeline is available.")
    else:
        show_empty_state("No core metric columns are available for the timeline chart.")


# =========================
# RECENT ANOMALY TABLE
# =========================
section_header("Recent Anomalies")

preview_df = get_anomaly_rows(filtered_df, n=10)

if preview_df.empty:
    show_empty_state("No anomalies detected in the selected range.")
else:
    preview_columns = [
        "timestamp",
        "anomaly_score",
        "severity",
        "dominant_driver",
        "cpu_percent",
        "memory_percent",
        "disk_percent",
        "net_sent_delta_mb",
        "net_recv_delta_mb",
    ]
    available_columns = [col for col in preview_columns if col in preview_df.columns]

    preview_display = preview_df[available_columns].copy()
    show_dataframe_preview(preview_display, max_rows=10)


# =========================
# OPTIONAL FULL RESULTS
# =========================
with st.expander("Full filtered results and export"):
    st.dataframe(
        filtered_df.sort_values("timestamp", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download filtered results as CSV",
        data=csv,
        file_name="anomaly_results_filtered.csv",
        mime="text/csv",
    )