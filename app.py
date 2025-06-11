from flask import Flask, render_template, jsonify, request
import sqlite3
import os
import json
from datetime import datetime, timedelta
import decimal

app = Flask(__name__)

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('stock-project.db')
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
    return [dict(row) for row in rows] if rows else []

# Home page route
@app.route('/')
def index():
    return render_template('index.html')

# --- Strategic Dashboard ---
@app.route('/dashboard/strategic')
def dashboard_strategic():
    conn = get_db_connection()
    
    # Get available categories for the filter
    categories = conn.execute(
        "SELECT DISTINCT [Product Category] FROM Products ORDER BY [Product Category]"
    ).fetchall()
    
    # Default query for average price trend per category
    query = """
    SELECT 
        p.[Product Category] as CategoryName,
        ph.EffectiveDate,
        ROUND(AVG(ph.Price), 2) AS AvgPrice
    FROM Pricing_History ph
    JOIN Products p ON ph.ProductID = p.[Product ID]
    GROUP BY p.[Product Category], ph.EffectiveDate
    ORDER BY p.[Product Category], ph.EffectiveDate
    """
    
    price_data = rows_to_dict_list(conn.execute(query).fetchall())
    
    # Price volatility by category
    volatility_query = """
    SELECT 
        p.[Product Category] as CategoryName,
        MAX(ph.Price) - MIN(ph.Price) AS PriceRange,
        ROUND(AVG(ph.Price), 2) AS AvgPrice
    FROM Pricing_History ph
    JOIN Products p ON ph.ProductID = p.[Product ID]
    GROUP BY p.[Product Category]
    ORDER BY PriceRange DESC
    """
    
    volatility_data = rows_to_dict_list(conn.execute(volatility_query).fetchall())
    
    # Category summary table
    summary_query = """
    SELECT 
        p.[Product Category] as CategoryName,
        COUNT(DISTINCT p.[Product ID]) AS ProductCount,
        ROUND(MIN(ph.Price), 2) AS MinPrice,
        ROUND(MAX(ph.Price), 2) AS MaxPrice,
        ROUND(AVG(ph.Price), 2) AS AvgPrice
    FROM Products p
    JOIN Pricing_History ph ON p.[Product ID] = ph.ProductID
    GROUP BY p.[Product Category]
    ORDER BY p.[Product Category]
    """
    
    summary_data = rows_to_dict_list(conn.execute(summary_query).fetchall())
    
    conn.close()

    # Prepare data for Chart.js
    chart_data = {}
    for row in price_data:
        category = row['CategoryName']
        date = row['EffectiveDate']
        avg_price = row['AvgPrice']
        if category not in chart_data:
            chart_data[category] = []
        chart_data[category].append({'x': date, 'y': avg_price})

    return render_template('dashboard_strategic.html', 
                           chart_data=chart_data,
                           volatility_data=volatility_data,
                           summary_data=summary_data,
                           categories=categories)

# AJAX endpoint for price trend data with filtering
@app.route('/api/price_trend')
def api_price_trend():
    category = request.args.get('category', '')
    
    conn = get_db_connection()
    
    # Add WHERE clause if category filter is applied
    where_clause = ""
    params = []
    if category and category != 'All':
        where_clause = "WHERE p.[Product Category] = ?"
        params.append(category)
    
    query = f"""
    SELECT 
        p.[Product Category] as CategoryName,
        ph.EffectiveDate,
        ROUND(AVG(ph.Price), 2) AS AvgPrice
    FROM Pricing_History ph
    JOIN Products p ON ph.ProductID = p.[Product ID]
    {where_clause}
    GROUP BY p.[Product Category], ph.EffectiveDate
    ORDER BY p.[Product Category], ph.EffectiveDate
    """
    
    price_data = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify(rows_to_dict_list(price_data))

# AJAX endpoint for volatility data with filtering
@app.route('/api/price_volatility')
def api_price_volatility():
    conn = get_db_connection()
    
    volatility_data = conn.execute(volatility_query).fetchall()
    conn.close()
    
    return jsonify(rows_to_dict_list(volatility_data))

# AJAX endpoint for category summary data
@app.route('/api/category_summary')
def api_category_summary():
    conn = get_db_connection()
    
    summary_data = conn.execute(summary_query).fetchall()
    conn.close()
    
    return jsonify(rows_to_dict_list(summary_data))

# --- Tactical Dashboard ---
@app.route('/dashboard/tactical')
def dashboard_tactical():
    conn = get_db_connection()
    
    # Default expiration window (30 days)
    expiration_window = request.args.get('expiration_window', '30')
    
    # Products expiring soon
    expiring_query = """
    SELECT 
        p.[Product Name] as ProductName,
        p.[Product Category] as CategoryName,
        i.StockQuantity,
        i.ExpirationDate
    FROM Inventory i
    JOIN Products p ON i.ProductID = p.[Product ID]
    WHERE i.ExpirationDate <= date('now', '+' || ? || ' days')
    ORDER BY i.ExpirationDate ASC
    """
    
    expiring_products = rows_to_dict_list(conn.execute(expiring_query, [expiration_window]).fetchall())
    
    # Stock levels by category
    stock_query = """
    SELECT 
        p.[Product Category] as CategoryName,
        SUM(i.StockQuantity) AS TotalStock
    FROM Inventory i
    JOIN Products p ON i.ProductID = p.[Product ID]
    GROUP BY p.[Product Category]
    ORDER BY TotalStock DESC
    """
    
    stock_data = rows_to_dict_list(conn.execute(stock_query).fetchall())
    
    # Low stock products
    low_stock_query = """
    SELECT 
        p.[Product Name] as ProductName,
        p.[Product Category] as CategoryName,
        i.StockQuantity
    FROM Inventory i
    JOIN Products p ON i.ProductID = p.[Product ID]
    WHERE i.StockQuantity <= 10
    ORDER BY i.StockQuantity ASC
    """
    
    low_stock_products = rows_to_dict_list(conn.execute(low_stock_query).fetchall())
    
    # Get categories for filter
    categories = rows_to_dict_list(conn.execute(
        "SELECT DISTINCT [Product Category] AS CategoryName FROM Products ORDER BY [Product Category]"
    ).fetchall())
    
    conn.close()
    
    # Prepare data for charts
    category_names = [row['CategoryName'] for row in stock_data]
    stock_quantities = [row['TotalStock'] for row in stock_data]
    
    return render_template('dashboard_tactical.html', 
                          expiring_products=expiring_products,
                          low_stock_products=low_stock_products,
                          categories=categories,
                          category_names=json.dumps(category_names),
                          stock_quantities=json.dumps(stock_quantities),
                          expiration_window=expiration_window)

# AJAX endpoint for expiring products data
@app.route('/api/expiring_products')
def api_expiring_products():
    expiration_window = request.args.get('expiration_window', '30')
    category = request.args.get('category', '')
    
    conn = get_db_connection()
    
    # Base query with expiration window parameter
    params = [expiration_window]
    where_clause = "WHERE i.ExpirationDate <= date('now', '+' || ? || ' days')"
    
    # Add category filter if provided
    if category and category != 'All':
        where_clause += " AND p.[Product Category] = ?"
        params.append(category)
    
    query = f"""
    SELECT 
        p.[Product Name] as ProductName,
        p.[Product Category] as CategoryName,
        i.StockQuantity,
        i.ExpirationDate
    FROM Inventory i
    JOIN Products p ON i.ProductID = p.[Product ID]
    {where_clause}
    ORDER BY i.ExpirationDate ASC
    """
    
    expiring_products = rows_to_dict_list(conn.execute(query, params).fetchall())
    conn.close()
    
    return jsonify(expiring_products)

# AJAX endpoint for stock levels data
@app.route('/api/stock_levels')
def api_stock_levels():
    conn = get_db_connection()
    
    stock_data = rows_to_dict_list(conn.execute(stock_query).fetchall())
    conn.close()
    
    return jsonify(stock_data)

# AJAX endpoint for low stock products
@app.route('/api/low_stock')
def api_low_stock():
    conn = get_db_connection()
    
    low_stock_data = rows_to_dict_list(conn.execute(low_stock_query).fetchall())
    conn.close()
    
    return jsonify(low_stock_data)

# --- Analytical Dashboard ---
@app.route('/dashboard/analytical')
def dashboard_analytical():
    conn = get_db_connection()
    
    # Top-rated products by tag
    tag_ratings_query = """
    SELECT 
        t.TagName,
        p.[Product Name] as ProductName,
        AVG(r.Rating) AS AvgRating,
        COUNT(r.Rating) AS RatingCount
    FROM Product_Tags pt
    JOIN Tags t ON pt.TagID = t.TagID
    JOIN Products p ON pt.ProductID = p.[Product ID]
    JOIN Product_Ratings r ON pt.ProductID = r.ProductID
    GROUP BY t.TagName, p.[Product Name]
    HAVING RatingCount >= 1
    ORDER BY AvgRating DESC
    LIMIT 20
    """
    
    tag_ratings = rows_to_dict_list(conn.execute(tag_ratings_query).fetchall())
    
    # Popular tags (for word cloud)
    popular_tags_query = """
    SELECT 
        t.TagName,
        COUNT(pt.ProductID) AS TagUsage
    FROM Product_Tags pt
    JOIN Tags t ON pt.TagID = t.TagID
    GROUP BY t.TagName
    ORDER BY TagUsage DESC
    LIMIT 30
    """
    
    popular_tags = rows_to_dict_list(conn.execute(popular_tags_query).fetchall())
    
    # Rating distribution by tag
    rating_distribution_query = """
    SELECT 
        t.TagName,
        r.Rating,
        COUNT(*) AS CountPerRating
    FROM Product_Tags pt
    JOIN Tags t ON pt.TagID = t.TagID
    JOIN Product_Ratings r ON pt.ProductID = r.ProductID
    GROUP BY t.TagName, r.Rating
    ORDER BY t.TagName, r.Rating
    """
    
    rating_distribution = rows_to_dict_list(conn.execute(rating_distribution_query).fetchall())
    
    # Get tags for filter
    tags = rows_to_dict_list(conn.execute(
        "SELECT DISTINCT TagName FROM Tags ORDER BY TagName"
    ).fetchall())
    
    conn.close()
    
    # Prepare data for charts
    tag_names = [row['TagName'] for row in popular_tags]
    tag_usage = [row['TagUsage'] for row in popular_tags]
    
    # Process rating distribution for visualization
    rating_data = {}
    for row in rating_distribution:
        tag = row['TagName']
        rating = row['Rating']
        count = row['CountPerRating']
        if tag not in rating_data:
            rating_data[tag] = {1:0, 2:0, 3:0, 4:0, 5:0}
        rating_data[tag][rating] = count
    
    return render_template('dashboard_analytical.html',
                          tag_ratings=tag_ratings,
                          popular_tags=popular_tags,
                          tag_names=json.dumps(tag_names),
                          tag_usage=json.dumps(tag_usage),
                          rating_data=json.dumps(rating_data),
                          tags=tags)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
