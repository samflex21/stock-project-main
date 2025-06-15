import sqlite3
import os

# Connect to the database
db_path = os.path.join(os.getcwd(), 'stock-project.db')
print(f"Connecting to database at: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List all tables in the database
print("\n== DATABASE TABLES ==")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
for table in tables:
    print(f"- {table[0]}")

# For each table, get its schema
print("\n== TABLE SCHEMAS ==")
for table in tables:
    table_name = table[0]
    print(f"\nTable: {table_name}")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        # col format: (cid, name, type, notnull, dflt_value, pk)
        print(f"  - {col[1]} ({col[2]}){' PRIMARY KEY' if col[5] else ''}")

    # Show first few rows to understand data
    try:
        print("\n  Sample data (first 3 rows):")
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"  {row}")
        else:
            print("  (no data)")
    except Exception as e:
        print(f"  Error getting sample data: {e}")
    
    print("\n" + "-"*50)

conn.close()
print("Database inspection complete!")
