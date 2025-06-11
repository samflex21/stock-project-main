import sqlite3
import os

def check_database_structure(db_path):
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"Tables in database ({db_path}):")
        for table in tables:
            table_name = table[0]
            print(f"\n- {table_name}")
            
            # Get columns for each table
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print("  Columns:")
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                print(f"    {col_name} ({col_type}){' PRIMARY KEY' if pk else ''}")
                
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")

# Check both database files
print("Checking stock-project.db:")
check_database_structure("stock-project.db")

print("\nChecking 'stock project.db':")
check_database_structure("stock project.db")
