import pandas as pd

from utils.config import (
    COLLECTION_GAP_MINUTES,
    CPU_WARNING_THRESHOLD,
    DEFAULT_RECENT_DAYS,
    DISK_WARNING_THRESHOLD,
    MEMORY_WARNING_THRESHOLD,
)


def ensure_datetime(df: pd.DataFrame, column: str = "timestamp") -> pd.DataFrame:
    """
    Return a copy of the DataFrame with the timestamp column converted to datetime.
    """
    if df.empty or column not in df.columns:
        return df.copy()

    df = df.copy()
    df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def get_latest_timestamp(df: pd.DataFrame, column: str = "timestamp"):
    """
    Return the latest timestamp in the DataFrame.
    """
    if df.empty or column not in df.columns:
        return None

    df = ensure_datetime(df, column)
    if df[column].dropna().empty:
        return None

    return df[column].max()


def get_first_timestamp(df: pd.DataFrame, column: str = "timestamp"):
    """
    Return the earliest timestamp in the DataFrame.
    """
    if df.empty or column not in df.columns:
        return None

    df = ensure_datetime(df, column)
    if df[column].dropna().empty:
        return None

    return df[column].min()


def get_time_range(df: pd.DataFrame, column: str = "timestamp") -> tuple:
    """
    Return the earliest and latest timestamps in the DataFrame.
    """
    return get_first_timestamp(df, column), get_latest_timestamp(df, column)


def get_row_count(df: pd.DataFrame) -> int:
    """
    Return the total number of rows in the DataFrame.
    """
    return len(df)


def get_recent_window(
    df: pd.DataFrame,
    days: int = DEFAULT_RECENT_DAYS,
    column: str = "timestamp",
) -> pd.DataFrame:
    """
    Return only rows within the most recent number of days.
    """
    if df.empty or column not in df.columns:
        return df.copy()

    df = ensure_datetime(df, column)
    latest_ts = get_latest_timestamp(df, column)

    if latest_ts is None:
        return df.copy()

    cutoff = latest_ts - pd.Timedelta(days=days)
    return df[df[column] >= cutoff].copy()


def get_recent_rows(
    df: pd.DataFrame,
    n: int = 10,
    column: str = "timestamp",
    ascending: bool = False,
) -> pd.DataFrame:
    """
    Return the most recent rows sorted by timestamp.
    """
    if df.empty or column not in df.columns:
        return df.copy()

    df = ensure_datetime(df, column)
    df = df.sort_values(by=column, ascending=ascending)
    return df.head(n).copy()


def get_summary_metrics(df: pd.DataFrame) -> dict:
    """
    Calculate high-level summary metrics from system metric data.
    """
    if df.empty:
        return {
            "row_count": 0,
            "latest_timestamp": None,
            "avg_cpu": None,
            "avg_memory": None,
            "avg_disk": None,
        }

    return {
        "row_count": len(df),
        "latest_timestamp": get_latest_timestamp(df),
        "avg_cpu": df["cpu_percent"].mean() if "cpu_percent" in df.columns else None,
        "avg_memory": df["memory_percent"].mean() if "memory_percent" in df.columns else None,
        "avg_disk": df["disk_percent"].mean() if "disk_percent" in df.columns else None,
    }


def calculate_collection_gaps(
    df: pd.DataFrame,
    column: str = "timestamp",
    expected_gap_minutes: int = COLLECTION_GAP_MINUTES,
) -> pd.DataFrame:
    """
    Identify collection gaps larger than the expected interval.
    """
    if df.empty or column not in df.columns:
        return pd.DataFrame()

    df = ensure_datetime(df, column)
    df = df.dropna(subset=[column]).sort_values(by=column).copy()

    if df.empty:
        return pd.DataFrame()

    df["gap_minutes"] = df[column].diff().dt.total_seconds() / 60
    return df[df["gap_minutes"] > expected_gap_minutes].copy()


def calculate_system_health(df: pd.DataFrame) -> dict:
    """
    Evaluate the latest system health based on CPU, memory, and disk thresholds.
    """
    if df.empty:
        return {
            "status": "No data",
            "cpu_percent": None,
            "memory_percent": None,
            "disk_percent": None,
        }

    latest_row = get_recent_rows(df, n=1).iloc[0]

    cpu = latest_row["cpu_percent"] if "cpu_percent" in latest_row.index else None
    memory = latest_row["memory_percent"] if "memory_percent" in latest_row.index else None
    disk = latest_row["disk_percent"] if "disk_percent" in latest_row.index else None

    warning = False

    if cpu is not None and pd.notna(cpu) and cpu >= CPU_WARNING_THRESHOLD:
        warning = True
    if memory is not None and pd.notna(memory) and memory >= MEMORY_WARNING_THRESHOLD:
        warning = True
    if disk is not None and pd.notna(disk) and disk >= DISK_WARNING_THRESHOLD:
        warning = True

    return {
        "status": "Warning" if warning else "Healthy",
        "cpu_percent": cpu,
        "memory_percent": memory,
        "disk_percent": disk,
    }