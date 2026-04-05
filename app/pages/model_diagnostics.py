from pathlib import Path
import sqlite3
from datetime import datetime

import joblib
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
    "Inspect model settings, anomaly scores, saved model artefacts, and anomaly behaviour over time."
)


# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "raw" / "system_metrics.db"

MODEL_PATH = BASE_DIR / "artifacts" / "models" / "isolation_forest_model.joblib"
SCALER_PATH = BASE_DIR / "artifacts" / "models" / "scaler.joblib"


# =========================
# DATABASE CONNECTION
# =========================
def get_connection():
    return sqlite3.connect(DB_PATH)


# =========================
# HELPERS
# =========================
def safe_file_time(path: Path):
    if path.exists():
        return datetime.fromtimestamp(path.stat().st_mtime)
    return None


def format_dt(dt_value):
    if dt_value is None:
        return "Not available"
    return dt_value.strftime("%Y-%m-%d %H:%M:%S")


def infer_prediction_column(df: pd.DataFrame):
    candidate_cols = [
        "prediction",
        "predictions",
        "is_anomaly",
        "anomaly_flag",
        "anomaly",
        "label"
    ]
    for col in candidate_cols:
        if col in df.columns:
            return col
    return None


def infer_score_column(df: pd.DataFrame):
    candidate_cols = [
        "anomaly_score",
        "score",
        "scores",
        "decision_score",
        "anomaly_scores"
    ]
    for col in candidate_cols:
        if col in df.columns:
            return col
    return None


def normalise_prediction_column(df: pd.DataFrame, pred_col: str):
    """
    Normalises prediction output to:
    is_anomaly = True for anomalous observations
    Handles:
    - boolean values
    - 1 / 0
    - -1 / 1 from Isolation Forest
    """
    if pred_col is None or pred_col not in df.columns:
        df["is_anomaly"] = False
        return df

    series = df[pred_col]

    if pd.api.types.is_bool_dtype(series):
        df["is_anomaly"] = series.fillna(False)
        return df

    unique_vals = set(pd.Series(series.dropna().unique()).astype(str).tolist())

    # Isolation Forest default output: -1 anomaly, 1 normal
    if "-1" in unique_vals and "1" in unique_vals:
        df["is_anomaly"] = pd.to_numeric(series, errors="coerce") == -1
        return df

    # Binary style: 1 anomaly, 0 normal
    if unique_vals.issubset({"0", "1"}):
        df["is_anomaly"] = pd.to_numeric(series, errors="coerce") == 1
        return df

    # Fallback: treat truthy strings as anomaly
    df["is_anomaly"] = series.astype(str).str.lower().isin(
        ["true", "1", "-1", "yes", "anomaly"]
    )
    return df


def build_feature_diagnostics(df: pd.DataFrame, feature_cols: list):
    rows = []

    anomalous_df = df[df["is_anomaly"] == True].copy()
    normal_df = df[df["is_anomaly"] == False].copy()

    for col in feature_cols:
        if col not in df.columns:
            continue

        overall_mean = df[col].mean() if not df[col].dropna().empty else np.nan
        anomaly_mean = anomalous_df[col].mean() if not anomalous_df.empty else np.nan
        normal_mean = normal_df[col].mean() if not normal_df.empty else np.nan

        if pd.notna(overall_mean) and overall_mean != 0 and pd.notna(anomaly_mean):
            deviation_pct = ((anomaly_mean - overall_mean) / overall_mean) * 100
        else:
            deviation_pct = np.nan

        if pd.notna(deviation_pct):
            if deviation_pct > 10:
                trend = "Higher in anomalies"
            elif deviation_pct < -10:
                trend = "Lower in anomalies"
            else:
                trend = "Similar to normal"
        else:
            trend = "Not enough data"

        rows.append({
            "feature": col,
            "overall_mean": round(float(overall_mean), 3) if pd.notna(overall_mean) else None,
            "normal_mean": round(float(normal_mean), 3) if pd.notna(normal_mean) else None,
            "anomaly_mean": round(float(anomaly_mean), 3) if pd.notna(anomaly_mean) else None,
            "deviation_pct": round(float(deviation_pct), 2) if pd.notna(deviation_pct) else None,
            "anomaly_pattern": trend
        })

    return pd.DataFrame(rows)


def extract_model_metadata(model, scaler, diagnostics_df):
    feature_candidates = [
        "cpu_percent",
        "memory_percent",
        "disk_percent",
        "net_sent_delta_mb",
        "net_recv_delta_mb",
        "uptime_seconds"
    ]

    features_used = [col for col in feature_candidates if col in diagnostics_df.columns]

    contamination = getattr(model, "contamination", "Not available") if model is not None else "Not available"
    n_estimators = getattr(model, "n_estimators", "Not available") if model is not None else "Not available"
    max_samples = getattr(model, "max_samples", "Not available") if model is not None else "Not available"
    random_state = getattr(model, "random_state", "Not available") if model is not None else "Not available"

    scaler_type = type(scaler).__name__ if scaler is not None else "Not available"
    model_type = type(model).__name__ if model is not None else "Not available"

    score_col = infer_score_column(diagnostics_df)
    pred_col = infer_prediction_column(diagnostics_df)

    threshold_note = "Isolation Forest does not use a fixed manual threshold in the same way as rule-based systems."
    if pred_col is not None and score_col is not None:
        threshold_note = "Anomaly labels are read directly from saved model results."

    model_info = {
        "model_name": "Isolation Forest",
        "model_type": model_type,
        "version": "Saved production artefact",
        "contamination": contamination,
        "n_estimators": n_estimators,
        "max_samples": max_samples,
        "random_state": random_state,
        "scaler_type": scaler_type,
        "features_used": features_used,
        "score_column": score_col if score_col else "Not available",
        "prediction_column": pred_col if pred_col else "Not available",
        "threshold_note": threshold_note,
        "model_saved_at": format_dt(safe_file_time(MODEL_PATH)),
        "scaler_saved_at": format_dt(safe_file_time(SCALER_PATH))
    }

    return model_info


# =========================
# DATA LOADERS
# =========================
@st.cache_data(ttl=60)
def load_diagnostics_data():
    if not DB_PATH.exists():
        return pd.DataFrame()

    conn = get_connection()

    tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables_df = pd.read_sql_query(tables_query, conn)
    tables = tables_df["name"].tolist()

    if "anomaly_results" not in tables:
        conn.close()
        return pd.DataFrame()

    query = """
        SELECT *
        FROM anomaly_results
        ORDER BY timestamp ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return df

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    score_col = infer_score_column(df)
    pred_col = infer_prediction_column(df)

    if score_col is None:
        df["anomaly_score"] = np.nan
    elif score_col != "anomaly_score":
        df["anomaly_score"] = pd.to_numeric(df[score_col], errors="coerce")
    else:
        df["anomaly_score"] = pd.to_numeric(df["anomaly_score"], errors="coerce")

    df = normalise_prediction_column(df, pred_col)

    return df


@st.cache_resource
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


# =========================
# LOAD DATA
# =========================
diagnostics_df = load_diagnostics_data()
model, scaler = load_saved_artifacts()


# =========================
# EMPTY STATE
# =========================
if diagnostics_df.empty:
    st.warning(
        "No model diagnostics data found. Make sure `train_model.py` has created the `anomaly_results` table."
    )
    st.stop()


# =========================
# PREPARE DATA
# =========================
model_info = extract_model_metadata(model, scaler, diagnostics_df)

feature_cols = [
    col for col in [
        "cpu_percent",
        "memory_percent",
        "disk_percent",
        "net_sent_delta_mb",
        "net_recv_delta_mb",
        "uptime_seconds"
    ]
    if col in diagnostics_df.columns
]

feature_diag_df = build_feature_diagnostics(diagnostics_df, feature_cols)

rows_scored = len(diagnostics_df)
anomaly_count = int(diagnostics_df["is_anomaly"].sum())
anomaly_rate = (anomaly_count / rows_scored * 100) if rows_scored > 0 else 0

score_min_val = diagnostics_df["anomaly_score"].dropna().min() if "anomaly_score" in diagnostics_df.columns else np.nan
score_max_val = diagnostics_df["anomaly_score"].dropna().max() if "anomaly_score" in diagnostics_df.columns else np.nan

latest_timestamp = diagnostics_df["timestamp"].max() if "timestamp" in diagnostics_df.columns else None
earliest_timestamp = diagnostics_df["timestamp"].min() if "timestamp" in diagnostics_df.columns else None


# =========================
# SIDEBAR
# =========================
st.sidebar.header("Diagnostics Controls")

show_only_anomalies = st.sidebar.checkbox("Show anomalies only", value=False)

max_rows = st.sidebar.slider(
    "Rows to display",
    min_value=10,
    max_value=200,
    value=25,
    step=5
)

if diagnostics_df["anomaly_score"].dropna().empty:
    filtered_df = diagnostics_df.copy()
else:
    score_slider_min = float(score_min_val)
    score_slider_max = float(score_max_val)

    selected_score_range = st.sidebar.slider(
        "Anomaly score range",
        min_value=score_slider_min,
        max_value=score_slider_max,
        value=(score_slider_min, score_slider_max)
    )

    filtered_df = diagnostics_df[
        diagnostics_df["anomaly_score"].between(selected_score_range[0], selected_score_range[1], inclusive="both")
    ].copy()

if show_only_anomalies:
    filtered_df = filtered_df[filtered_df["is_anomaly"] == True]


# =========================
# TOP METRICS
# =========================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Model", model_info["model_name"])
col2.metric("Rows Scored", f"{rows_scored:,}")
col3.metric("Detected Anomalies", f"{anomaly_count:,}")
col4.metric("Anomaly Rate", f"{anomaly_rate:.2f}%")


# =========================
# MODEL SUMMARY
# =========================
st.subheader("Model Summary")

sum_col1, sum_col2, sum_col3 = st.columns(3)

with sum_col1:
    st.info(
        f"""
**Model Type:** {model_info['model_type']}  
**Scaler:** {model_info['scaler_type']}  
**Version:** {model_info['version']}
"""
    )

with sum_col2:
    st.info(
        f"""
**Contamination:** {model_info['contamination']}  
**Estimators:** {model_info['n_estimators']}  
**Max Samples:** {model_info['max_samples']}
"""
    )

with sum_col3:
    st.info(
        f"""
**Model Saved:** {model_info['model_saved_at']}  
**Scaler Saved:** {model_info['scaler_saved_at']}  
**Random State:** {model_info['random_state']}
"""
    )


# =========================
# MODEL SETTINGS
# =========================
with st.expander("Model Settings and Saved Artefacts", expanded=True):
    settings_col1, settings_col2 = st.columns(2)

    with settings_col1:
        st.write(f"**Model Name:** {model_info['model_name']}")
        st.write(f"**Model Type:** {model_info['model_type']}")
        st.write(f"**Score Column:** {model_info['score_column']}")
        st.write(f"**Prediction Column:** {model_info['prediction_column']}")
        st.write(f"**Contamination:** {model_info['contamination']}")
        st.write(f"**Number of Trees:** {model_info['n_estimators']}")
        st.write(f"**Max Samples:** {model_info['max_samples']}")

    with settings_col2:
        st.write("**Features Used:**")
        for feature in model_info["features_used"]:
            st.write(f"- {feature}")

        st.write(f"**Scaler Type:** {model_info['scaler_type']}")
        st.write(f"**Model Saved At:** {model_info['model_saved_at']}")
        st.write(f"**Scaler Saved At:** {model_info['scaler_saved_at']}")
        st.write(f"**Detection Note:** {model_info['threshold_note']}")


# =========================
# DATA COVERAGE
# =========================
with st.expander("Scored Data Coverage", expanded=False):
    cover_col1, cover_col2, cover_col3 = st.columns(3)

    cover_col1.metric("First Timestamp", format_dt(earliest_timestamp) if earliest_timestamp is not None else "N/A")
    cover_col2.metric("Last Timestamp", format_dt(latest_timestamp) if latest_timestamp is not None else "N/A")
    cover_col3.metric("Filtered Rows", f"{len(filtered_df):,}")


# =========================
# SCORE DISTRIBUTION
# =========================
if diagnostics_df["anomaly_score"].notna().any():
    st.subheader("Anomaly Score Distribution")

    fig_hist = px.histogram(
        diagnostics_df,
        x="anomaly_score",
        nbins=50,
        title="Distribution of Saved Anomaly Scores"
    )
    st.plotly_chart(fig_hist, use_container_width=True)


# =========================
# SCORE OVER TIME
# =========================
if "timestamp" in diagnostics_df.columns and diagnostics_df["anomaly_score"].notna().any():
    st.subheader("Anomaly Score Over Time")

    fig_time = px.line(
        diagnostics_df,
        x="timestamp",
        y="anomaly_score",
        title="Saved Anomaly Scores Across Time"
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
# ANOMALY COUNTS OVER TIME
# =========================
if "timestamp" in diagnostics_df.columns:
    st.subheader("Anomaly Frequency by Day")

    daily_counts = diagnostics_df.copy()
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
        title="Detected Anomalies per Day"
    )
    st.plotly_chart(fig_daily, use_container_width=True)


# =========================
# FEATURE-LEVEL DIAGNOSTICS
# =========================
st.subheader("Feature-Level Detection Details")

if feature_diag_df.empty:
    st.info("No feature-level diagnostics could be generated.")
else:
    st.dataframe(feature_diag_df, use_container_width=True, hide_index=True)


# =========================
# FEATURE COMPARISON CHART
# =========================
if not feature_diag_df.empty:
    st.subheader("Average Feature Behaviour in Normal vs Anomalous Records")

    chart_df = feature_diag_df.melt(
        id_vars="feature",
        value_vars=["normal_mean", "anomaly_mean"],
        var_name="group",
        value_name="value"
    )

    chart_df["group"] = chart_df["group"].replace({
        "normal_mean": "Normal records",
        "anomaly_mean": "Anomalous records"
    })

    fig_features = px.bar(
        chart_df,
        x="feature",
        y="value",
        color="group",
        barmode="group",
        title="Feature Mean Comparison"
    )
    st.plotly_chart(fig_features, use_container_width=True)


# =========================
# INTERPRETATION / INSIGHTS
# =========================
st.subheader("Diagnostic Insights")

insight_lines = []

insight_lines.append(
    f"The model scored {rows_scored:,} records and flagged {anomaly_count:,} of them as anomalous, "
    f"which corresponds to an anomaly rate of {anomaly_rate:.2f}%."
)

if pd.notna(score_min_val) and pd.notna(score_max_val):
    insight_lines.append(
        f"The saved anomaly scores range from {score_min_val:.6f} to {score_max_val:.6f}, "
        f"showing the spread of observations identified by the model."
    )

if latest_timestamp is not None and earliest_timestamp is not None:
    insight_lines.append(
        f"The scored data currently covers the period from {format_dt(earliest_timestamp)} "
        f"to {format_dt(latest_timestamp)}."
    )

if not feature_diag_df.empty:
    strongest_feature = feature_diag_df["deviation_pct"].abs().idxmax()
    strongest_row = feature_diag_df.loc[strongest_feature]

    if pd.notna(strongest_row["deviation_pct"]):
        insight_lines.append(
            f"The strongest difference between anomalous and normal observations was seen in "
            f"`{strongest_row['feature']}`, where anomalous records were described as "
            f"'{strongest_row['anomaly_pattern']}' compared with the overall behaviour."
        )

for line in insight_lines:
    st.write(f"- {line}")


# =========================
# TOP ANOMALOUS ROWS
# =========================
st.subheader("Highest Priority Anomalous Observations")

top_anomalies = (
    filtered_df[filtered_df["is_anomaly"] == True]
    .sort_values("anomaly_score", ascending=True)
    .head(max_rows)
    .copy()
)

# For Isolation Forest, lower scores are usually more abnormal.
# If your saved scores are reversed, change ascending=True to False.

display_cols = [
    "timestamp",
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "net_sent_delta_mb",
    "net_recv_delta_mb",
    "uptime_seconds",
    "anomaly_score",
    "is_anomaly"
]

available_display_cols = [col for col in display_cols if col in top_anomalies.columns]

if top_anomalies.empty:
    st.info("No anomalous rows found for the current filter.")
else:
    st.dataframe(
        top_anomalies[available_display_cols],
        use_container_width=True,
        hide_index=True
    )


# =========================
# RAW OUTPUT
# =========================
with st.expander("Raw Diagnostic Output"):
    st.dataframe(
        filtered_df.head(max_rows),
        use_container_width=True,
        hide_index=True
    )