import sqlite3

# Connect to (or create) the database
conn = sqlite3.connect('system_metrics.db')
cursor = conn.cursor()

# Create the table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS metrics (
        timestamp TEXT,
        cpu_percent REAL,
        memory_percent REAL,
        disk_percent REAL,
        net_sent REAL,
        net_recv REAL
    )
''')

# Save and close the connection
conn.commit()
conn.close()
