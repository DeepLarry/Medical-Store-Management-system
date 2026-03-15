// Expose refresh function globally so dashboard.html can call it
window.refreshDashboard = function () {
    console.log("Refreshing Dashboard Data...");
    fetchDashboardStats();
    fetchSalesChart();
    fetchLowStock();
    fetchExpiryAlerts();
    fetchTopProducts();
    fetchSupplierInsights();
}

// Initial fetch - Use load event to ensure all resources including Chart.js are ready
window.addEventListener('load', function () {
    console.log("Dashboard Integration Loaded (Window Load)");
    window.refreshDashboard();
});

function fetchDashboardStats() {
    console.log("Fetching Stats...");
    const salesEl = document.getElementById('total-sales');
    if (!salesEl) {
        console.warn("Dashboard elements not found, skipping stats fetch.");
        return;
    }

    fetch('/api/dashboard/stats')
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (data.error) {
                console.error('Error fetching stats:', data.error);
                // Set error state in UI
                updateElement('total-sales', 'Err');
                updateElement('total-medicines', 'Err');
                updateElement('net-profit', 'Err');
                return;
            }

            // Update DOM elements
            updateElement('total-sales', formatCurrency(data.total_sales));
            updateElement('total-medicines', data.total_medicines);
            updateElement('net-profit', formatCurrency(data.net_profit));
            updateElement('low-stock-count', data.low_stock_count);
        })
        .catch(error => {
            console.error('Stats fetch failed:', error);
            updateElement('total-sales', '-');
        });
}

function fetchSalesChart() {
    fetch('/api/dashboard/analytics/monthly')
        .then(response => response.json())
        .then(data => {
            if (data.error) return;
            renderSalesChart(data);
        })
        .catch(error => console.error('Error fetching chart data:', error));
}

function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
        // Remove loading class if exists
        element.classList.remove('loading');
    }
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

// Chart.js integration (assuming Chart.js is loaded)
function renderSalesChart(data) {
    const ctx = document.getElementById('monthlySalesChart');
    if (!ctx) return;

    if (typeof Chart === 'undefined') {
        console.error("Chart.js library is not loaded.");
        ctx.parentNode.innerHTML = "<p style='color:red; text-align:center;'>Chart library missing</p>";
        return;
    }

    // Check if we received daily data (array) or monthly analytics (object with keys)
    // The new API returns { labels: [], revenue: [], profit: [] }
    let chartData = {};

    if (Array.isArray(data)) {
        // Fallback for old daily format if somehow still used
        const labels = data.map(item => item.date);
        const values = data.map(item => item.amount);
        chartData = {
            labels: labels,
            datasets: [{
                label: 'Daily Sales',
                data: values,
                borderColor: '#0ea5e9',
                backgroundColor: 'rgba(14, 165, 233, 0.1)',
                tension: 0.4,
                fill: true
            }]
        };
    } else {
        // New Monthly Format
        chartData = {
            labels: data.labels,
            datasets: [
                {
                    label: 'Revenue',
                    data: data.revenue,
                    borderColor: '#0ea5e9',
                    backgroundColor: 'rgba(14, 165, 233, 0.2)',
                    tension: 0.3,
                    fill: false // Removed fill for cleaner line chart
                },
                {
                    label: 'Profit',
                    data: data.profit,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                    tension: 0.3,
                    fill: false
                }
            ]
        };
    }

    // Destroy existing chart if any
    if (window.salesChartInstance) {
        window.salesChartInstance.destroy();
    }

    window.salesChartInstance = new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true, position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += formatCurrency(context.parsed.y);
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Chart.js - Top Selling Integration
function fetchTopProducts() {
    const ctx = document.getElementById('topMedicinesChart');
    if (!ctx) return;

    fetch('/api/dashboard/top-products')
        .then(response => response.json())
        .then(data => {
            if (data.error) return;

            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels, // Medicine Names
                    datasets: [{
                        label: 'Quantity Sold',
                        data: data.quantities,
                        backgroundColor: 'rgba(16, 185, 129, 0.6)',
                        borderColor: '#10b981',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    indexAxis: 'y', // Horizontal Bar Chart
                    scales: {
                        x: { beginAtZero: true }
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                afterLabel: function (context) {
                                    const revenue = data.revenues[context.dataIndex];
                                    return 'Revenue: ' + formatCurrency(revenue);
                                }
                            }
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Error fetching top products:', error));
}

function fetchSupplierInsights() {
    const tableBody = document.getElementById('supplier-stats-body');
    if (!tableBody) return;

    fetch('/api/dashboard/suppliers')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching suppliers:', data.error);
                return;
            }

            tableBody.innerHTML = '';

            if (data.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 1rem;">No supplier data yet.</td></tr>';
                return;
            }

            data.forEach(item => {
                const row = document.createElement('tr');
                // Pending amount warning if > 0
                const pendingClass = item.pending_amount > 0 ? 'text-danger' : 'text-success';

                row.innerHTML = `
                    <td>${item.supplier_name}</td>
                    <td>${item.total_orders}</td>
                    <td>${formatCurrency(item.total_purchase_value)}</td>
                    <td class="${pendingClass}">${formatCurrency(item.pending_amount)}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error fetching supplier stats:', error));
}

function fetchLowStock() {
    const tableBody = document.getElementById('low-stock-body');
    if (!tableBody) return;

    fetch('/api/dashboard/alerts?limit=5')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching alerts:', data.error);
                return;
            }

            tableBody.innerHTML = '';

            if (data.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 1rem;">All stock levels are healthy!</td></tr>';
                return;
            }

            data.forEach(item => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>
                        <div style="font-weight: 500;">${item.medicine_name}</div>
                        <small style="color: var(--text-secondary); font-size: 0.75rem;">Min: ${item.min_stock}</small>
                    </td>
                    <td>
                        <span class="badge ${item.current_stock === 0 ? 'danger' : 'warning'}">
                            ${item.current_stock}
                        </span>
                    </td>
                    <td>${item.supplier_name}</td>
                    <td>${item.expiry_date}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error fetching low stock:', error));
}

function fetchExpiryAlerts() {
    const tableBody = document.getElementById('expiry-medicines-body');
    if (!tableBody) return;

    fetch('/api/dashboard/expiry?limit=5')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error fetching expiry alerts:', data.error);
                return;
            }

            tableBody.innerHTML = '';

            if (data.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 1rem;">No medicines expiring soon!</td></tr>';
                return;
            }

            data.forEach(item => {
                const row = document.createElement('tr');

                // Determine badge class for status
                let badgeClass = 'primary';
                if (item.status === 'Expired') badgeClass = 'danger';
                else if (item.status.includes('15d')) badgeClass = 'warning';

                row.innerHTML = `
                    <td>
                        <div style="font-weight: 500;">${item.medicine_name}</div>
                    </td>
                    <td><small>${item.batch_number || 'N/A'}</small></td>
                    <td>${item.expiry_date}</td>
                    <td>${item.stock}</td>
                    <td>
                        <span class="badge ${badgeClass}" style="font-size: 0.75rem;">
                            ${item.status}
                        </span>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error fetching expiry alerts:', error));
}
