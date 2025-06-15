import sqlite3
import os
from datetime import datetime

def rows_to_dict_list(rows):
    return [dict(row) for row in rows] if rows else []

def main():
    # Database path - using the absolute path
    db_path = r'C:\Users\samuel\Documents\final project\stock-project-main\stock-project.db'
    
    print(f"Checking database at: {db_path}")
    print(f"Database exists: {os.path.exists(db_path)}")
    print(f"Database size: {os.path.getsize(db_path) / (1024*1024):.2f} MB")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Test basic database connection with simple query
    try:
        product_count = conn.execute("SELECT COUNT(*) as count FROM Products").fetchone()['count']
        print(f"Database connection successful - found {product_count} products")
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return
    
    # Check Inventory table 
    try:
        inventory_count = conn.execute("SELECT COUNT(*) as count FROM Inventory").fetchone()['count']
        print(f"Inventory table has {inventory_count} records")
    except Exception as e:
        print(f"Error accessing Inventory table: {str(e)}")
    
    # Expiring stock over time (next 8 weeks by week) - using the same query from the app
    print("\nChecking expiring timeline data...")
    expiring_timeline_query = """
    WITH weeks(week_num) AS (
      SELECT 0 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 
      UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7
    )
    SELECT 
        w.week_num,
        'Week ' || (w.week_num + 1) as week_label,
        COUNT(i.ProductID) as expiring_count
    FROM weeks w
    LEFT JOIN Inventory i ON 
        i.ExpirationDate BETWEEN date('now', '+' || (w.week_num * 7) || ' days') 
        AND date('now', '+' || ((w.week_num + 1) * 7 - 1) || ' days')
    GROUP BY w.week_num
    ORDER BY w.week_num
    """
    
    try:
        expiring_timeline = rows_to_dict_list(conn.execute(expiring_timeline_query).fetchall())
        print(f"Timeline data: Found {len(expiring_timeline)} data points")
        
        for week in expiring_timeline:
            print(f"  Week {week['week_num'] + 1}: {week['expiring_count']} products expiring")
            
        # Check for zero data
        total_expiring = sum(week['expiring_count'] for week in expiring_timeline)
        if total_expiring == 0:
            print("\nWARNING: No expiring products found in timeline!")
            print("Checking for any expiring products in the database...")
            
            # Check if there are any products with expiration dates
            expiring_check_query = """
            SELECT COUNT(*) as count FROM Inventory 
            WHERE ExpirationDate IS NOT NULL 
            AND ExpirationDate > date('now')
            """
            expiring_count = conn.execute(expiring_check_query).fetchone()['count']
            print(f"Found {expiring_count} products with future expiration dates")
            
            # Sample some expiration dates
            if expiring_count > 0:
                sample_query = """
                SELECT p.[Product Name], i.ExpirationDate
                FROM Inventory i
                JOIN Products p ON i.ProductID = p.[Product ID]
                WHERE i.ExpirationDate IS NOT NULL
                LIMIT 5
                """
                samples = rows_to_dict_list(conn.execute(sample_query).fetchall())
                print("\nSample expiration dates:")
                for sample in samples:
                    print(f"  {sample['Product Name']}: {sample['ExpirationDate']}")
    except Exception as e:
        print(f"Error running expiring timeline query: {str(e)}")
    
    conn.close()

if __name__ == "__main__":
    main()
