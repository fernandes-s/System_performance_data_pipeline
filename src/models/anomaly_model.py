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
        feature_cols = DEFAULT_FEATURES

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


def transform_features(scaler: StandardScaler, X: pd.DataFrame):
    """
    Transforms the feature matrix using a fitted scaler.
    """
    return scaler.transform(X)


# =========================
# MODEL TRAINING
# =========================
def train_isolation_forest(
    X,
    contamination=0.02,
    random_state=42,
    n_estimators=200,
    max_samples="auto"
) -> IsolationForest:
    """
    Trains an Isolation Forest model.

    Parameters
    ----------
    X : array-like
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
def score_model(model: IsolationForest, X):
    """
    Scores the feature matrix using a trained Isolation Forest.

    Returns
    -------
    tuple
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

    anomaly_score = -raw_scores
    is_anomaly = (predictions == -1).astype(int)

    return anomaly_score, is_anomaly


def add_anomaly_results(
    df: pd.DataFrame,
    anomaly_score,
    is_anomaly
) -> pd.DataFrame:
    """
    Returns a copy of the dataframe with anomaly outputs added.
    """
    result_df = df.copy()
    result_df["anomaly_score"] = anomaly_score
    result_df["is_anomaly"] = is_anomaly
    return result_df


# =========================
# MODEL PIPELINE
# =========================
def run_anomaly_pipeline(
    df: pd.DataFrame,
    feature_cols=None,
    contamination=0.02,
    random_state=42,
    n_estimators=200
):
    """
    Full model pipeline:
    1. select features
    2. fit scaler
    3. transform features
    4. train Isolation Forest
    5. score rows
    6. return dataframe with anomaly outputs

    Returns
    -------
    tuple
        results_df, model, scaler
    """
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
    results_df = add_anomaly_results(df, anomaly_score, is_anomaly)

    return results_df, model, scaler


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
    return joblib.load(file_path)