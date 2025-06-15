"""
Fix for the Top Rated Products by Category chart in the analytical dashboard.
This script runs a standalone version of the dashboard_analytical route 
that focuses specifically on the category chart data.
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
import json
import os
import sys

app = Flask(__name__)
app.template_folder = 'templates'

# Use absolute path to ensure consistent connection
DB_PATH = r'C:\Users\samuel\Documents\final project\stock-project-main\stock-project.db'

def get_db_connection():
    """Get a connection to the SQLite database using the absolute path."""
    print(f"Connecting to database at: {DB_PATH}")
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        raise

def rows_to_dict_list(rows):
    """Convert SQLite Row objects to a list of dictionaries."""
    return [dict(row) for row in rows] if rows else []

@app.route('/')
def index():
    """Simple index page that links to the fixed category chart demo."""
    return """
    <h1>Category Chart Fix Demo</h1>
    <p>Click below to see the fixed category chart:</p>
    <a href="/fixed-chart">View Fixed Chart</a>
    """

@app.route('/fixed-chart')
def fixed_chart():
    """Simplified version of the dashboard_analytical route focusing only on category data."""
    try:
        conn = get_db_connection()
        print("Successfully connected to database")
        
        # Query for category product ratings - the exact same query from the main app
        category_query = """
        SELECT 
            COALESCE(p.[Product Category], 'Uncategorized') AS Category,
            ROUND(AVG(CAST(r.Rating AS FLOAT)), 2) AS AvgRating,
            COUNT(DISTINCT r.ProductID) AS ProductCount
        FROM Products p
        LEFT JOIN Product_Ratings r ON p.[Product ID] = r.ProductID
        WHERE p.[Product Category] IS NOT NULL AND p.[Product Category] != ''
        GROUP BY p.[Product Category]
        HAVING COUNT(r.ProductID) > 0
        ORDER BY AVG(r.Rating) DESC
        LIMIT 10
        """
        
        category_data = rows_to_dict_list(conn.execute(category_query).fetchall())
        
        if category_data and len(category_data) > 0:
            print(f"SUCCESS: Retrieved {len(category_data)} categories with ratings")
            category_names = [item['Category'] for item in category_data]
            category_ratings = [float(item['AvgRating']) for item in category_data]
            
            print("Category data retrieved from database:")
            for i, (name, rating) in enumerate(zip(category_names, category_ratings)):
                print(f"  {i+1}. {name}: {rating} stars")
            
            # JSON-encode the data exactly as in the main app
            category_names_json = json.dumps(category_names)
            category_ratings_json = json.dumps(category_ratings)
            
            print(f"JSON-encoded category names: {category_names_json}")
            print(f"JSON-encoded category ratings: {category_ratings_json}")
            
            # Render a simple template with just the chart
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Fixed Category Chart</title>
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #2c3e50;
                        color: white;
                        padding: 20px;
                    }}
                    .chart-container {{
                        width: 80%;
                        height: 400px;
                        margin: 30px auto;
                        background-color: #34495e;
                        padding: 20px;
                        border-radius: 10px;
                    }}
                    h1, h2 {{
                        text-align: center;
                    }}
                    pre {{
                        background-color: #1e2a38;
                        padding: 15px;
                        border-radius: 5px;
                        overflow-x: auto;
                    }}
                    .data-section {{
                        margin: 20px auto;
                        width: 80%;
                    }}
                </style>
            </head>
            <body>
                <h1>Fixed Category Chart</h1>
                
                <div class="chart-container">
                    <canvas id="categoryChart"></canvas>
                </div>
                
                <div class="data-section">
                    <h2>Raw Data from Database</h2>
                    <pre>{category_names_json}</pre>
                    <pre>{category_ratings_json}</pre>
                </div>
                
                <script>
                    // Debug log to console
                    console.log('Category names from server:', {category_names_json});
                    console.log('Category ratings from server:', {category_ratings_json});
                    
                    // Parse the data - these are already JSON objects, no need for JSON.parse
                    const categoryNames = {category_names_json};
                    const categoryRatings = {category_ratings_json};
                    
                    // Create the chart
                    const ctx = document.getElementById('categoryChart').getContext('2d');
                    new Chart(ctx, {{
                        type: 'bar',
                        data: {{
                            labels: categoryNames,
                            datasets: [{{
                                label: 'Average Rating',
                                data: categoryRatings,
                                backgroundColor: 'rgba(0, 230, 118, 0.7)',
                                borderColor: 'rgba(0, 230, 118, 1)',
                                borderWidth: 1
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {{
                                y: {{
                                    beginAtZero: true,
                                    max: 5,
                                    title: {{
                                        display: true,
                                        text: 'Average Rating (1-5)',
                                        color: 'rgba(255, 255, 255, 0.9)'
                                    }},
                                    ticks: {{
                                        color: 'rgba(255, 255, 255, 0.7)'
                                    }}
                                }},
                                x: {{
                                    ticks: {{
                                        color: 'rgba(255, 255, 255, 0.7)'
                                    }}
                                }}
                            }}
                        }}
                    }});
                </script>
            </body>
            </html>
            """
        else:
            return "No category data found in database."
        
    except Exception as e:
        return f"Error retrieving category data: {str(e)}"

if __name__ == '__main__':
    # Run on a different port to avoid conflict with main app
    print(f"Starting fixed chart demo app on http://127.0.0.1:5555")
    app.run(debug=True, port=5555)
