from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify, send_from_directory
import sqlite3
import os
import json
from datetime import datetime, timedelta
import decimal

app = Flask(__name__)

# Database helper function - Use absolute path to ensure consistent connections
def get_db_connection():
    # Always use the absolute path to the database
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stock-project.db')
    app.config['DATABASE'] = db_path
    print(f"Database path: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Helper function to convert SQLite Row objects to dictionaries
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# Helper function to convert SQLite Row objects to a list of dictionaries
def rows_to_dict_list(rows):
    return [dict(row) for row in rows]

# --- Tactical Dashboard ---
@app.route('/dashboard/tactical')
def dashboard_tactical():
    # Database connection
    conn = get_db_connection()
    
    # Query expiring products
    expiration_window = request.args.get('expiration_window', '30')
    category_filter = request.args.get('category', '')
    
    # Base query with expiration window parameter
    params = [expiration_window]
    where_clause = "WHERE i.ExpirationDate <= date('now', '+' || ? || ' days')"
    
    # Add category filter if provided
    if category_filter and category_filter != 'All':
        where_clause += " AND p.[Product Category] = ?"
        params.append(category_filter)
    
    # Query for expiring products
    expiring_query = f"""
    SELECT 
        p.[Product Name] as ProductName,
        p.[Product Category] as CategoryName,
        i.StockQuantity,
        i.ExpirationDate
    FROM Inventory i
    JOIN Products p ON i.ProductID = p.[Product ID]
    {where_clause}
    ORDER BY i.ExpirationDate
    LIMIT 100
    """
    
    expiring_products = rows_to_dict_list(conn.execute(expiring_query, params).fetchall())
    
    # Calculate expiration timeline (now grouped by quarter or year)
    expiration_timeline_query = """
    SELECT 
        CASE 
            WHEN julianday(i.ExpirationDate) - julianday('now') BETWEEN 0 AND 90 
            THEN 'Q1: 0-90 days' 
            WHEN julianday(i.ExpirationDate) - julianday('now') BETWEEN 91 AND 180 
            THEN 'Q2: 91-180 days'
            WHEN julianday(i.ExpirationDate) - julianday('now') BETWEEN 181 AND 270 
            THEN 'Q3: 181-270 days'
            WHEN julianday(i.ExpirationDate) - julianday('now') BETWEEN 271 AND 365 
            THEN 'Q4: 271-365 days'
            ELSE strftime('%Y', i.ExpirationDate)
        END as time_label,
        CASE 
            WHEN julianday(i.ExpirationDate) - julianday('now') BETWEEN 0 AND 365 
            THEN 'quarter_label' 
            ELSE 'year_label'
        END as label_type,
        COUNT(*) as expiring_count,
        SUM(i.StockQuantity) as total_stock
    FROM Inventory i
    WHERE i.ExpirationDate IS NOT NULL
    GROUP BY time_label
    ORDER BY 
        CASE 
            WHEN label_type = 'quarter_label' THEN 0
            ELSE 1
        END,
        time_label
    """
    
    expiration_timeline_results = conn.execute(expiration_timeline_query).fetchall()
    expiring_timeline = []
    
    for row in expiration_timeline_results:
        time_label = row['time_label']
        label_type = row['label_type']
        
        timeline_item = {
            'expiring_count': row['expiring_count']
        }
        
        if label_type == 'quarter_label':
            timeline_item['quarter_label'] = time_label
        else:
            timeline_item['year_label'] = time_label
            
        expiring_timeline.append(timeline_item)
    
    # Query for low stock products (less than 10 items)
    low_stock_query = """
    SELECT 
        p.[Product Name] as ProductName,
        p.[Product Category] as CategoryName,
        i.StockQuantity
    FROM Inventory i
    JOIN Products p ON i.ProductID = p.[Product ID]
    WHERE i.StockQuantity < 10
    ORDER BY i.StockQuantity
    LIMIT 100
    """
    
    # Context metrics for tactical dashboard
    # Get total products count
    total_products = conn.execute(
        "SELECT COUNT(*) as count FROM Products"
    ).fetchone()['count']
    
    # Get average stock level
    avg_stock_level = conn.execute(
        "SELECT ROUND(AVG(StockQuantity), 1) as avg FROM Inventory"
    ).fetchone()['avg']
    
    # Get average price
    avg_price = conn.execute(
        "SELECT ROUND(AVG(Price), 2) as avg FROM Products"
    ).fetchone()['avg']
    
    # Get top rated category
    top_rated_query = """
    SELECT 
        p.[Product Category] as CategoryName,
        ROUND(AVG(r.Rating), 1) as AvgRating,
        COUNT(*) as RatingCount
    FROM Product_Ratings r
    JOIN Products p ON r.ProductID = p.[Product ID]
    GROUP BY p.[Product Category]
    HAVING COUNT(*) > 5
    ORDER BY AvgRating DESC
    LIMIT 1
    """
    
    top_rated_result = conn.execute(top_rated_query).fetchone()
    if top_rated_result:
        top_rated_category = {
            'name': top_rated_result['CategoryName'],
            'rating': top_rated_result['AvgRating']
        }
    else:
        top_rated_category = {'name': 'Unknown', 'rating': 0}
    
    # Stock levels by category
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
    
    stock_data = rows_to_dict_list(conn.execute(stock_query).fetchall())
    
    # Price by category
    price_by_category_query = """
    SELECT 
        p.[Product Category] as CategoryName,
        ROUND(AVG(p.Price), 2) as AvgPrice
    FROM Products p
    GROUP BY p.[Product Category]
    ORDER BY AvgPrice DESC
    """
    
    price_by_category = rows_to_dict_list(conn.execute(price_by_category_query).fetchall())
    
    # Tags and ratings
    tags_ratings_query = """
    SELECT 
        t.TagName,
        ROUND(AVG(r.Rating), 1) as AvgRating,
        COUNT(DISTINCT pt.ProductID) as ProductCount
    FROM Product_Tags pt
    JOIN Tags t ON pt.TagID = t.TagID
    LEFT JOIN Product_Ratings r ON pt.ProductID = r.ProductID
    GROUP BY t.TagName
    HAVING COUNT(DISTINCT pt.ProductID) > 3
    ORDER BY AvgRating DESC
    LIMIT 15
    """
    
    tags_ratings = rows_to_dict_list(conn.execute(tags_ratings_query).fetchall())
    
    low_stock_products = rows_to_dict_list(conn.execute(low_stock_query).fetchall())
    
    # Get categories for filter
    # Updated to use correct column name from our schema inspection
    categories = rows_to_dict_list(conn.execute(
        "SELECT DISTINCT [Product Category] AS CategoryName FROM Products ORDER BY [Product Category]"
    ).fetchall())
    
    conn.close()
    
    # Prepare data for charts 
    category_names = [row['CategoryName'] for row in stock_data]
    stock_quantities = [row['TotalStock'] for row in stock_data]
    
    # Create a formatted version of the stock data for easier chart use
    stock_chart_data = json.dumps([{
        'category': row['CategoryName'],
        'stock': row['TotalStock']
    } for row in stock_data])
    
    # Debug info
    print(f"Found {len(stock_data)} categories with stock data")
    print(f"Category names: {category_names}")
    print(f"Stock quantities: {stock_quantities}")
    
    return render_template('dashboard_tactical.html',
                         # Original data
                         expiring_products=expiring_products,
                         low_stock_products=low_stock_products,
                         categories=categories,
                         category_names=category_names,
                         stock_quantities=stock_quantities,
                         expiration_window=expiration_window,
                         
                         # New metrics for context cards
                         total_products=total_products,
                         avg_stock_level=avg_stock_level,
                         avg_price=avg_price,
                         top_rated_category=top_rated_category,
                         
                         # Stock chart data in JSON format
                         stock_chart_data=stock_chart_data,
                         
                         # New chart data
                         expiring_timeline=json.dumps([{
                             'label': item.get('quarter_label') or item.get('year_label') or 'Expiring',
                             'count': item['expiring_count']
                         } for item in expiring_timeline]),
                         price_by_category=json.dumps([{
                             'category': item['CategoryName'],
                             'price': item['AvgPrice']
                         } for item in price_by_category]),
                         tags_ratings=json.dumps([{
                             'tag': item['TagName'],
                             'rating': item['AvgRating'],
                             'count': item['ProductCount']
                         } for item in tags_ratings])
                        )

if __name__ == '__main__':
    app.run(debug=True)
