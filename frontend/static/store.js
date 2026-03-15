/**
 * Pharmacy POS Frontend Logic
 * Modern, fast, and optimized for desktop use.
 */

// ==========================================
// 1. State Management
// ==========================================

const APP_STATE = {
    cart: [],
    // Load medicines from CONFIG or empty array
    medicines: (typeof CONFIG !== 'undefined' && CONFIG.medicines) ? CONFIG.medicines : [],
    currentCategory: 'All',
    searchQuery: '',
    heldBills: []
};

// ==========================================
// 2. DOM Elements
// ==========================================

const DOM = {
    searchInput: document.getElementById('searchInput'),
    suggestionsBox: document.getElementById('suggestions'),
    productGrid: document.getElementById('productGrid'),
    cartItemsBox: document.getElementById('cartItems'),
    itemCountBadge: document.getElementById('itemCount'),
    subTotalEl: document.getElementById('subTotal'),
    totalEl: document.getElementById('cartTotal'),
    discountInput: document.getElementById('discountInput'),
    customerName: document.getElementById('customerName'),
    customerPhone: document.getElementById('customerPhone'),
    themeToggle: document.getElementById('themeToggle'),
    modalOverlay: document.getElementById('modalOverlay'),
    modalBody: document.getElementById('modalBody')
};

// ==========================================
// 3. Initialization
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    renderProductGrid();
    setupEventListeners();

    // Focus search on load
    if (DOM.searchInput) DOM.searchInput.focus();

    // Restore held bills from local storage if any
    const savedBills = localStorage.getItem('heldBills');
    if (savedBills) {
        APP_STATE.heldBills = JSON.parse(savedBills);
    }
});

function setupEventListeners() {
    // Search Input
    DOM.searchInput.addEventListener('input', (e) => {
        APP_STATE.searchQuery = e.target.value.trim().toLowerCase();
        renderProductGrid();
    });

    // Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'F2') {
            e.preventDefault();
            DOM.searchInput.focus();
        }
        if (e.key === 'Escape') {
            if (DOM.suggestionsBox) DOM.suggestionsBox.style.display = 'none';
            closeModal();
        }
    });

    // Close modal on outside click
    if (DOM.modalOverlay) {
        DOM.modalOverlay.addEventListener('click', (e) => {
            if (e.target === DOM.modalOverlay) closeModal();
        });
    }
}

// ==========================================
// 4. Product Grid & Filtering
// ==========================================

function filterCategory(category) {
    APP_STATE.currentCategory = category;

    // Update active button state
    document.querySelectorAll('.cat-pill').forEach(btn => {
        btn.classList.toggle('active', btn.innerText === category || (category === 'All' && btn.innerText === 'All'));
    });

    renderProductGrid();
}

function renderProductGrid() {
    DOM.productGrid.innerHTML = '';

    const query = APP_STATE.searchQuery;
    const category = APP_STATE.currentCategory;

    let filtered = APP_STATE.medicines.filter(m => {
        // Category Filter (Case insensitive check if needed, but strict is fine for now)
        const catMatch = category === 'All' || (m.category && m.category === category);

        // Search Filter
        const nameMatch = m.medicine_name.toLowerCase().includes(query);
        const barcodeMatch = m.barcode && m.barcode.toString().includes(query);

        return catMatch && (query === '' || nameMatch || barcodeMatch);
    });

    // Limit display for performance if no search
    const displayItems = query ? filtered : filtered.slice(0, 50);

    if (displayItems.length === 0) {
        DOM.productGrid.innerHTML = `<div style='grid-column: 1/-1; text-align: center; padding: 20px; color: var(--text-light);'>No medicines found.</div>`;
        return;
    }

    displayItems.forEach(med => {
        const card = document.createElement('div');
        card.className = 'product-card';
        card.onclick = () => addToCart(med);

        // Determine stock status
        let stockClass = 'stock-high';
        let stockText = 'In Stock';

        if (med.stock <= 0) {
            stockClass = 'stock-out';
            stockText = 'Out of Stock';
        } else if (med.stock < 10) {
            stockClass = 'stock-low';
            stockText = 'Low Stock';
        } else if (med.stock < 50) {
            stockClass = 'stock-medium';
            stockText = 'Selling Fast';
        }

        // Initials for Avatar
        const initials = med.medicine_name.substring(0, 2).toUpperCase();

        card.innerHTML = `
            <div class="card-header">
                <div class="avatar">${initials}</div>
                <div class="stock-badge ${stockClass}">${stockText} (${med.stock})</div>
            </div>
            <div class="card-body">
                <h3 title="${med.medicine_name}">${med.medicine_name}</h3>
                <div class="meta-info">
                   <span class="category-tag">${med.category || 'General'}</span>
                </div>
            </div>
            <div class="card-footer">
                <div class="price">₹${parseFloat(med.price).toFixed(2)}</div>
                <button class="add-btn"><i class="fas fa-plus"></i> Add</button>
            </div>
        `;
        DOM.productGrid.appendChild(card);
    });
}

// ==========================================
// 5. Cart Logic
// ==========================================

function addToCart(med) {
    const existing = APP_STATE.cart.find(i => i.id === med.medicine_id);

    if (existing) {
        if (existing.qty + 1 > med.stock) {
            showToast(`Insufficient stock`, 'error');
            return;
        }
        existing.qty++;
        showToast('Quantity increased', 'success');
    } else {
        if (med.stock < 1) {
            showToast('Out of Stock', 'error');
            return;
        }
        APP_STATE.cart.push({
            id: med.medicine_id,
            name: med.medicine_name,
            price: parseFloat(med.price),
            qty: 1,
            stock: med.stock
        });
        showToast('Added to cart', 'success');
    }

    // Play sound (optional)
    // new Audio('/static/beep.mp3').play().catch(e=>{});

    renderCart();
}

function updateQty(id, change) {
    const item = APP_STATE.cart.find(i => i.id === id);
    if (!item) return;

    const newQty = item.qty + change;

    if (newQty <= 0) {
        // Remove item
        APP_STATE.cart = APP_STATE.cart.filter(i => i.id !== id);
    } else {
        if (newQty > item.stock) {
            showToast('Stock limit reached!', 'error');
            return;
        }
        item.qty = newQty;
    }
    renderCart();
}

function removeItem(id) {
    if (confirm('Remove item from cart?')) {
        APP_STATE.cart = APP_STATE.cart.filter(i => i.id !== id);
        renderCart();
    }
}

function clearCart() {
    if (APP_STATE.cart.length > 0 && confirm('Are you sure you want to clear the bill?')) {
        APP_STATE.cart = [];
        renderCart();
        DOM.customerName.value = '';
        DOM.customerPhone.value = '';
        DOM.discountInput.value = '';
        showToast('Bill cleared', 'success');
    }
}

function renderCart() {
    DOM.cartItemsBox.innerHTML = '';

    if (APP_STATE.cart.length === 0) {
        DOM.cartItemsBox.innerHTML = `
            <div class='empty-cart'>
                <i class='fas fa-shopping-basket'></i>
                <p>Cart is empty</p>
                <small>Scan or select items</small>
            </div>`;
        updateTotals();
        return;
    }

    APP_STATE.cart.forEach(item => {
        const div = document.createElement('div');
        div.className = 'cart-item';
        div.innerHTML = `
            <div class='cart-item-info'>
                <h4>${item.name}</h4>
                <small>₹${item.price.toFixed(2)}</small>
            </div>
            <div class='qty-control'>
                <button class='qty-btn' onclick='updateQty(${item.id}, -1)'>-</button>
                <div class='qty-val'>${item.qty}</div>
                <button class='qty-btn' onclick='updateQty(${item.id}, 1)'>+</button>
            </div>
            <button class='remove-btn' onclick='removeItem(${item.id})'>
                <i class='fas fa-times'></i>
            </button>
        `;
        DOM.cartItemsBox.appendChild(div);
    });

    updateTotals();
}

function updateTotals() {
    let subTotal = 0;
    let itemCount = 0;

    APP_STATE.cart.forEach(i => {
        subTotal += i.price * i.qty;
        itemCount += i.qty;
    });

    const discount = parseFloat(DOM.discountInput.value) || 0;
    const total = Math.max(0, subTotal - discount);

    DOM.subTotalEl.innerText = subTotal.toFixed(2);
    DOM.totalEl.innerText = total.toFixed(2);
    DOM.itemCountBadge.innerText = itemCount + (itemCount === 1 ? ' Item' : ' Items');

    // Update Checkout Button Total
    const btnTotal = document.getElementById('btnTotal');
    if (btnTotal) btnTotal.innerText = total.toFixed(2);
}


// ==========================================
// 6. Checkout & Features
// ==========================================

function checkout() {
    if (APP_STATE.cart.length === 0) {
        showToast('Cart is empty!', 'error');
        return;
    }

    const saleData = {
        customer_name: DOM.customerName.value,
        customer_phone: DOM.customerPhone.value,
        items: APP_STATE.cart.map(i => ({ medicine_id: i.id, quantity: i.qty })),
        payment_mode: document.querySelector('input[name="payment"]:checked').value,
        discount: parseFloat(DOM.discountInput.value) || 0
    };

    fetch(CONFIG.createSaleUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(saleData)
    })
        .then(res => res.json())
        .then(data => {
            if (data.success || data.status === 'success') {
                showToast('Sale completed successfully!', 'success');

                // Update local stock
                saleData.items.forEach(item => {
                    const med = APP_STATE.medicines.find(m => m.medicine_id === item.medicine_id);
                    if (med) {
                        med.stock -= item.quantity;
                    }
                });
                renderProductGrid();

                APP_STATE.cart = [];
                DOM.customerName.value = '';
                DOM.customerPhone.value = '';
                DOM.discountInput.value = '';
                renderCart();
                // Optional: Print Receipt
                if (data.invoice_id) {
                    // Maybe open receipt in new tab?
                    // window.open(`/sales/invoice/${data.invoice_id}`, '_blank');
                }
            } else {
                showToast('Error: ' + (data.error || 'Unknown error'), 'error');
            }
        })
        .catch(err => {
            console.error(err);
            showToast('Failed to process sale.', 'error');
        });
}

function holdBill() {
    if (APP_STATE.cart.length === 0) return;

    const bill = {
        id: Date.now(),
        timestamp: new Date().toLocaleTimeString(),
        cart: [...APP_STATE.cart], // Clone
        customer: DOM.customerName.value
    };

    APP_STATE.heldBills.push(bill);
    localStorage.setItem('heldBills', JSON.stringify(APP_STATE.heldBills));

    APP_STATE.cart = [];
    DOM.customerName.value = '';
    renderCart();
    showToast('Bill put on hold', 'success');
}

// Minimal Toast Implementation
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerText = message;
    document.body.appendChild(toast);

    // Trigger reflow
    toast.offsetHeight;

    requestAnimationFrame(() => {
        toast.classList.add('show');
    });

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function initTheme() {
    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-mode');
    }
}

function toggleFrontendTheme() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
}


// ==========================================
// 7. Recent Bills / Modal Logic
// ==========================================

function viewRecentBills() {
    if (!DOM.modalOverlay) return;

    DOM.modalOverlay.style.display = 'flex';

    if (APP_STATE.heldBills.length === 0) {
        DOM.modalBody.innerHTML = '<p>No held bills found.</p>';
        return;
    }

    let html = '<ul style="list-style:none; padding:0;">';
    APP_STATE.heldBills.forEach((bill, idx) => {
        html += `
            <li style="border-bottom:1px solid #eee; padding:10px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <strong>${bill.customer || 'Guest'}</strong><br>
                    <small>${bill.timestamp}</small>
                </div>
                <div>
                    <span class="badge" style="background:var(--text-light)">${bill.cart.length} Items</span>
                    <button class="icon-btn" onclick="restoreBill(${idx})"><i class="fas fa-undo"></i></button>
                    <button class="icon-btn" style="color:var(--danger);" onclick="deleteHeldBill(${idx})"><i class="fas fa-trash"></i></button>
                </div>
            </li>
        `;
    });
    html += '</ul>';
    DOM.modalBody.innerHTML = html;
}

function restoreBill(idx) {
    if (APP_STATE.cart.length > 0) {
        if (!confirm('Current cart is not empty. Overwrite?')) return;
    }

    const bill = APP_STATE.heldBills[idx];
    APP_STATE.cart = bill.cart;
    DOM.customerName.value = bill.customer || '';

    // Remove from held
    APP_STATE.heldBills.splice(idx, 1);
    localStorage.setItem('heldBills', JSON.stringify(APP_STATE.heldBills));

    closeModal();
    renderCart();
    showToast('Bill restored', 'success');
}

function deleteHeldBill(idx) {
    if (confirm('Delete this held bill?')) {
        APP_STATE.heldBills.splice(idx, 1);
        localStorage.setItem('heldBills', JSON.stringify(APP_STATE.heldBills));
        viewRecentBills(); // Refresh list
    }
}

function closeModal() {
    if (DOM.modalOverlay) DOM.modalOverlay.style.display = 'none';
}
