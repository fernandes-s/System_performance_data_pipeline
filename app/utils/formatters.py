import math
from datetime import timedelta

import pandas as pd


def format_timestamp(value) -> str:
    """
    Format a timestamp-like value into a readable string.

    Args:
        value: A datetime, pandas timestamp, or timestamp-like value.

    Returns:
        str: Formatted timestamp or fallback text if missing.
    """
    if value is None or pd.isna(value):
        return "N/A"

    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return "N/A"

    return ts.strftime("%d %b %Y, %H:%M")


def format_percentage(value, decimals: int = 1) -> str:
    """
    Format a numeric value as a percentage string.

    Args:
        value: Numeric percentage value.
        decimals (int): Number of decimal places.

    Returns:
        str: Formatted percentage or fallback text if missing.
    """
    if value is None or pd.isna(value):
        return "N/A"

    return f"{float(value):.{decimals}f}%"


def format_large_number(value, decimals: int = 1) -> str:
    """
    Format large numbers using K, M, or B suffixes.

    Args:
        value: Numeric value.
        decimals (int): Number of decimal places.

    Returns:
        str: Formatted number or fallback text if missing.
    """
    if value is None or pd.isna(value):
        return "N/A"

    value = float(value)
    abs_value = abs(value)

    if abs_value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.{decimals}f}B"
    if abs_value >= 1_000_000:
        return f"{value / 1_000_000:.{decimals}f}M"
    if abs_value >= 1_000:
        return f"{value / 1_000:.{decimals}f}K"

    if value.is_integer():
        return str(int(value))

    return f"{value:.{decimals}f}"


def format_duration(seconds) -> str:
    """
    Format a duration in seconds into a human-readable string.

    Args:
        seconds: Duration in seconds.

    Returns:
        str: Human-readable duration or fallback text if missing.
    """
    if seconds is None or pd.isna(seconds):
        return "N/A"

    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return "N/A"

    if seconds < 0:
        return "N/A"

    duration = timedelta(seconds=seconds)

    total_days = duration.days
    total_seconds = duration.seconds

    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []

    if total_days > 0:
        parts.append(f"{total_days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def format_number(value, decimals: int = 2) -> str:
    """
    Format a standard numeric value with optional decimals.

    Args:
        value: Numeric value.
        decimals (int): Number of decimal places.

    Returns:
        str: Formatted number or fallback text if missing.
    """
    if value is None or pd.isna(value):
        return "N/A"

    try:
        value = float(value)
    except (TypeError, ValueError):
        return "N/A"

    if math.isclose(value, round(value)):
        return str(int(round(value)))

    return f"{value:.{decimals}f}"


def format_nullable_text(value, fallback: str = "N/A") -> str:
    """
    Return a clean string for text values, with fallback for missing values.

    Args:
        value: Input value.
        fallback (str): Fallback text for missing values.

    Returns:
        str: Clean text output.
    """
    if value is None or pd.isna(value):
        return fallback

    text = str(value).strip()
    return text if text else fallback