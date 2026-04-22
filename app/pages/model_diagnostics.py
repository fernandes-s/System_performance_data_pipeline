from pathlib import Path
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from utils.db import database_exists
from utils.queries import load_anomaly_results
from utils.anomaly import classify_anomaly_severity
from utils.charts import (
    make_score_distribution_chart,
    make_driver_bar_chart,
)
from utils.formatters import (
    format_timestamp,
    format_large_number,
    format_percentage,
    format_number,
)
from utils.ui_helpers import (
    section_header,
    show_empty_state,
    show_chart_or_empty,
    show_dataframe_preview,
    four_column_kpis,
)
from utils.config import MODEL_PATH, SCALER_PATH


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Model Diagnostics",
    page_icon="🧠",
    layout="wide",
)

st.title("Model Diagnostics")
st.caption("A concise view of model settings, anomaly score behaviour, and the main features associated with flagged rows.")


# =========================
# HELPERS
# =========================
def safe_file_time(path: Path):
    if path.exists():
        return datetime.fromtimestamp(path.stat().st_mtime)
    return None


def normalize_anomaly_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardise anomaly result columns so the page works with
    both older and newer saved outputs.
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


def load_saved_artifacts():
    model = None
    scaler = None

    if MODEL_PATH.exists():
        try:
            model = joblib.load(MODEL_PATH)
        except Exception:
            model = None

    if SCALER_PATH.exists():
        try:
            scaler = joblib.load(SCALER_PATH)
        except Exception:
            scaler = None

    return model, scaler


def extract_model_info(model, scaler, df: pd.DataFrame) -> dict:
    feature_candidates = [
        "cpu_percent",
        "memory_percent",
        "disk_percent",
        "net_sent_delta_mb",
        "net_recv_delta_mb",
        "uptime_seconds",
    ]
    features_used = [col for col in feature_candidates if col in df.columns]

    return {
        "model_name": "Isolation Forest",
        "model_type": type(model).__name__ if model is not None else "Not available",
        "scaler_type": type(scaler).__name__ if scaler is not None else "Not available",
        "contamination": getattr(model, "contamination", "Not available") if model is not None else "Not available",
        "n_estimators": getattr(model, "n_estimators", "Not available") if model is not None else "Not available",
        "max_samples": getattr(model, "max_samples", "Not available") if model is not None else "Not available",
        "random_state": getattr(model, "random_state", "Not available") if model is not None else "Not available",
        "features_used": features_used,
        "model_saved_at": format_timestamp(safe_file_time(MODEL_PATH)),
        "scaler_saved_at": format_timestamp(safe_file_time(SCALER_PATH)),
    }


def build_feature_diagnostics(df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    """
    Compare mean feature values between normal and anomalous rows.
    """
    if df.empty or "anomaly_flag" not in df.columns:
        return pd.DataFrame()

    rows = []
    anomaly_df = df[df["anomaly_flag"] == 1].copy()
    normal_df = df[df["anomaly_flag"] == 0].copy()

    for col in feature_cols:
        if col not in df.columns:
            continue

        overall_mean = pd.to_numeric(df[col], errors="coerce").mean()
        anomaly_mean = pd.to_numeric(anomaly_df[col], errors="coerce").mean() if not anomaly_df.empty else np.nan
        normal_mean = pd.to_numeric(normal_df[col], errors="coerce").mean() if not normal_df.empty else np.nan

        difference = anomaly_mean - normal_mean if pd.notna(anomaly_mean) and pd.notna(normal_mean) else np.nan

        if pd.notna(difference):
            if difference > 0:
                trend = "Higher in anomalies"
            elif difference < 0:
                trend = "Lower in anomalies"
            else:
                trend = "Similar"
        else:
            trend = "Not enough data"

        rows.append({
            "feature": col,
            "overall_mean": round(float(overall_mean), 3) if pd.notna(overall_mean) else None,
            "normal_mean": round(float(normal_mean), 3) if pd.notna(normal_mean) else None,
            "anomaly_mean": round(float(anomaly_mean), 3) if pd.notna(anomaly_mean) else None,
            "difference_vs_normal": round(float(difference), 3) if pd.notna(difference) else None,
            "pattern": trend,
        })

    return pd.DataFrame(rows)


def make_score_timeline_chart(df: pd.DataFrame):
    """
    Build a simple anomaly score over time chart.
    """
    import plotly.express as px

    required = {"timestamp", "anomaly_score"}
    if df.empty or not required.issubset(df.columns):
        return None

    chart_df = df.dropna(subset=["timestamp", "anomaly_score"]).copy()
    if chart_df.empty:
        return None

    fig = px.line(
        chart_df,
        x="timestamp",
        y="anomaly_score",
        title="Anomaly Score Over Time",
        labels={
            "timestamp": "Timestamp",
            "anomaly_score": "Anomaly Score",
        },
    )

    if "anomaly_flag" in chart_df.columns:
        anomaly_points = chart_df[chart_df["anomaly_flag"] == 1]
        if not anomaly_points.empty:
            fig.add_scatter(
                x=anomaly_points["timestamp"],
                y=anomaly_points["anomaly_score"],
                mode="markers",
                name="Detected Anomalies",
            )

    fig.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=50, b=20),
        template="plotly_white",
        legend_title_text="",
    )
    return fig


# =========================
# LOAD DATA
# =========================
if not database_exists():
    st.error("Database not found. Please check that data/raw/system_metrics.db exists.")
    st.stop()

diagnostics_df = load_anomaly_results()
diagnostics_df = normalize_anomaly_columns(diagnostics_df)

if diagnostics_df.empty:
    st.warning("No model diagnostics data found. Make sure the anomaly results table has been created.")
    st.stop()

required_columns = ["timestamp", "anomaly_score", "anomaly_flag"]
missing_columns = [col for col in required_columns if col not in diagnostics_df.columns]
if missing_columns:
    st.error(f"Missing required columns in anomaly results: {missing_columns}")
    st.stop()

diagnostics_df = diagnostics_df.dropna(subset=["timestamp"]).copy()

if "severity" not in diagnostics_df.columns:
    diagnostics_df = classify_anomaly_severity(diagnostics_df)

model, scaler = load_saved_artifacts()
model_info = extract_model_info(model, scaler, diagnostics_df)


# =========================
# METRICS
# =========================
rows_scored = len(diagnostics_df)
anomaly_count = int((diagnostics_df["anomaly_flag"] == 1).sum())
anomaly_rate = (anomaly_count / rows_scored * 100) if rows_scored > 0 else None
latest_timestamp = diagnostics_df["timestamp"].max()
score_min = diagnostics_df["anomaly_score"].min()
score_max = diagnostics_df["anomaly_score"].max()

four_column_kpis([
    {
        "label": "Model",
        "value": model_info["model_name"],
    },
    {
        "label": "Rows Scored",
        "value": format_large_number(rows_scored),
    },
    {
        "label": "Detected Anomalies",
        "value": format_large_number(anomaly_count),
    },
    {
        "label": "Anomaly Rate",
        "value": format_percentage(anomaly_rate, decimals=2) if anomaly_rate is not None else "N/A",
    },
])


# =========================
# MODEL SUMMARY
# =========================
section_header("Model Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.info(
        f"**Model Type:** {model_info['model_type']}\n\n"
        f"**Scaler:** {model_info['scaler_type']}\n\n"
        f"**Latest Scored Row:** {format_timestamp(latest_timestamp)}"
    )

with col2:
    st.info(
        f"**Contamination:** {model_info['contamination']}\n\n"
        f"**Estimators:** {model_info['n_estimators']}\n\n"
        f"**Max Samples:** {model_info['max_samples']}"
    )

with col3:
    st.info(
        f"**Score Min:** {format_number(score_min, 4)}\n\n"
        f"**Score Max:** {format_number(score_max, 4)}\n\n"
        f"**Random State:** {model_info['random_state']}"
    )


# =========================
# SCORE BEHAVIOUR
# =========================
section_header("Score Behaviour")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    fig_dist = make_score_distribution_chart(
        diagnostics_df,
        score_column="anomaly_score",
        title="Anomaly Score Distribution",
    )
    show_chart_or_empty(fig_dist, "No anomaly score distribution is available.")

with chart_col2:
    fig_time = make_score_timeline_chart(diagnostics_df)
    show_chart_or_empty(fig_time, "No anomaly score timeline is available.")


# =========================
# FEATURE DIAGNOSTICS
# =========================
section_header("Feature Diagnostics")

feature_cols = [
    col for col in [
        "cpu_percent",
        "memory_percent",
        "disk_percent",
        "net_sent_delta_mb",
        "net_recv_delta_mb",
        "uptime_seconds",
    ]
    if col in diagnostics_df.columns
]

feature_diag_df = build_feature_diagnostics(diagnostics_df, feature_cols)

if feature_diag_df.empty:
    show_empty_state("No feature diagnostics are available.")
else:
    show_dataframe_preview(feature_diag_df, max_rows=len(feature_diag_df))


# =========================
# ADVANCED DETAILS
# =========================
with st.expander("Advanced diagnostics"):
    driver_rows = diagnostics_df.copy()

    if "dominant_driver" in driver_rows.columns:
        driver_summary = (
            driver_rows[driver_rows["anomaly_flag"] == 1]["dominant_driver"]
            .dropna()
            .value_counts()
            .reset_index()
        )
        driver_summary.columns = ["feature", "avg_abs_zscore"]

        if not driver_summary.empty:
            fig_driver = make_driver_bar_chart(
                driver_summary.head(6),
                feature_column="feature",
                value_column="avg_abs_zscore",
                title="Most Common Dominant Drivers",
            )
            show_chart_or_empty(fig_driver, "No dominant driver summary is available.")

    st.markdown("**Saved artefacts**")
    st.write(f"Model saved at: {model_info['model_saved_at']}")
    st.write(f"Scaler saved at: {model_info['scaler_saved_at']}")
    st.write(f"Features used: {', '.join(model_info['features_used']) if model_info['features_used'] else 'Not available'}")

    st.markdown("**Recent scored rows**")
    preview_cols = [
        "timestamp",
        "anomaly_score",
        "severity",
        "dominant_driver",
        "cpu_percent",
        "memory_percent",
        "disk_percent",
    ]
    available_cols = [col for col in preview_cols if col in diagnostics_df.columns]
    show_dataframe_preview(
        diagnostics_df.sort_values("timestamp", ascending=False)[available_cols],
        max_rows=10,
    )