import sqlite3

def create_db(db_path="system_metrics.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            timestamp TEXT NOT NULL,

            cpu_percent REAL,
            memory_percent REAL,
            disk_percent REAL,

            -- cumulative network counters (since boot)
            net_sent_total_mb REAL,
            net_recv_total_mb REAL,

            -- per-interval deltas (used for analysis)
            net_sent_delta_mb REAL,
            net_recv_delta_mb REAL,

            -- system context
            uptime_seconds REAL
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_db()
