import pandas as pd
from sklearn.ensemble import IsolationForest


# =========================
# FEATURE PREPARATION
# =========================
def prepare_features(df):
    feature_cols = [
        "cpu_percent",
        "memory_percent",
        "disk_percent",
        "net_sent_delta_mb",
        "net_recv_delta_mb",
        "uptime_seconds",
    ]

    available_cols = [col for col in feature_cols if col in df.columns]

    feature_df = df[available_cols].copy()
    feature_df = feature_df.fillna(0)

    return feature_df, available_cols


# =========================
# RUN ISOLATION FOREST
# =========================
def run_isolation_forest(df, contamination=0.02, random_state=42):
    """
    Returns a copy of df with:
    - anomaly_flag (1 = anomaly, 0 = normal)
    - anomaly_score
    """
    if df.empty:
        result = df.copy()
        result["anomaly_flag"] = []
        result["anomaly_score"] = []
        return result

    result_df = df.copy()

    X, feature_cols = prepare_features(result_df)

    if X.empty or X.shape[0] < 5:
        result_df["anomaly_flag"] = 0
        result_df["anomaly_score"] = 0.0
        return result_df

    model = IsolationForest(
        contamination=contamination,
        random_state=random_state
    )

    model.fit(X)

    predictions = model.predict(X)  # -1 = anomaly, 1 = normal
    scores = model.decision_function(X)

    result_df["anomaly_flag"] = (predictions == -1).astype(int)
    result_df["anomaly_score"] = scores

    return result_df


# =========================
# SUMMARY HELPERS
# =========================
def get_anomaly_count(df, anomaly_flag_col="anomaly_flag"):
    if df.empty or anomaly_flag_col not in df.columns:
        return 0
    return int(df[anomaly_flag_col].sum())


def get_anomaly_rows(df, anomaly_flag_col="anomaly_flag"):
    if df.empty or anomaly_flag_col not in df.columns:
        return df.copy()

    anomaly_df = df[df[anomaly_flag_col] == 1].copy()
    return anomaly_df.sort_values("timestamp", ascending=False)