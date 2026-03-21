from pathlib import Path
import sqlite3
import pandas as pd

# Resolve project root
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "raw" / "system_metrics.db"

# connect to database


# ===============================
# QUERY LIBRARY FOR METRICS DB
# ===============================


# Query 1 — Check latest rows
# df = pd.read_sql_query(
#     "SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 5",
#     conn
# )


# Query 2 — Check first rows (oldest data)
# Useful to confirm when collection started
# df = pd.read_sql_query(
#     "SELECT * FROM metrics ORDER BY timestamp ASC LIMIT 5",
#     conn
# )


# Query 3 — Count total rows
# Useful to know how much data you have
# df = pd.read_sql_query(
#     "SELECT COUNT(*) as total_rows FROM metrics",
#     conn
# )


# Query 4 — Last 100 rows
# Useful for plotting recent behaviour
# df = pd.read_sql_query(
#     "SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 100",
#     conn
# )


# Query 5 — Last 24 hours of data
# Useful for dashboards
# df = pd.read_sql_query(
#     "SELECT * FROM metrics WHERE timestamp >= datetime('now','-24 hours') ORDER BY timestamp",
#     conn
# )


# Query 6 — Last 1 hour of data
# Useful for short-term monitoring
# df = pd.read_sql_query(
#     "SELECT * FROM metrics WHERE timestamp >= datetime('now','-1 hour') ORDER BY timestamp",
#     conn
# )


# Query 7 — Average CPU usage
# Useful baseline metric
df = pd.read_sql_query(
    "SELECT AVG(cpu_percent) as avg_cpu FROM metrics",
    conn
)


# Query 8 — Average memory usage
# df = pd.read_sql_query(
#     "SELECT AVG(memory_percent) as avg_memory FROM metrics",
#     conn
# )


# Query 9 — Average disk usage
# df = pd.read_sql_query(
#     "SELECT AVG(disk_percent) as avg_disk FROM metrics",
#     conn
# )


# Query 10 — Maximum CPU usage recorded
# df = pd.read_sql_query(
#     "SELECT MAX(cpu_percent) as max_cpu FROM metrics",
#     conn
# )


# Query 11 — Maximum memory usage recorded
# df = pd.read_sql_query(
#     "SELECT MAX(memory_percent) as max_memory FROM metrics",
#     conn
# )


# Query 12 — Detect potential CPU spikes
# df = pd.read_sql_query(
#     "SELECT * FROM metrics WHERE cpu_percent > 90 ORDER BY timestamp DESC",
#     conn
# )


# Query 13 — Detect potential memory spikes
# df = pd.read_sql_query(
#     "SELECT * FROM metrics WHERE memory_percent > 90 ORDER BY timestamp DESC",
#     conn
# )


# Query 14 — Detect potential disk pressure
# df = pd.read_sql_query(
#     "SELECT * FROM metrics WHERE disk_percent > 90 ORDER BY timestamp DESC",
#     conn
# )


# Query 15 — Network spikes (sent data)
# df = pd.read_sql_query(
#     "SELECT * FROM metrics WHERE net_sent_delta_mb > 10 ORDER BY timestamp DESC",
#     conn
# )


# Query 16 — Network spikes (received data)
# df = pd.read_sql_query(
#     "SELECT * FROM metrics WHERE net_recv_delta_mb > 10 ORDER BY timestamp DESC",
#     conn
# )


# Query 17 — Latest system state (single row)
# Useful for dashboard summary cards
# df = pd.read_sql_query(
#     "SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 1",
#     conn
# )


# Query 18 — Average metrics per hour
# Useful for trend analysis
# df = pd.read_sql_query(
#     """
#     SELECT
#         strftime('%Y-%m-%d %H:00', timestamp) as hour,
#         AVG(cpu_percent) as avg_cpu,
#         AVG(memory_percent) as avg_memory,
#         AVG(disk_percent) as avg_disk
#     FROM metrics
#     GROUP BY hour
#     ORDER BY hour
#     """,
#     conn
# )


# Query 19 — Check uptime progression
# Useful to confirm system restart events
# df = pd.read_sql_query(
#     "SELECT timestamp, uptime_seconds FROM metrics ORDER BY timestamp DESC LIMIT 50",
#     conn
# )


# Query 20 — Detect possible system restart
# If uptime suddenly drops
# df = pd.read_sql_query(
#     """
#     SELECT *
#     FROM metrics
#     WHERE uptime_seconds < 1000
#     ORDER BY timestamp DESC
#     """,
#     conn
# )


# ===============================

print(df)

conn.close()