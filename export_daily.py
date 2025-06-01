import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os

# Ensure export folder exists
os.makedirs("daily_metrics", exist_ok=True)

# Get today's date
today = datetime.now().date()
start_time = datetime.combine(today, datetime.min.time())
end_time = datetime.combine(today, datetime.max.time())

# Connect to DB and query today's metrics
conn = sqlite3.connect('system_metrics.db')
query = f"""
    SELECT * FROM metrics 
    WHERE timestamp BETWEEN '{start_time.isoformat()}' AND '{end_time.isoformat()}'
"""
df = pd.read_sql_query(query, conn)
conn.close()

# Save with filename as today's date
output_file = f"daily_metrics/{today.isoformat()}.csv"
df.to_csv(output_file, index=False)

print(f"[{datetime.now().isoformat()}] Exported {len(df)} records to {output_file}")
