from flask import Flask, render_template, jsonify, request
import sqlite3
import json
import sys

app = Flask(__name__)

@app.route('/')
def debug_dashboard():
    # Use the absolute path to ensure consistent connections
    db_path = r'C:\Users\samuel\Documents\final project\stock-project-main\stock-project.db'
    print(f"Testing connection to database: {db_path}", file=sys.stderr)

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        print("Connection successful", file=sys.stderr)
        
        # Query for getting category product ratings
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
        
        # Execute query and fetch results
        category_data = conn.execute(category_query).fetchall()
        
        if category_data and len(category_data) > 0:
            print(f"SUCCESS: Retrieved {len(category_data)} categories with ratings", file=sys.stderr)
            
            category_names = []
            category_ratings = []
            
            for item in category_data:
                category_name = item['Category']
                avg_rating = item['AvgRating']
                product_count = item['ProductCount']
                print(f"  {category_name}: {avg_rating} avg rating ({product_count} products)", file=sys.stderr)
                category_names.append(category_name)
                category_ratings.append(float(avg_rating))
            
            # Print the exact JSON strings we're passing to the template
            category_names_json = json.dumps(category_names)
            category_ratings_json = json.dumps(category_ratings)
            
            print(f"JSON category names: {category_names_json}", file=sys.stderr)
            print(f"JSON category ratings: {category_ratings_json}", file=sys.stderr)
            
            # Create a simple HTML page that displays debugging info and tries to render the chart
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Dashboard Debug</title>
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            </head>
            <body style="background-color: #2c3e50; color: white; font-family: Arial, sans-serif; padding: 20px;">
                <h1>Dashboard Debug</h1>
                
                <h2>Database Data:</h2>
                <pre>{category_names_json}</pre>
                <pre>{category_ratings_json}</pre>
                
                <h2>Chart Test:</h2>
                <div style="width: 80%; height: 400px; margin: 20px auto; background-color: #34495e; padding: 20px; border-radius: 10px;">
                    <canvas id="testChart" height="350"></canvas>
                </div>
                
                <script>
                    // Log variables to console for inspection
                    console.log('category_names:', {category_names_json});
                    console.log('category_ratings:', {category_ratings_json});
                    
                    // Try to render a chart with this data
                    const ctx = document.getElementById('testChart').getContext('2d');
                    new Chart(ctx, {{
                        type: 'bar',
                        data: {{
                            labels: {category_names_json},
                            datasets: [{{
                                label: 'Average Rating',
                                data: {category_ratings_json},
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
            return "No category data found in database"
        
    except Exception as e:
        return f"ERROR: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, port=5555)
