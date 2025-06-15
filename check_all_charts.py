import sqlite3
import os
import json
from datetime import datetime

def rows_to_dict_list(rows):
    return [dict(row) for row in rows] if rows else []

def check_database():
    # Database path - using the absolute path
    db_path = r'C:\Users\samuel\Documents\final project\stock-project-main\stock-project.db'
    
    print(f"Checking database at: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {db_path}")
        return
    
    print(f"Database size: {os.path.getsize(db_path) / (1024*1024):.2f} MB")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Test all dashboard queries
    
    # 1. Check Stock Level by Category
    print("\n--- Stock Level by Category ---")
    stock_query = """
    SELECT 
        Category,
        SUM(CurrentStockLevel) as TotalStock
    FROM Products
    WHERE Category IS NOT NULL AND Category != ''
    GROUP BY Category
    ORDER BY TotalStock DESC
    """
    
    try:
        stock_results = rows_to_dict_list(conn.execute(stock_query).fetchall())
        print(f"Found {len(stock_results)} categories with stock data")
        for row in stock_results[:5]:  # Show top 5
            print(f"  {row['Category']}: {row['TotalStock']} items")
    except Exception as e:
        print(f"Error with stock query: {str(e)}")
    
    # 2. Check Expiring Timeline
    print("\n--- Expiring Timeline (Monthly) ---")
    monthly_query = """
    WITH months(month_num) AS (
      SELECT 0 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 
      UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7
      UNION SELECT 8 UNION SELECT 9 UNION SELECT 10 UNION SELECT 11
    )
    SELECT 
        m.month_num,
        strftime('%m/%Y', date('now', '+' || (m.month_num) || ' months')) as month_label,
        COUNT(i.ProductID) as expiring_count
    FROM months m
    LEFT JOIN Inventory i ON 
        i.ExpirationDate BETWEEN date('now', '+' || (m.month_num) || ' months') 
        AND date('now', '+' || (m.month_num + 1) || ' months', '-1 day')
    GROUP BY m.month_num
    ORDER BY m.month_num
    """
    
    try:
        monthly_results = rows_to_dict_list(conn.execute(monthly_query).fetchall())
        print(f"Found {len(monthly_results)} months of expiry data")
        total_monthly = sum(item['expiring_count'] for item in monthly_results)
        print(f"Total products expiring in the next 12 months: {total_monthly}")
        for row in monthly_results:
            print(f"  {row['month_label']}: {row['expiring_count']} products")
    except Exception as e:
        print(f"Error with monthly query: {str(e)}")
    
    # 3. Check Yearly Expiration
    print("\n--- Expiring Timeline (Yearly) ---")
    yearly_query = """
    WITH years(year_num) AS (
      SELECT 0 UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 
      UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7
    )
    SELECT 
        y.year_num,
        strftime('%Y', date('now', '+' || (y.year_num) || ' years')) as year_label,
        COUNT(i.ProductID) as expiring_count
    FROM years y
    LEFT JOIN Inventory i ON 
        i.ExpirationDate BETWEEN date('now', '+' || (y.year_num) || ' years') 
        AND date('now', '+' || (y.year_num + 1) || ' years', '-1 day')
    GROUP BY y.year_num
    ORDER BY y.year_num
    """
    
    try:
        yearly_results = rows_to_dict_list(conn.execute(yearly_query).fetchall())
        print(f"Found {len(yearly_results)} years of expiry data")
        total_yearly = sum(item['expiring_count'] for item in yearly_results)
        print(f"Total products expiring in the next 8 years: {total_yearly}")
        for row in yearly_results:
            print(f"  {row['year_label']}: {row['expiring_count']} products")
    except Exception as e:
        print(f"Error with yearly query: {str(e)}")
    
    # 4. Check Price by Category
    print("\n--- Price by Category ---")
    price_query = """
    SELECT 
        p.Category, 
        AVG(ph.Price) as AveragePrice
    FROM Products p
    JOIN (
        SELECT 
            ProductID,
            Price,
            ROW_NUMBER() OVER (PARTITION BY ProductID ORDER BY PriceDate DESC) as rn
        FROM PriceHistory
    ) ph ON p.ProductID = ph.ProductID AND ph.rn = 1
    WHERE p.Category IS NOT NULL AND p.Category != ''
    GROUP BY p.Category
    ORDER BY AveragePrice DESC
    """
    
    try:
        price_results = rows_to_dict_list(conn.execute(price_query).fetchall())
        print(f"Found {len(price_results)} categories with price data")
        for row in price_results[:5]:  # Show top 5
            print(f"  {row['Category']}: ${row['AveragePrice']:.2f} average price")
    except Exception as e:
        print(f"Error with price query: {str(e)}")
    
    # 5. Check Tags vs Ratings
    print("\n--- Tags vs Ratings ---")
    tags_query = """
    SELECT 
        t.Tag as tag,
        AVG(p.Rating) as rating,
        COUNT(p.[Product ID]) as count
    FROM Products p
    JOIN Tags t ON p.[Product ID] = t.ProductID
    WHERE p.Rating IS NOT NULL
    GROUP BY t.Tag
    HAVING COUNT(p.[Product ID]) > 5
    ORDER BY rating DESC
    """
    
    try:
        tags_results = rows_to_dict_list(conn.execute(tags_query).fetchall())
        print(f"Found {len(tags_results)} tags with rating data")
        for row in tags_results[:5]:  # Show top 5
            print(f"  {row['tag']}: {row['rating']:.2f} avg rating ({row['count']} products)")
    except Exception as e:
        print(f"Error with tags query: {str(e)}")
    
    # Close connection
    conn.close()
    print("\nDatabase checks complete!")

if __name__ == "__main__":
    check_database()
