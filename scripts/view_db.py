# view_db.py
import sqlite3
import pandas as pd
import os

# force project root
os.chdir(r"C:\git\system-performance-pipeline")

conn = sqlite3.connect('data/raw/system_metrics.db')

df = pd.read_sql_query(
    "SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 10",
    conn
)

print(df)
conn.close()