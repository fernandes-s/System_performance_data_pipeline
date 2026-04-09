import pandas as pd


# =========================
# DEFAULT FEATURE COLUMNS
# =========================
CORE_COLUMNS = [
    "cpu_percent",
    "memory_percent",
    "disk_percent",
    "net_sent_delta_mb",
    "net_recv_delta_mb",
    "uptime_seconds",
]


# =========================
# VALIDATION RULES
# =========================
def validate_required_columns(df: pd.DataFrame):
    """
    Ensures required columns exist in the dataframe.
    """
    missing = [col for col in CORE_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if "timestamp" not in df.columns:
        raise ValueError("Missing required column: ['timestamp']")


# =========================
# TIMESTAMP FILTERING
# =========================
def keep_exact_minute_timestamps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keeps only rows where the timestamp is exactly on the minute
    (seconds == 0).

    Examples kept:
    - 2026-04-05T12:17:00.662978
    - 2026-04-05 12:17:00

    Examples removed:
    - 2026-04-05T12:09:47.738971
    - 2026-04-05T12:08:24.794534
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    return df[df["timestamp"].notna() & (df["timestamp"].dt.second == 0)]


# =========================
# CLEANING FUNCTIONS
# =========================
def drop_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes rows with missing values in core columns.
    """
    return df.dropna(subset=CORE_COLUMNS)


def filter_valid_ranges(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keeps only rows with realistic system metric values.
    """
    df = df[
        (df["cpu_percent"].between(0, 100)) &
        (df["memory_percent"].between(0, 100)) &
        (df["disk_percent"].between(0, 100))
    ]
    return df


def filter_network_deltas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes rows where network deltas are negative.
    """
    return df[
        (df["net_sent_delta_mb"] >= 0) &
        (df["net_recv_delta_mb"] >= 0)
    ]


def remove_extreme_outliers(df: pd.DataFrame, quantile=0.995) -> pd.DataFrame:
    """
    Removes extreme spikes in network usage using quantile filtering.
    """
    df = df.copy()

    for col in ["net_sent_delta_mb", "net_recv_delta_mb"]:
        upper = df[col].quantile(quantile)
        df = df[df[col] <= upper]

    return df


# =========================
# OPTIONAL: CLIPPING INSTEAD OF DROPPING
# =========================
def clip_ranges(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clips values to valid ranges instead of removing rows.
    Useful if too much data is lost.
    """
    df = df.copy()

    df["cpu_percent"] = df["cpu_percent"].clip(0, 100)
    df["memory_percent"] = df["memory_percent"].clip(0, 100)
    df["disk_percent"] = df["disk_percent"].clip(0, 100)

    df["net_sent_delta_mb"] = df["net_sent_delta_mb"].clip(lower=0)
    df["net_recv_delta_mb"] = df["net_recv_delta_mb"].clip(lower=0)

    return df


# =========================
# SUMMARY HELPERS
# =========================
def build_cleaning_summary(
    original_len: int,
    after_timestamp: int,
    after_na: int,
    after_range: int,
    after_network: int,
    after_outliers: int,
    use_clipping: bool,
    remove_outliers: bool
) -> dict:
    """
    Builds a row-count summary for each cleaning stage.
    """
    summary = {
        "original_rows": original_len,
        "after_timestamp_filter": after_timestamp,
        "after_na_removal": after_na,
        "after_range_handling": after_range,
        "after_network_filtering": after_network,
        "after_outlier_removal": after_outliers,
        "removed_at_timestamp_filter": original_len - after_timestamp,
        "removed_at_na_removal": after_timestamp - after_na,
        "removed_at_range_handling": after_na - after_range,
        "removed_at_network_filtering": after_range - after_network,
        "removed_at_outlier_removal": after_network - after_outliers,
        "total_rows_removed": original_len - after_outliers,
        "use_clipping": use_clipping,
        "remove_outliers": remove_outliers,
    }
    return summary


def summary_dict_to_dataframe(summary: dict) -> pd.DataFrame:
    """
    Converts the cleaning summary dictionary to a dataframe.
    Useful for saving or displaying in diagnostics pages.
    """
    return pd.DataFrame(
        [{"step": key, "value": value} for key, value in summary.items()]
    )


def print_cleaning_summary(summary: dict):
    """
    Prints the cleaning summary in a clearer report format.
    """
    print("\n=== DATA CLEANING SUMMARY ===")
    print(f"Original rows: {summary['original_rows']}")
    print(
        f"After timestamp filtering: {summary['after_timestamp_filter']} "
        f"(removed {summary['removed_at_timestamp_filter']})"
    )
    print(
        f"After NA removal: {summary['after_na_removal']} "
        f"(removed {summary['removed_at_na_removal']})"
    )
    print(
        f"After range handling: {summary['after_range_handling']} "
        f"(removed {summary['removed_at_range_handling']})"
    )
    print(
        f"After network filtering: {summary['after_network_filtering']} "
        f"(removed {summary['removed_at_network_filtering']})"
    )
    print(
        f"After outlier removal: {summary['after_outlier_removal']} "
        f"(removed {summary['removed_at_outlier_removal']})"
    )
    print(f"Total rows removed: {summary['total_rows_removed']}")
    print("=============================\n")


# =========================
# MAIN CLEANING PIPELINE
# =========================
def clean_metrics(
    df: pd.DataFrame,
    use_clipping: bool = False,
    remove_outliers: bool = True,
    verbose: bool = True,
    return_summary: bool = False
):
    """
    Full cleaning pipeline.

    Parameters
    ----------
    df : pd.DataFrame
        Raw dataframe from SQLite.
    use_clipping : bool
        If True, clip invalid values instead of dropping rows.
    remove_outliers : bool
        If True, remove extreme values (network spikes).
    verbose : bool
        If True, print cleaning summary.
    return_summary : bool
        If True, returns both cleaned dataframe and cleaning summary.

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe

    or

    tuple[pd.DataFrame, dict]
        Cleaned dataframe and cleaning summary
    """
    validate_required_columns(df)

    original_len = len(df)

    # Step 0 — keep only exact minute timestamps
    df_clean = keep_exact_minute_timestamps(df)
    after_timestamp = len(df_clean)

    # Step 1 — remove missing values
    df_clean = drop_missing(df_clean)
    after_na = len(df_clean)

    # Step 2 — handle invalid ranges
    if use_clipping:
        df_clean = clip_ranges(df_clean)
        after_range = len(df_clean)
    else:
        df_clean = filter_valid_ranges(df_clean)
        after_range = len(df_clean)

    # Step 3 — network deltas
    df_clean = filter_network_deltas(df_clean)
    after_network = len(df_clean)

    # Step 4 — outliers (optional)
    if remove_outliers:
        df_clean = remove_extreme_outliers(df_clean)
        after_outliers = len(df_clean)
    else:
        after_outliers = len(df_clean)

    summary = build_cleaning_summary(
        original_len=original_len,
        after_timestamp=after_timestamp,
        after_na=after_na,
        after_range=after_range,
        after_network=after_network,
        after_outliers=after_outliers,
        use_clipping=use_clipping,
        remove_outliers=remove_outliers
    )

    if verbose:
        print_cleaning_summary(summary)

    df_clean = df_clean.reset_index(drop=True)

    if return_summary:
        return df_clean, summary

    return df_clean