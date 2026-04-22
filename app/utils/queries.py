import pandas as pd

from utils.config import (
    ANOMALY_TABLE,
    DEFAULT_RECENT_DAYS,
    METRICS_TABLE,
)
from utils.database import run_query, table_exists


def get_table_names() -> list[str]:
    """
    Return the list of tables available in the SQLite database.

    Returns:
        list[str]: Table names sorted alphabetically.
    """
    query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """
    df = run_query(query)
    return df["name"].tolist()


def load_metrics() -> pd.DataFrame:
    """
    Load all rows from the metrics table ordered by timestamp.

    Returns:
        pd.DataFrame: Full metrics dataset.
    """
    query = f"""
        SELECT *
        FROM {METRICS_TABLE}
        ORDER BY timestamp
    """
    return run_query(query)


def load_latest_metrics(limit: int = 10) -> pd.DataFrame:
    """
    Load the most recent rows from the metrics table.

    Args:
        limit (int): Number of latest rows to return.

    Returns:
        pd.DataFrame: Recent metrics rows ordered from newest to oldest.
    """
    query = f"""
        SELECT *
        FROM {METRICS_TABLE}
        ORDER BY timestamp DESC
        LIMIT ?
    """
    return run_query(query, (limit,))


def load_recent_metrics(days: int = DEFAULT_RECENT_DAYS) -> pd.DataFrame:
    """
    Load metrics from the most recent number of days.

    Args:
        days (int): Number of recent days to include.

    Returns:
        pd.DataFrame: Recent metrics rows ordered by timestamp.
    """
    query = f"""
        SELECT *
        FROM {METRICS_TABLE}
        WHERE timestamp >= datetime('now', ?)
        ORDER BY timestamp
    """
    return run_query(query, (f"-{days} days",))


def load_anomaly_results() -> pd.DataFrame:
    """
    Load all rows from the anomaly results table ordered by timestamp.

    Returns:
        pd.DataFrame: Anomaly results dataset, or empty DataFrame if table is missing.
    """
    if not table_exists(ANOMALY_TABLE):
        return pd.DataFrame()

    query = f"""
        SELECT *
        FROM {ANOMALY_TABLE}
        ORDER BY timestamp
    """
    return run_query(query)


def load_latest_anomalies(limit: int = 10) -> pd.DataFrame:
    """
    Load the most recent anomaly rows.

    Args:
        limit (int): Number of latest anomaly rows to return.

    Returns:
        pd.DataFrame: Recent anomaly rows, or empty DataFrame if table is missing.
    """
    if not table_exists(ANOMALY_TABLE):
        return pd.DataFrame()

    query = f"""
        SELECT *
        FROM {ANOMALY_TABLE}
        ORDER BY timestamp DESC
        LIMIT ?
    """
    return run_query(query, (limit,))


def load_flagged_anomalies() -> pd.DataFrame:
    """
    Load only rows flagged as anomalies.

    Returns:
        pd.DataFrame: Flagged anomaly rows, or empty DataFrame if table is missing.
    """
    if not table_exists(ANOMALY_TABLE):
        return pd.DataFrame()

    query = f"""
        SELECT *
        FROM {ANOMALY_TABLE}
        WHERE anomaly_flag = 1
        ORDER BY timestamp DESC
    """
    return run_query(query)


def load_recent_flagged_anomalies(days: int = DEFAULT_RECENT_DAYS) -> pd.DataFrame:
    """
    Load flagged anomalies from the most recent number of days.

    Args:
        days (int): Number of recent days to include.

    Returns:
        pd.DataFrame: Recent flagged anomalies, or empty DataFrame if table is missing.
    """
    if not table_exists(ANOMALY_TABLE):
        return pd.DataFrame()

    query = f"""
        SELECT *
        FROM {ANOMALY_TABLE}
        WHERE anomaly_flag = 1
          AND timestamp >= datetime('now', ?)
        ORDER BY timestamp DESC
    """
    return run_query(query, (f"-{days} days",))