import sqlite3
import json
import os

def get_db_connection():
    """Connect to the SQLite database"""
    db_path = os.path.join(os.getcwd(), 'stock-project.db')
    print(f"Using database at: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def rows_to_dict_list(rows):
    """Convert sqlite3.Row objects to list of dictionaries"""
    return [dict(row) for row in rows]

def fix_expiring_chart():
    """Fix the expiring timeline chart with data from Q4 2025"""
    conn = get_db_connection()
    
    # Check how many products expire in December 2025
    check_q4_query = """
    SELECT COUNT(*) as count
    FROM Inventory
    WHERE ExpirationDate BETWEEN '2025-10-01' AND '2025-12-31'
    """
    q4_count = conn.execute(check_q4_query).fetchone()["count"]
    print(f"Products expiring in Q4 2025: {q4_count}")

    # Create quarterly expiration data for chart
    quarterly_query = """
    WITH quarters AS (
        SELECT 0 AS quarter_num, 'Q1 2025' AS quarter_label, '2025-01-01' AS start_date, '2025-03-31' AS end_date UNION
        SELECT 1, 'Q2 2025', '2025-04-01', '2025-06-30' UNION
        SELECT 2, 'Q3 2025', '2025-07-01', '2025-09-30' UNION
        SELECT 3, 'Q4 2025', '2025-10-01', '2025-12-31' UNION
        SELECT 4, 'Q1 2026', '2026-01-01', '2026-03-31' UNION
        SELECT 5, 'Q2 2026', '2026-04-01', '2026-06-30' UNION
        SELECT 6, 'Q3 2026', '2026-07-01', '2026-09-30' UNION
        SELECT 7, 'Q4 2026', '2026-10-01', '2026-12-31'
    )
    SELECT 
        q.quarter_num,
        q.quarter_label,
        COUNT(i.ProductID) as expiring_count
    FROM quarters q
    LEFT JOIN Inventory i ON 
        date(i.ExpirationDate) BETWEEN date(q.start_date) AND date(q.end_date)
    GROUP BY q.quarter_num
    ORDER BY q.quarter_num
    """
    
    timeline_data = rows_to_dict_list(conn.execute(quarterly_query).fetchall())
    
    # Get stock data by category
    stock_query = """
    SELECT 
        p.[Product Category] as CategoryName,
        SUM(i.StockQuantity) AS TotalStock
    FROM Inventory i
    JOIN Products p ON i.ProductID = p.[Product ID]
    GROUP BY p.[Product Category]
    ORDER BY TotalStock DESC
    LIMIT 10
    """
    
    stock_data = rows_to_dict_list(conn.execute(stock_query).fetchall())
    
    # Create patch file for tactical dashboard
    patch_data = {
        'timeline_data': timeline_data,
        'category_data': stock_data
    }
    
    # Save as JSON for use in debugging
    with open('tactical_data_patch.json', 'w') as f:
        json.dump(patch_data, f, indent=2)
    
    conn.close()
    print(f"Fixed expiring timeline data with {len(timeline_data)} quarterly data points")
    print(f"Fixed stock category data with {len(stock_data)} categories")
    
    print("\nExpiring Timeline Data:")
    for quarter in timeline_data:
        print(f"  {quarter['quarter_label']}: {quarter['expiring_count']} products")
        
    print("\nStock Category Data:")
    for category in stock_data:
        print(f"  {category['CategoryName']}: {category['TotalStock']} items")
        
    print("\nSaved data to tactical_data_patch.json for debugging")

if __name__ == "__main__":
    fix_expiring_chart()
