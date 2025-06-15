import sqlite3
import json
import os

# Full absolute path to both potential database files
main_db = os.path.join(os.path.dirname(__file__), 'stock-project.db')
alt_db = os.path.join(os.path.dirname(__file__), 'stock project.db')

def check_tables(conn):
    """Check what tables exist in the database"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Found {len(tables)} tables in database:")
    for table in tables:
        print(f"- {table[0]}")
    return [t[0] for t in tables]

def check_columns(conn, table_name):
    """Check columns in a specific table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    print(f"\nColumns in {table_name}:")
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
    return columns

def rows_to_dict_list(rows):
    """Convert rows to a list of dictionaries"""
    if not rows:
        return []
    return [dict(row) for row in rows]

def check_stock_data():
    """Diagnostic function to check stock level data"""
    # Try main database first
    if os.path.exists(main_db):
        print(f"Using main database: {main_db}")
        conn = sqlite3.connect(main_db)
        conn.row_factory = sqlite3.Row
    elif os.path.exists(alt_db):
        print(f"Using alternative database: {alt_db}")
        conn = sqlite3.connect(alt_db)
        conn.row_factory = sqlite3.Row
    else:
        print("No database file found!")
        return

    # Check tables
    tables = check_tables(conn)
    
    # Check Product and Inventory tables
    if 'Products' in tables:
        check_columns(conn, 'Products')
    
    if 'Inventory' in tables:
        check_columns(conn, 'Inventory')
    
    # Try original stock query
    try:
        print("\nTrying original stock query...")
        stock_query = """
        SELECT 
            p.[Product Category] as CategoryName,
            SUM(i.StockQuantity) AS TotalStock,
            COUNT(DISTINCT p.[Product ID]) as ProductCount,
            ROUND(AVG(i.StockQuantity), 1) as AvgStock
        FROM Inventory i
        JOIN Products p ON i.ProductID = p.[Product ID]
        GROUP BY p.[Product Category]
        ORDER BY TotalStock DESC
        """
        
        cursor = conn.cursor()
        cursor.execute(stock_query)
        stock_data = rows_to_dict_list(cursor.fetchall())
        
        print(f"Query returned {len(stock_data)} results")
        if stock_data:
            # Extract data for chart
            category_names = [row['CategoryName'] for row in stock_data]
            stock_quantities = [row['TotalStock'] for row in stock_data]
            
            print("\nStock Categories:")
            for i, (cat, qty) in enumerate(zip(category_names, stock_quantities)):
                print(f"{i+1}. {cat}: {qty} units")
                
            # Save to diagnostic file
            with open('stock_level_diagnostic.json', 'w') as f:
                json.dump({
                    'stock_data': stock_data,
                    'category_names': category_names,
                    'stock_quantities': stock_quantities
                }, f, indent=2)
                
            print("\nDiagnostic data saved to stock_level_diagnostic.json")
        else:
            print("No stock data returned from query!")
            
        # Try a simpler query to double-check
        print("\nTrying simplified query to verify joins...")
        cursor.execute("""
        SELECT COUNT(*) FROM Inventory i
        JOIN Products p ON i.ProductID = p.[Product ID]
        """)
        join_count = cursor.fetchone()[0]
        print(f"Join count: {join_count} records match between Inventory and Products")
            
    except Exception as e:
        print(f"Error executing stock query: {e}")
        
        # Try alternative query without brackets
        print("\nTrying alternative query without brackets...")
        try:
            alt_query = """
            SELECT 
                p."Product Category" as CategoryName,
                SUM(i.StockQuantity) AS TotalStock,
                COUNT(DISTINCT p."Product ID") as ProductCount,
                ROUND(AVG(i.StockQuantity), 1) as AvgStock
            FROM Inventory i
            JOIN Products p ON i.ProductID = p."Product ID"
            GROUP BY p."Product Category"
            ORDER BY TotalStock DESC
            """
            
            cursor.execute(alt_query)
            alt_stock_data = rows_to_dict_list(cursor.fetchall())
            
            print(f"Alternative query returned {len(alt_stock_data)} results")
            if alt_stock_data:
                print("\nAlternative Stock Categories:")
                for i, row in enumerate(alt_stock_data):
                    print(f"{i+1}. {row['CategoryName']}: {row['TotalStock']} units")
        except Exception as e:
            print(f"Error executing alternative query: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_stock_data()
    print("\nAll diagnostics complete.")
