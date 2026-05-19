-- ============================================================
--  PharmaCare Database Schema
--  Run this file in MySQL: source pharmacare.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS pharmacare;
USE pharmacare;

-- ─── Users ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    full_name  VARCHAR(100) NOT NULL,
    username   VARCHAR(50)  NOT NULL UNIQUE,
    email      VARCHAR(100) UNIQUE,
    password   VARCHAR(255) NOT NULL,
    role       ENUM('admin','pharmacist','staff') DEFAULT 'staff',
    is_active  TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default admin: username=admin, password=admin123
INSERT IGNORE INTO users(full_name,username,email,password,role) VALUES
('Administrator','admin','admin@pharmacare.com',
 SHA2('admin123',256),'admin');

-- ─── Medicines ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS medicines (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    name             VARCHAR(150) NOT NULL,
    generic_name     VARCHAR(150),
    category         VARCHAR(100),
    manufacturer     VARCHAR(150),
    batch_number     VARCHAR(50),
    barcode          VARCHAR(50),
    stock_quantity   DECIMAL(10,2) DEFAULT 0,
    unit             VARCHAR(20)   DEFAULT 'tablets',
    purchase_price   DECIMAL(10,2) DEFAULT 0,
    selling_price    DECIMAL(10,2) DEFAULT 0,
    reorder_level    DECIMAL(10,2) DEFAULT 10,
    manufacture_date DATE,
    expiry_date      DATE,
    description      TEXT,
    is_active        TINYINT(1) DEFAULT 1,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Sample medicines
INSERT IGNORE INTO medicines(name,generic_name,category,manufacturer,batch_number,stock_quantity,unit,purchase_price,selling_price,reorder_level,manufacture_date,expiry_date) VALUES
('Paracetamol 500mg','Paracetamol','Analgesic','Sun Pharma','BAT001',500,'tablets',1.50,3.00,50,'2024-01-01','2026-12-31'),
('Amoxicillin 250mg','Amoxicillin','Antibiotic','Cipla','BAT002',200,'capsules',5.00,12.00,30,'2024-02-01','2026-06-30'),
('Omeprazole 20mg','Omeprazole','Antacid','Ranbaxy','BAT003',300,'capsules',3.50,8.00,40,'2024-03-01','2026-09-30'),
('Metformin 500mg','Metformin','Antidiabetic','Dr Reddy','BAT004',150,'tablets',4.00,9.00,25,'2024-01-15','2026-11-30'),
('Atorvastatin 10mg','Atorvastatin','Statin','Zydus','BAT005',80,'tablets',8.00,18.00,20,'2024-04-01','2026-08-31'),
('Cetirizine 10mg','Cetirizine','Antihistamine','Abbott','BAT006',8,'tablets',2.00,5.00,30,'2024-05-01','2024-12-31');

-- ─── Customers ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    phone         VARCHAR(15),
    email         VARCHAR(100),
    address       TEXT,
    date_of_birth DATE,
    gender        ENUM('Male','Female','Other',''),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── Suppliers ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS suppliers (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(150) NOT NULL,
    contact_person VARCHAR(100),
    phone          VARCHAR(15),
    email          VARCHAR(100),
    address        TEXT,
    gst_number     VARCHAR(20),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── Sales ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sales (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    bill_number    VARCHAR(50) NOT NULL UNIQUE,
    customer_id    INT,
    subtotal       DECIMAL(10,2) DEFAULT 0,
    discount       DECIMAL(10,2) DEFAULT 0,
    tax            DECIMAL(10,2) DEFAULT 0,
    total_amount   DECIMAL(10,2) DEFAULT 0,
    payment_method ENUM('Cash','Card','UPI','Credit') DEFAULT 'Cash',
    notes          TEXT,
    created_by     INT,
    sale_date      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE SET NULL,
    FOREIGN KEY(created_by)  REFERENCES users(id)     ON DELETE SET NULL
);

-- ─── Sale Items ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sale_items (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    sale_id     INT NOT NULL,
    medicine_id INT NOT NULL,
    quantity    DECIMAL(10,2) NOT NULL,
    unit_price  DECIMAL(10,2) NOT NULL,
    subtotal    DECIMAL(10,2) NOT NULL,
    FOREIGN KEY(sale_id)     REFERENCES sales(id)     ON DELETE CASCADE,
    FOREIGN KEY(medicine_id) REFERENCES medicines(id) ON DELETE RESTRICT
);
