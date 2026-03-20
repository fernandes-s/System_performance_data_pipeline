from pathlib import Path
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "raw" / "system_metrics.db"
EXPORT_DIR = BASE_DIR / "data" / "exports" / "daily"

# Ensure export folder exists
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# Define today's time window (half-open interval)
today = datetime.now().date()
start_time = datetime.combine(today, datetime.min.time())
end_time = start_time + timedelta(days=1)

# Connect to database
conn = sqlite3.connect(DB_PATH)

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
output_file = EXPORT_DIR / f"{today.isoformat()}.csv"
df.to_csv(output_file, index=False)

print(
    f"[{datetime.now().isoformat()}] "
    f"Exported {len(df)} records to {output_file}"
)