import sqlite3
import json

# Use the absolute path to ensure consistent connections
db_path = r'C:\Users\samuel\Documents\final project\stock-project-main\stock-project.db'
print(f"Testing connection to database: {db_path}")

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    print("Connection successful")
    
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
        print(f"SUCCESS: Retrieved {len(category_data)} categories with ratings")
        print("Category data:")
        category_names = []
        category_ratings = []
        
        for item in category_data:
            category_name = item['Category']
            avg_rating = item['AvgRating']
            product_count = item['ProductCount']
            print(f"  {category_name}: {avg_rating} avg rating ({product_count} products)")
            category_names.append(category_name)
            category_ratings.append(float(avg_rating))
        
        print("\nJavaScript variables that should be in the template:")
        print(f"category_names = {json.dumps(category_names)}")
        print(f"category_ratings = {json.dumps(category_ratings)}")
        
        # Since we have the data in Python, let's look at why it's not showing in the chart
        print("\nChecking for any potential issues...")
        
        # Check 1: Are our names and ratings arrays aligned and of the same length?
        if len(category_names) == len(category_ratings):
            print(f"✓ Data arrays are aligned (both length {len(category_names)})")
        else:
            print(f"✗ Data arrays are mismatched lengths: names={len(category_names)}, ratings={len(category_ratings)}")
        
        # Check 2: Are there any null/None values?
        if None in category_names or None in category_ratings:
            print("✗ Found NULL values in the data")
        else:
            print("✓ No NULL values in the data")
    else:
        print("No category data found in database")
    
    # Let's also check if there might be any issue with the dashboard_analytical route
    print("\nImportant app.py checks to make:")
    print("1. Make sure category_names and category_ratings are properly JSON-encoded")
    print("2. Ensure they're being passed to the template correctly as category_names and category_ratings")
    print("3. Verify there's no accidental name mismatch between app.py and the template")
    
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
