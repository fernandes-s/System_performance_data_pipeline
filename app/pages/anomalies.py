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
# pages/1_Anomalies.py -> app -> project root
BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "raw" / "system_metrics.db"
ANOMALY_TABLE = "anomaly_results"


# =========================
# DATABASE FUNCTIONS
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
def load_anomaly_data():
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


# =========================
# HELPER FUNCTIONS
# =========================
def format_metric(value, decimals=0):
    if pd.isna(value):
        return "N/A"
    if decimals == 0:
        return f"{value:,.0f}"
    return f"{value:,.{decimals}f}"


def get_available_columns(df: pd.DataFrame, columns: list[str]) -> list[str]:
    return [col for col in columns if col in df.columns]


def build_metric_chart(
    df: pd.DataFrame,
    anomaly_points: pd.DataFrame,
    y_col: str,
    title: str,
    y_axis_title: str
):
    fig = px.line(
        df,
        x="timestamp",
        y=y_col,
        title=title
    )

    if not anomaly_points.empty and y_col in anomaly_points.columns:
        fig.add_scatter(
            x=anomaly_points["timestamp"],
            y=anomaly_points[y_col],
            mode="markers",
            name="Anomalies",
            text=anomaly_points["top_driver"] if "top_driver" in anomaly_points.columns else None,
            hovertemplate=(
                "<b>Timestamp</b>: %{x}<br>"
                f"<b>{y_axis_title}</b>: " + "%{y}<br>"
                "<b>Driver</b>: %{text}<extra></extra>"
            ) if "top_driver" in anomaly_points.columns else None
        )

    fig.update_layout(
        xaxis_title="Timestamp",
        yaxis_title=y_axis_title
    )
    return fig


def ensure_required_columns(df: pd.DataFrame, required_columns: list[str]):
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(
            f"The table '{ANOMALY_TABLE}' is missing these required columns: {missing_columns}"
        )
        st.stop()


# =========================
# PAGE TITLE
# =========================
st.title("🚨 Anomaly Detection")
st.markdown(
    "This page shows the anomaly detection results saved by the model pipeline, "
    "including which behaviours were flagged and why they look unusual."
)


# =========================
# DATABASE CHECKS
# =========================
if not DB_PATH.exists():
    st.error(f"Database not found: {DB_PATH}")
    st.stop()

table_names = get_table_names()

if ANOMALY_TABLE not in table_names:
    st.warning(
        f"The table '{ANOMALY_TABLE}' was not found in the database. "
        "Run your training script first so the model results are written to SQLite."
    )

    with st.expander("Available tables in the database"):
        st.write(table_names)

    st.stop()


# =========================
# LOAD DATA
# =========================
df = load_anomaly_data()

if df.empty:
    st.warning("No anomaly results found in the database yet.")
    st.stop()

required_columns = [
    "timestamp",
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "anomaly_score",
    "is_anomaly",
]

ensure_required_columns(df, required_columns)

df = df.dropna(subset=["timestamp"]).copy()

if df.empty:
    st.warning("All anomaly rows have invalid timestamps.")
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

available_strengths = []
if "anomaly_strength" in filtered_df.columns:
    available_strengths = sorted(filtered_df["anomaly_strength"].dropna().unique().tolist())

selected_strengths = available_strengths
if available_strengths:
    selected_strengths = st.sidebar.multiselect(
        "Filter anomaly strength",
        options=available_strengths,
        default=available_strengths
    )

    if show_only_anomalies and selected_strengths:
        filtered_df = filtered_df[
            filtered_df["anomaly_strength"].isin(selected_strengths)
        ].copy()

if filtered_df.empty:
    st.warning("No records found for the selected filters.")
    st.stop()

anomaly_points = filtered_df[filtered_df["is_anomaly"] == 1].copy()


# =========================
# KPI CARDS
# =========================
total_records = len(filtered_df)
total_anomalies = int(filtered_df["is_anomaly"].sum())
anomaly_rate = (total_anomalies / total_records * 100) if total_records > 0 else 0
latest_timestamp = filtered_df["timestamp"].max()

anomaly_scores = anomaly_points["anomaly_score"] if not anomaly_points.empty else pd.Series(dtype=float)
highest_score = anomaly_scores.max() if not anomaly_scores.empty else None

strong_count = int((anomaly_points["anomaly_strength"] == "strong").sum()) if "anomaly_strength" in anomaly_points.columns else 0
moderate_count = int((anomaly_points["anomaly_strength"] == "moderate").sum()) if "anomaly_strength" in anomaly_points.columns else 0
weak_count = int((anomaly_points["anomaly_strength"] == "weak").sum()) if "anomaly_strength" in anomaly_points.columns else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Records", format_metric(total_records))
col2.metric("Detected Anomalies", format_metric(total_anomalies))
col3.metric("Anomaly Rate", f"{anomaly_rate:.2f}%")
col4.metric("Latest Timestamp", str(latest_timestamp))

if "anomaly_strength" in filtered_df.columns:
    col5, col6, col7 = st.columns(3)
    col5.metric("Strong Anomalies", format_metric(strong_count))
    col6.metric("Moderate Anomalies", format_metric(moderate_count))
    col7.metric("Weak Anomalies", format_metric(weak_count))

st.divider()


# =========================
# RUN SUMMARY
# =========================
with st.expander("Run summary"):
    st.write(f"**Database:** `{DB_PATH}`")
    st.write(f"**Results table:** `{ANOMALY_TABLE}`")
    st.write(f"**Filtered date range:** {start_date} to {end_date}")

    if highest_score is not None:
        st.write(f"**Highest anomaly score in current view:** {highest_score:.6f}")

    if not anomaly_points.empty and "top_driver" in anomaly_points.columns:
        top_driver_counts = anomaly_points["top_driver"].value_counts().head(3)
        if not top_driver_counts.empty:
            st.write("**Most common anomaly drivers in current view:**")
            for driver, count in top_driver_counts.items():
                st.write(f"- {driver}: {count}")


# =========================
# CASE STUDIES
# =========================
st.subheader("Anomaly Case Studies")

if anomaly_points.empty:
    st.info("No anomalies detected in the selected date range.")
else:
    case_study_cols = get_available_columns(
        anomaly_points,
        [
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
            "uptime_seconds",
        ]
    )

    case_studies = (
        anomaly_points
        .sort_values("anomaly_score", ascending=False)
        .head(4)
        .copy()
    )

    for i, (_, row) in enumerate(case_studies.iterrows(), start=1):
        with st.container(border=True):
            st.markdown(f"**Case Study {i}**")
            st.write(f"**Timestamp:** {row['timestamp']}")
            st.write(f"**Anomaly score:** {row['anomaly_score']:.6f}")

            if "anomaly_strength" in row.index:
                st.write(f"**Strength:** {row['anomaly_strength']}")

            if "top_driver" in row.index:
                st.write(f"**Main driver:** {row['top_driver']}")

            if "explanation" in row.index:
                st.write(f"**Interpretation:** {row['explanation']}")

            detail_cols = st.columns(3)

            if "cpu_percent" in row.index:
                detail_cols[0].metric("CPU %", format_metric(row["cpu_percent"], 2))
            if "memory_percent" in row.index:
                detail_cols[1].metric("Memory %", format_metric(row["memory_percent"], 2))
            if "disk_percent" in row.index:
                detail_cols[2].metric("Disk %", format_metric(row["disk_percent"], 2))

            detail_cols_2 = st.columns(3)

            if "net_sent_delta_mb" in row.index:
                detail_cols_2[0].metric("Net Sent Δ MB", format_metric(row["net_sent_delta_mb"], 3))
            if "net_recv_delta_mb" in row.index:
                detail_cols_2[1].metric("Net Recv Δ MB", format_metric(row["net_recv_delta_mb"], 3))
            if "uptime_seconds" in row.index:
                detail_cols_2[2].metric("Uptime Sec", format_metric(row["uptime_seconds"], 0))


st.divider()


# =========================
# DRIVER DISTRIBUTION
# =========================
st.subheader("What Kind of Behaviour Is Being Flagged?")

if anomaly_points.empty or "top_driver" not in anomaly_points.columns:
    st.info("Driver information is not available yet.")
else:
    driver_counts = (
        anomaly_points["top_driver"]
        .value_counts()
        .reset_index()
    )
    driver_counts.columns = ["top_driver", "count"]

    fig_driver = px.bar(
        driver_counts.head(10),
        x="top_driver",
        y="count",
        title="Most Common Anomaly Drivers"
    )
    fig_driver.update_layout(
        xaxis_title="Detected behaviour",
        yaxis_title="Count"
    )
    st.plotly_chart(fig_driver, use_container_width=True)


# =========================
# CPU / MEMORY / DISK TIMELINES
# =========================
st.subheader("Metric Timelines with Anomaly Markers")

fig_cpu = build_metric_chart(
    filtered_df,
    anomaly_points,
    y_col="cpu_percent",
    title="CPU Usage Timeline",
    y_axis_title="CPU %"
)
st.plotly_chart(fig_cpu, use_container_width=True)

col_left, col_right = st.columns(2)

with col_left:
    fig_mem = build_metric_chart(
        filtered_df,
        anomaly_points,
        y_col="memory_percent",
        title="Memory Usage Timeline",
        y_axis_title="Memory %"
    )
    st.plotly_chart(fig_mem, use_container_width=True)

with col_right:
    fig_disk = build_metric_chart(
        filtered_df,
        anomaly_points,
        y_col="disk_percent",
        title="Disk Usage Timeline",
        y_axis_title="Disk %"
    )
    st.plotly_chart(fig_disk, use_container_width=True)


# =========================
# NETWORK TIMELINES
# =========================
network_cols_available = {
    "net_sent_delta_mb": "Network Sent Delta (MB)",
    "net_recv_delta_mb": "Network Received Delta (MB)",
}

available_network_cols = [col for col in network_cols_available if col in filtered_df.columns]

if available_network_cols:
    st.subheader("Network Behaviour Around Anomalies")

    net_col1, net_col2 = st.columns(len(available_network_cols))

    for idx, col_name in enumerate(available_network_cols):
        fig_net = build_metric_chart(
            filtered_df,
            anomaly_points,
            y_col=col_name,
            title=f"{network_cols_available[col_name]} Timeline",
            y_axis_title=network_cols_available[col_name]
        )
        if len(available_network_cols) == 1:
            st.plotly_chart(fig_net, use_container_width=True)
        else:
            with [net_col1, net_col2][idx]:
                st.plotly_chart(fig_net, use_container_width=True)


# =========================
# ANOMALY SCORE CHART
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
        name="Detected Anomalies",
        text=anomaly_points["explanation"] if "explanation" in anomaly_points.columns else None,
        hovertemplate=(
            "<b>Timestamp</b>: %{x}<br>"
            "<b>Anomaly score</b>: %{y}<br>"
            "<b>Interpretation</b>: %{text}<extra></extra>"
        ) if "explanation" in anomaly_points.columns else None
    )

fig_score.update_layout(
    xaxis_title="Timestamp",
    yaxis_title="Anomaly Score"
)

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

fig_daily.update_layout(
    xaxis_title="Date",
    yaxis_title="Anomaly Count"
)

st.plotly_chart(fig_daily, use_container_width=True)


# =========================
# NORMAL VS ANOMALY COMPARISON
# =========================
st.subheader("Normal vs Anomaly Behaviour")

comparison_metrics = get_available_columns(
    filtered_df,
    [
        "cpu_percent",
        "memory_percent",
        "disk_percent",
        "net_sent_delta_mb",
        "net_recv_delta_mb",
        "uptime_seconds",
    ]
)

if len(comparison_metrics) == 0:
    st.info("Not enough columns available for comparison.")
else:
    comparison_df = (
        filtered_df
        .groupby("is_anomaly")[comparison_metrics]
        .mean()
        .T
        .reset_index()
    )

    comparison_df = comparison_df.rename(columns={"index": "metric"})

    if 0 not in comparison_df.columns:
        comparison_df[0] = None
    if 1 not in comparison_df.columns:
        comparison_df[1] = None

    comparison_df = comparison_df.rename(
        columns={
            0: "normal_mean",
            1: "anomaly_mean",
        }
    )

    fig_compare = px.bar(
        comparison_df,
        x="metric",
        y=["normal_mean", "anomaly_mean"],
        barmode="group",
        title="Average Metric Values: Normal vs Anomaly Rows"
    )
    fig_compare.update_layout(
        xaxis_title="Metric",
        yaxis_title="Average value"
    )
    st.plotly_chart(fig_compare, use_container_width=True)

    st.dataframe(
        comparison_df,
        use_container_width=True,
        hide_index=True
    )


# =========================
# ANOMALIES TABLE
# =========================
st.subheader("Detected Anomalies Table")

anomalies_only = filtered_df[filtered_df["is_anomaly"] == 1].copy()

preferred_columns = [
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
    "uptime_seconds",
    "cpu_zscore",
    "memory_zscore",
    "disk_zscore",
    "net_sent_zscore",
    "net_recv_zscore",
    "uptime_zscore",
    "is_anomaly",
]

anomaly_table_columns = get_available_columns(anomalies_only, preferred_columns)

if anomalies_only.empty:
    st.info("No anomalies detected in the selected date range.")
else:
    st.dataframe(
        anomalies_only[anomaly_table_columns].sort_values("timestamp", ascending=False),
        use_container_width=True,
        hide_index=True
    )


# =========================
# FULL RESULTS TABLE
# =========================
st.subheader("Full Results")

full_table_columns = get_available_columns(
    filtered_df,
    [
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
        "uptime_seconds",
        "is_anomaly",
    ]
)

st.dataframe(
    filtered_df[full_table_columns].sort_values("timestamp", ascending=False),
    use_container_width=True,
    hide_index=True
)


# =========================
# DOWNLOAD SECTION
# =========================
st.subheader("Export Results")

csv = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download anomaly results as CSV",
    data=csv,
    file_name="anomaly_results_filtered.csv",
    mime="text/csv"
)