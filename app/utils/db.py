from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st


# =========================
# PATHS
# =========================
# db.py is inside app/utils/
# parents[2] goes back to project root
BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "raw" / "system_metrics.db"


# =========================
# CONNECTION
# =========================
def get_connection():
    return sqlite3.connect(DB_PATH)


def database_exists():
    return DB_PATH.exists()


def get_db_path():
    return DB_PATH


# =========================
# DATA LOADING
# =========================
@st.cache_data
def load_data():
    conn = get_connection()
    query = """
        SELECT
            id,
            timestamp,
            cpu_percent,
            memory_percent,
            disk_percent,
            net_sent_total_mb,
            net_recv_total_mb,
            net_sent_delta_mb,
            net_recv_delta_mb,
            uptime_seconds
        FROM metrics
        ORDER BY timestamp ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"]).copy()

    return df


# =========================
# SUMMARY HELPERS
# =========================
def get_latest_timestamp(df):
    if df.empty:
        return None
    return df["timestamp"].max()


def format_latest_timestamp(timestamp):
    if timestamp is None:
        return "N/A"
    return timestamp.strftime("%d %b %Y, %H:%M:%S")


def get_summary_metrics(df):
    if df.empty:
        return {
            "latest_timestamp": None,
            "latest_timestamp_display": "N/A",
            "total_records": 0,
            "avg_cpu": 0.0,
            "avg_memory": 0.0,
        }

    latest_timestamp = get_latest_timestamp(df)

    return {
        "latest_timestamp": latest_timestamp,
        "latest_timestamp_display": format_latest_timestamp(latest_timestamp),
        "total_records": len(df),
        "avg_cpu": df["cpu_percent"].mean(),
        "avg_memory": df["memory_percent"].mean(),
    }


def get_recent_rows(df, n=20):
    if df.empty:
        return df.copy()

    recent_df = (
        df.sort_values("timestamp", ascending=False)
          .head(n)
          .copy()
    )

    recent_df["timestamp"] = recent_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return recent_df


def get_recent_window(df, days=7):
    if df.empty:
        return df.copy()

    latest_timestamp = df["timestamp"].max()
    cutoff = latest_timestamp - pd.Timedelta(days=days)

    recent_df = df[df["timestamp"] >= cutoff].copy()

    if recent_df.empty:
        return df.copy()

    return recent_df


def get_first_timestamp(df):
    if df.empty:
        return None
    return df["timestamp"].min()


def get_row_count(df):
    return len(df)


def get_time_range(df):
    if df.empty:
        return None, None
    return df["timestamp"].min(), df["timestamp"].max()