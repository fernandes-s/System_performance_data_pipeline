import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os

# Ensure export folder exists
os.makedirs("daily_metrics", exist_ok=True)

# Define today's time window (half-open interval)
today = datetime.now().date()
start_time = datetime.combine(today, datetime.min.time())
end_time = start_time + timedelta(days=1)

# Connect to database
conn = sqlite3.connect("system_metrics.db")

# Query today's metrics safely
query = """
    SELECT *
    FROM metrics
    WHERE timestamp >= ?
      AND timestamp < ?
"""

df = pd.read_sql_query(
    query,
    conn,
    params=(start_time.isoformat(), end_time.isoformat())
)

conn.close()

# Save CSV using ISO date
output_file = f"daily_metrics/{today.isoformat()}.csv"
df.to_csv(output_file, index=False)

print(
    f"[{datetime.now().isoformat()}] "
    f"Exported {len(df)} records to {output_file}"
)
