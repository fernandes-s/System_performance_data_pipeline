# app/pages/system_info.py

from pathlib import Path
import sqlite3
from datetime import datetime, timedelta

import pandas as pd
import platform
import psutil
import streamlit as st


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="System Info",
    page_icon="🖥️",
    layout="wide"
)


# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "raw" / "system_metrics.db"


# =========================
# DATABASE FUNCTIONS
# =========================
def get_connection():
    return sqlite3.connect(DB_PATH)


@st.cache_data(ttl=30)
def load_latest_metrics():
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
        ORDER BY timestamp DESC
        LIMIT 1
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return None

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.iloc[0]


@st.cache_data(ttl=30)
def load_recent_metrics(limit=120):
    conn = get_connection()

    query = f"""
        SELECT
            timestamp,
            cpu_percent,
            memory_percent,
            disk_percent,
            net_sent_delta_mb,
            net_recv_delta_mb
        FROM metrics
        ORDER BY timestamp DESC
        LIMIT {limit}
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return df

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


# =========================
# HEALTH RULES
# =========================
def get_status(value, warning, critical):
    if value >= critical:
        return "🔴 Critical"
    elif value >= warning:
        return "🟡 Warning"
    return "🟢 Healthy"


def calculate_health_score(cpu, memory, disk, pipeline_delay_seconds):
    score = 100

    # CPU
    if cpu >= 90:
        score -= 25
    elif cpu >= 80:
        score -= 15
    elif cpu >= 70:
        score -= 5

    # Memory
    if memory >= 95:
        score -= 25
    elif memory >= 85:
        score -= 15
    elif memory >= 75:
        score -= 5

    # Disk
    if disk >= 95:
        score -= 30
    elif disk >= 90:
        score -= 20
    elif disk >= 80:
        score -= 8

    # Pipeline freshness
    if pipeline_delay_seconds >= 300:
        score -= 25
    elif pipeline_delay_seconds >= 120:
        score -= 15
    elif pipeline_delay_seconds >= 60:
        score -= 5

    return max(score, 0)


def get_health_label(score):
    if score >= 80:
        return "🟢 Healthy"
    elif score >= 50:
        return "🟡 Moderate"
    return "🔴 Critical"


def classify_uptime(uptime_seconds):
    if uptime_seconds is None:
        return "Unknown"

    hours = uptime_seconds / 3600

    if hours < 1:
        return "Recent restart"
    elif hours < 24:
        return "Stable"
    elif hours < 24 * 7:
        return "Long-running"
    return "Very stable"


def format_uptime(seconds):
    if seconds is None:
        return "N/A"

    seconds = int(seconds)
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)

    if days > 0:
        return f"{days}d {hours}h {minutes}m {secs}s"
    return f"{hours}h {minutes}m {secs}s"


def detect_collection_gaps(df, expected_interval_minutes=1):
    if df.empty or len(df) < 2:
        return 0, None

    df = df.copy()
    df["time_diff"] = df["timestamp"].diff()

    threshold = pd.Timedelta(minutes=expected_interval_minutes * 1.5)
    gaps = df[df["time_diff"] > threshold]

    if gaps.empty:
        return 0, None

    largest_gap = gaps["time_diff"].max()
    return len(gaps), largest_gap


# =========================
# HEADER
# =========================
st.title("🖥️ System Information")
st.caption("Live system state, rule-based health checks, and pipeline status")


# =========================
# LOAD DATA
# =========================
latest = load_latest_metrics()
recent_df = load_recent_metrics(limit=180)

if latest is None:
    st.error("No metrics found in the database yet.")
    st.stop()


# =========================
# CURRENT VALUES
# =========================
cpu = float(latest["cpu_percent"])
memory = float(latest["memory_percent"])
disk = float(latest["disk_percent"])
last_timestamp = latest["timestamp"]
uptime_seconds = latest["uptime_seconds"]

now = pd.Timestamp.now()
pipeline_delay = now - last_timestamp
pipeline_delay_seconds = pipeline_delay.total_seconds()

health_score = calculate_health_score(cpu, memory, disk, pipeline_delay_seconds)
health_label = get_health_label(health_score)
uptime_label = classify_uptime(uptime_seconds)

gap_count, largest_gap = detect_collection_gaps(recent_df, expected_interval_minutes=1)


# =========================
# TOP SUMMARY
# =========================
st.subheader("System Health Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Health Score", f"{health_score}/100")
col2.metric("Health Status", health_label)
col3.metric("Last Metric Time", last_timestamp.strftime("%Y-%m-%d %H:%M:%S"))
col4.metric("Pipeline Delay", str(pipeline_delay).split(".")[0])


# =========================
# RESOURCE STATUS
# =========================
st.subheader("Resource Health")

r1, r2, r3 = st.columns(3)

with r1:
    st.metric("CPU Usage", f"{cpu:.2f}%")
    st.write(get_status(cpu, warning=70, critical=85))

with r2:
    st.metric("Memory Usage", f"{memory:.2f}%")
    st.write(get_status(memory, warning=75, critical=85))

with r3:
    st.metric("Disk Usage", f"{disk:.2f}%")
    st.write(get_status(disk, warning=80, critical=90))


# =========================
# PIPELINE HEALTH
# =========================
st.subheader("Pipeline Health")

p1, p2, p3 = st.columns(3)

if pipeline_delay_seconds >= 300:
    pipeline_status = "🔴 Pipeline Delayed"
elif pipeline_delay_seconds >= 120:
    pipeline_status = "🟡 Slight Delay"
else:
    pipeline_status = "🟢 Pipeline Active"

with p1:
    st.metric("Pipeline Status", pipeline_status)

with p2:
    st.metric("Collection Gaps Detected", gap_count)

with p3:
    if largest_gap is not None:
        st.metric("Largest Gap", str(largest_gap).split(".")[0])
    else:
        st.metric("Largest Gap", "No gaps")


# =========================
# SYSTEM DETAILS
# =========================
st.subheader("Machine Details")

m1, m2 = st.columns(2)

with m1:
    st.write(f"**Operating System:** {platform.system()}")
    st.write(f"**OS Version:** {platform.version()}")
    st.write(f"**Machine Type:** {platform.machine()}")
    st.write(f"**Hostname:** {platform.node()}")

with m2:
    st.write(f"**Processor:** {platform.processor()}")
    st.write(f"**Python Version:** {platform.python_version()}")
    st.write(f"**Physical Cores:** {psutil.cpu_count(logical=False)}")
    st.write(f"**Logical Cores:** {psutil.cpu_count(logical=True)}")


# =========================
# MEMORY / DISK / NETWORK
# =========================
st.subheader("Hardware and Network Overview")

memory_info = psutil.virtual_memory()
disk_info = psutil.disk_usage("/")
net_info = psutil.net_io_counters()

h1, h2, h3 = st.columns(3)

with h1:
    st.markdown("**Memory**")
    st.write(f"Total: {memory_info.total / (1024**3):.2f} GB")
    st.write(f"Available: {memory_info.available / (1024**3):.2f} GB")
    st.write(f"Used: {memory_info.percent:.2f}%")

with h2:
    st.markdown("**Disk**")
    st.write(f"Total: {disk_info.total / (1024**3):.2f} GB")
    st.write(f"Free: {disk_info.free / (1024**3):.2f} GB")
    st.write(f"Used: {disk_info.percent:.2f}%")

with h3:
    st.markdown("**Network**")
    st.write(f"Total Sent: {net_info.bytes_sent / (1024**2):.2f} MB")
    st.write(f"Total Received: {net_info.bytes_recv / (1024**2):.2f} MB")
    st.write(f"Uptime: {format_uptime(uptime_seconds)}")


# =========================
# UPTIME STATUS
# =========================
st.subheader("Stability")

s1, s2 = st.columns(2)

with s1:
    st.metric("System Uptime", format_uptime(uptime_seconds))

with s2:
    st.metric("Uptime Classification", uptime_label)


# =========================
# RECENT BASELINE COMPARISON
# =========================
st.subheader("Recent Baseline Comparison")

if not recent_df.empty:
    avg_cpu = recent_df["cpu_percent"].mean()
    avg_memory = recent_df["memory_percent"].mean()
    avg_disk = recent_df["disk_percent"].mean()

    b1, b2, b3 = st.columns(3)

    b1.metric(
        "CPU vs Recent Average",
        f"{cpu:.2f}%",
        delta=f"{cpu - avg_cpu:.2f}%"
    )

    b2.metric(
        "Memory vs Recent Average",
        f"{memory:.2f}%",
        delta=f"{memory - avg_memory:.2f}%"
    )

    b3.metric(
        "Disk vs Recent Average",
        f"{disk:.2f}%",
        delta=f"{disk - avg_disk:.2f}%"
    )
else:
    st.info("Not enough recent data available for baseline comparison.")


# =========================
# HEALTH INTERPRETATION
# =========================
st.subheader("Interpretation")

if health_score >= 80:
    st.success(
        "The system is currently operating within healthy limits. "
        "Resource usage is stable and the monitoring pipeline appears active."
    )
elif health_score >= 50:
    st.warning(
        "The system is operational but showing moderate pressure in one or more areas. "
        "This may indicate elevated resource usage or delays in metric collection."
    )
else:
    st.error(
        "The system is currently in a critical state based on rule-based health evaluation. "
        "Immediate attention may be required for resource pressure or pipeline reliability."
    )