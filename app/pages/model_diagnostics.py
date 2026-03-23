from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Model Diagnostics",
    page_icon="🧠",
    layout="wide"
)

st.title("Model Diagnostics")
st.caption(
    "Inspect model settings, anomaly scores, and feature-level detection details."
)


# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "raw" / "system_metrics.db"


# =========================
# DATABASE CONNECTION
# =========================
def get_connection():
    return sqlite3.connect(DB_PATH)


# =========================
# DATA LOADERS
# =========================
@st.cache_data
def load_metrics_data():
    """
    Loads metrics from the main metrics table.
    This is used as fallback input until the model output tables exist.
    """
    if not DB_PATH.exists():
        return pd.DataFrame()

    conn = get_connection()
    query = """
        SELECT
            id,
            timestamp,
            cpu_percent,
            memory_percent,
            disk_percent,
            net_sent_delta_mb,
            net_recv_delta_mb,
            uptime_seconds
        FROM metrics
        ORDER BY timestamp ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    return df


@st.cache_data
def load_model_outputs():
    """
    Placeholder model diagnostics loader.

    Later, replace this with:
    - a real predictions table
    - saved anomaly scores
    - feature contribution output
    - model metadata/config table
    """
    df = load_metrics_data()

    if df.empty:
        return pd.DataFrame(), {}, pd.DataFrame()

    # -----------------------------------------
    # TEMPORARY PLACEHOLDER LOGIC
    # -----------------------------------------
    # Simulated anomaly score from system metrics
    working_df = df.copy()

    numeric_cols = [
        "cpu_percent",
        "memory_percent",
        "disk_percent",
        "net_sent_delta_mb",
        "net_recv_delta_mb"
    ]

    for col in numeric_cols:
        if col in working_df.columns:
            working_df[col] = working_df[col].fillna(0)

    # Simple synthetic score until real model is plugged in
    working_df["anomaly_score"] = (
        0.30 * working_df["cpu_percent"]
        + 0.25 * working_df["memory_percent"]
        + 0.20 * working_df["disk_percent"]
        + 8 * working_df["net_sent_delta_mb"]
        + 8 * working_df["net_recv_delta_mb"]
    )

    # Normalise score to 0-1
    min_score = working_df["anomaly_score"].min()
    max_score = working_df["anomaly_score"].max()

    if max_score > min_score:
        working_df["anomaly_score"] = (
            (working_df["anomaly_score"] - min_score) / (max_score - min_score)
        )
    else:
        working_df["anomaly_score"] = 0.0

    threshold = working_df["anomaly_score"].quantile(0.95)
    working_df["is_anomaly"] = working_df["anomaly_score"] >= threshold

    # Placeholder model metadata
    model_info = {
        "model_name": "Placeholder Scoring Logic",
        "model_type": "Rule-based / temporary stand-in",
        "version": "0.1",
        "threshold": round(float(threshold), 4),
        "features_used": numeric_cols,
        "notes": "Replace with real model metadata later."
    }

    # Feature-level diagnostic table
    feature_diagnostics = pd.DataFrame({
        "feature": numeric_cols,
        "role_in_detection": [
            "Resource pressure",
            "Resource pressure",
            "Storage pressure",
            "Network burst activity",
            "Network burst activity"
        ],
        "status": [
            "Active",
            "Active",
            "Active",
            "Active",
            "Active"
        ]
    })

    return working_df, model_info, feature_diagnostics


# =========================
# LOAD DATA
# =========================
diagnostics_df, model_info, feature_diag_df = load_model_outputs()


# =========================
# EMPTY STATE
# =========================
if diagnostics_df.empty:
    st.warning("No diagnostics data available yet. Collect metrics first, then connect model outputs.")
    st.stop()


# =========================
# SIDEBAR
# =========================
st.sidebar.header("Diagnostics Controls")

score_min, score_max = float(diagnostics_df["anomaly_score"].min()), float(diagnostics_df["anomaly_score"].max())

selected_score_range = st.sidebar.slider(
    "Anomaly score range",
    min_value=0.0,
    max_value=1.0,
    value=(max(0.0, round(score_min, 2)), min(1.0, round(score_max, 2))),
    step=0.01
)

show_only_anomalies = st.sidebar.checkbox("Show anomalies only", value=False)

max_rows = st.sidebar.slider(
    "Rows to display",
    min_value=10,
    max_value=200,
    value=25,
    step=5
)


filtered_df = diagnostics_df[
    diagnostics_df["anomaly_score"].between(selected_score_range[0], selected_score_range[1])
].copy()

if show_only_anomalies:
    filtered_df = filtered_df[filtered_df["is_anomaly"] == True]


# =========================
# TOP METRICS
# =========================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Model", model_info["model_name"])
col2.metric("Threshold", model_info["threshold"])
col3.metric("Detected Anomalies", int(diagnostics_df["is_anomaly"].sum()))
col4.metric("Rows Scored", len(diagnostics_df))


# =========================
# MODEL SETTINGS
# =========================
with st.expander("Model Settings", expanded=True):
    settings_col1, settings_col2 = st.columns(2)

    with settings_col1:
        st.write(f"**Model Type:** {model_info['model_type']}")
        st.write(f"**Version:** {model_info['version']}")
        st.write(f"**Threshold:** {model_info['threshold']}")

    with settings_col2:
        st.write("**Features Used:**")
        for feature in model_info["features_used"]:
            st.write(f"- {feature}")

        st.write(f"**Notes:** {model_info['notes']}")


# =========================
# SCORE DISTRIBUTION
# =========================
st.subheader("Anomaly Score Distribution")

fig_hist = px.histogram(
    diagnostics_df,
    x="anomaly_score",
    nbins=40,
    title="Distribution of Anomaly Scores"
)
fig_hist.add_vline(
    x=model_info["threshold"],
    line_dash="dash",
    annotation_text="Threshold",
    annotation_position="top right"
)
st.plotly_chart(fig_hist, use_container_width=True)


# =========================
# SCORE OVER TIME
# =========================
st.subheader("Anomaly Score Over Time")

fig_time = px.line(
    diagnostics_df,
    x="timestamp",
    y="anomaly_score",
    title="Anomaly Score Timeline"
)

anomaly_points = diagnostics_df[diagnostics_df["is_anomaly"] == True]
if not anomaly_points.empty:
    fig_time.add_scatter(
        x=anomaly_points["timestamp"],
        y=anomaly_points["anomaly_score"],
        mode="markers",
        name="Detected anomalies"
    )

st.plotly_chart(fig_time, use_container_width=True)


# =========================
# FEATURE-LEVEL DIAGNOSTICS
# =========================
st.subheader("Feature-Level Detection Details")
st.dataframe(feature_diag_df, use_container_width=True, hide_index=True)


# =========================
# TOP ANOMALOUS ROWS
# =========================
st.subheader("Highest Scoring Observations")

top_anomalies = (
    filtered_df.sort_values("anomaly_score", ascending=False)
    .head(max_rows)
    .copy()
)

display_cols = [
    "timestamp",
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "net_sent_delta_mb",
    "net_recv_delta_mb",
    "anomaly_score",
    "is_anomaly"
]

available_display_cols = [col for col in display_cols if col in top_anomalies.columns]

st.dataframe(
    top_anomalies[available_display_cols],
    use_container_width=True,
    hide_index=True
)


# =========================
# RAW DIAGNOSTIC VIEW
# =========================
with st.expander("Raw Diagnostic Output"):
    st.dataframe(filtered_df.head(max_rows), use_container_width=True, hide_index=True)


# =========================
# NEXT INTEGRATION NOTES
# =========================
with st.expander("What to connect later"):
    st.markdown("""
    Replace the placeholder logic with your real model pipeline output.

    Recommended additions:
    - saved anomaly score per timestamp
    - prediction label per timestamp
    - threshold used by the model
    - model version and training date
    - feature importance or contribution values
    - confusion matrix / evaluation metrics if you later label anomalies
    """)