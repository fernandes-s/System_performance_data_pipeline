from pathlib import Path
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Anomalies | System Performance Dashboard",
    page_icon="🚨",
    layout="wide"
)


# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parents[2]
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


@st.cache_data(ttl=60)
def load_latest_training_info():
    """
    Tries to pull a quick summary from anomaly_results itself.
    If you later create a metadata table, this function can be replaced easily.
    """
    conn = get_connection()

    try:
        query = f"""
            SELECT *
            FROM {ANOMALY_TABLE}
            ORDER BY timestamp DESC
            LIMIT 1
        """
        df = pd.read_sql_query(query, conn)
    except Exception:
        df = pd.DataFrame()

    conn.close()
    return df


def safe_metric(value, fmt="{:,.0f}", fallback="N/A"):
    if value is None:
        return fallback
    try:
        if pd.isna(value):
            return fallback
        return fmt.format(value)
    except Exception:
        return str(value)


# =========================
# PAGE HEADER
# =========================
st.title("🚨 Anomaly Detection")
st.markdown(
    "This page shows the anomaly detection output saved by the training pipeline."
)


# =========================
# CHECK DATABASE / TABLE
# =========================
if not DB_PATH.exists():
    st.error(f"Database not found: {DB_PATH}")
    st.stop()

table_names = get_table_names()

if ANOMALY_TABLE not in table_names:
    st.warning(
        f"Table '{ANOMALY_TABLE}' was not found in the database.\n\n"
        "Run your training script first so the model results are written to SQLite."
    )

    with st.expander("Available tables"):
        st.write(table_names)

    st.stop()


# =========================
# LOAD DATA
# =========================
df = load_anomaly_results()

if df.empty:
    st.warning("The anomaly_results table exists, but it is empty.")
    st.stop()

required_columns = [
    "timestamp",
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "anomaly_score",
    "is_anomaly",
]

missing_required = [col for col in required_columns if col not in df.columns]
if missing_required:
    st.error(f"Missing required columns in '{ANOMALY_TABLE}': {missing_required}")
    st.stop()

df = df.dropna(subset=["timestamp"]).copy()

if df.empty:
    st.warning("No valid timestamps found in anomaly results.")
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
    max_value=max_date
)

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date, end_date = min_date, max_date

filtered_df = df[
    (df["timestamp"].dt.date >= start_date) &
    (df["timestamp"].dt.date <= end_date)
].copy()

show_only_anomalies = st.sidebar.checkbox("Show anomalies only", value=False)

if show_only_anomalies:
    filtered_df = filtered_df[filtered_df["is_anomaly"] == 1].copy()

if filtered_df.empty:
    st.warning("No records found for the selected filters.")
    st.stop()


# =========================
# KPI SECTION
# =========================
total_records = len(filtered_df)
total_anomalies = int(filtered_df["is_anomaly"].sum())
anomaly_rate = (total_anomalies / total_records * 100) if total_records > 0 else 0
latest_timestamp = filtered_df["timestamp"].max()

if total_anomalies > 0:
    max_anomaly_score = filtered_df.loc[filtered_df["is_anomaly"] == 1, "anomaly_score"].max()
else:
    max_anomaly_score = None

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Records", safe_metric(total_records))
col2.metric("Anomalies", safe_metric(total_anomalies))
col3.metric("Anomaly Rate", f"{anomaly_rate:.2f}%")
col4.metric("Latest Record", str(latest_timestamp))

st.divider()


# =========================
# MODEL / RUN INFO
# =========================
latest_info = load_latest_training_info()

with st.expander("Run details"):
    st.write(f"Database: `{DB_PATH}`")
    st.write(f"Source table: `{ANOMALY_TABLE}`")
    st.write(f"Date range in filtered view: **{start_date}** to **{end_date}**")

    if max_anomaly_score is not None:
        st.write(f"Highest anomaly score in current view: **{max_anomaly_score:.6f}**")

    if not latest_info.empty:
        st.write("Latest saved row preview:")
        st.dataframe(latest_info, use_container_width=True)


# =========================
# MAIN CHART - CPU WITH ANOMALY POINTS
# =========================
st.subheader("CPU Usage with Detected Anomalies")

fig_cpu = px.line(
    filtered_df,
    x="timestamp",
    y="cpu_percent",
    title="CPU Usage Over Time"
)

anomaly_points = filtered_df[filtered_df["is_anomaly"] == 1]

if not anomaly_points.empty:
    fig_cpu.add_scatter(
        x=anomaly_points["timestamp"],
        y=anomaly_points["cpu_percent"],
        mode="markers",
        name="Anomalies"
    )

fig_cpu.update_layout(xaxis_title="Timestamp", yaxis_title="CPU %")
st.plotly_chart(fig_cpu, use_container_width=True)


# =========================
# SECOND ROW OF CHARTS
# =========================
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Memory Usage")
    fig_mem = px.line(
        filtered_df,
        x="timestamp",
        y="memory_percent",
        title="Memory Usage Over Time"
    )

    if not anomaly_points.empty:
        fig_mem.add_scatter(
            x=anomaly_points["timestamp"],
            y=anomaly_points["memory_percent"],
            mode="markers",
            name="Anomalies"
        )

    fig_mem.update_layout(xaxis_title="Timestamp", yaxis_title="Memory %")
    st.plotly_chart(fig_mem, use_container_width=True)

with right_col:
    st.subheader("Disk Usage")
    fig_disk = px.line(
        filtered_df,
        x="timestamp",
        y="disk_percent",
        title="Disk Usage Over Time"
    )

    if not anomaly_points.empty:
        fig_disk.add_scatter(
            x=anomaly_points["timestamp"],
            y=anomaly_points["disk_percent"],
            mode="markers",
            name="Anomalies"
        )

    fig_disk.update_layout(xaxis_title="Timestamp", yaxis_title="Disk %")
    st.plotly_chart(fig_disk, use_container_width=True)


# =========================
# ANOMALY SCORE OVER TIME
# =========================
st.subheader("Anomaly Score Over Time")

fig_score = px.line(
    filtered_df,
    x="timestamp",
    y="anomaly_score",
    title="Anomaly Score Timeline"
)

if not anomaly_points.empty:
    fig_score.add_scatter(
        x=anomaly_points["timestamp"],
        y=anomaly_points["anomaly_score"],
        mode="markers",
        name="Detected Anomalies"
    )

fig_score.update_layout(xaxis_title="Timestamp", yaxis_title="Anomaly Score")
st.plotly_chart(fig_score, use_container_width=True)


# =========================
# DAILY ANOMALY COUNTS
# =========================
st.subheader("Daily Anomaly Counts")

daily_counts = filtered_df.copy()
daily_counts["date"] = daily_counts["timestamp"].dt.date
daily_counts = (
    daily_counts.groupby("date", as_index=False)["is_anomaly"]
    .sum()
    .rename(columns={"is_anomaly": "anomaly_count"})
)

fig_daily = px.bar(
    daily_counts,
    x="date",
    y="anomaly_count",
    title="Number of Anomalies Per Day"
)
fig_daily.update_layout(xaxis_title="Date", yaxis_title="Count")
st.plotly_chart(fig_daily, use_container_width=True)


# =========================
# DETAILED ANOMALY TABLE
# =========================
st.subheader("Detected Anomalies")

anomalies_only = filtered_df[filtered_df["is_anomaly"] == 1].copy()

preferred_columns = [
    "timestamp",
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "net_sent_delta_mb",
    "net_recv_delta_mb",
    "uptime_seconds",
    "anomaly_score",
    "is_anomaly",
]

table_columns = [col for col in preferred_columns if col in anomalies_only.columns]

if anomalies_only.empty:
    st.info("No anomalies detected in the selected date range.")
else:
    st.dataframe(
        anomalies_only[table_columns].sort_values("timestamp", ascending=False),
        use_container_width=True,
        hide_index=True
    )


# =========================
# FULL RESULTS TABLE
# =========================
st.subheader("Full Results")

full_table_columns = [col for col in preferred_columns if col in filtered_df.columns]

st.dataframe(
    filtered_df[full_table_columns].sort_values("timestamp", ascending=False),
    use_container_width=True,
    hide_index=True
)


# =========================
# DOWNLOAD SECTION
# =========================
st.subheader("Export")

csv_data = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download filtered anomaly results as CSV",
    data=csv_data,
    file_name="filtered_anomaly_results.csv",
    mime="text/csv"
)