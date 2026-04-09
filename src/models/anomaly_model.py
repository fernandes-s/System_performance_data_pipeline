from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


# =========================
# DEFAULT FEATURE LIST
# =========================
DEFAULT_FEATURES = [
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "net_sent_delta_mb",
    "net_recv_delta_mb",
    "uptime_seconds",
]

FEATURE_LABELS = {
    "cpu_percent": "CPU usage",
    "memory_percent": "Memory usage",
    "disk_percent": "Disk usage",
    "net_sent_delta_mb": "Network sent",
    "net_recv_delta_mb": "Network received",
    "uptime_seconds": "System uptime",
}


# =========================
# FEATURE PREPARATION
# =========================
def build_feature_matrix(df: pd.DataFrame, feature_cols=None) -> pd.DataFrame:
    """
    Selects the feature columns used by the anomaly model.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned dataframe.
    feature_cols : list[str] | None
        List of columns to use. If None, uses DEFAULT_FEATURES.

    Returns
    -------
    pd.DataFrame
        Feature-only dataframe.

    Raises
    ------
    ValueError
        If required columns are missing.
    """
    if feature_cols is None:
        feature_cols = DEFAULT_FEATURES.copy()

    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns: {missing_cols}")

    return df[feature_cols].copy()


# =========================
# SCALING
# =========================
def fit_scaler(X: pd.DataFrame) -> StandardScaler:
    """
    Fits a StandardScaler on the feature matrix.
    """
    scaler = StandardScaler()
    scaler.fit(X)
    return scaler


def transform_features(scaler: StandardScaler, X: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms the feature matrix using a fitted scaler.

    Returns
    -------
    pd.DataFrame
        Scaled feature matrix with original column names and index preserved.
    """
    X_scaled = scaler.transform(X)
    return pd.DataFrame(X_scaled, columns=X.columns, index=X.index)


# =========================
# MODEL TRAINING
# =========================
def train_isolation_forest(
    X: pd.DataFrame,
    contamination: float = 0.02,
    random_state: int = 42,
    n_estimators: int = 200,
    max_samples="auto"
) -> IsolationForest:
    """
    Trains an Isolation Forest model.

    Parameters
    ----------
    X : pd.DataFrame
        Scaled feature matrix.
    contamination : float
        Expected proportion of anomalies in the dataset.
    random_state : int
        Random seed for reproducibility.
    n_estimators : int
        Number of trees.
    max_samples : int | str
        Number of samples to draw for each base estimator.

    Returns
    -------
    IsolationForest
        Trained Isolation Forest model.
    """
    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=n_estimators,
        max_samples=max_samples
    )
    model.fit(X)
    return model


# =========================
# SCORING
# =========================
def score_model(model: IsolationForest, X: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """
    Scores the feature matrix using a trained Isolation Forest.

    Returns
    -------
    tuple[pd.Series, pd.Series]
        anomaly_score, is_anomaly

    Notes
    -----
    - sklearn decision_function():
        higher = more normal
        lower = more anomalous

    - Here we invert it so that:
        higher anomaly_score = more anomalous
    """
    raw_scores = model.decision_function(X)
    predictions = model.predict(X)

    anomaly_score = pd.Series(-raw_scores, index=X.index, name="anomaly_score")
    is_anomaly = pd.Series((predictions == -1).astype(int), index=X.index, name="is_anomaly")

    return anomaly_score, is_anomaly


# =========================
# INTERPRETATION HELPERS
# =========================
def get_zscore_column_name(feature_name: str) -> str:
    """
    Converts an original feature name into a readable z-score column name.
    """
    mapping = {
        "cpu_percent": "cpu_zscore",
        "memory_percent": "memory_zscore",
        "disk_percent": "disk_zscore",
        "net_sent_delta_mb": "net_sent_zscore",
        "net_recv_delta_mb": "net_recv_zscore",
        "uptime_seconds": "uptime_zscore",
    }
    return mapping.get(feature_name, f"{feature_name}_zscore")


def classify_anomaly_strength(anomaly_score: float) -> str:
    """
    Converts anomaly score into a simple strength label.

    Higher anomaly_score = more anomalous.
    """
    if anomaly_score >= 0.09:
        return "strong"
    if anomaly_score >= 0.05:
        return "moderate"
    return "weak"


def get_feature_direction(z_value: float) -> str:
    """
    Returns whether a feature is unusually high or low.
    """
    return "high" if z_value > 0 else "low"


def build_explanation_from_row(row: pd.Series, feature_cols: list[str]) -> str:
    """
    Builds a short human-readable explanation for one row based on z-scores.
    """
    feature_details = []

    for feature in feature_cols:
        z_col = get_zscore_column_name(feature)
        z_value = row[z_col]
        abs_z = abs(z_value)

        feature_details.append(
            {
                "feature": feature,
                "label": FEATURE_LABELS.get(feature, feature),
                "z_value": z_value,
                "abs_z": abs_z,
                "direction": get_feature_direction(z_value),
            }
        )

    feature_details = sorted(feature_details, key=lambda x: x["abs_z"], reverse=True)

    strong_drivers = [item for item in feature_details if item["abs_z"] >= 2.0]
    top_feature = feature_details[0]

    if strong_drivers:
        driver_parts = [
            f"{item['label']} unusually {item['direction']}"
            for item in strong_drivers[:3]
        ]
        return "; ".join(driver_parts)

    return (
        f"{top_feature['label']} slightly unusual "
        f"({top_feature['direction']}) compared to normal behaviour"
    )


def add_interpretation_columns(
    df: pd.DataFrame,
    X_scaled: pd.DataFrame,
    feature_cols: list[str]
) -> pd.DataFrame:
    """
    Adds z-score columns and anomaly interpretation fields.

    Added columns
    -------------
    - one z-score column per feature
    - top_driver
    - driver_count
    - explanation
    - anomaly_strength
    """
    result_df = df.copy()

    # Add z-score columns
    zscore_cols = []
    for feature in feature_cols:
        z_col = get_zscore_column_name(feature)
        result_df[z_col] = X_scaled[feature]
        zscore_cols.append(z_col)

    top_drivers = []
    driver_counts = []
    explanations = []
    anomaly_strengths = []

    for _, row in result_df.iterrows():
        feature_rank = []

        for feature in feature_cols:
            z_col = get_zscore_column_name(feature)
            z_value = row[z_col]

            feature_rank.append(
                {
                    "feature": feature,
                    "label": FEATURE_LABELS.get(feature, feature),
                    "z_value": z_value,
                    "abs_z": abs(z_value),
                    "direction": get_feature_direction(z_value),
                }
            )

        feature_rank = sorted(feature_rank, key=lambda x: x["abs_z"], reverse=True)
        strong_drivers = [item for item in feature_rank if item["abs_z"] >= 2.0]
        top_feature = feature_rank[0]

        if strong_drivers:
            top_driver = f"{strong_drivers[0]['label']} unusually {strong_drivers[0]['direction']}"
            driver_count = len(strong_drivers)
        else:
            top_driver = f"{top_feature['label']} slightly unusual ({top_feature['direction']})"
            driver_count = 1

        explanation = build_explanation_from_row(row, feature_cols)
        strength = classify_anomaly_strength(row["anomaly_score"])

        top_drivers.append(top_driver)
        driver_counts.append(driver_count)
        explanations.append(explanation)
        anomaly_strengths.append(strength)

    result_df["top_driver"] = top_drivers
    result_df["driver_count"] = driver_counts
    result_df["explanation"] = explanations
    result_df["anomaly_strength"] = anomaly_strengths

    return result_df


def add_anomaly_results(
    df: pd.DataFrame,
    anomaly_score,
    is_anomaly,
    X_scaled: pd.DataFrame,
    feature_cols: list[str]
) -> pd.DataFrame:
    """
    Returns a copy of the dataframe with anomaly outputs and interpretation added.
    """
    result_df = df.copy()
    result_df["anomaly_score"] = anomaly_score
    result_df["is_anomaly"] = is_anomaly

    result_df = add_interpretation_columns(
        df=result_df,
        X_scaled=X_scaled,
        feature_cols=feature_cols
    )

    return result_df


# =========================
# MODEL PIPELINE
# =========================
def run_anomaly_pipeline(
    df: pd.DataFrame,
    feature_cols=None,
    contamination: float = 0.02,
    random_state: int = 42,
    n_estimators: int = 200
):
    """
    Full model pipeline:
    1. select features
    2. fit scaler
    3. transform features
    4. train Isolation Forest
    5. score rows
    6. add interpretation columns
    7. return dataframe with anomaly outputs

    Returns
    -------
    tuple
        results_df, model, scaler, feature_cols
    """
    if feature_cols is None:
        feature_cols = DEFAULT_FEATURES.copy()

    X = build_feature_matrix(df, feature_cols)
    scaler = fit_scaler(X)
    X_scaled = transform_features(scaler, X)

    model = train_isolation_forest(
        X=X_scaled,
        contamination=contamination,
        random_state=random_state,
        n_estimators=n_estimators
    )

    anomaly_score, is_anomaly = score_model(model, X_scaled)

    results_df = add_anomaly_results(
        df=df,
        anomaly_score=anomaly_score,
        is_anomaly=is_anomaly,
        X_scaled=X_scaled,
        feature_cols=feature_cols
    )

    return results_df, model, scaler, feature_cols


# =========================
# SAVE / LOAD ARTEFACTS
# =========================
def save_model(model, file_path: str | Path):
    """
    Saves the trained model to disk.
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, file_path)


def load_model(file_path: str | Path):
    """
    Loads a trained model from disk.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Model file not found: {file_path}")
    return joblib.load(file_path)


def save_scaler(scaler, file_path: str | Path):
    """
    Saves the fitted scaler to disk.
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, file_path)


def load_scaler(file_path: str | Path):
    """
    Loads a fitted scaler from disk.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Scaler file not found: {file_path}")
    return joblib.load(file_path)