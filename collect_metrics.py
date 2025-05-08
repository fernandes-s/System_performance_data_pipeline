import psutil
import sqlite3
from datetime import datetime
import time
import pandas as pd


# Collect system metrics every 60 seconds
while True:
    conn = sqlite3.connect('system_metrics.db')
    cursor = conn.cursor()

    timestamp = datetime.now().isoformat()
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    net = psutil.net_io_counters()
    net_sent = net.bytes_sent / (1024 * 1024)  # Convert to MB
    net_recv = net.bytes_recv / (1024 * 1024)  # Convert to MB

    cursor.execute('''
        INSERT INTO metrics (timestamp, cpu_percent, memory_percent, disk_percent, net_sent, net_recv)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (timestamp, cpu, memory, disk, net_sent, net_recv))

    conn.commit()

    # Export a fresh sample every time
    df = pd.read_sql_query("SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 100", conn)
    df.to_csv("sample_metrics.csv", index=False)

    conn.close()
    print(f"[{timestamp}] CPU: {cpu}%, Mem: {memory}%, Disk: {disk}%, Sent: {net_sent:.2f}MB, Recv: {net_recv:.2f}MB")
    time.sleep(60)
