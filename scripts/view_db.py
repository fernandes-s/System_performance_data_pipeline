from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "raw" / "system_metrics.db"

conn = sqlite3.connect(DB_PATH)

df = pd.read_sql_query(
    "SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 10",
    conn
)

print(df)
conn.close()