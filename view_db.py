# view_db.py
import sqlite3
import pandas as pd

conn = sqlite3.connect('system_metrics.db')
df = pd.read_sql_query("SELECT * FROM metrics ORDER BY timestamp DESC LIMIT 10", conn)
print(df)
conn.close()
