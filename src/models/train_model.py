import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import sqlite3
import pandas as pd
import json
from datetime import datetime

from models.preprocessing import clean_metrics
from models.anomaly_model import run_anomaly_pipeline, save_model, save_scaler


# =========================
# PATHS
# =========================
# Assumes:
# project_root/
#   ├── app/
#   ├── data/raw/system_metrics.db
#   └── src/models/train_model.py
BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "raw" / "system_metrics.db"
MODEL_DIR = BASE_DIR / "artifacts" / "models"
MODEL_PATH = MODEL_DIR / "isolation_forest_model.joblib"
SCALER_PATH = MODEL_DIR / "scaler.joblib"


# =========================
# DATABASE FUNCTIONS
# =========================
def get_connection():
    return sqlite3.connect(DB_PATH)


def load_model_data(conn) -> pd.DataFrame:
    """
    Loads raw metrics from SQLite for modelling.
    """
    query = """
        SELECT
            id,
            timestamp,
            cpu_percent,
            memory_percent,
            disk_percent,
            net_sent_delta_mb,
            net_recv_delta_mb,
            uptime_seconds
        FROM metrics
        ORDER BY timestamp ASC
    """
    df = pd.read_sql_query(query, conn)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


def save_anomaly_results(
    conn,
    results_df: pd.DataFrame,
    table_name: str = "anomaly_results"
):
    """
    Saves anomaly results into the existing SQLite table.
    Replaces the table on each run so results stay consistent with the latest model run.
    The table itself is already part of the DB structure from create_db.py.
    """
    output_cols = [
        "id",
        "timestamp",
        "cpu_percent",
        "memory_percent",
        "disk_percent",
        "net_sent_delta_mb",
        "net_recv_delta_mb",
        "uptime_seconds",
        "anomaly_score",
        "is_anomaly",
        "cpu_zscore",
        "memory_zscore",
        "disk_zscore",
        "net_sent_zscore",
        "net_recv_zscore",
        "uptime_zscore",
        "top_driver",
        "driver_count",
        "explanation",
        "anomaly_strength",
    ]

    available_cols = [col for col in output_cols if col in results_df.columns]
    save_df = results_df[available_cols].copy()
    save_df["timestamp"] = save_df["timestamp"].astype(str)

    # Keeps latest model results only
    save_df.to_sql(table_name, conn, if_exists="replace", index=False)


def save_training_run(
    conn,
    model_name: str,
    raw_rows: int,
    cleaned_rows: int,
    anomalies_detected: int,
    contamination: float,
    score_min: float | None,
    score_max: float | None,
    features_used: list[str],
    notes: str = ""
) -> int:
    """
    Saves one row into training_runs for model run tracking.
    """
    removed_rows = raw_rows - cleaned_rows

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO training_runs (
            trained_at,
            model_name,
            raw_rows,
            cleaned_rows,
            removed_rows,
            anomalies_detected,
            contamination,
            score_min,
            score_max,
            features_used,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        model_name,
        raw_rows,
        cleaned_rows,
        removed_rows,
        anomalies_detected,
        contamination,
        score_min,
        score_max,
        json.dumps(features_used),
        notes
    ))

    conn.commit()
    return cursor.lastrowid


# =========================
# REPORTING HELPERS
# =========================
def get_anomaly_only_df(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns only the flagged anomaly rows.
    """
    if results_df.empty or "is_anomaly" not in results_df.columns:
        return pd.DataFrame()

    return results_df[results_df["is_anomaly"] == 1].copy()


def print_driver_summary(anomaly_df: pd.DataFrame, top_n: int = 5):
    """
    Prints the most common anomaly drivers.
    """
    if anomaly_df.empty or "top_driver" not in anomaly_df.columns:
        print("Top drivers: not available")
        return

    driver_counts = anomaly_df["top_driver"].value_counts().head(top_n)

    if driver_counts.empty:
        print("Top drivers: none")
        return

    print("\nMost common anomaly drivers:")
    for driver, count in driver_counts.items():
        print(f"  - {driver}: {count}")


def print_example_case_studies(anomaly_df: pd.DataFrame, top_n: int = 3):
    """
    Prints a few of the strongest anomaly examples for interpretation.
    """
    if anomaly_df.empty:
        print("\nNo anomaly case studies available.")
        return

    case_df = anomaly_df.sort_values("anomaly_score", ascending=False).head(top_n)

    print("\nExample anomaly case studies:")
    for _, row in case_df.iterrows():
        timestamp = row.get("timestamp", "N/A")
        score = row.get("anomaly_score", None)
        top_driver = row.get("top_driver", "N/A")
        strength = row.get("anomaly_strength", "N/A")
        explanation = row.get("explanation", "N/A")

        score_text = f"{score:.6f}" if pd.notna(score) else "N/A"

        print(f"  - Timestamp: {timestamp}")
        print(f"    Score: {score_text}")
        print(f"    Strength: {strength}")
        print(f"    Driver: {top_driver}")
        print(f"    Interpretation: {explanation}")


def print_run_summary(
    raw_df: pd.DataFrame,
    clean_df: pd.DataFrame,
    results_df: pd.DataFrame,
    feature_cols: list[str],
    run_id: int
):
    """
    Prints a stronger training summary with anomaly interpretation.
    """
    total_rows = len(raw_df)
    clean_rows = len(clean_df)
    removed_rows = total_rows - clean_rows
    anomaly_df = get_anomaly_only_df(results_df)
    anomaly_count = len(anomaly_df)

    print("\n=== MODEL TRAINING SUMMARY ===")
    print(f"Database path: {DB_PATH}")
    print(f"Training run ID: {run_id}")
    print(f"Raw rows loaded: {total_rows}")
    print(f"Rows after cleaning: {clean_rows}")
    print(f"Rows removed during cleaning: {removed_rows}")
    print(f"Features used: {', '.join(feature_cols)}")
    print(f"Anomalies detected: {anomaly_count}")

    if not results_df.empty:
        print(f"Anomaly score min: {results_df['anomaly_score'].min():.6f}")
        print(f"Anomaly score max: {results_df['anomaly_score'].max():.6f}")

    if not anomaly_df.empty:
        strong_count = (anomaly_df["anomaly_strength"] == "strong").sum()
        moderate_count = (anomaly_df["anomaly_strength"] == "moderate").sum()
        weak_count = (anomaly_df["anomaly_strength"] == "weak").sum()

        print(f"Strong anomalies: {strong_count}")
        print(f"Moderate anomalies: {moderate_count}")
        print(f"Weak anomalies: {weak_count}")

        print_driver_summary(anomaly_df)
        print_example_case_studies(anomaly_df, top_n=3)

    print(f"\nResults saved to table: anomaly_results")
    print(f"Training metadata saved to table: training_runs")
    print(f"Model saved to: {MODEL_PATH}")
    print(f"Scaler saved to: {SCALER_PATH}")
    print("==============================\n")


# =========================
# MAIN PIPELINE
# =========================
def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at: {DB_PATH}")

    conn = get_connection()

    try:
        # 1. Load raw data
        df = load_model_data(conn)

        if df.empty:
            raise ValueError("No data found in the metrics table.")

        # 2. Clean data
        df_clean = clean_metrics(
            df,
            use_clipping=False,
            remove_outliers=True,
            verbose=True
        )

        if df_clean.empty:
            raise ValueError("No rows left after cleaning. Check your cleaning rules or raw data quality.")

        # 3. Train model and score anomalies
        contamination = 0.02

        results_df, model, scaler, feature_cols = run_anomaly_pipeline(
            df=df_clean,
            feature_cols=None,      # uses DEFAULT_FEATURES from anomaly_model.py
            contamination=contamination,
            random_state=42,
            n_estimators=200
        )

        # 4. Save anomaly results back to SQLite
        save_anomaly_results(conn, results_df, table_name="anomaly_results")

        # 5. Save training run metadata
        anomaly_df = get_anomaly_only_df(results_df)
        score_min = float(results_df["anomaly_score"].min()) if not results_df.empty else None
        score_max = float(results_df["anomaly_score"].max()) if not results_df.empty else None

        run_id = save_training_run(
            conn=conn,
            model_name="IsolationForest",
            raw_rows=len(df),
            cleaned_rows=len(df_clean),
            anomalies_detected=len(anomaly_df),
            contamination=contamination,
            score_min=score_min,
            score_max=score_max,
            features_used=feature_cols,
            notes="Main training run"
        )

        # 6. Save artefacts
        save_model(model, MODEL_PATH)
        save_scaler(scaler, SCALER_PATH)

        # 7. Print summary
        print_run_summary(df, df_clean, results_df, feature_cols, run_id)

    finally:
        conn.close()


if __name__ == "__main__":
    main()