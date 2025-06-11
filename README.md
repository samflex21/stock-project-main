# Integrated Dashboard Solution — Final Project

**Student:** Samuel Olumide Adebimpe

---

## Project Description

This project implements an Integrated Dashboard Solution that provides comprehensive analytics and visualization for stock management:

- **Strategic Dashboard**: Analyzing pricing trends across product categories
- **Tactical Dashboard**: Optimizing shipment logistics based on stock levels and expiration dates
- **Analytical Dashboard**: Building recommendation systems using product tags and ratings

The application is built with Flask and Chart.js to provide interactive, web-based dashboards that support critical business decisions.

## Features

### 1️⃣ Strategic Dashboard — Pricing Trends

- Average price trend per category over time
- Price volatility by category
- Category price summary with min/max/avg prices
- Filtering by product category and date range

### 2️⃣ Tactical Dashboard — Shipment Optimization

- Products expiring soon with priority indicators
- Current stock levels across product categories
- Low stock products requiring immediate attention
- Filtering by expiration window and category

### 3️⃣ Analytical Dashboard — Recommendation System

- Top-rated products by tag
- Popular tags visualization (word cloud)
- Rating distribution analysis
- Filtering by tag and minimum rating

## How to Run the Project

### Prerequisites

- Python 3.x
- SQLite3
- Web browser (Chrome or Firefox recommended)

### Setup

1. Clone the repository or navigate to the project folder:

```bash
cd "C:\Users\samuel\Documents\final project\stock-project"
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Run the Flask application:

```bash
python app.py
```

4. Open your web browser and navigate to:

```
http://127.0.0.1:5000/
```

## Project Structure

```
/stock-project
│   app.py                     # Flask application
│   requirements.txt           # Python dependencies
│   stock-project.db           # SQLite database
│   README.md                  # Project documentation
│
├───templates
│   │   base.html              # Base template with shared layout
│   │   index.html             # Home page / navigation
│   │   dashboard_strategic.html
│   │   dashboard_tactical.html
│   │   dashboard_analytical.html
│   
└───static
    ├───css
    │       style.css          # Custom CSS styles
    │
    └───js
            # Chart.js is loaded via CDN, additional JS can be added here
```

## Database Schema

The application relies on the following key tables:

- **Products**: Core product information
- **Categories**: Product categorization
- **Inventory**: Stock levels and expiration dates
- **Pricing_History**: Historical pricing data
- **Tags**: Product tag definitions
- **Product_Tags**: Many-to-many relationship between products and tags
- **Product_Ratings**: User ratings for products

## Submission Checklist

- ✅ Case Study Report
- ✅ Data Collection Report + Dataset
- ✅ Physical ERD
- ✅ Dashboard Plan
- ✅ GitHub Repository with README
- ✅ Flask Application (3 Dashboards)
- ✅ Screenshots of Dashboards
