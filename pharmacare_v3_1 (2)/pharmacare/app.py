from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import hashlib
from datetime import datetime, date, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = 'pharmacare_secret_2024'

DATABASE = 'pharmacare.db'

# ─── Database Helper ─────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name  TEXT NOT NULL,
        username   TEXT NOT NULL UNIQUE,
        email      TEXT,
        password   TEXT NOT NULL,
        role       TEXT DEFAULT 'staff',
        is_active  INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS medicines (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        name             TEXT NOT NULL,
        generic_name     TEXT,
        category         TEXT,
        manufacturer     TEXT,
        batch_number     TEXT,
        barcode          TEXT,
        stock_quantity   REAL DEFAULT 0,
        unit             TEXT DEFAULT 'tablets',
        purchase_price   REAL DEFAULT 0,
        selling_price    REAL DEFAULT 0,
        reorder_level    REAL DEFAULT 10,
        manufacture_date TEXT,
        expiry_date      TEXT,
        description      TEXT,
        is_active        INTEGER DEFAULT 1,
        created_at       TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS customers (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT NOT NULL,
        phone         TEXT,
        email         TEXT,
        address       TEXT,
        date_of_birth TEXT,
        gender        TEXT,
        created_at    TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS suppliers (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        name           TEXT NOT NULL,
        contact_person TEXT,
        phone          TEXT,
        email          TEXT,
        address        TEXT,
        gst_number     TEXT,
        created_at     TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS sales (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        bill_number    TEXT NOT NULL UNIQUE,
        customer_id    INTEGER,
        subtotal       REAL DEFAULT 0,
        discount       REAL DEFAULT 0,
        tax            REAL DEFAULT 0,
        total_amount   REAL DEFAULT 0,
        payment_method TEXT DEFAULT 'Cash',
        notes          TEXT,
        created_by     INTEGER,
        sale_date      TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS sale_items (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id     INTEGER NOT NULL,
        medicine_id INTEGER NOT NULL,
        quantity    REAL NOT NULL,
        unit_price  REAL NOT NULL,
        subtotal    REAL NOT NULL
    );
    """)

    pw = hashlib.sha256('admin123'.encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users(full_name,username,email,password,role) VALUES(?,?,?,?,?)",
              ('Administrator','admin','admin@pharmacare.com', pw, 'admin'))

    samples = [
        ('Paracetamol 500mg','Paracetamol','Analgesic','Sun Pharma','BAT001',500,'tablets',1.50,3.00,50,'2024-01-01','2026-12-31'),
        ('Amoxicillin 250mg','Amoxicillin','Antibiotic','Cipla','BAT002',200,'capsules',5.00,12.00,30,'2024-02-01','2026-06-30'),
        ('Omeprazole 20mg','Omeprazole','Antacid','Ranbaxy','BAT003',300,'capsules',3.50,8.00,40,'2024-03-01','2026-09-30'),
        ('Metformin 500mg','Metformin','Antidiabetic','Dr Reddy','BAT004',150,'tablets',4.00,9.00,25,'2024-01-15','2026-11-30'),
        ('Atorvastatin 10mg','Atorvastatin','Statin','Zydus','BAT005',80,'tablets',8.00,18.00,20,'2024-04-01','2026-08-31'),
        ('Cetirizine 10mg','Cetirizine','Antihistamine','Abbott','BAT006',8,'tablets',2.00,5.00,30,'2024-05-01','2024-12-31'),
    ]
    for s in samples:
        c.execute("""INSERT OR IGNORE INTO medicines
            (name,generic_name,category,manufacturer,batch_number,stock_quantity,unit,
             purchase_price,selling_price,reorder_level,manufacture_date,expiry_date)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", s)

    conn.commit()
    conn.close()

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('role') not in roles:
                flash('Access denied.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator

def query(sql, params=(), one=False):
    conn = get_db()
    cur = conn.execute(sql, params)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def execute(sql, params=()):
    conn = get_db()
    cur = conn.execute(sql, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id

# ════════════════════════════════════════════════════════════════
# AUTH
# ════════════════════════════════════════════════════════════════
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        user = query("SELECT * FROM users WHERE username=? AND password=? AND is_active=1",
                     (username, password), one=True)
        if user:
            session['user_id']  = user['id']
            session['username'] = user['username']
            session['role']     = user['role']
            session['name']     = user['full_name']
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        username  = request.form['username']
        email     = request.form['email']
        password  = hash_password(request.form['password'])
        role      = request.form.get('role', 'staff')
        existing  = query("SELECT id FROM users WHERE username=? OR email=?", (username, email), one=True)
        if existing:
            flash('Username or email already exists.', 'danger')
        else:
            execute("INSERT INTO users(full_name,username,email,password,role) VALUES(?,?,?,?,?)",
                    (full_name, username, email, password, role))
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# ════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════
@app.route('/dashboard')
@login_required
def dashboard():
    today_str = date.today().isoformat()
    soon_str  = (date.today() + timedelta(days=30)).isoformat()
    month     = date.today().strftime('%Y-%m')

    total_medicines = query("SELECT COUNT(*) as c FROM medicines WHERE is_active=1", one=True)['c']
    low_stock       = query("SELECT COUNT(*) as c FROM medicines WHERE stock_quantity<=reorder_level AND is_active=1", one=True)['c']
    expired         = query("SELECT COUNT(*) as c FROM medicines WHERE expiry_date<=? AND is_active=1", (today_str,), one=True)['c']
    expiring_soon   = query("SELECT COUNT(*) as c FROM medicines WHERE expiry_date BETWEEN ? AND ? AND is_active=1", (today_str, soon_str), one=True)['c']
    today_revenue   = query("SELECT SUM(total_amount) as r FROM sales WHERE date(sale_date)=?", (today_str,), one=True)['r'] or 0
    monthly_revenue = query("SELECT SUM(total_amount) as r FROM sales WHERE strftime('%Y-%m',sale_date)=?", (month,), one=True)['r'] or 0
    total_customers = query("SELECT COUNT(*) as c FROM customers", one=True)['c']
    total_suppliers = query("SELECT COUNT(*) as c FROM suppliers", one=True)['c']
    recent_sales    = query("""SELECT s.id, s.bill_number, c.name as customer_name, s.total_amount, s.sale_date
                               FROM sales s LEFT JOIN customers c ON s.customer_id=c.id
                               ORDER BY s.sale_date DESC LIMIT 5""")
    low_stock_meds  = query("""SELECT name, stock_quantity, reorder_level, unit
                               FROM medicines WHERE stock_quantity<=reorder_level AND is_active=1 LIMIT 5""")

    return render_template('dashboard.html',
        total_medicines=total_medicines, low_stock=low_stock,
        expired=expired, expiring_soon=expiring_soon,
        today_revenue=today_revenue, monthly_revenue=monthly_revenue,
        total_customers=total_customers, total_suppliers=total_suppliers,
        recent_sales=recent_sales, low_stock_meds=low_stock_meds)

# ════════════════════════════════════════════════════════════════
# MEDICINES
# ════════════════════════════════════════════════════════════════
@app.route('/medicines')
@login_required
def medicines():
    search = request.args.get('search', '')
    if search:
        meds = query("""SELECT * FROM medicines WHERE is_active=1 AND
                        (name LIKE ? OR generic_name LIKE ? OR category LIKE ?) ORDER BY name""",
                     (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        meds = query("SELECT * FROM medicines WHERE is_active=1 ORDER BY name")
    today_str = date.today().isoformat()
    soon_str  = (date.today() + timedelta(days=30)).isoformat()
    return render_template('medicines.html', medicines=meds, search=search, today=today_str, soon=soon_str)

@app.route('/medicines/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pharmacist')
def add_medicine():
    if request.method == 'POST':
        execute("""INSERT INTO medicines
            (name,generic_name,category,manufacturer,batch_number,barcode,stock_quantity,unit,
             purchase_price,selling_price,reorder_level,manufacture_date,expiry_date,description)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (request.form['name'], request.form['generic_name'], request.form['category'],
             request.form['manufacturer'], request.form['batch_number'], request.form.get('barcode',''),
             request.form['stock_quantity'], request.form['unit'],
             request.form['purchase_price'], request.form['selling_price'],
             request.form['reorder_level'], request.form['manufacture_date'],
             request.form['expiry_date'], request.form.get('description','')))
        flash('Medicine added successfully!', 'success')
        return redirect(url_for('medicines'))
    return render_template('medicine_form.html', medicine=None, action='Add')

@app.route('/medicines/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pharmacist')
def edit_medicine(id):
    if request.method == 'POST':
        execute("""UPDATE medicines SET name=?,generic_name=?,category=?,manufacturer=?,batch_number=?,
            barcode=?,stock_quantity=?,unit=?,purchase_price=?,selling_price=?,reorder_level=?,
            manufacture_date=?,expiry_date=?,description=? WHERE id=?""",
            (request.form['name'], request.form['generic_name'], request.form['category'],
             request.form['manufacturer'], request.form['batch_number'], request.form.get('barcode',''),
             request.form['stock_quantity'], request.form['unit'],
             request.form['purchase_price'], request.form['selling_price'],
             request.form['reorder_level'], request.form['manufacture_date'],
             request.form['expiry_date'], request.form.get('description',''), id))
        flash('Medicine updated!', 'success')
        return redirect(url_for('medicines'))
    medicine = query("SELECT * FROM medicines WHERE id=?", (id,), one=True)
    return render_template('medicine_form.html', medicine=medicine, action='Edit')

@app.route('/medicines/delete/<int:id>')
@login_required
@role_required('admin')
def delete_medicine(id):
    execute("UPDATE medicines SET is_active=0 WHERE id=?", (id,))
    flash('Medicine removed.', 'info')
    return redirect(url_for('medicines'))

@app.route('/api/medicine/<int:id>')
@login_required
def get_medicine_api(id):
    med = query("SELECT * FROM medicines WHERE id=? AND is_active=1", (id,), one=True)
    if med:
        return jsonify(dict(med))
    return jsonify({'error': 'Not found'}), 404

# ════════════════════════════════════════════════════════════════
# BILLING
# ════════════════════════════════════════════════════════════════
@app.route('/billing')
@login_required
def billing():
    customers = query("SELECT * FROM customers ORDER BY name")
    meds      = query("SELECT * FROM medicines WHERE is_active=1 AND stock_quantity>0 ORDER BY name")
    bill_number = f"BILL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return render_template('billing.html', customers=customers, medicines=meds, bill_number=bill_number)

@app.route('/billing/save', methods=['POST'])
@login_required
def save_bill():
    data = request.get_json()
    conn = get_db()
    try:
        cur = conn.execute("""INSERT INTO sales
            (bill_number,customer_id,subtotal,discount,tax,total_amount,payment_method,notes,created_by)
            VALUES(?,?,?,?,?,?,?,?,?)""",
            (data['bill_number'], data.get('customer_id') or None,
             data['subtotal'], data['discount'], data['tax'],
             data['total_amount'], data['payment_method'],
             data.get('notes',''), session['user_id']))
        sale_id = cur.lastrowid
        for item in data['items']:
            conn.execute("INSERT INTO sale_items(sale_id,medicine_id,quantity,unit_price,subtotal) VALUES(?,?,?,?,?)",
                         (sale_id, item['medicine_id'], item['quantity'], item['unit_price'], item['subtotal']))
            conn.execute("UPDATE medicines SET stock_quantity=stock_quantity-? WHERE id=?",
                         (item['quantity'], item['medicine_id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'sale_id': sale_id})
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/billing/invoice/<int:sale_id>')
@login_required
def invoice(sale_id):
    sale  = query("""SELECT s.*, c.name as customer_name, c.phone as customer_phone,
                     c.address as customer_address, u.full_name as cashier
                     FROM sales s LEFT JOIN customers c ON s.customer_id=c.id
                     LEFT JOIN users u ON s.created_by=u.id WHERE s.id=?""", (sale_id,), one=True)
    items = query("""SELECT si.*, m.name, m.generic_name, m.unit
                     FROM sale_items si JOIN medicines m ON si.medicine_id=m.id WHERE si.sale_id=?""", (sale_id,))
    return render_template('invoice.html', sale=sale, items=items)

@app.route('/sales')
@login_required
def sales():
    date_from = request.args.get('date_from', '')
    date_to   = request.args.get('date_to', '')
    if date_from and date_to:
        sales_list = query("""SELECT s.*, c.name as customer_name, u.full_name as cashier
                              FROM sales s LEFT JOIN customers c ON s.customer_id=c.id
                              LEFT JOIN users u ON s.created_by=u.id
                              WHERE date(s.sale_date) BETWEEN ? AND ?
                              ORDER BY s.sale_date DESC""", (date_from, date_to))
    else:
        sales_list = query("""SELECT s.*, c.name as customer_name, u.full_name as cashier
                              FROM sales s LEFT JOIN customers c ON s.customer_id=c.id
                              LEFT JOIN users u ON s.created_by=u.id ORDER BY s.sale_date DESC""")
    return render_template('sales.html', sales=sales_list, date_from=date_from, date_to=date_to)

# ════════════════════════════════════════════════════════════════
# CUSTOMERS
# ════════════════════════════════════════════════════════════════
@app.route('/customers')
@login_required
def customers():
    search = request.args.get('search', '')
    if search:
        data = query("SELECT * FROM customers WHERE name LIKE ? OR phone LIKE ? ORDER BY name",
                     (f'%{search}%', f'%{search}%'))
    else:
        data = query("SELECT * FROM customers ORDER BY name")
    return render_template('customers.html', customers=data, search=search)

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        execute("INSERT INTO customers(name,phone,email,address,date_of_birth,gender) VALUES(?,?,?,?,?,?)",
                (request.form['name'], request.form['phone'], request.form.get('email',''),
                 request.form.get('address',''), request.form.get('date_of_birth',''), request.form.get('gender','')))
        flash('Customer added!', 'success')
        return redirect(url_for('customers'))
    return render_template('customer_form.html', customer=None, action='Add')

@app.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    if request.method == 'POST':
        execute("UPDATE customers SET name=?,phone=?,email=?,address=?,date_of_birth=?,gender=? WHERE id=?",
                (request.form['name'], request.form['phone'], request.form.get('email',''),
                 request.form.get('address',''), request.form.get('date_of_birth',''), request.form.get('gender',''), id))
        flash('Customer updated!', 'success')
        return redirect(url_for('customers'))
    customer = query("SELECT * FROM customers WHERE id=?", (id,), one=True)
    return render_template('customer_form.html', customer=customer, action='Edit')

@app.route('/customers/delete/<int:id>')
@login_required
@role_required('admin')
def delete_customer(id):
    execute("DELETE FROM customers WHERE id=?", (id,))
    flash('Customer deleted.', 'info')
    return redirect(url_for('customers'))

# ════════════════════════════════════════════════════════════════
# SUPPLIERS
# ════════════════════════════════════════════════════════════════
@app.route('/suppliers')
@login_required
def suppliers():
    search = request.args.get('search', '')
    if search:
        data = query("SELECT * FROM suppliers WHERE name LIKE ? OR contact_person LIKE ? ORDER BY name",
                     (f'%{search}%', f'%{search}%'))
    else:
        data = query("SELECT * FROM suppliers ORDER BY name")
    return render_template('suppliers.html', suppliers=data, search=search)

@app.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pharmacist')
def add_supplier():
    if request.method == 'POST':
        execute("INSERT INTO suppliers(name,contact_person,phone,email,address,gst_number) VALUES(?,?,?,?,?,?)",
                (request.form['name'], request.form['contact_person'], request.form['phone'],
                 request.form.get('email',''), request.form.get('address',''), request.form.get('gst_number','')))
        flash('Supplier added!', 'success')
        return redirect(url_for('suppliers'))
    return render_template('supplier_form.html', supplier=None, action='Add')

@app.route('/suppliers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pharmacist')
def edit_supplier(id):
    if request.method == 'POST':
        execute("UPDATE suppliers SET name=?,contact_person=?,phone=?,email=?,address=?,gst_number=? WHERE id=?",
                (request.form['name'], request.form['contact_person'], request.form['phone'],
                 request.form.get('email',''), request.form.get('address',''), request.form.get('gst_number',''), id))
        flash('Supplier updated!', 'success')
        return redirect(url_for('suppliers'))
    supplier = query("SELECT * FROM suppliers WHERE id=?", (id,), one=True)
    return render_template('supplier_form.html', supplier=supplier, action='Edit')

@app.route('/suppliers/delete/<int:id>')
@login_required
@role_required('admin')
def delete_supplier(id):
    execute("DELETE FROM suppliers WHERE id=?", (id,))
    flash('Supplier deleted.', 'info')
    return redirect(url_for('suppliers'))

# ════════════════════════════════════════════════════════════════
# REPORTS
# ════════════════════════════════════════════════════════════════
@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/reports/stock')
@login_required
def report_stock():
    meds = query("SELECT * FROM medicines WHERE is_active=1 ORDER BY stock_quantity ASC")
    return render_template('report_stock.html', medicines=meds, today=date.today().isoformat())

@app.route('/reports/sales')
@login_required
def report_sales():
    period    = request.args.get('period', 'today')
    today_str = date.today().isoformat()
    month     = date.today().strftime('%Y-%m')
    week_ago  = (date.today() - timedelta(days=7)).isoformat()
    if period == 'today':
        where = f"WHERE date(s.sale_date)='{today_str}'"
    elif period == 'week':
        where = f"WHERE date(s.sale_date)>='{week_ago}'"
    elif period == 'month':
        where = f"WHERE strftime('%Y-%m',s.sale_date)='{month}'"
    else:
        where = ""
    sales_list = query(f"""SELECT s.*, c.name as customer_name FROM sales s
                           LEFT JOIN customers c ON s.customer_id=c.id {where} ORDER BY s.sale_date DESC""")
    total = sum(s['total_amount'] for s in sales_list)
    return render_template('report_sales.html', sales=sales_list, total=total, period=period)

@app.route('/reports/expired')
@login_required
def report_expired():
    soon_str = (date.today() + timedelta(days=60)).isoformat()
    meds = query("SELECT * FROM medicines WHERE expiry_date<=? AND is_active=1 ORDER BY expiry_date ASC", (soon_str,))
    return render_template('report_expired.html', medicines=meds, today=date.today().isoformat())

@app.route('/reports/profit')
@login_required
@role_required('admin')
def report_profit():
    data = query("""SELECT m.name, SUM(si.quantity) as qty_sold,
                    SUM(si.quantity * m.purchase_price) as cost,
                    SUM(si.subtotal) as revenue,
                    SUM(si.subtotal - si.quantity * m.purchase_price) as profit
                    FROM sale_items si JOIN medicines m ON si.medicine_id=m.id
                    GROUP BY m.id, m.name ORDER BY profit DESC""")
    total_rev = query("SELECT SUM(total_amount) as t FROM sales", one=True)['t'] or 0
    return render_template('report_profit.html', data=data, total_revenue=total_rev)

# ════════════════════════════════════════════════════════════════
# USERS
# ════════════════════════════════════════════════════════════════
@app.route('/users')
@login_required
@role_required('admin')
def users():
    users_list = query("SELECT * FROM users ORDER BY full_name")
    return render_template('users.html', users=users_list)

@app.route('/users/toggle/<int:id>')
@login_required
@role_required('admin')
def toggle_user(id):
    execute("UPDATE users SET is_active=CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE id=?", (id,))
    flash('User status updated.', 'info')
    return redirect(url_for('users'))

# ════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    init_db()
    app.jinja_env.globals['timedelta'] = timedelta
    app.run(debug=True)
