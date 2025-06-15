from flask import Blueprint, jsonify
import sqlite3
from app import get_db_connection

# Create a Blueprint for debug routes
debug_bp = Blueprint('debug', __name__)

def rows_to_dict_list(rows):
    """Convert rows to a list of dictionaries"""
    if not rows:
        return []
    return [dict(row) for row in rows]

@debug_bp.route('/debug/stock_data')
def debug_stock_data():
    """Debug endpoint specifically for stock level data"""
    conn = get_db_connection()
    
    # Stock levels by category - direct query to verify data
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
    
    # Extract data for chart
    category_names = [row['CategoryName'] for row in stock_data]
    stock_quantities = [row['TotalStock'] for row in stock_data]
    
    conn.close()
    
    # Return debug data as JSON
    return jsonify({
        'success': True,
        'stock_data': stock_data,
        'category_names': category_names,
        'stock_quantities': stock_quantities,
    })
