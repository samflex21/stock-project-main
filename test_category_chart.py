import sqlite3
import json

# Use the exact absolute path as specified
DB_PATH = r"C:\Users\samuel\Documents\final project\stock-project-main\stock-project.db"

def rows_to_dict_list(rows):
    """Convert SQL rows to a list of dictionaries"""
    return [dict(row) for row in rows] if rows else []

def main():
    print(f"Testing connection to database: {DB_PATH}")
    
    try:
        # Connect to the database with the absolute path
        conn = sqlite3.connect(DB_PATH)
        print("Connection successful")
        
        # Enable row factory to access columns by name
        conn.row_factory = sqlite3.Row
        
        # Test a simple query to check if we can access the database
        test_query = "SELECT COUNT(*) as count FROM Products"
        result = conn.execute(test_query).fetchone()
        print(f"Products count: {result['count']}")
        
        # Use the exact query from app.py
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
        
        print("Executing category query...")
        category_data = rows_to_dict_list(conn.execute(category_query).fetchall())
        
        if category_data and len(category_data) > 0:
            print(f"SUCCESS: Retrieved {len(category_data)} categories with ratings")
            print("Category data:")
            for item in category_data:
                print(f"  {item['Category']}: {item['AvgRating']} avg rating ({item['ProductCount']} products)")
                
            # Format as JavaScript arrays for debugging
            category_names = [item['Category'] for item in category_data]
            category_ratings = [float(item['AvgRating']) for item in category_data]
            
            print("\nJavaScript variables that should be in the template:")
            print(f"category_names = {json.dumps(category_names)}")
            print(f"category_ratings = {json.dumps(category_ratings)}")
        else:
            print("WARNING: No category data found from query")
            
            # Try simpler queries to diagnose
            print("\nDiagnostic queries:")
            
            # Check if Product Category has any values
            cat_check = "SELECT DISTINCT [Product Category] FROM Products LIMIT 10"
            categories = conn.execute(cat_check).fetchall()
            print(f"Product Categories in database: {[row[0] for row in categories]}")
            
            # Check if ratings exist
            rating_check = "SELECT COUNT(*) as count FROM Product_Ratings"
            rating_count = conn.execute(rating_check).fetchone()['count']
            print(f"Total ratings in database: {rating_count}")
            
            # Check if any join records exist
            join_check = """
            SELECT COUNT(*) as count FROM Products p
            JOIN Product_Ratings r ON p.[Product ID] = r.ProductID
            """
            join_count = conn.execute(join_check).fetchone()['count']
            print(f"Products with ratings (join count): {join_count}")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
