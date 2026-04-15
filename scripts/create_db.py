from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "raw" / "system_metrics.db"


def create_metrics_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            cpu_percent REAL,
            memory_percent REAL,
            disk_percent REAL,
            net_sent_total_mb REAL,
            net_recv_total_mb REAL,
            net_sent_delta_mb REAL,
            net_recv_delta_mb REAL,
            uptime_seconds REAL
        )
    """)


def create_training_runs_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS training_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            trained_at TEXT NOT NULL,
            model_name TEXT,
            raw_rows INTEGER,
            cleaned_rows INTEGER,
            removed_rows INTEGER,
            anomalies_detected INTEGER,
            contamination REAL,
            score_min REAL,
            score_max REAL,
            features_used TEXT,
            top_anomaly_driver TEXT,
            notes TEXT
        )
    """)


def create_anomaly_results_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomaly_results (
            id INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            cpu_percent REAL,
            memory_percent REAL,
            disk_percent REAL,
            net_sent_delta_mb REAL,
            net_recv_delta_mb REAL,
            uptime_seconds REAL,
            anomaly_score REAL,
            is_anomaly INTEGER,
            cpu_zscore REAL,
            memory_zscore REAL,
            disk_zscore REAL,
            net_sent_zscore REAL,
            net_recv_zscore REAL,
            uptime_zscore REAL,
            top_driver TEXT,
            driver_count INTEGER,
            explanation TEXT,
            anomaly_strength TEXT
        )
    """)


def create_db(db_path=DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    create_metrics_table(cursor)
    create_training_runs_table(cursor)
    create_anomaly_results_table(cursor)

    conn.commit()
    conn.close()

    print(f"Database ready at: {db_path}")


if __name__ == "__main__":
    create_db()