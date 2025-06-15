import sqlite3
import os
import json

DB_PATH = r'C:\Users\samuel\Documents\final project\stock-project-main\stock-project.db'

def check_database():
    print(f"Checking database at: {DB_PATH}")
    print(f"Database exists: {os.path.exists(DB_PATH)}")
    
    if not os.path.exists(DB_PATH):
        print("Database file not found!")
        return
        
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\nTables in database: {tables}")
        
        # Check Products table structure
        if 'Products' in tables:
            cursor.execute("PRAGMA table_info(Products)")
            columns = cursor.fetchall()
            print("\nProducts table structure:")
            for col in columns:
                print(f"  {col['name']} ({col['type']})")
            
            # Check if Products has Category column and sample data
            category_col = next((col['name'] for col in columns if col['name'].lower() == 'category'), None)
            if category_col:
                print(f"\nFound Category column: {category_col}")
                cursor.execute(f"SELECT DISTINCT {category_col} FROM Products LIMIT 10")
                categories = [row[0] for row in cursor.fetchall() if row[0]]
                print(f"Sample categories ({len(categories)}): {categories[:5]}")
                
                # Count products per category
                cursor.execute(f"SELECT {category_col}, COUNT(*) as count FROM Products WHERE {category_col} IS NOT NULL GROUP BY {category_col} LIMIT 10")
                cat_counts = cursor.fetchall()
                print("\nProducts per category:")
                for row in cat_counts:
                    print(f"  {row[0]}: {row[1]} products")
            else:
                print("No Category column found in Products table!")
        
        # Check Product_Ratings table
        if 'Product_Ratings' in tables:
            cursor.execute("PRAGMA table_info(Product_Ratings)")
            columns = cursor.fetchall()
            print("\nProduct_Ratings table structure:")
            for col in columns:
                print(f"  {col['name']} ({col['type']})")
            
            # Check sample ratings
            cursor.execute("SELECT COUNT(*) FROM Product_Ratings")
            count = cursor.fetchone()[0]
            print(f"Total ratings count: {count}")
            
            if count > 0:
                cursor.execute("SELECT ProductID, Rating FROM Product_Ratings LIMIT 5")
                ratings = cursor.fetchall()
                print("Sample ratings:")
                for row in ratings:
                    print(f"  Product {row[0]}: {row[1]} stars")
            
            # Check ProductID in both tables
            if 'Products' in tables:
                product_id_col = None
                for col in columns:
                    if col['name'].lower() in ('productid', 'product id'):
                        product_id_col = col['name']
                        break
                        
                if product_id_col:
                    print("\nChecking join between Products and Product_Ratings:")
                    
                    # Try to identify ProductID column in Products table
                    cursor.execute("PRAGMA table_info(Products)")
                    products_cols = cursor.fetchall()
                    products_id_col = None
                    for col in products_cols:
                        if col['name'].lower() in ('productid', 'product id', 'id'):
                            products_id_col = col['name']
                            break
                    
                    if products_id_col:
                        query = f"""
                        SELECT COUNT(*) FROM Products p
                        JOIN Product_Ratings r ON p.[{products_id_col}] = r.{product_id_col}
                        """
                        cursor.execute(query)
                        join_count = cursor.fetchone()[0]
                        print(f"Products with ratings (using {products_id_col}={product_id_col}): {join_count}")
                        
                        # Try the query we're using for the chart
                        print("\nTesting simplified category ratings query:")
                        try:
                            test_query = f"""
                            SELECT 
                                p.Category,
                                AVG(r.Rating) AS AvgRating,
                                COUNT(r.{product_id_col}) AS ProductCount
                            FROM Products p
                            JOIN Product_Ratings r ON p.[{products_id_col}] = r.{product_id_col}
                            WHERE p.Category IS NOT NULL AND p.Category != ''
                            GROUP BY p.Category
                            ORDER BY AVG(r.Rating) DESC
                            LIMIT 10
                            """
                            cursor.execute(test_query)
                            category_data = cursor.fetchall()
                            print(f"Found {len(category_data)} categories with ratings")
                            for row in category_data:
                                print(f"  {row[0]}: {row[1]} avg rating ({row[2]} products)")
                                
                        except Exception as e:
                            print(f"Error running category query: {str(e)}")
                    else:
                        print("Could not identify ProductID column in Products table")
        
        # Check JavaScript variables in dashboard_analytical.html
        try:
            test_query = """
            SELECT 
                'Electronics' as Category, 
                4.5 as AvgRating,
                10 as ProductCount
            UNION ALL SELECT 'Clothing', 4.2, 8
            UNION ALL SELECT 'Beauty', 3.9, 5
            """
            cursor.execute(test_query)
            test_data = cursor.fetchall()
            print("\nTest data for JavaScript:")
            test_category_names = [row[0] for row in test_data]
            test_category_ratings = [row[1] for row in test_data]
            print(f"category_names = {json.dumps(test_category_names)}")
            print(f"category_ratings = {json.dumps(test_category_ratings)}")
        except Exception as e:
            print(f"Error generating test data: {str(e)}")
                
    except Exception as e:
        print(f"Database error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_database()
