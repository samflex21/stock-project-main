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
    WITH category_price_stats AS (
        SELECT 
            p.[Product Category] as CategoryName,
            MAX(ph.Price) - MIN(ph.Price) AS PriceRange,
            ROUND(AVG(ph.Price), 2) AS AvgPrice,
            COUNT(DISTINCT ph.ProductID) AS ProductCount,
            MIN(ph.Price) AS MinPrice,
            MAX(ph.Price) AS MaxPrice
        FROM Pricing_History ph
        JOIN Products p ON ph.ProductID = p.[Product ID]
        GROUP BY p.[Product Category]
    )
    SELECT
        CategoryName,
        PriceRange,
        AvgPrice,
        ProductCount,
        MinPrice,
        MaxPrice,
        PriceRange / CASE WHEN AvgPrice = 0 THEN 1 ELSE AvgPrice END AS VolatilityScore
    FROM category_price_stats
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
    
    # Calculate total product count
    total_products_query = """
    SELECT COUNT(DISTINCT [Product ID]) AS TotalProducts FROM Products
    """
    
    total_products_result = conn.execute(total_products_query).fetchone()
    total_products = total_products_result['TotalProducts'] if total_products_result else 0
    
    # Get the most stable and most volatile categories
    # Stable category has the lowest price range relative to its average price
    stable_category_query = """
    WITH category_volatility AS (
        SELECT 
            p.[Product Category] as CategoryName,
            (MAX(ph.Price) - MIN(ph.Price)) / CASE WHEN AVG(ph.Price) = 0 THEN 1 ELSE AVG(ph.Price) END AS RelativeVolatility
        FROM Pricing_History ph
        JOIN Products p ON ph.ProductID = p.[Product ID]
        GROUP BY p.[Product Category]
        HAVING COUNT(DISTINCT ph.ProductID) > 0
    )
    SELECT CategoryName, RelativeVolatility
    FROM category_volatility
    ORDER BY RelativeVolatility ASC
    LIMIT 1
    """
    
    stable_category_result = conn.execute(stable_category_query).fetchone()
    most_stable_category = stable_category_result['CategoryName'] if stable_category_result else "N/A"
    
    # Volatile category has the highest price range relative to its average price
    volatile_category_query = """
    WITH category_volatility AS (
        SELECT 
            p.[Product Category] as CategoryName,
            (MAX(ph.Price) - MIN(ph.Price)) / CASE WHEN AVG(ph.Price) = 0 THEN 1 ELSE AVG(ph.Price) END AS RelativeVolatility
        FROM Pricing_History ph
        JOIN Products p ON ph.ProductID = p.[Product ID]
        GROUP BY p.[Product Category]
        HAVING COUNT(DISTINCT ph.ProductID) > 0
    )
    SELECT CategoryName, RelativeVolatility
    FROM category_volatility
    ORDER BY RelativeVolatility DESC
    LIMIT 1
    """
    
    volatile_category_result = conn.execute(volatile_category_query).fetchone()
    most_volatile_category = volatile_category_result['CategoryName'] if volatile_category_result else "N/A"
    
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
                           categories=categories,
                           total_products=total_products,
                           most_stable_category=most_stable_category,
                           most_volatile_category=most_volatile_category)

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

# API endpoint for price volatility by category data
@app.route('/api/price_volatility_data')
def api_price_volatility_data():
    category = request.args.get('category', 'all')
    months = int(request.args.get('months', '6'))
    cutoff_date = (datetime.now() - timedelta(days=months*30)).strftime("%Y-%m-%d")
    conn = get_db_connection()
    where_clause = ""
    params = [cutoff_date]
    if category and category != 'all':
        where_clause = "AND p.[Product Category] = ?"
        params.append(category)
    
    # Simplified approach to calculate price statistics without using STDEV
    # Using SQLite-compatible calculations that avoid nested aggregates
    query = f"""
    WITH price_averages AS (
        -- First calculate the average price per product
        SELECT 
            p.[Product Category] AS category_name,
            ph.ProductID,
            AVG(ph.Price) AS avg_price,
            MAX(ph.Price) AS max_price,
            MIN(ph.Price) AS min_price,
            COUNT(ph.Price) AS price_count
        FROM 
            Pricing_History ph
        JOIN 
            Products p ON ph.ProductID = p.[Product ID]
        WHERE 
            ph.EffectiveDate >= ? {where_clause}
        GROUP BY 
            p.[Product Category], ph.ProductID
        HAVING 
            COUNT(ph.Price) >= 2
    ),
    price_stats AS (
        -- Use price range as a proxy for volatility instead of standard deviation
        SELECT 
            category_name,
            ProductID,
            ROUND(avg_price, 2) AS avg_price,
            ROUND(max_price, 2) AS max_price,
            ROUND(min_price, 2) AS min_price,
            price_count,
            ROUND(max_price - min_price, 2) AS price_range,
            -- Coefficient of variation approximated by price range percentage
            ROUND((max_price - min_price) / NULLIF(avg_price, 0) * 100, 2) AS price_volatility
        FROM 
            price_averages
        WHERE 
            avg_price > 0
    ),
    category_volatility AS (
        SELECT
            category_name,
            ROUND(AVG(price_range), 2) AS avg_price_range,
            ROUND(AVG((max_price - min_price) / NULLIF(avg_price, 0) * 100), 2) AS avg_range_pct,
            ROUND(AVG(price_volatility), 2) AS coefficient_of_variation,
            COUNT(DISTINCT ProductID) AS product_count
        FROM
            price_stats
        WHERE
            avg_price > 0
        GROUP BY
            category_name
        HAVING
            COUNT(DISTINCT ProductID) > 0
        ORDER BY
            coefficient_of_variation DESC
    )
    SELECT
        category_name,
        avg_price_range AS avg_std_dev, -- Keeps the same field name for compatibility
        avg_range_pct,
        coefficient_of_variation,
        product_count
    FROM
        category_volatility
    """
    
    try:
        volatility_data = conn.execute(query, params).fetchall()
        data = rows_to_dict_list(volatility_data)
        
        # Format the data for the chart
        categories = [item['category_name'] for item in data]
        volatility_values = [item['coefficient_of_variation'] for item in data]
        range_values = [item['avg_range_pct'] for item in data]
        std_dev_values = [item['avg_std_dev'] for item in data]
        
        result = {
            'categories': categories,
            'volatility': volatility_values,
            'range_pct': range_values,
            'std_dev': std_dev_values,
            'raw_data': data
        }
        
        conn.close()
        return jsonify(result)
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e), 'categories': [], 'volatility': [], 'range_pct': [], 'std_dev': []})

# AJAX endpoint for category summary data
@app.route('/api/category_summary')
def api_category_summary():
    conn = get_db_connection()
    
    summary_data = conn.execute(summary_query).fetchall()
    conn.close()
    
    return jsonify(rows_to_dict_list(summary_data))

# API endpoint for price trend heatmap data (Category vs Month)
@app.route('/api/price_heatmap_data')
def api_price_heatmap_data():
    category = request.args.get('category', 'all')
    months = int(request.args.get('months', '6'))
    
    # Calculate the cutoff date based on months parameter
    cutoff_date = (datetime.now() - timedelta(days=months*30)).strftime("%Y-%m-%d")
    
    conn = get_db_connection()
    
    # Set up query based on category filter
    where_clause = ""
    params = [cutoff_date]
    
    if category and category != 'all':
        where_clause = "AND p.[Product Category] = ?"
        params.append(category)
    
    # Get monthly average prices per category
    query = f"""
    WITH monthly_avg_prices AS (
        SELECT 
            p.[Product Category] AS category_name,
            strftime('%Y-%m', ph.EffectiveDate) AS month_year,
            ROUND(AVG(ph.Price), 2) AS avg_price
        FROM 
            Pricing_History ph
        JOIN 
            Products p ON ph.ProductID = p.[Product ID]
        WHERE 
            ph.EffectiveDate >= ? {where_clause}
        GROUP BY 
            p.[Product Category], strftime('%Y-%m', ph.EffectiveDate)
    ),
    month_changes AS (
        SELECT 
            curr.category_name,
            curr.month_year,
            curr.avg_price,
            prev.avg_price AS prev_avg_price,
            CASE 
                WHEN prev.avg_price > 0 
                THEN ROUND(((curr.avg_price - prev.avg_price) / prev.avg_price * 100), 2)
                ELSE 0
            END AS price_change_pct
        FROM 
            monthly_avg_prices curr
        LEFT JOIN 
            monthly_avg_prices prev
        ON 
            curr.category_name = prev.category_name AND
            prev.month_year = (
                SELECT MAX(m.month_year)
                FROM monthly_avg_prices m
                WHERE 
                    m.category_name = curr.category_name AND
                    m.month_year < curr.month_year
            )
    )
    SELECT 
        category_name,
        month_year,
        avg_price,
        prev_avg_price,
        price_change_pct
    FROM 
        month_changes
    ORDER BY 
        category_name, month_year
    """
    
    try:
        price_data = conn.execute(query, params).fetchall()
        price_data = rows_to_dict_list(price_data)
        
        # Collect all unique categories and months
        categories = []
        months_set = set()
        
        for row in price_data:
            if row['category_name'] not in categories:
                categories.append(row['category_name'])
            months_set.add(row['month_year'])
        
        # Sort months chronologically
        months_list = sorted(list(months_set))
        
        # Format month labels for better display
        month_labels = []
        for month_year in months_list:
            year, month = month_year.split('-')
            month_name = datetime(int(year), int(month), 1).strftime('%b %Y')
            month_labels.append(month_name)
        
        # Prepare the matrix data format for the heatmap
        matrix_data = []
        
        for cat_idx, category_name in enumerate(categories):
            for month_idx, month_year in enumerate(months_list):
                # Find the data point for this category and month
                data_point = next((item for item in price_data if 
                                  item['category_name'] == category_name and 
                                  item['month_year'] == month_year), None)
                
                if data_point:
                    matrix_data.append({
                        'x': month_idx,
                        'y': cat_idx,
                        'v': data_point['price_change_pct'],
                        'month': month_labels[month_idx],
                        'category': category_name,
                        'currentPrice': data_point['avg_price'],
                        'previousPrice': data_point['prev_avg_price'] if data_point['prev_avg_price'] else None
                    })
        
        result = {
            'data': matrix_data,
            'categories': categories,
            'months': month_labels
        }
        
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e), 'data': [], 'categories': [], 'months': []})

# API endpoint for price growth rate data
@app.route('/api/price_growth_data')
def api_price_growth_data():
    category = request.args.get('category', 'all')
    months = int(request.args.get('months', '6'))
    
    # Calculate the cutoff date based on months parameter
    cutoff_date = (datetime.now() - timedelta(days=months*30)).strftime("%Y-%m-%d")
    
    conn = get_db_connection()
    
    # Set up query based on category filter
    where_clause = ""
    params = [cutoff_date]
    
    if category and category != 'all':
        where_clause = "AND p.[Product Category] = ?"
        params.append(category)
    
    # Get monthly average prices per category
    query = f"""
    SELECT 
        p.[Product Category] AS category_name,
        strftime('%Y-%m', ph.EffectiveDate) AS month_year,
        ROUND(AVG(ph.Price), 2) AS avg_price
    FROM 
        Pricing_History ph
    JOIN 
        Products p ON ph.ProductID = p.[Product ID]
    WHERE 
        ph.EffectiveDate >= ? {where_clause}
    GROUP BY 
        p.[Product Category], strftime('%Y-%m', ph.EffectiveDate)
    ORDER BY 
        p.[Product Category], month_year
    """
    
    price_data = conn.execute(query, params).fetchall()
    price_data = rows_to_dict_list(price_data)
    
    # Process the data to calculate growth rates
    categories = {}
    time_periods = set()
    
    # First pass: organize data by category and collect time periods
    for row in price_data:
        category_name = row['category_name']
        month_year = row['month_year']
        avg_price = float(row['avg_price'])
        
        if category_name not in categories:
            categories[category_name] = {}
        
        categories[category_name][month_year] = avg_price
        time_periods.add(month_year)
    
    # Sort time periods chronologically
    time_periods = sorted(list(time_periods))
    
    # Prepare result structure
    result = {
        'time_periods': time_periods,
        'categories': []
    }
    
    # Calculate growth rates for each category
    for category_name, prices in categories.items():
        category_data = {
            'name': category_name,
            'growth_rates': []
        }
        
        # Get the base price (first period or 0 if not available)
        first_period = time_periods[0] if time_periods else None
        base_price = prices.get(first_period, 0)
        
        # Calculate growth rate for each time period
        for period in time_periods:
            current_price = prices.get(period, 0)
            
            if base_price > 0 and current_price > 0:
                # Calculate percentage growth from first period
                growth_rate = ((current_price - base_price) / base_price) * 100
                category_data['growth_rates'].append(round(growth_rate, 2))
            else:
                category_data['growth_rates'].append(0)
        
        result['categories'].append(category_data)
    
    conn.close()
    return jsonify(result)

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
