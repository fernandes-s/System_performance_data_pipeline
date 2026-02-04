import psutil
import time
import sqlite3
from datetime import datetime

DB_PATH = "system_metrics.db"

def get_last_net_totals(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT net_sent_total_mb, net_recv_total_mb
        FROM metrics
        ORDER BY id DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()
    return row  # (sent_mb, recv_mb) or None

def collect_metrics(db_path=DB_PATH):
    timestamp = datetime.now()

    # CPU: interval=None often returns 0 on first call in a new process.
    # Use a small interval for a real sample:
    cpu_percent = psutil.cpu_percent(interval=0.2)

    memory_percent = psutil.virtual_memory().percent
    disk_percent = psutil.disk_usage('/').percent

    net = psutil.net_io_counters()
    net_sent_mb = net.bytes_sent / (1024 * 1024)
    net_recv_mb = net.bytes_recv / (1024 * 1024)

    uptime_seconds = time.time() - psutil.boot_time()

    last = get_last_net_totals(db_path)
    if last is None:
        net_sent_delta_mb = 0.0
        net_recv_delta_mb = 0.0
    else:
        last_sent_mb, last_recv_mb = last

        # Handle reset/wrap: if total goes backwards, set delta to 0
        net_sent_delta_mb = max(net_sent_mb - last_sent_mb, 0.0)
        net_recv_delta_mb = max(net_recv_mb - last_recv_mb, 0.0)

    return {
        "timestamp": timestamp.isoformat(),
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "disk_percent": disk_percent,
        "net_sent_total_mb": net_sent_mb,
        "net_recv_total_mb": net_recv_mb,
        "net_sent_delta_mb": net_sent_delta_mb,
        "net_recv_delta_mb": net_recv_delta_mb,
        "uptime_seconds": uptime_seconds
    }

def insert_metrics(metrics, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO metrics (
            timestamp, cpu_percent, memory_percent, disk_percent,
            net_sent_total_mb, net_recv_total_mb,
            net_sent_delta_mb, net_recv_delta_mb,
            uptime_seconds
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        metrics["timestamp"],
        metrics["cpu_percent"],
        metrics["memory_percent"],
        metrics["disk_percent"],
        metrics["net_sent_total_mb"],
        metrics["net_recv_total_mb"],
        metrics["net_sent_delta_mb"],
        metrics["net_recv_delta_mb"],
        metrics["uptime_seconds"]
    ))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    m = collect_metrics(DB_PATH)
    insert_metrics(m, DB_PATH)
