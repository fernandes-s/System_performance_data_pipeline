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
# MAIN CLEANING PIPELINE
# =========================
def clean_metrics(
    df: pd.DataFrame,
    use_clipping: bool = False,
    remove_outliers: bool = True,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Full cleaning pipeline.

    Parameters
    ----------
    df : pd.DataFrame
        Raw dataframe from SQLite
    use_clipping : bool
        If True, clip invalid values instead of dropping rows
    remove_outliers : bool
        If True, remove extreme values (network spikes)
    verbose : bool
        If True, print cleaning summary

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe
    """
    validate_required_columns(df)

    original_len = len(df)

    # Step 1 — remove missing values
    df_clean = drop_missing(df)
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

    # =========================
    # REPORTING (IMPORTANT FOR YOUR PROJECT)
    # =========================
    if verbose:
        print("\n=== DATA CLEANING SUMMARY ===")
        print(f"Original rows: {original_len}")
        print(f"After NA removal: {after_na}")
        print(f"After range handling: {after_range}")
        print(f"After network filtering: {after_network}")
        print(f"After outlier removal: {after_outliers}")
        print(f"Total rows removed: {original_len - after_outliers}")
        print("=============================\n")

    return df_clean.reset_index(drop=True)