from pathlib import Path
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Anomalies | System Metrics Dashboard",
    page_icon="🚨",
    layout="wide"
)


# =========================
# PATHS
# =========================
# pages/anomalies.py -> app -> project root
BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "raw" / "system_metrics.db"


# =========================
# DATABASE FUNCTIONS
# =========================
def get_connection():
    return sqlite3.connect(DB_PATH)


@st.cache_data
def load_data():
    conn = get_connection()

    query = """
        SELECT
            id,
            timestamp,
            cpu_percent,
            memory_percent,
            disk_percent,
            net_sent_total_mb,
            net_recv_total_mb,
            net_sent_delta_mb,
            net_recv_delta_mb,
            uptime_seconds
        FROM metrics
        ORDER BY timestamp ASC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df


# =========================
# PLACEHOLDER MODEL FUNCTION
# =========================
def run_anomaly_detection(df):
    """
    Placeholder anomaly function.
    Replace this later with your actual model logic.

    Expected future output:
    - anomaly_flag: 1 for anomaly, 0 for normal
    - anomaly_score: optional numeric score
    """

    df = df.copy()

    # Temporary placeholder logic:
    # mark high CPU or memory usage as anomalies
    df["anomaly_flag"] = (
        (df["cpu_percent"] > 85) |
        (df["memory_percent"] > 90) |
        (df["disk_percent"] > 95)
    ).astype(int)

    # Placeholder score
    df["anomaly_score"] = (
        df["cpu_percent"].fillna(0) * 0.4 +
        df["memory_percent"].fillna(0) * 0.4 +
        df["disk_percent"].fillna(0) * 0.2
    )

    return df


# =========================
# PAGE TITLE
# =========================
st.title("🚨 Anomaly Detection")
st.markdown(
    "This page is reserved for anomaly detection results. "
    "For now, it uses placeholder logic so the dashboard structure is ready."
)


# =========================
# LOAD DATA
# =========================
df = load_data()

if df.empty:
    st.warning("No data found in the database yet.")
    st.stop()


# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.header("Filters")

min_date = df["timestamp"].min().date()
max_date = df["timestamp"].max().date()

selected_dates = st.sidebar.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Handle both single-date and tuple returns safely
if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = min_date
    end_date = max_date

filtered_df = df[
    (df["timestamp"].dt.date >= start_date) &
    (df["timestamp"].dt.date <= end_date)
].copy()

if filtered_df.empty:
    st.warning("No records found for the selected date range.")
    st.stop()


# =========================
# PLACEHOLDER ANOMALY RESULTS
# =========================
results_df = run_anomaly_detection(filtered_df)

total_records = len(results_df)
total_anomalies = int(results_df["anomaly_flag"].sum())
anomaly_rate = (total_anomalies / total_records * 100) if total_records > 0 else 0
latest_timestamp = results_df["timestamp"].max()


# =========================
# KPI CARDS
# =========================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Records", f"{total_records:,}")
col2.metric("Detected Anomalies", f"{total_anomalies:,}")
col3.metric("Anomaly Rate", f"{anomaly_rate:.2f}%")
col4.metric("Latest Timestamp", str(latest_timestamp))


st.divider()


# =========================
# MAIN CHART - CPU WITH ANOMALIES
# =========================
st.subheader("CPU Usage Over Time")

fig_cpu = px.line(
    results_df,
    x="timestamp",
    y="cpu_percent",
    title="CPU Usage Timeline"
)

anomaly_points = results_df[results_df["anomaly_flag"] == 1]

if not anomaly_points.empty:
    fig_cpu.add_scatter(
        x=anomaly_points["timestamp"],
        y=anomaly_points["cpu_percent"],
        mode="markers",
        name="Anomalies"
    )

st.plotly_chart(fig_cpu, use_container_width=True)


# =========================
# SECONDARY CHARTS
# =========================
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Memory Usage Over Time")
    fig_mem = px.line(
        results_df,
        x="timestamp",
        y="memory_percent",
        title="Memory Usage Timeline"
    )
    st.plotly_chart(fig_mem, use_container_width=True)

with col_right:
    st.subheader("Disk Usage Over Time")
    fig_disk = px.line(
        results_df,
        x="timestamp",
        y="disk_percent",
        title="Disk Usage Timeline"
    )
    st.plotly_chart(fig_disk, use_container_width=True)


# =========================
# ANOMALY TABLE
# =========================
st.subheader("Detected Anomalies Table")

anomalies_only = results_df[results_df["anomaly_flag"] == 1].copy()

if anomalies_only.empty:
    st.info("No anomalies detected with the current placeholder logic.")
else:
    st.dataframe(
        anomalies_only[
            [
                "timestamp",
                "cpu_percent",
                "memory_percent",
                "disk_percent",
                "anomaly_score"
            ]
        ].sort_values("timestamp", ascending=False),
        use_container_width=True
    )


# =========================
# MODEL PLACEHOLDER SECTION
# =========================
st.divider()
st.subheader("Model Section")

st.info(
    "Your real anomaly detection model will be added here later. "
    "For example: Isolation Forest, threshold-based rules, or rolling-statistics detection."
)

with st.expander("Planned model integration"):
    st.markdown("""
    **Later you can replace the placeholder logic with:**
    - feature engineering
    - model loading
    - model inference
    - anomaly scoring
    - threshold tuning
    - explanation of flagged points
    """)


# =========================
# DOWNLOAD SECTION
# =========================
st.subheader("Export Results")

csv = results_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download anomaly results as CSV",
    data=csv,
    file_name="anomaly_results.csv",
    mime="text/csv"
)