# 💊 PharmaCare — Medical Store Management System

A full-stack pharmacy management web application built with **Python Flask** and **MySQL**.

---

## 📁 Project Structure

```
pharmacare/
├── app.py                  ← Main Flask application (all routes & logic)
├── pharmacare.sql          ← MySQL database schema + sample data
├── requirements.txt        ← Python dependencies
├── README.md
└── templates/
    ├── base.html           ← Sidebar layout (shared by all pages)
    ├── login.html          ← Login page
    ├── register.html       ← Registration page
    ├── dashboard.html      ← Home dashboard with stats
    ├── medicines.html      ← Medicine inventory list
    ├── medicine_form.html  ← Add / Edit medicine form
    ├── billing.html        ← New bill / POS page
    ├── invoice.html        ← Printable invoice
    ├── sales.html          ← Sales history
    ├── customers.html      ← Customer list
    ├── customer_form.html  ← Add / Edit customer
    ├── suppliers.html      ← Supplier list
    ├── supplier_form.html  ← Add / Edit supplier
    ├── reports.html        ← Reports hub
    ├── report_stock.html   ← Stock status report
    ├── report_sales.html   ← Sales report (by period)
    ├── report_expired.html ← Expired medicines report
    ├── report_profit.html  ← Profit & Loss report
    └── users.html          ← User management (admin only)
```

---

## ⚙️ Setup Instructions

### Step 1 — Install Python & MySQL

Make sure you have:
- **Python 3.10+**
- **MySQL 8.0+** (XAMPP / WAMP / standalone MySQL)

---

### Step 2 — Install Python dependencies

Open terminal in the project folder and run:

```bash
pip install -r requirements.txt
```

If you face issues installing `mysqlclient` on Windows, try:
```bash
pip install Flask Flask-MySQLdb PyMySQL
```
And in `app.py`, replace `from flask_mysqldb import MySQL` with PyMySQL if needed.

---

### Step 3 — Set up the Database

1. Open **phpMyAdmin** or MySQL Workbench
2. Run the SQL file:

```sql
source /path/to/pharmacare/pharmacare.sql
```

Or paste the contents of `pharmacare.sql` in your MySQL client and execute.

This will create:
- The `pharmacare` database
- All required tables (`users`, `medicines`, `customers`, `suppliers`, `sales`, `sale_items`)
- Sample medicines and a default admin user

---

### Step 4 — Configure Database in app.py

Open `app.py` and update these lines with your MySQL credentials:

```python
app.config['MYSQL_HOST']     = 'localhost'
app.config['MYSQL_USER']     = 'root'
app.config['MYSQL_PASSWORD'] = ''        # ← your MySQL password
app.config['MYSQL_DB']       = 'pharmacare'
```

---

### Step 5 — Run the Application

```bash
python app.py
```

Then open your browser and go to:

```
http://127.0.0.1:5000
```

---

## 🔐 Default Login

| Field    | Value      |
|----------|------------|
| Username | `admin`    |
| Password | `admin123` |
| Role     | Admin      |

---

## 👥 User Roles

| Role         | Permissions                                           |
|--------------|-------------------------------------------------------|
| **Admin**    | Full access: users, delete, all reports               |
| **Pharmacist**| Add/edit medicines, billing, suppliers, reports      |
| **Staff**    | Billing and viewing only                              |

---

## 🧩 Modules Included

| Module                     | Features                                              |
|----------------------------|-------------------------------------------------------|
| 🔐 Login / Registration    | Secure auth, password hashing, session management    |
| 💊 Medicine Inventory       | Add/Edit/Delete, stock tracking, expiry alerts       |
| 🧾 Billing / POS            | Dynamic cart, discount, tax, invoice generation      |
| 📋 Sales History            | Date filter, view invoices                           |
| 👤 Customer Management      | Add/Edit/Delete customers                            |
| 🚚 Supplier Management      | Add/Edit/Delete suppliers, GST number                |
| 📊 Reports                  | Stock, Sales, Expiry, Profit & Loss                  |
| 👨‍💼 User Management         | Role-based access, enable/disable users              |

---

## 🔒 Security Features

- SHA-256 password hashing
- Session-based authentication
- Role-based access control (RBAC)
- Input validation on all forms
- SQL injection prevention via parameterized queries

---

## 🚀 Future Enhancements (from Synopsis)

1. Cloud deployment (AWS / Heroku / Railway)
2. Mobile-responsive PWA
3. AI-based stock prediction
4. Barcode scanner integration
5. SMS/Email alerts for low stock
6. Government drug database API integration

---

## 📚 Tech Stack

| Layer      | Technology                    |
|------------|-------------------------------|
| Backend    | Python 3, Flask               |
| Database   | MySQL                         |
| Frontend   | HTML5, Bootstrap 5, JS        |
| Icons      | Font Awesome 6                |
| Auth       | Flask sessions + SHA-256      |

---

*Project by: Nitin Rana & Ritik Singh | Uttaranchal University | 2024–2025*
