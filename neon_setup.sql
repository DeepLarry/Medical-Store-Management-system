-- 1. CLEANUP (If exists)
DROP TABLE IF EXISTS sales CASCADE;
DROP TABLE IF EXISTS medicines CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;
DROP TABLE IF EXISTS admins CASCADE;
DROP TABLE IF EXISTS invoices CASCADE;
DROP TABLE IF EXISTS settings CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;

-- 2. CREATE TABLES
CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email VARCHAR(100),
    role VARCHAR(20) DEFAULT 'admin',
    store_id INTEGER
);

CREATE TABLE medicines (
    medicine_id SERIAL PRIMARY KEY,
    medicine_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price NUMERIC(10,2),
    stock INTEGER,
    supplier_id INTEGER,
    expiry_date DATE,
    purchase_price NUMERIC(10,2) DEFAULT 0.00,
    barcode VARCHAR(100),
    minimum_stock_level INTEGER DEFAULT 10,
    batch_number VARCHAR(50) DEFAULT 'BATCH-001',
    store_id INTEGER
);

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(100),
    phone VARCHAR(15),
    city VARCHAR(50),
    store_id INTEGER
);

CREATE TABLE sales (
    sale_id SERIAL PRIMARY KEY,
    invoice_id INTEGER,
    medicine_id INTEGER REFERENCES medicines(medicine_id),
    customer_id INTEGER,
    quantity INTEGER,
    price_per_unit NUMERIC(10,2),
    total_amount NUMERIC(10,2),
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_mode VARCHAR(50) DEFAULT 'Cash',
    store_id INTEGER
);

CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    store_id INTEGER
);

CREATE TABLE invoices (
    invoice_id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount NUMERIC(10,2),
    payment_mode VARCHAR(50) DEFAULT 'Cash',
    discount NUMERIC(10,2) DEFAULT 0.00,
    store_id INTEGER
);

CREATE TABLE settings (
    setting_key VARCHAR(50) PRIMARY KEY,
    setting_value TEXT,
    store_id INTEGER
);

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    type VARCHAR(20) DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    store_id INTEGER
);

-- 3. INSERT DEFAULT ADMIN (User: admin, Pass: admin123)
-- Hash generated for 'admin123'
INSERT INTO admins (username, password_hash, role, store_id) 
VALUES ('admin', 'scrypt:32768:8:1$YrnbRtryHcnda70C$838b79b1fa9eba9202f9e58eb25bff80c5a9854444a3e3792f8da4a5401c444a88e66a3d15d47bd20301cfc8c20d024565f17aa24211529f7e23209f16fb4d86', 'super_admin', 1);

-- 4. INSERT STORE SETTINGS
INSERT INTO settings (setting_key, setting_value, store_id) VALUES ('store_name', 'Deep Medical Store', 1);
INSERT INTO settings (setting_key, setting_value, store_id) VALUES ('address', 'New Delhi, India', 1);
INSERT INTO settings (setting_key, setting_value, store_id) VALUES ('phone', '+91 9876543210', 1);
