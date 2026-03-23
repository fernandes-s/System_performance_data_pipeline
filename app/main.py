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


# =========================
# PREP DATA
# =========================
summary = get_summary_metrics(df)
chart_df = get_recent_window(df, days=7)


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