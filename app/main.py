from pathlib import Path
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st


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
# app/main.py -> project root -> data/raw/system_metrics.db
BASE_DIR = Path(__file__).resolve().parents[1]
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
# LOAD DATA
# =========================
st.title("System Metrics Monitoring Dashboard")
st.write(
    "This dashboard shows recent system performance data collected from the local machine "
    "and stored in SQLite. It provides a simple view of current system state and recent trends."
)

# check database exists
if not DB_PATH.exists():
    st.error(f"Database not found at: {DB_PATH}")
    st.stop()

df = load_data()

if df.empty:
    st.warning("No data found in the metrics table yet.")
    st.stop()


# =========================
# LATEST TIMESTAMP / BASIC INFO
# =========================
latest_timestamp = df["timestamp"].max()

col1, col2 = st.columns(2)
with col1:
    st.metric("Latest Timestamp", str(latest_timestamp))
with col2:
    st.metric("Total Records", len(df))


# =========================
# LAST 20 ROWS
# =========================
st.subheader("Last 20 Rows")
st.dataframe(
    df.sort_values("timestamp", ascending=False).head(20),
    use_container_width=True
)


# =========================
# CPU OVER TIME
# =========================
st.subheader("CPU Usage Over Time")
fig_cpu = px.line(
    df,
    x="timestamp",
    y="cpu_percent",
    title="CPU Usage (%)"
)
fig_cpu.update_layout(xaxis_title="Timestamp", yaxis_title="CPU %")
st.plotly_chart(fig_cpu, use_container_width=True)


# =========================
# MEMORY OVER TIME
# =========================
st.subheader("Memory Usage Over Time")
fig_memory = px.line(
    df,
    x="timestamp",
    y="memory_percent",
    title="Memory Usage (%)"
)
fig_memory.update_layout(xaxis_title="Timestamp", yaxis_title="Memory %")
st.plotly_chart(fig_memory, use_container_width=True)


# =========================
# DISK OVER TIME
# =========================
st.subheader("Disk Usage Over Time")
fig_disk = px.line(
    df,
    x="timestamp",
    y="disk_percent",
    title="Disk Usage (%)"
)
fig_disk.update_layout(xaxis_title="Timestamp", yaxis_title="Disk %")
st.plotly_chart(fig_disk, use_container_width=True)


# =========================
# NETWORK DELTAS
# =========================
st.subheader("Network Activity Over Time")

col3, col4 = st.columns(2)

with col3:
    fig_net_sent = px.line(
        df,
        x="timestamp",
        y="net_sent_delta_mb",
        title="Network Sent Delta (MB)"
    )
    fig_net_sent.update_layout(xaxis_title="Timestamp", yaxis_title="MB Sent")
    st.plotly_chart(fig_net_sent, use_container_width=True)

with col4:
    fig_net_recv = px.line(
        df,
        x="timestamp",
        y="net_recv_delta_mb",
        title="Network Received Delta (MB)"
    )
    fig_net_recv.update_layout(xaxis_title="Timestamp", yaxis_title="MB Received")
    st.plotly_chart(fig_net_recv, use_container_width=True)