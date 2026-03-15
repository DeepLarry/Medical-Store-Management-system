/**
 * Dashboard & Admin Scripts
 * Handles charts, data fetching, and general interactions for the Admin Dashboard.
 */

// ==========================================
// 1. Global State & Initialization
// ==========================================

// Store chart instances to allow destroying/updating them
let topMedicinesChartInstance = null;
let monthlySalesChartInstance = null;

// Store fetched data for client-side filtering
let allMonthlySalesData = [];

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", function () {
    // Check if we are on the dashboard page by looking for a specific element
    if (document.getElementById('total-sales')) {
        refreshDashboard();
    }

    // Attach Event Listeners
    setupEventListeners();
});

function setupEventListeners() {
    // Refresh Button
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshDashboard);
    }

    // Revenue Filter Dropdown
    const revenueFilter = document.getElementById('revenue-filter');
    if (revenueFilter) {
        revenueFilter.addEventListener('change', updateRevenueChart);
    }
}

// ==========================================
// 2. Main Dashboard Logic
// ==========================================

/**
 * Triggers all data fetching functions to update the dashboard.
 * Shows a spinner on the refresh button during the process.
 */
function refreshDashboard() {
    const refreshBtn = document.getElementById('refresh-btn');
    const icon = refreshBtn ? refreshBtn.querySelector('i') : null;

    // Add spinning animation
    if (icon) icon.classList.add('fa-spin-fast');

    // Create an array of promises to fetch data in parallel
    const promises = [
        fetchTotalSales(),
        fetchTotalMedicinesCount(),
        fetchNetProfit(),
        fetchLowStockCount(),
        fetchTopMedicines(),
        fetchMonthlySales(),
        fetchLowStock(),
        fetchExpiryMedicines()
    ];

    // Execute all updates
    Promise.all(promises)
        .then(() => {
            // Keep spinner for at least 500ms for visual feedback
            setTimeout(() => {
                if (icon) icon.classList.remove('fa-spin-fast');
                showToast("Dashboard updated successfully", "success");
            }, 500);
        })
        .catch(err => {
            console.error("Dashboard refresh failed:", err);
            if (icon) icon.classList.remove('fa-spin-fast');
            showToast("Failed to update dashboard", "error");
        });
}

// ==========================================
// 3. Data Fetching Functions
// ==========================================

// --- API Helpers ---

async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (e) {
        throw e;
    }
}

// --- KPI Cards ---

async function fetchTotalSales() {
    const el = document.getElementById("total-sales");
    if (!el) return;
    setLoading(el);

    try {
        const data = await fetchData("/total_sales");
        const amount = Number(data.total_sales) || 0;
        animateValue(el, 0, amount, 1000, true);
    } catch (error) {
        setError(el, error);
    }
}

async function fetchNetProfit() {
    const el = document.getElementById("net-profit");
    if (!el) return;
    setLoading(el);

    try {
        const data = await fetchData("/total_profit");
        const profit = Number(data.total_profit) || 0;
        animateValue(el, 0, profit, 1000, true);
    } catch (error) {
        setError(el, error);
    }
}

async function fetchTotalMedicinesCount() {
    const el = document.getElementById("total-medicines");
    if (!el) return;
    setLoading(el);

    try {
        const data = await fetchData("/total_medicines_count");
        const count = Number(data.count) || 0;
        animateValue(el, 0, count, 1000, false);
    } catch (error) {
        setError(el, error);
    }
}

async function fetchLowStockCount() {
    const el = document.getElementById("low-stock-count");
    if (!el) return;
    setLoading(el);

    try {
        const data = await fetchData("/low_stock_count");
        const count = Number(data.count) || 0;
        animateValue(el, 0, count, 1000, false);
    } catch (error) {
        setError(el, error);
    }
}

// --- Charts ---

async function fetchTopMedicines() {
    const chartCanvas = document.getElementById('topMedicinesChart');
    if (!chartCanvas) return;

    const container = chartCanvas.parentElement;
    showOverlayLoader(container, true);

    try {
        const data = await fetchData("/top_medicines");
        renderTopMedicinesChart(chartCanvas, data);
    } catch (error) {
        console.error("Error fetching top medicines:", error);
        // Don't show confusing error text in chart area, just log it
    } finally {
        showOverlayLoader(container, false);
    }
}

async function fetchMonthlySales() {
    const chartCanvas = document.getElementById('monthlySalesChart');
    if (!chartCanvas) return;

    const container = chartCanvas.parentElement;
    showOverlayLoader(container, true);

    try {
        allMonthlySalesData = await fetchData("/monthly_sales");
        updateRevenueChart(); // Render chart with current filter
    } catch (error) {
        console.error("Error fetching monthly sales:", error);
    } finally {
        showOverlayLoader(container, false);
    }
}

// --- Tables ---

async function fetchLowStock() {
    const tbody = document.getElementById("low-stock-body");
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 20px;"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>';

    try {
        const data = await fetchData("/low_stock");
        tbody.innerHTML = "";

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-secondary); padding: 20px;">All stock levels are healthy.</td></tr>`;
            return;
        }

        // Limit to 5 items for dashboard view
        data.slice(0, 5).forEach(item => {
            const row = `
                <tr>
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

    } catch (error) {
        console.error("Error fetching low stock:", error);
        tbody.innerHTML = `<tr><td colspan="4" style="color:var(--danger-color); text-align:center; padding: 20px;">Failed to load data</td></tr>`;
    }
}

async function fetchExpiryMedicines() {
    const tbody = document.getElementById("expiry-body");
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="3" style="text-align:center; padding: 20px;"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>';

    try {
        const data = await fetchData("/expiry_medicines");
        tbody.innerHTML = "";

        if (data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="3" style="text-align:center; color:var(--text-secondary); padding: 20px;">No items expiring soon.</td></tr>`;
            return;
        }

        data.slice(0, 5).forEach(item => {
            const today = new Date();
            const expiryDate = new Date(item.expiry);
            const timeDiff = expiryDate - today;
            const daysLeft = Math.ceil(timeDiff / (1000 * 60 * 60 * 24));

            const badgeClass = daysLeft < 10 ? 'danger' : 'warning';
            const dateStr = expiryDate.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });

            const row = `
                <tr>
                    <td style="font-weight: 500;">${item.medicine}</td>
                    <td>${dateStr}</td>
                    <td><span class="badge ${badgeClass}">${daysLeft} Days</span></td>
                </tr>`;
            tbody.innerHTML += row;
        });

    } catch (error) {
        console.error("Error fetching expiry:", error);
        tbody.innerHTML = `<tr><td colspan="3" style="color:var(--danger-color); text-align:center; padding: 20px;">Failed to load data</td></tr>`;
    }
}

// ==========================================
// 4. Chart Renderers
// ==========================================

function renderTopMedicinesChart(ctx, data) {
    const labels = data.map(item => item.medicine);
    const values = data.map(item => item.sold);

    // Get styles from CSS variables
    const styles = getComputedStyle(document.body);
    const primaryColor = styles.getPropertyValue('--primary-color').trim() || '#6366f1';
    const textColor = styles.getPropertyValue('--text-secondary').trim() || '#94a3b8';
    const borderColor = styles.getPropertyValue('--border-color').trim() || '#e2e8f0';

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
                barThickness: 30,
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
                    grid: { color: borderColor, borderDash: [5, 5] },
                    ticks: { color: textColor }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: textColor }
                }
            }
        }
    });
}

function updateRevenueChart() {
    const filterEl = document.getElementById('revenue-filter');
    if (!filterEl) return;

    const filterVal = filterEl.value;
    let dataToRender = [...allMonthlySalesData];

    // Apply Filter client-side
    if (filterVal !== 'all') {
        const months = parseInt(filterVal);
        if (dataToRender.length > months) {
            dataToRender = dataToRender.slice(-months); // Get last N months
        }
    }

    // Handle empty data
    if (dataToRender.length === 0) return;

    const labels = dataToRender.map(item => {
        const date = new Date(item.month);
        return date.toLocaleDateString('en-IN', { month: 'short', year: '2-digit' });
    });
    const revenueValues = dataToRender.map(item => item.sales);
    const profitValues = dataToRender.map(item => item.profit || 0);

    // Chart Styling
    const styles = getComputedStyle(document.body);
    const secondaryColor = styles.getPropertyValue('--secondary-color').trim() || '#0ea5e9';
    const profitColor = '#10b981'; // Green
    const textColor = styles.getPropertyValue('--text-secondary').trim() || '#94a3b8';
    const tooltipTitleColor = styles.getPropertyValue('--text-primary').trim() || '#1e293b';
    const tooltipBodyColor = styles.getPropertyValue('--text-secondary').trim() || '#64748b';
    const borderColor = styles.getPropertyValue('--border-color').trim() || '#e2e8f0';
    const cardBg = styles.getPropertyValue('--card-bg').trim() || '#ffffff';

    const canvas = document.getElementById('monthlySalesChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    // Create Gradients
    const gradientRevenue = ctx.createLinearGradient(0, 0, 0, 300);
    gradientRevenue.addColorStop(0, 'rgba(14, 165, 233, 0.5)');
    gradientRevenue.addColorStop(1, 'rgba(14, 165, 233, 0.0)');

    const gradientProfit = ctx.createLinearGradient(0, 0, 0, 300);
    gradientProfit.addColorStop(0, 'rgba(16, 185, 129, 0.5)');
    gradientProfit.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

    if (monthlySalesChartInstance) {
        monthlySalesChartInstance.destroy();
    }

    monthlySalesChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Revenue',
                    data: revenueValues,
                    borderColor: secondaryColor,
                    backgroundColor: gradientRevenue,
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: cardBg,
                    pointBorderColor: secondaryColor
                },
                {
                    label: 'Net Profit',
                    data: profitValues,
                    borderColor: profitColor,
                    backgroundColor: gradientProfit,
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: cardBg,
                    pointBorderColor: profitColor
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    display: true,
                    labels: { color: textColor, usePointStyle: true }
                },
                tooltip: {
                    backgroundColor: cardBg,
                    titleColor: tooltipTitleColor,
                    bodyColor: tooltipBodyColor,
                    borderColor: borderColor,
                    borderWidth: 1,
                    padding: 10,
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || '';
                            if (label) label += ': ';
                            if (context.parsed.y !== null) {
                                label += new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(context.parsed.y);
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: textColor }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: borderColor, borderDash: [5, 5] },
                    ticks: {
                        color: textColor,
                        callback: function (value) {
                            if (value >= 1000) return '₹' + (value / 1000).toFixed(1) + 'k';
                            return '₹' + value;
                        }
                    }
                }
            }
        }
    });
}

// ==========================================
// 5. Utilities
// ==========================================

function setLoading(element) {
    if (element) {
        element.innerHTML = '<i class="fas fa-spinner fa-spin" style="font-size: 1.5rem; color: var(--text-secondary);"></i>';
    }
}

function setError(element, error) {
    console.error(error);
    if (element) {
        element.innerText = "Error";
        element.style.color = "var(--danger-color)";
    }
}

function showOverlayLoader(container, show) {
    if (!container) return;

    if (show) {
        if (!container.querySelector('.loading-overlay')) {
            const loader = document.createElement('div');
            loader.className = 'loading-overlay';
            loader.innerHTML = '<div class="loading-spinner"></div>';

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

function animateValue(obj, start, end, duration, isCurrency) {
    if (!obj) return;

    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const easeProgress = 1 - (1 - progress) * (1 - progress); // Ease out cubic

        let currentVal = easeProgress * (end - start) + start;

        if (isCurrency) {
            // Check if end has decimals
            if (end % 1 !== 0) {
                // Keep decimals during animation
            } else {
                currentVal = Math.floor(currentVal);
            }
            obj.innerHTML = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(currentVal);
        } else {
            obj.innerHTML = Math.floor(currentVal);
        }

        if (progress < 1) {
            window.requestAnimationFrame(step);
        } else {
            // Final value
            if (isCurrency) {
                obj.innerHTML = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(end);
            } else {
                obj.innerHTML = end;
            }
            // Removed color override to preserve CSS styling
        }
    };
    window.requestAnimationFrame(step);
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'toast';

    // Determine colors
    let bg;
    if (type === 'success') bg = 'var(--success-color)';
    else if (type === 'error') bg = 'var(--danger-color)';
    else bg = 'var(--primary-color)';

    Object.assign(toast.style, {
        position: 'fixed',
        bottom: '20px',
        right: '24px',
        padding: '12px 24px',
        background: bg,
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
