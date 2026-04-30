import pandas as pd

from utils.config import METRIC_COLUMNS


def prepare_features(
    df: pd.DataFrame,
    feature_columns: list[str] | None = None,
) -> pd.DataFrame:
    """
    Return a clean feature DataFrame for anomaly-related analysis.

    Args:
        df (pd.DataFrame): Input DataFrame.
        feature_columns (list[str] | None): Columns to keep as features.

    Returns:
        pd.DataFrame: Numeric feature DataFrame with missing rows removed.
    """
    if df.empty:
        return pd.DataFrame()

    feature_columns = feature_columns or METRIC_COLUMNS
    available_columns = [col for col in feature_columns if col in df.columns]

    if not available_columns:
        return pd.DataFrame()

    features = df[available_columns].copy()

    for col in available_columns:
        features[col] = pd.to_numeric(features[col], errors="coerce")

    features = features.dropna()
    return features


def get_flagged_anomalies(
    df: pd.DataFrame,
    flag_column: str = "anomaly_flag",
) -> pd.DataFrame:
    """
    Return only rows flagged as anomalies.

    Args:
        df (pd.DataFrame): Input anomaly results DataFrame.
        flag_column (str): Column indicating anomaly status.

    Returns:
        pd.DataFrame: Rows where anomaly flag equals 1.
    """
    if df.empty or flag_column not in df.columns:
        return pd.DataFrame()

    flagged = df[df[flag_column] == 1].copy()
    return flagged


def get_anomaly_count(
    df: pd.DataFrame,
    flag_column: str = "anomaly_flag",
) -> int:
    """
    Count how many rows are flagged as anomalies.

    Args:
        df (pd.DataFrame): Input anomaly results DataFrame.
        flag_column (str): Column indicating anomaly status.

    Returns:
        int: Number of flagged anomalies.
    """
    return len(get_flagged_anomalies(df, flag_column=flag_column))


def get_anomaly_rate(
    df: pd.DataFrame,
    flag_column: str = "anomaly_flag",
) -> float | None:
    """
    Calculate the proportion of rows flagged as anomalies.

    Args:
        df (pd.DataFrame): Input anomaly results DataFrame.
        flag_column (str): Column indicating anomaly status.

    Returns:
        float | None: Anomaly rate as a percentage, or None if unavailable.
    """
    if df.empty or flag_column not in df.columns:
        return None

    total_rows = len(df)
    if total_rows == 0:
        return None

    anomaly_count = get_anomaly_count(df, flag_column=flag_column)
    return (anomaly_count / total_rows) * 100


def classify_anomaly_severity(
    df: pd.DataFrame,
    score_column: str = "anomaly_score",
    output_column: str = "severity",
) -> pd.DataFrame:
    """
    Classify anomaly severity using anomaly score quantiles.

    Higher anomaly scores are treated as stronger anomalies.

    Args:
        df (pd.DataFrame): Input anomaly results DataFrame.
        score_column (str): Column containing anomaly scores.
        output_column (str): Name of the output severity column.

    Returns:
        pd.DataFrame: DataFrame with an added severity column.
    """
    if df.empty or score_column not in df.columns:
        return df.copy()

    result = df.copy()
    result[score_column] = pd.to_numeric(result[score_column], errors="coerce")

    valid_scores = result[score_column].dropna()
    if valid_scores.empty:
        result[output_column] = "Unknown"
        return result

    severe_cutoff = valid_scores.quantile(0.90)
    moderate_cutoff = valid_scores.quantile(0.70)

    def assign_severity(score):
        if pd.isna(score):
            return "Unknown"
        if score >= severe_cutoff:
            return "Severe"
        if score >= moderate_cutoff:
            return "Moderate"
        return "Mild"

    result[output_column] = result[score_column].apply(assign_severity)
    return result


def get_anomaly_rows(
    df: pd.DataFrame,
    n: int = 10,
    flag_column: str = "anomaly_flag",
    score_column: str = "anomaly_score",
) -> pd.DataFrame:
    """
    Return the top anomaly rows ordered by anomaly score.

    More negative scores are treated as stronger anomalies.

    Args:
        df (pd.DataFrame): Input anomaly results DataFrame.
        n (int): Number of rows to return.
        flag_column (str): Column indicating anomaly status.
        score_column (str): Column containing anomaly scores.

    Returns:
        pd.DataFrame: Top anomaly rows.
    """
    flagged = get_flagged_anomalies(df, flag_column=flag_column)

    if flagged.empty:
        return flagged

    if score_column in flagged.columns:
        flagged = flagged.copy()
        flagged[score_column] = pd.to_numeric(flagged[score_column], errors="coerce")
        flagged = flagged.sort_values(by=score_column, ascending=False)

    return flagged.head(n).copy()


def get_top_anomaly_drivers(
    df: pd.DataFrame,
    feature_columns: list[str] | None = None,
    score_column: str = "anomaly_score",
    flag_column: str = "anomaly_flag",
) -> pd.DataFrame:
    """
    Estimate which features contribute most to anomalies by comparing
    flagged rows against the overall dataset using absolute z-score distance.

    Args:
        df (pd.DataFrame): Input anomaly results DataFrame.
        feature_columns (list[str] | None): Metric columns to compare.
        score_column (str): Included for compatibility with anomaly datasets.
        flag_column (str): Column indicating anomaly status.

    Returns:
        pd.DataFrame: Feature importance-style summary with average deviation.
    """
    if df.empty:
        return pd.DataFrame(columns=["feature", "avg_abs_zscore"])

    feature_columns = feature_columns or METRIC_COLUMNS
    available_columns = [col for col in feature_columns if col in df.columns]

    if not available_columns:
        return pd.DataFrame(columns=["feature", "avg_abs_zscore"])

    flagged = get_flagged_anomalies(df, flag_column=flag_column)
    if flagged.empty:
        return pd.DataFrame(columns=["feature", "avg_abs_zscore"])

    baseline = df[available_columns].copy()
    anomaly_subset = flagged[available_columns].copy()

    for col in available_columns:
        baseline[col] = pd.to_numeric(baseline[col], errors="coerce")
        anomaly_subset[col] = pd.to_numeric(anomaly_subset[col], errors="coerce")

    means = baseline.mean()
    stds = baseline.std().replace(0, pd.NA)

    zscores = (anomaly_subset - means) / stds
    avg_abs_zscores = zscores.abs().mean().dropna().sort_values(ascending=False)

    return pd.DataFrame({
        "feature": avg_abs_zscores.index,
        "avg_abs_zscore": avg_abs_zscores.values,
    })


def add_dominant_driver(
    df: pd.DataFrame,
    feature_columns: list[str] | None = None,
    output_column: str = "dominant_driver",
) -> pd.DataFrame:
    """
    Add a dominant driver column by selecting the feature with the largest
    absolute z-score deviation for each row.

    Args:
        df (pd.DataFrame): Input anomaly results DataFrame.
        feature_columns (list[str] | None): Metric columns to compare.
        output_column (str): Name of output column.

    Returns:
        pd.DataFrame: DataFrame with dominant driver column added.
    """
    if df.empty:
        return df.copy()

    feature_columns = feature_columns or METRIC_COLUMNS
    available_columns = [col for col in feature_columns if col in df.columns]

    if not available_columns:
        result = df.copy()
        result[output_column] = None
        return result

    result = df.copy()
    numeric_df = result[available_columns].apply(pd.to_numeric, errors="coerce")

    means = numeric_df.mean()
    stds = numeric_df.std().replace(0, pd.NA)
    zscores = ((numeric_df - means) / stds).abs()

    result[output_column] = zscores.idxmax(axis=1)
    return result