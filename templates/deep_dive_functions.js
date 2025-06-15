// Deep Dive Section functionality
function initDeepDiveSection() {
    console.log('Initializing Deep Dive section...');
    
    // Load category options from database
    loadCategoryOptions();
    
    // Set up event listener for filter button
    document.getElementById('applyFilters').addEventListener('click', applyFilters);
    
    // Initial loading of data
    fetchLowStockProducts();
    fetchExpiryProducts();
    fetchRestockRecommendations();
}

// Load category options from database
function loadCategoryOptions() {
    fetch('/api/stock_levels')
        .then(response => response.json())
        .then(data => {
            const categories = new Set();
            data.forEach(item => {
                if (item.Category) {
                    categories.add(item.Category);
                }
            });
            
            const categoryFilter = document.getElementById('categoryFilter');
            categoryFilter.innerHTML = '<option value="all">All Categories</option>';
            
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                categoryFilter.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading categories:', error);
        });
}

function applyFilters() {
    const category = document.getElementById('categoryFilter').value;
    const stockLevel = document.getElementById('stockLevelFilter').value;
    const expiryRange = document.getElementById('expiryRangeFilter').value;
    const tag = document.getElementById('tagFilter').value;

    console.log('Applying filters:', { category, stockLevel, expiryRange, tag });

    // Update the deep dive tables and charts with selected filters
    fetchLowStockProducts(category, stockLevel, tag);
    fetchExpiryProducts(category, expiryRange, tag);
    fetchRestockRecommendations(category, stockLevel, tag);
    
    // Update the main dashboard charts with the same filters
    updateMainCharts(category, stockLevel, expiryRange, tag);
}

// Update main dashboard charts with filters
function updateMainCharts(category='all', stockLevel='all', expiryRange='all', tag='all') {
    // Construct the query parameters
    const params = new URLSearchParams();
    if (category !== 'all') params.append('category', category);
    if (stockLevel !== 'all') params.append('stockLevel', stockLevel);
    if (expiryRange !== 'all') params.append('expiryRange', expiryRange);
    if (tag !== 'all') params.append('tag', tag);
    
    const queryString = params.toString();
    const queryParam = queryString ? '?' + queryString : '';
    
    // Refetch data for all charts with filters
    fetchStockMatrixData(queryParam);
    fetchExpiringProductsData(queryParam);
    fetchLowStockWarningsData(queryParam);
    fetchStockUtilizationData(queryParam);
}

// Fetch low stock products from API with filters
function fetchLowStockProducts(category = 'all', stockLevel = 'all', tag = 'all') {
    // Show loading indicator
    const lowStockTable = document.getElementById('lowStockTable');
    if (lowStockTable) {
        lowStockTable.innerHTML = '<tr><td colspan="5" class="text-center">Loading...</td></tr>';
    }
    
    // Build query parameters
    const params = new URLSearchParams();
    if (category !== 'all') params.append('category', category);
    if (stockLevel !== 'all') params.append('stock_level', stockLevel);
    if (tag !== 'all') params.append('tag', tag);
    
    const queryString = params.toString();
    const queryParam = queryString ? '?' + queryString : '';
    
    // Fetch data from our API
    fetch('/api/low_stock' + queryParam)
        .then(response => response.json())
        .then(data => {
            // Update the table with filtered data
            updateLowStockTable(data);
        })
        .catch(error => {
            console.error('Error fetching low stock products:', error);
            // Show error in table
            if (lowStockTable) {
                lowStockTable.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Error loading data</td></tr>';
            }
        });
}

// Update low stock table with data from API
function updateLowStockTable(data) {
    const table = document.getElementById('lowStockTable');
    table.innerHTML = '';
    
    if (!data || data.length === 0) {
        table.innerHTML = '<tr><td colspan="5" class="text-center">No low stock products found</td></tr>';
        return;
    }
    
    data.forEach(item => {
        const row = document.createElement('tr');
        row.className = 'glassmorphic';
        
        // Determine badge class based on stock level
        let badgeClass = 'bg-primary';
        let levelText = 'Normal';
        
        if (item.StockQuantity <= 5) {
            badgeClass = 'bg-danger';
            levelText = 'Critical';
        } else if (item.StockQuantity <= 15) {
            badgeClass = 'bg-warning';
            levelText = 'Low';
        }
        
        row.innerHTML = `
            <td>${item.ProductName}</td>
            <td>${item.Category}</td>
            <td>${item.StockQuantity}</td>
            <td><span class="badge ${badgeClass} glassmorphic-badge">${levelText}</span></td>
            <td><button class="btn btn-sm btn-primary glassmorphic-button">Restock</button></td>
        `;
        
        table.appendChild(row);
    });
}

// Fetch expiring products from API with filters
function fetchExpiryProducts(category = 'all', expiryRange = 'all', tag = 'all') {
    // Show loading indicator
    const expiryTimeline = document.getElementById('expiryTimeline');
    if (expiryTimeline) {
        expiryTimeline.innerHTML = '<div class="text-center">Loading...</div>';
    }
    
    // Build query parameters
    const params = new URLSearchParams();
    if (category !== 'all') params.append('category', category);
    if (expiryRange !== 'all') params.append('days', expiryRange);
    if (tag !== 'all') params.append('tag', tag);
    
    const queryString = params.toString();
    const queryParam = queryString ? '?' + queryString : '';
    
    // Fetch data from our API
    fetch('/api/expiring_products' + queryParam)
        .then(response => response.json())
        .then(data => {
            // Organize data into time groups
            const organizedData = {
                next7Days: data.filter(item => item.DaysUntilExpiry <= 7).map(item => ({
                    name: item.ProductName,
                    units: item.StockQuantity,
                    date: item.ExpiryDate,
                    critical: item.DaysUntilExpiry <= 3
                })),
                next14Days: data.filter(item => item.DaysUntilExpiry > 7 && item.DaysUntilExpiry <= 14).map(item => ({
                    name: item.ProductName,
                    units: item.StockQuantity,
                    date: item.ExpiryDate,
                    critical: false
                })),
                next30Days: data.filter(item => item.DaysUntilExpiry > 14 && item.DaysUntilExpiry <= 30).map(item => ({
                    name: item.ProductName,
                    units: item.StockQuantity,
                    date: item.ExpiryDate,
                    critical: false
                }))
            };
            
            // Update the timeline with filtered data
            updateExpiryTimeline(organizedData);
        })
        .catch(error => {
            console.error('Error fetching expiring products:', error);
            // Show error in timeline
            if (expiryTimeline) {
                expiryTimeline.innerHTML = '<div class="text-center text-danger">Error loading data</div>';
            }
        });
}

// Update expiry timeline with data from API
function updateExpiryTimeline(data) {
    const timeline = document.getElementById('expiryTimeline');
    timeline.innerHTML = '';
    
    // Create 7 days section
    const group7Days = document.createElement('div');
    group7Days.className = 'timeline-group';
    group7Days.innerHTML = `
        <div class="timeline-header">Next 7 Days</div>
        <div class="timeline-items" id="timeline7Days"></div>
    `;
    timeline.appendChild(group7Days);
    
    const items7Days = document.getElementById('timeline7Days');
    
    if (!data.next7Days || data.next7Days.length === 0) {
        items7Days.innerHTML = '<div class="timeline-item">No products expiring in this period</div>';
    } else {
        data.next7Days.forEach(item => {
            const timelineItem = document.createElement('div');
            timelineItem.className = `timeline-item ${item.critical ? 'critical' : 'normal'}`;
            timelineItem.innerHTML = `
                <div class="item-header">${item.name} (${item.units} units)</div>
                <div class="item-date">${item.date}</div>
                <button class="btn btn-xs btn-danger">Priority Ship</button>
            `;
            items7Days.appendChild(timelineItem);
        });
    }
    
    // Create 8-14 days section
    const group14Days = document.createElement('div');
    group14Days.className = 'timeline-group';
    group14Days.innerHTML = `
        <div class="timeline-header">8-14 Days</div>
        <div class="timeline-items" id="timeline14Days"></div>
    `;
    timeline.appendChild(group14Days);
    
    const items14Days = document.getElementById('timeline14Days');
    
    if (!data.next14Days || data.next14Days.length === 0) {
        items14Days.innerHTML = '<div class="timeline-item">No products expiring in this period</div>';
    } else {
        data.next14Days.forEach(item => {
            const timelineItem = document.createElement('div');
            timelineItem.className = 'timeline-item warning';
            timelineItem.innerHTML = `
                <div class="item-header">${item.name} (${item.units} units)</div>
                <div class="item-date">${item.date}</div>
                <button class="btn btn-xs btn-warning">Plan Shipment</button>
            `;
            items14Days.appendChild(timelineItem);
        });
    }
    
    // Create 15-30 days section
    const group30Days = document.createElement('div');
    group30Days.className = 'timeline-group';
    group30Days.innerHTML = `
        <div class="timeline-header">15-30 Days</div>
        <div class="timeline-items" id="timeline30Days"></div>
    `;
    timeline.appendChild(group30Days);
    
    const items30Days = document.getElementById('timeline30Days');
    
    if (!data.next30Days || data.next30Days.length === 0) {
        items30Days.innerHTML = '<div class="timeline-item">No products expiring in this period</div>';
    } else {
        data.next30Days.forEach(item => {
            const timelineItem = document.createElement('div');
            timelineItem.className = 'timeline-item normal';
            timelineItem.innerHTML = `
                <div class="item-header">${item.name} (${item.units} units)</div>
                <div class="item-date">${item.date}</div>
                <button class="btn btn-xs btn-secondary">Monitor</button>
            `;
            items30Days.appendChild(timelineItem);
        });
    }
}

// Fetch restock recommendations from API with filters
function fetchRestockRecommendations(category = 'all', stockLevel = 'all', tag = 'all') {
    // Show loading indicator
    const container = document.getElementById('restockRecommendations');
    if (container) {
        container.innerHTML = '<div class="text-center">Loading...</div>';
    }
    
    // Build query parameters
    const params = new URLSearchParams();
    if (category !== 'all') params.append('category', category);
    if (stockLevel !== 'all') params.append('stock_level', stockLevel);
    if (tag !== 'all') params.append('tag', tag);
    
    const queryString = params.toString();
    const queryParam = queryString ? '?' + queryString : '';
    
    // Fetch data from our API
    fetch('/api/restock_recommendations' + queryParam)
        .then(response => response.json())
        .then(data => {
            // Update the restock recommendations
            updateRestockRecommendations(data);
        })
        .catch(error => {
            console.error('Error fetching restock recommendations:', error);
            // Show error in container
            if (container) {
                container.innerHTML = '<div class="text-center text-danger">Error loading data</div>';
            }
        });
}

// Update restock recommendations with data from API
function updateRestockRecommendations(data) {
    const container = document.getElementById('restockRecommendations');
    container.innerHTML = '';
    
    if (!data || data.length === 0) {
        container.innerHTML = '<div class="text-center">No restock recommendations found</div>';
        return;
    }
    
    data.forEach(item => {
        const restockItem = document.createElement('div');
        restockItem.className = 'restock-item';
        
        // Calculate percentage
        let percentage = Math.round((item.CurrentStock / item.RecommendedStock) * 100);
        if (percentage > 100) percentage = 100;
        
        // Determine color class based on percentage
        let colorClass = 'bg-danger';
        if (percentage > 30) {
            colorClass = 'bg-warning';
        } 
        if (percentage > 60) {
            colorClass = 'bg-success';
        }
        
        restockItem.innerHTML = `
            <div class="restock-info">
                <div class="item-name">${item.ProductName}</div>
                <div class="item-category">${item.Category}</div>
            </div>
            <div class="restock-progress">
                <div class="progress-label">
                    <span>Current: ${item.CurrentStock}</span>
                    <span>Recommended: ${item.RecommendedStock}</span>
                </div>
                <div class="progress">
                    <div class="progress-bar ${colorClass}" role="progressbar" 
                         style="width: ${percentage}%" 
                         aria-valuenow="${item.CurrentStock}" 
                         aria-valuemin="0" 
                         aria-valuemax="${item.RecommendedStock}"></div>
                </div>
            </div>
            <button class="btn btn-sm btn-primary">Order Now</button>
        `;
        
        container.appendChild(restockItem);
    });
}

// Initialize the Deep Dive section when the page loads
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(initDeepDiveSection, 1000); // Slight delay to ensure all other scripts have run
});
