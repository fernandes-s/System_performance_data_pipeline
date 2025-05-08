import psutil
import sqlite3
from datetime import datetime
import time

# Collect system metrics every 60 seconds
while True:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent

    conn = sqlite3.connect('system_metrics.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO metrics (timestamp, cpu_percent, memory_percent) VALUES (?, ?, ?)",
                   (timestamp, cpu, memory))
    conn.commit()
    conn.close()

    print(f"[{timestamp}] CPU: {cpu}%, Memory: {memory}%")
    time.sleep(45)
