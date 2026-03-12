// Global variables to store chart instances
let topMedicinesChartInstance = null;
let monthlySalesChartInstance = null;

// Store fetched data for filtering
let allMonthlySalesData = [];

document.addEventListener("DOMContentLoaded", function () {
    // Initial Load - only if we are on the dashboard
    if (document.getElementById('total-sales')) {
        refreshDashboard();
    }

    // Event Listeners
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshDashboard);
    }

    const revenueFilter = document.getElementById('revenue-filter');
    if (revenueFilter) {
        revenueFilter.addEventListener('change', updateRevenueChart);
    }
});

// Main Refresh Function
function refreshDashboard() {
    const refreshBtn = document.getElementById('refresh-btn');
    const icon = refreshBtn.querySelector('i');

    // Add spinning animation
    icon.classList.add('fa-spin-fast');

    // Create an array of promises
    const promises = [
        fetchTotalSales(),
        fetchTotalMedicinesCount(),
        fetchSuppliers(),
        fetchLowStockCount(),
        fetchTopMedicines(),
        fetchMonthlySales(),
        fetchLowStock(),
        fetchExpiryMedicines()
    ];

    // Execute all updates
    Promise.all(promises)
        .then(() => {
            // setTimeout to let user see the spinner for at least 500ms for feedback
            setTimeout(() => {
                icon.classList.remove('fa-spin-fast');
                showToast("Dashboard updated successfully", "success");
            }, 500);
        })
        .catch(err => {
            console.error("Dashboard refresh failed:", err);
            icon.classList.remove('fa-spin-fast');
            showToast("Failed to update dashboard", "error");
        });
}

// Data Fetching Functions with Loaders

// 1. Total Sales
async function fetchTotalSales() {
    const el = document.getElementById("total-sales");
    // Simple loader
    el.innerHTML = '<i class="fas fa-spinner fa-spin" style="font-size: 1.5rem; color: var(--text-secondary);"></i>';

    try {
        const response = await fetch("/total_sales");
        if (!response.ok) throw new Error("Network response was not ok");
        const data = await response.json();
        const amount = data.total_sales !== null ? data.total_sales : 0;
        // Animate counter
        animateValue(el, 0, amount, 1000, true);
    } catch (error) {
        console.error('Error fetching sales:', error);
        el.innerText = "Error";
        el.style.color = "var(--danger-color)";
    }
}

// 2. Suppliers Count
async function fetchSuppliers() {
    const el = document.getElementById("total-suppliers");
    el.innerHTML = '<i class="fas fa-spinner fa-spin" style="font-size: 1.5rem; color: var(--text-secondary);"></i>';

    try {
        const response = await fetch("/suppliers");
        if (!response.ok) throw new Error("Network response was not ok");
        const data = await response.json();
        const count = data.total_suppliers || 0;
        animateValue(el, 0, count, 1000, false);
    } catch (error) {
        console.error('Error fetching suppliers:', error);
        el.innerText = "-";
    }
}

// 2b. Total Medicines Count
async function fetchTotalMedicinesCount() {
    const el = document.getElementById("total-medicines");
    if (!el) return;
    el.innerHTML = '<i class="fas fa-spinner fa-spin" style="font-size: 1.5rem; color: var(--text-secondary);"></i>';
    try {
        const response = await fetch("/total_medicines_count");
        if (!response.ok) throw new Error("Network response was not ok");
        const data = await response.json();
        const count = data.count || 0;
        animateValue(el, 0, count, 1000, false);
    } catch (error) {
        console.error('Error fetching total medicines count:', error);
        el.innerText = "-";
    }
}

// 2c. Low Stock Count
async function fetchLowStockCount() {
    const el = document.getElementById("low-stock-count");
    if (!el) return;
    el.innerHTML = '<i class="fas fa-spinner fa-spin" style="font-size: 1.5rem; color: var(--text-secondary);"></i>';
    try {
        const response = await fetch("/low_stock_count");
        if (!response.ok) throw new Error("Network response was not ok");
        const data = await response.json();
        const count = data.count || 0;
        animateValue(el, 0, count, 1000, false);
    } catch (error) {
        console.error('Error fetching low stock count:', error);
        el.innerText = "-";
    }
}

// 3. Top Medicines Chart
async function fetchTopMedicines() {
    const container = document.getElementById('topMedicinesChart').parentElement;
    showOverlayLoader(container, true);

    try {
        const response = await fetch("/top_medicines");
        if (!response.ok) throw new Error("Network response was not ok");
        const data = await response.json();

        const labels = data.map(item => item.medicine);
        const values = data.map(item => item.sold);

        // Styling
        const styles = getComputedStyle(document.body);
        const primaryColor = styles.getPropertyValue('--primary-color').trim();
        const textColor = styles.getPropertyValue('--text-secondary').trim();
        const borderColor = styles.getPropertyValue('--border-color').trim();

        const ctx = document.getElementById('topMedicinesChart').getContext('2d');

        // Destroy existing chart if it exists
        if (topMedicinesChartInstance) {
            topMedicinesChartInstance.destroy();
        }

        topMedicinesChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Sold Quantity',
                    data: values,
                    backgroundColor: primaryColor,
                    borderRadius: 4,
                    barThickness: 30, // Thicker bars
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: borderColor,
                            borderDash: [5, 5]
                        },
                        ticks: { color: textColor }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: textColor }
                    }
                }
            }
        });

    } catch (error) {
        console.error("Error fetching top medicines:", error);
    } finally {
        showOverlayLoader(container, false);
    }
}

// 4. Monthly Sales Chart
async function fetchMonthlySales() {
    const container = document.getElementById('monthlySalesChart').parentElement;
    showOverlayLoader(container, true);

    try {
        const response = await fetch("/monthly_sales");
        if (!response.ok) throw new Error("Network response was not ok");
        allMonthlySalesData = await response.json(); // Store for filtering
        updateRevenueChart(); // Render chart with current filter
    } catch (error) {
        console.error("Error fetching monthly sales:", error);
    } finally {
        showOverlayLoader(container, false);
    }
}

function updateRevenueChart() {
    const filterVal = document.getElementById('revenue-filter').value;
    let dataToRender = [...allMonthlySalesData];

    // Apply Filter client-side
    if (filterVal !== 'all') {
        const months = parseInt(filterVal);
        if (dataToRender.length > months) {
            dataToRender = dataToRender.slice(-months);
        }
    }

    // If no data
    if (dataToRender.length === 0) return;

    const labels = dataToRender.map(item => {
        const date = new Date(item.month);
        return date.toLocaleDateString('en-IN', { month: 'short', year: '2-digit' });
    });
    const values = dataToRender.map(item => item.sales);

    // Styling
    const styles = getComputedStyle(document.body);
    const secondaryColor = styles.getPropertyValue('--secondary-color').trim();
    const textColor = styles.getPropertyValue('--text-secondary').trim();
    const borderColor = styles.getPropertyValue('--border-color').trim();
    const cardBg = styles.getPropertyValue('--card-bg').trim();

    const ctx = document.getElementById('monthlySalesChart').getContext('2d');

    // Create Gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(14, 165, 233, 0.5)');
    gradient.addColorStop(1, 'rgba(14, 165, 233, 0.0)');

    if (monthlySalesChartInstance) {
        monthlySalesChartInstance.destroy();
    }

    monthlySalesChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Revenue',
                data: values,
                borderColor: secondaryColor,
                backgroundColor: gradient,
                borderWidth: 2,
                pointBackgroundColor: cardBg,
                pointBorderColor: secondaryColor,
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: cardBg,
                    titleColor: styles.getPropertyValue('--text-primary').trim(),
                    bodyColor: styles.getPropertyValue('--text-secondary').trim(),
                    borderColor: borderColor,
                    borderWidth: 1,
                    padding: 10,
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(context.parsed.y);
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: borderColor,
                        borderDash: [5, 5]
                    },
                    ticks: {
                        color: textColor,
                        callback: function (value) {
                            if (value >= 1000) return '₹' + (value / 1000).toFixed(1) + 'k';
                            return '₹' + value;
                        }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: textColor }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}


// 5. Low Stock Table
async function fetchLowStock() {
    const tbody = document.getElementById("low-stock-body");
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 20px;"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>';

    try {
        const response = await fetch("/low_stock");
        if (!response.ok) throw new Error("Network response was not ok");
        const data = await response.json();
        tbody.innerHTML = "";

        // Limit to 5
        data.slice(0, 5).forEach(item => {
            const row = `<tr>
                <td>
                    <div style="display:flex; align-items:center;">
                        <span style="width: 8px; height: 8px; background: #ef4444; border-radius:50%; margin-right: 8px;"></span>
                        <span style="font-weight: 500;">${item.medicine}</span>
                    </div>
                </td>
                <td class="stock-status low">${item.stock} Units</td>
                <td><span class="badge warning">Low Stock</span></td>
                <td>
                    <button class="icon-btn" title="Reorder" onclick="showToast('Reorder request sent for ${item.medicine}', 'success')">
                        <i class="fas fa-cart-arrow-down" style="color:var(--secondary-color); font-size: 0.9rem;"></i>
                    </button>
                </td>
            </tr>`;
            tbody.innerHTML += row;
        });

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-secondary); padding: 20px;">All stock levels are healthy.</td></tr>`;
        }
    } catch (error) {
        console.error("Error fetching low stock:", error);
        tbody.innerHTML = `<tr><td colspan="4" style="color:var(--danger-color); text-align:center; padding: 20px;">Failed to load data</td></tr>`;
    }
}

// 6. Expiry Medicines Table
async function fetchExpiryMedicines() {
    const tbody = document.getElementById("expiry-body");
    tbody.innerHTML = '<tr><td colspan="3" style="text-align:center; padding: 20px;"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>';

    try {
        const response = await fetch("/expiry_medicines");
        if (!response.ok) throw new Error("Network response was not ok");
        const data = await response.json();
        tbody.innerHTML = "";

        data.slice(0, 5).forEach(item => {
            const today = new Date();
            const expiryDate = new Date(item.expiry);
            const timeDiff = expiryDate - today;
            const daysLeft = Math.ceil(timeDiff / (1000 * 60 * 60 * 24));

            const badgeClass = daysLeft < 10 ? 'danger' : 'warning';
            const dateStr = expiryDate.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });

            const row = `<tr>
                <td style="font-weight: 500;">${item.medicine}</td>
                <td>${dateStr}</td>
                <td><span class="badge ${badgeClass}">${daysLeft} Days</span></td>
            </tr>`;
            tbody.innerHTML += row;
        });

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="3" style="text-align:center; color:var(--text-secondary); padding: 20px;">No expiring items soon.</td></tr>`;
        }
    } catch (error) {
        console.error("Error fetching expiry:", error);
        tbody.innerHTML = `<tr><td colspan="3" style="color:var(--danger-color); text-align:center; padding: 20px;">Failed to load data</td></tr>`;
    }
}

// --- Helpers ---

// Loader for charts
function showOverlayLoader(container, show) {
    if (show) {
        // checks if loader exists
        if (!container.querySelector('.loading-overlay')) {
            const loader = document.createElement('div');
            loader.className = 'loading-overlay';
            loader.innerHTML = '<div class="loading-spinner"></div>';

            // Ensure positioning context
            if (getComputedStyle(container).position === 'static') {
                container.style.position = 'relative';
            }
            container.appendChild(loader);
        }
    } else {
        const loader = container.querySelector('.loading-overlay');
        if (loader) loader.remove();
    }
}

// Number Animation
function animateValue(obj, start, end, duration, isCurrency) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);

        // Easing function for smooth animation
        // easeOutQuad
        const easeProgress = 1 - (1 - progress) * (1 - progress);

        const currentVal = Math.floor(easeProgress * (end - start) + start);

        if (isCurrency) {
            obj.innerHTML = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(currentVal);
        } else {
            obj.innerHTML = currentVal;
        }

        if (progress < 1) {
            window.requestAnimationFrame(step);
        } else {
            // Ensure final value is accurate
            if (isCurrency) {
                obj.innerHTML = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(end);
            } else {
                obj.innerHTML = end;
            }
            obj.style.color = "var(--secondary-color)"; // Final color
        }
    };
    window.requestAnimationFrame(step);
}

// Simple Toast Notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'toast';

    // Style directly in JS for reliability
    Object.assign(toast.style, {
        position: 'fixed',
        bottom: '20px',
        right: '24px',
        padding: '12px 24px',
        background: type === 'success' ? 'var(--success-color)' : (type === 'error' ? 'var(--danger-color)' : 'var(--primary-color)'),
        color: '#fff',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        zIndex: '9999',
        fontSize: '0.9rem',
        opacity: '0',
        transition: 'opacity 0.3s ease, transform 0.3s ease',
        transform: 'translateY(10px)',
        fontWeight: '500'
    });

    toast.innerText = message;
    document.body.appendChild(toast);

    // Trigger reflow/animation
    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    });

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}