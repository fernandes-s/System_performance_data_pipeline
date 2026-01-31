import psutil
import time
import sqlite3
from datetime import datetime

prev_net_sent = None
prev_net_recv = None


def collect_metrics():
    global prev_net_sent, prev_net_recv

    timestamp = datetime.now()

    cpu_percent = psutil.cpu_percent(interval=None)
    memory_percent = psutil.virtual_memory().percent
    disk_percent = psutil.disk_usage('/').percent

    net = psutil.net_io_counters()
    net_sent = net.bytes_sent
    net_recv = net.bytes_recv

    uptime_seconds = time.time() - psutil.boot_time()

    if prev_net_sent is None or net_sent < prev_net_sent:
        net_sent_delta_mb = 0.0
    else:
        net_sent_delta_mb = (net_sent - prev_net_sent) / (1024 * 1024)

    if prev_net_recv is None or net_recv < prev_net_recv:
        net_recv_delta_mb = 0.0
    else:
        net_recv_delta_mb = (net_recv - prev_net_recv) / (1024 * 1024)

    prev_net_sent = net_sent
    prev_net_recv = net_recv

    return {
        "timestamp": timestamp.isoformat(),
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "disk_percent": disk_percent,
        "net_sent_total_mb": net_sent / (1024 * 1024),
        "net_recv_total_mb": net_recv / (1024 * 1024),
        "net_sent_delta_mb": net_sent_delta_mb,
        "net_recv_delta_mb": net_recv_delta_mb,
        "uptime_seconds": uptime_seconds
    }


def insert_metrics(metrics, db_path="system_metrics.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO metrics (
            timestamp,
            cpu_percent,
            memory_percent,
            disk_percent,
            net_sent_total_mb,
            net_recv_total_mb,
            net_sent_delta_mb,
            net_recv_delta_mb,
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
    metrics = collect_metrics()
    insert_metrics(metrics)
