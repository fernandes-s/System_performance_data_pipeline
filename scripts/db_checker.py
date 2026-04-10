from pathlib import Path
import sqlite3
import pandas as pd

# ===============================
# PATH SETUP
# ===============================
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "raw" / "system_metrics.db"

# ===============================
# CONNECT TO DATABASE
# ===============================
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# ===============================
# GET ALL USER TABLES
# ===============================
cur.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='table'
      AND name NOT LIKE 'sqlite_%'
    ORDER BY name;
""")
tables = [row[0] for row in cur.fetchall()]

print("=" * 70)
print("DATABASE STRUCTURE REPORT")
print("=" * 70)
print(f"Database path: {DB_PATH}\n")

print("Tables in DB:")
for table in tables:
    print(f" - {table}")

# ===============================
# LOOP THROUGH EACH TABLE
# ===============================
for table_name in tables:
    print("\n" + "=" * 70)
    print(f"TABLE: {table_name}")
    print("=" * 70)

    # -------------------------------
    # 1. CREATE TABLE STATEMENT
    # -------------------------------
    create_stmt = cur.execute("""
        SELECT sql
        FROM sqlite_master
        WHERE type='table' AND name=?;
    """, (table_name,)).fetchone()

    print("\nCREATE STATEMENT:")
    print(create_stmt[0] if create_stmt and create_stmt[0] else "Not available")

    # -------------------------------
    # 2. COLUMN DETAILS
    # -------------------------------
    print("\nCOLUMNS:")
    columns = cur.execute(f"PRAGMA table_info({table_name});").fetchall()

    if columns:
        column_df = pd.DataFrame(
            columns,
            columns=["cid", "name", "type", "notnull", "default_value", "pk"]
        )
        print(column_df.to_string(index=False))
    else:
        print("No columns found.")

    # -------------------------------
    # 3. FOREIGN KEYS
    # -------------------------------
    print("\nFOREIGN KEYS:")
    foreign_keys = cur.execute(f"PRAGMA foreign_key_list({table_name});").fetchall()

    if foreign_keys:
        fk_df = pd.DataFrame(
            foreign_keys,
            columns=[
                "id", "seq", "referenced_table", "from_column",
                "to_column", "on_update", "on_delete", "match"
            ]
        )
        print(fk_df.to_string(index=False))
    else:
        print("No foreign keys found.")

    # -------------------------------
    # 4. INDEXES
    # -------------------------------
    print("\nINDEXES:")
    indexes = cur.execute(f"PRAGMA index_list({table_name});").fetchall()

    if indexes:
        idx_df = pd.DataFrame(
            indexes,
            columns=["seq", "name", "unique", "origin", "partial"]
        )
        print(idx_df.to_string(index=False))

        for idx in indexes:
            idx_name = idx[1]
            print(f"\n  Index columns for: {idx_name}")
            idx_info = cur.execute(f"PRAGMA index_info({idx_name});").fetchall()
            if idx_info:
                idx_info_df = pd.DataFrame(
                    idx_info,
                    columns=["seqno", "cid", "column_name"]
                )
                print(idx_info_df.to_string(index=False))
            else:
                print("  No index column details found.")
    else:
        print("No indexes found.")

    # -------------------------------
    # 5. ROW COUNT
    # -------------------------------
    print("\nROW COUNT:")
    row_count = cur.execute(f"SELECT COUNT(*) FROM {table_name};").fetchone()[0]
    print(row_count)

    # -------------------------------
    # 6. SAMPLE DATA
    # -------------------------------
    print("\nSAMPLE ROWS (up to 5):")
    sample_df = pd.read_sql_query(
        f"SELECT * FROM {table_name} LIMIT 5",
        conn
    )
    print(sample_df.to_string(index=False))

# ===============================
# CLOSE CONNECTION
# ===============================
conn.close()

print("\n" + "=" * 70)
print("END OF DATABASE REPORT")
print("=" * 70)




"""
_______________________________________
_______________________________________
_______________________________________
_______________________________________
_______________________________________
"""

# from pathlib import Path
# import sqlite3

# BASE_DIR = Path(__file__).resolve().parents[1]
# DB_PATH = BASE_DIR / "data" / "raw" / "system_metrics.db"

# print(f"DB path being used: {DB_PATH}")
# print(f"DB exists: {DB_PATH.exists()}")

# conn = sqlite3.connect(DB_PATH)
# cur = conn.cursor()

# cur.execute("""
#     SELECT name
#     FROM sqlite_master
#     WHERE type='table'
#     ORDER BY name;
# """)
# tables = cur.fetchall()

# print("\nTables in DB:")
# for t in tables:
#     print("-", t[0])

# conn.close()
