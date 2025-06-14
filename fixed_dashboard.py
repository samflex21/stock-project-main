@app.route('/dashboard/analytical')
@app.route('/dashboard_analytical')
def dashboard_analytical():
    """Route handler for the analytical dashboard."""
    try:
        import json
        import random
        
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
        ORDER BY AvgRating DESC
        """
        
        tag_ratings_result = conn.execute(tag_ratings_query).fetchall()
        tag_ratings = []
        
        for row in tag_ratings_result:
            tag_ratings.append({
                'TagName': row['TagName'],
                'ProductName': row['ProductName'],
                'AvgRating': row['AvgRating'],
                'RatingCount': row['RatingCount']
            })
        
        # Query to get popular tags with usage counts
        popular_tags_query = """
        SELECT 
            t.TagName,
            COUNT(pt.ProductID) as TagUsage 
        FROM Product_Tags pt
        JOIN Tags t ON pt.TagID = t.TagID
        GROUP BY t.TagName
        ORDER BY TagUsage DESC
        LIMIT 15
        """
        
        popular_tags = conn.execute(popular_tags_query).fetchall()
        
        # Get tag names and usage counts for charts
        tag_names = [row['TagName'] for row in popular_tags]
        tag_usage = [row['TagUsage'] for row in popular_tags]
        
        # Calculate tag activity for line chart (previously radar chart)
        tag_activity = tag_usage[:10] if len(tag_usage) > 10 else tag_usage
        
        # Generate data for tag ratings (for bar chart)
        tag_ratings_data = []
        for tag in tag_names[:10]:  # Limit to top 10 tags
            avg_tag_rating = 0
            for item in tag_ratings:
                if item['TagName'] == tag:
                    avg_tag_rating = item.get('AvgRating', 0)
                    break
            tag_ratings_data.append(avg_tag_rating)
        
        # Get category data for Top Rated Products by Category chart
        category_query = """
        SELECT 
            p.Category,
            AVG(r.Rating) AS AvgRating,
            COUNT(r.ProductID) AS ProductCount
        FROM Products p
        JOIN Product_Ratings r ON p.[Product ID] = r.ProductID
        WHERE p.Category IS NOT NULL AND p.Category != ''
        GROUP BY p.Category
        HAVING COUNT(r.ProductID) > 0
        ORDER BY AvgRating DESC
        LIMIT 10
        """
        
        category_ratings_result = conn.execute(category_query).fetchall()
        
        # Prepare category data for the chart
        category_names = []
        category_ratings = []
        
        if category_ratings_result:
            for row in category_ratings_result:
                category_names.append(row['Category'])
                category_ratings.append(row['AvgRating'])
        else:
            # Sample data if no results
            category_names = ['Electronics', 'Clothing', 'Home', 'Sports', 'Books', 'Beauty', 'Toys', 'Automotive', 'Health', 'Garden']
            category_ratings = [4.7, 4.3, 4.1, 3.9, 4.5, 4.2, 3.8, 3.5, 4.0, 3.7]
        
        # Calculate Rating Distribution
        rating_dist_query = """
        SELECT 
            Rating,
            COUNT(Rating) as Count
        FROM Product_Ratings
        GROUP BY Rating
        ORDER BY Rating ASC
        """
        
        rating_dist_result = conn.execute(rating_dist_query).fetchall()
        
        rating_dist = []
        
        if rating_dist_result:
            for row in rating_dist_result:
                rating_dist.append({
                    'Rating': row['Rating'],
                    'Count': row['Count']
                })
        else:
            # Sample data if no results
            for i in range(1, 6):
                rating_dist.append({
                    'Rating': i,
                    'Count': random.randint(5, 30)
                })
        
        # Get product rating data for other visualizations
        rating_data_query = """
        SELECT 
            p.[Product Name],
            r.Rating
        FROM Product_Ratings r
        JOIN Products p ON r.ProductID = p.[Product ID]
        ORDER BY r.Rating DESC
        LIMIT 50
        """
        
        rating_data_result = conn.execute(rating_data_query).fetchall()
        
        rating_data = []
        for row in rating_data_result:
            rating_data.append({
                'Product': row['Product Name'],
                'Rating': row['Rating']
            })
        
        # Get total products for context cards
        total_products_query = "SELECT COUNT(*) as Count FROM Products"
        total_products_result = conn.execute(total_products_query).fetchone()
        total_products = total_products_result['Count'] if total_products_result else 0
        
        # Get total unique tags for context cards
        total_tags_query = "SELECT COUNT(*) as Count FROM Tags"
        total_tags_result = conn.execute(total_tags_query).fetchone()
        total_tags = total_tags_result['Count'] if total_tags_result else 0
        
        # Calculate average rating for context cards
        avg_rating_query = "SELECT AVG(Rating) as AvgRating FROM Product_Ratings"
        avg_rating_result = conn.execute(avg_rating_query).fetchone()
        avg_rating = round(avg_rating_result['AvgRating'], 1) if avg_rating_result and avg_rating_result['AvgRating'] else 0
        
        # Find lowest rated tag for context
        lowest_rated_tag_query = """
        SELECT 
            t.TagName,
            AVG(r.Rating) as AvgRating
        FROM Product_Tags pt
        JOIN Tags t ON pt.TagID = t.TagID
        JOIN Product_Ratings r ON pt.ProductID = r.ProductID
        GROUP BY t.TagName
        HAVING COUNT(r.Rating) > 2
        ORDER BY AvgRating ASC
        LIMIT 1
        """
        
        lowest_rated_tag_result = conn.execute(lowest_rated_tag_query).fetchone()
        lowest_rated_tag = lowest_rated_tag_result['TagName'] if lowest_rated_tag_result else "Unknown"
        
        # Find product with most tags for context
        most_tags_query = """
        SELECT 
            p.[Product Name],
            COUNT(pt.TagID) as TagCount
        FROM Products p
        JOIN Product_Tags pt ON p.[Product ID] = pt.ProductID
        GROUP BY p.[Product ID], p.[Product Name]
        ORDER BY TagCount DESC
        LIMIT 1
        """
        
        most_tags_result = conn.execute(most_tags_query).fetchone()
        most_tags_count = most_tags_result['TagCount'] if most_tags_result else 0
        
        # Calculate recommendation strength based on tags and ratings
        recommend_query = """
        SELECT 
            AVG(r.Rating) as AvgRating,
            COUNT(DISTINCT pt.TagID) as UniqueTags
        FROM Products p
        JOIN Product_Tags pt ON p.[Product ID] = pt.ProductID
        JOIN Product_Ratings r ON p.[Product ID] = r.ProductID
        """
        
        recommend_result = conn.execute(recommend_query).fetchone()
        
        if recommend_result and recommend_result['AvgRating'] and recommend_result['UniqueTags']:
            recommendation_strength = min(100, int((recommend_result['AvgRating'] / 5) * 
                                          (recommend_result['UniqueTags'] / 10) * 100))
        else:
            recommendation_strength = 65  # Default value
        
        # Get all tags for filtering
        tags_query = "SELECT TagName FROM Tags ORDER BY TagName"
        tags_result = conn.execute(tags_query).fetchall()
        tags = [row['TagName'] for row in tags_result]
        
        # Render template with all the data
        response = render_template('dashboard_analytical.html',
                           tag_ratings=tag_ratings,
                           popular_tags=popular_tags,
                           tag_names=json.dumps(tag_names[:10]),  # Limit to top 10 for chart readability
                           tag_ratings_data=json.dumps(tag_ratings_data),
                           tag_activity=json.dumps(tag_activity),
                           rating_distribution=json.dumps(rating_dist),
                           category_names=json.dumps(category_names),
                           category_ratings=json.dumps(category_ratings),
                           rating_data=json.dumps(rating_data),
                           tags=tags,
                           total_products=total_products,
                           total_tags=total_tags,
                           avg_rating=avg_rating,
                           lowest_rated_tag=lowest_rated_tag,
                           most_tags_count=most_tags_count,
                           recommendation_strength=recommendation_strength)
        
        # Close the database connection only at the very end after all operations
        conn.close()
        
        return response
        
    except Exception as e:
        # Log the error
        print(f"ERROR in dashboard_analytical: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return an error page or message
        return render_template('error.html', error=str(e)), 500
