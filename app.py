from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, g
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from datetime import datetime, timedelta
from io import BytesIO
from openpyxl import Workbook
from math import ceil
import json
import psycopg2
from psycopg2.extras import DictCursor

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'a-strong-default-key-for-development-only')
app.permanent_session_lifetime = timedelta(days=7)

# --- Centralized Database Connection ---
def get_db():
    if 'db' not in g:
        db_url = os.environ.get('DATABASE_URL')
        g.db = psycopg2.connect(db_url)
        # --- NEW: Set the timezone for the entire session ---
        with g.db.cursor() as cursor:
            cursor.execute("SET TIMEZONE='Asia/Kolkata'")
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# --- Decorators ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash('Access denied: You must be an admin to view this page.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = get_db().cursor(cursor_factory=DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['role'] = user['role']
            session.permanent = True # Keep user logged in
            session['_just_logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    if session.pop('_just_logged_in', None):
        flash('Login successful!', 'success')

    db = get_db()
    c = db.cursor(cursor_factory=DictCursor)
    
    today_str = datetime.now().date()
    
    # FIX: Used PostgreSQL date casting `::date`
    c.execute("SELECT SUM(total_amount) AS total FROM invoices WHERE created_on::date = %s", (today_str,))
    total_revenue_today = c.fetchone()['total'] or 0
    
    c.execute("SELECT COUNT(id) AS count FROM invoices WHERE created_on::date = %s", (today_str,))
    total_invoices_today = c.fetchone()['count'] or 0

    c.execute("SELECT SUM(ii.quantity) AS total FROM invoice_items ii JOIN invoices i ON ii.invoice_id = i.id WHERE i.created_on::date = %s", (today_str,))
    total_items_today = c.fetchone()['total'] or 0

    c.execute("""
        SELECT p.name FROM invoice_items ii
        JOIN products p ON ii.product_id = p.id JOIN invoices i ON ii.invoice_id = i.id
        WHERE i.created_on::date = %s
        GROUP BY p.name ORDER BY SUM(ii.quantity) DESC LIMIT 1
    """, (today_str,))
    top_product_result = c.fetchone()
    top_product_today = top_product_result['name'] if top_product_result else "N/A"

    last_7_days = [(datetime.now().date() - timedelta(days=i)) for i in reversed(range(7))]
    daily_totals = []
    for day in last_7_days:
        c.execute("SELECT SUM(total_amount) AS total FROM invoices WHERE created_on::date = %s", (day,))
        total = c.fetchone()['total'] or 0
        daily_totals.append(float(total)) # FIX: Cast Decimal to float for JSON

    c.execute("""
        SELECT p.name, SUM(ii.line_total) as total_revenue FROM invoice_items ii
        JOIN products p ON ii.product_id = p.id
        GROUP BY p.name ORDER BY total_revenue DESC LIMIT 5
    """)
    top_products_data = c.fetchall()
    top_products_labels = [row['name'] for row in top_products_data]
    top_products_values = [float(row['total_revenue']) for row in top_products_data]

    c.execute("""
        SELECT p.category, SUM(ii.line_total) as total_revenue FROM invoice_items ii
        JOIN products p ON ii.product_id = p.id
        GROUP BY p.category ORDER BY total_revenue DESC
    """)
    category_sales_data = c.fetchall()
    category_labels = [row['category'] for row in category_sales_data if row['category']]
    category_values = [float(row['total_revenue']) for row in category_sales_data if row['category']]

    c.execute("SELECT name, stock FROM products ORDER BY stock ASC LIMIT 5")
    low_stock_items = c.fetchall()

    c.execute("SELECT customer_name, total_amount FROM invoices ORDER BY id DESC LIMIT 5")
    recent_transactions = c.fetchall()

    c.execute("""
        SELECT customer_name, SUM(total_amount) as total_spent 
        FROM invoices 
        WHERE customer_name IS NOT NULL AND customer_name != '' 
        GROUP BY customer_name 
        ORDER BY total_spent DESC 
        LIMIT 5
    """)
    most_valuable_customers = c.fetchall()

    return render_template('dashboard.html',
                           total_revenue_today=total_revenue_today,
                           total_items_today=total_items_today,
                           total_invoices_today=total_invoices_today,
                           top_product_today=top_product_today,
                           last_7_days=[d.strftime('%Y-%m-%d') for d in last_7_days],
                           daily_totals=daily_totals,
                           top_products_labels=json.dumps(top_products_labels),
                           top_products_values=json.dumps(top_products_values),
                           category_labels=json.dumps(category_labels),
                           category_values=json.dumps(category_values),
                           low_stock_items=low_stock_items,
                           recent_transactions=recent_transactions,
                           most_valuable_customers=most_valuable_customers)

# --- Admin Routes ---
@app.route('/view_users')
@admin_required
def view_users():
    cursor = get_db().cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT id, username, role FROM users")
    users = cursor.fetchall()
    return render_template('view_users.html', users=users)

@app.route('/add_user', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        hashed_password = generate_password_hash(password)
        try:
            conn = get_db()
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
                           (username, hashed_password, role))
            conn.commit()
            flash(f'User {username} added successfully!', 'success')
        except psycopg2.IntegrityError: # FIX: Changed from sqlite3.IntegrityError
            get_db().rollback()
            flash(f'Username {username} already exists.', 'danger')
        return redirect(url_for('view_users'))
    return render_template('add_user.html')

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
    user_to_delete = cursor.fetchone()
    if user_to_delete and user_to_delete['username'] == session['username']:
        flash('You cannot delete your own account.', 'danger')
    else:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        flash('User deleted successfully.', 'success')
    return redirect(url_for('view_users'))

# --- Inventory Routes ---
@app.route('/inventory', defaults={'page': 1})
@app.route('/inventory/page/<int:page>')
@admin_required 
def inventory(page):
    cursor = get_db().cursor(cursor_factory=DictCursor)
    search_query = request.args.get('search', '')
    count_query = "SELECT COUNT(*) AS count FROM products"
    select_query = "SELECT id, name, category, price, stock, to_char(created_on, 'YYYY-MM-DD HH24:MI:SS') AS created_on FROM products"
    params = []
    if search_query:
        search_term = f"%{search_query}%"
        count_query += " WHERE name ILIKE%s"
        select_query += " WHERE name ILIKE%s"
        params.append(search_term)

    per_page = 10
    offset = (page - 1) * per_page
    cursor.execute(count_query, params)
    total_products = cursor.fetchone()['count']
    total_pages = ceil(total_products / per_page) if total_products > 0 else 0
    
    select_query += " ORDER BY id DESC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])
    cursor.execute(select_query, params)
    products = cursor.fetchall()
    
    return render_template('inventory.html', products=products, page=page, total_pages=total_pages, search_query=search_query)

@app.route('/add_product', methods=['POST'])
@admin_required
def add_product():
    try:
        name = request.form['name']
        category = request.form['category']
        price = float(request.form['price'])
        stock = int(request.form['stock'])
        if stock <= 0 or price <= 0:
            flash('Price and stock quantity must be positive numbers.', 'danger')
            return redirect(url_for('inventory'))
        
        conn = get_db()
        cursor = conn.cursor(cursor_factory=DictCursor)
        cursor.execute(
            'INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)',
            (name, category, price, stock)
        )
        conn.commit()
        flash(f"Product '{name}' added successfully!", 'success')
    except (KeyError, ValueError):
        flash('Invalid form data submitted. Please check all fields.', 'danger')
    return redirect(url_for('inventory'))

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_product(id):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=DictCursor)
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        stock = request.form['stock']
        cursor.execute('UPDATE products SET name = %s, category = %s, price = %s, stock = %s WHERE id = %s', (name, category, price, stock, id))
        conn.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('inventory'))
    cursor.execute("SELECT * FROM products WHERE id = %s", (id,))
    product = cursor.fetchone()
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('inventory'))
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:id>')
@admin_required
def delete_product(id):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("DELETE FROM products WHERE id = %s", (id,))
    conn.commit()
    flash('Product deleted successfully.', 'info')
    return redirect(url_for('inventory'))

# --- Sales & Reporting Routes ---

@app.route('/sales_report')
@login_required
def sales_report():
    cursor = get_db().cursor(cursor_factory=DictCursor)
    page = request.args.get('page', 1, type=int)
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    search_query = request.args.get('search', '')
    invoices, total_invoices, total_pages, summary = [], 0, 0, {"total_revenue": 0, "total_invoices": 0, "total_items_sold": 0}

    if start_date or end_date or search_query:
        where_clauses, params = [], []

        # --- CORRECTED & SIMPLIFIED DATE LOGIC ---
        if start_date:
            where_clauses.append("i.created_on::date >= %s")
            params.append(start_date)
        if end_date:
            where_clauses.append("i.created_on::date <= %s")
            params.append(end_date)
        # --- END OF LOGIC ---

        if search_query:
            search_term = f"%{search_query}%"
            where_clauses.append("(i.customer_name ILIKE %s OR i.cashier_username ILIKE %s)")
            params.extend([search_term, search_term])

        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        count_query = f"SELECT COUNT(i.id) AS count FROM invoices i {where_sql}"
        cursor.execute(count_query, params)
        total_invoices = cursor.fetchone()['count']

        if total_invoices > 0:
            per_page = 10
            total_pages = ceil(total_invoices / per_page)
            offset = (page - 1) * per_page

            select_query = f"""
                SELECT i.id, i.customer_name, i.payment_mode, i.total_amount, 
                       to_char(i.created_on, 'YYYY-MM-DD HH24:MI:SS') AS created_on, 
                       i.cashier_username, 
                       (SELECT SUM(quantity) FROM invoice_items WHERE invoice_id = i.id) as item_count 
                FROM invoices i {where_sql} ORDER BY i.created_on DESC LIMIT %s OFFSET %s
            """
            cursor.execute(select_query, params + [per_page, offset])
            invoices = cursor.fetchall()

            summary_query = f"SELECT SUM(i.total_amount) AS total_revenue, COUNT(i.id) AS total_invoices FROM invoices i {where_sql}"
            cursor.execute(summary_query, params)
            summary_data = cursor.fetchone()

            items_sold_query = f"SELECT SUM(ii.quantity) AS total_items FROM invoice_items ii JOIN invoices i ON ii.invoice_id = i.id {where_sql}"
            cursor.execute(items_sold_query, params)
            items_sold_data = cursor.fetchone()

            summary = {
                "total_revenue": summary_data['total_revenue'] or 0,
                "total_invoices": summary_data['total_invoices'] or 0,
                "total_items_sold": items_sold_data['total_items'] or 0
            }

    return render_template('sales_report.html', invoices=invoices, summary=summary, total_invoices=total_invoices, page=page, total_pages=total_pages, start_date=start_date, end_date=end_date, search_query=search_query)

# --- Legacy Sales Page ---
@app.route('/sales', defaults={'page': 1}, methods=['GET', 'POST'])
@app.route('/sales/page/<int:page>', methods=['GET', 'POST'])
@login_required
def sales(page):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])
        customer_name = request.form['customer_name']
        payment_mode = request.form['payment_mode']

        cursor.execute("SELECT price, stock FROM products WHERE id = %s", (product_id,))
        product_data = cursor.fetchone()

        if not product_data:
            flash('Invalid product selected.', 'danger')
        elif product_data['stock'] < quantity:
            flash(f"Not enough stock for this product. Only {product_data['stock']} available.", 'danger')
        else:
            price = float(product_data['price'])
            total_price = price * quantity
            cursor.execute('INSERT INTO sales (product_id, quantity, total_price, customer_name, payment_mode) VALUES (%s, %s, %s, %s, %s)', (product_id, quantity, total_price, customer_name, payment_mode))
            new_stock = product_data['stock'] - quantity
            cursor.execute("UPDATE products SET stock = %s WHERE id = %s", (new_stock, product_id))
            conn.commit()
            flash('Sale recorded successfully. Stock updated.', 'success')
        return redirect(url_for('sales'))
    
    cursor.execute("SELECT id, name FROM products")
    products = cursor.fetchall()
    
    search_query = request.args.get('search', '')
    per_page = 10
    offset = (page - 1) * per_page
    
    count_query = "SELECT COUNT(s.id) AS count FROM sales s JOIN products p ON s.product_id = p.id"
    select_query = "SELECT s.id, p.name, s.quantity, s.total_price, s.customer_name, s.payment_mode, to_char(s.created_on, 'YYYY-MM-DD HH24:MI:SS') AS created_on FROM sales s JOIN products p ON s.product_id = p.id"
    params = []
    
    if search_query:
        search_term = f"%{search_query}%"
        where_clause = " WHERE s.customer_name ILIKE%s OR p.name ILIKE%s"
        count_query += where_clause
        select_query += where_clause
        params.extend([search_term, search_term])

    cursor.execute(count_query, params)
    total_sales_records = cursor.fetchone()['count']
    total_pages = ceil(total_sales_records / per_page) if total_sales_records > 0 else 0

    select_query += " ORDER BY s.id DESC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])
    cursor.execute(select_query, params)
    sales_data = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) AS count FROM sales")
    total_sales = cursor.fetchone()['count']
    cursor.execute("SELECT SUM(total_price) AS total FROM sales")
    total_revenue = cursor.fetchone()['total'] or 0.0
    cursor.execute('SELECT p.name, SUM(s.quantity) as total_qty FROM sales s JOIN products p ON s.product_id = p.id GROUP BY p.name ORDER BY total_qty DESC LIMIT 1')
    top_product_res = cursor.fetchone()
    top_product_name = top_product_res['name'] if top_product_res else "N/A"

    return render_template('sales.html', products=products, sales=sales_data, total_sales=total_sales, total_revenue=total_revenue, top_product=top_product_name, page=page, total_pages=total_pages, search_query=search_query)

@app.route('/export_sales')
@admin_required
def export_sales():
    cursor = get_db().cursor(cursor_factory=DictCursor)
    cursor.execute('SELECT s.id, p.name, s.quantity, s.total_price, s.customer_name, s.payment_mode, s.created_on FROM sales s JOIN products p ON s.product_id = p.id ORDER BY s.id DESC')
    sales_data = cursor.fetchall()

    wb = Workbook()
    ws = wb.active
    ws.title = "Sales Report"
    headers = ['S.No.', 'Product Name', 'Quantity', 'Total Price (₹)', 'Customer Name', 'Payment Mode', 'Timestamp']
    ws.append(headers)
    for i, row in enumerate(sales_data, start=1):
        # This is the changed line:
        formatted_timestamp = row['created_on'].strftime('%Y-%m-%d %H:%M:%S')
        ws.append([i, row['name'], row['quantity'], float(row['total_price']), row['customer_name'], row['payment_mode'], formatted_timestamp])

    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)
    return send_file(file_stream, as_attachment=True, download_name='sales_report.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/sales/edit/<int:sale_id>', methods=['GET', 'POST'])
@admin_required
def edit_sale(sale_id):
    conn = get_db()
    c = conn.cursor(cursor_factory=DictCursor)

    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        quantity = int(request.form['quantity'])
        customer_name = request.form['customer_name']
        payment_mode = request.form['payment_mode']
        c.execute("SELECT price FROM products WHERE id = %s", (product_id,))
        result = c.fetchone()
        if result:
            price = result['price']
            total_price = float(price) * quantity
            c.execute("UPDATE sales SET product_id = %s, quantity = %s, total_price = %s, customer_name = %s, payment_mode = %s WHERE id = %s", (product_id, quantity, total_price, customer_name, payment_mode, sale_id))
            conn.commit()
            flash('Sale updated successfully!', 'success')
        return redirect(url_for('sales'))

    c.execute("SELECT * FROM sales WHERE id = %s", (sale_id,))
    sale = c.fetchone()
    c.execute("SELECT id, name FROM products")
    products = c.fetchall()
    return render_template('edit_sale.html', sale=sale, products=products)

@app.route('/sales/delete/<int:sale_id>', methods=['POST'])
@admin_required
def delete_sale(sale_id):
    conn = get_db()
    c = conn.cursor(cursor_factory=DictCursor)
    c.execute("DELETE FROM sales WHERE id = %s", (sale_id,))
    conn.commit()
    flash('Sale record deleted successfully.', 'info')
    return redirect(url_for('sales'))

# --- Billing & Checkout Routes ---
@app.route('/billing')
@login_required
def billing():
    cursor = get_db().cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT id, name, category, price, stock FROM products WHERE stock > 0 ORDER BY name")
    products = cursor.fetchall()
    return render_template('billing.html', products=products)

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    form_data = request.form
    customer_name = form_data.get('customer_name')
    payment_mode = form_data.get('payment_mode')
    if not customer_name or not customer_name.strip():
        flash('Customer name is a mandatory field.', 'danger')
        return redirect(url_for('billing'))
    
    try:
        cart = json.loads(form_data.get('cart_data', '{}'))
    except json.JSONDecodeError:
        flash('There was an error processing your cart. Please try again.', 'danger')
        return redirect(url_for('billing'))

    if not cart:
        flash('Cannot process an empty cart.', 'danger')
        return redirect(url_for('billing'))

    conn = get_db()
    cursor = conn.cursor(cursor_factory=DictCursor)

    try:
        total_amount = 0
        for product_id, item in cart.items():
            cursor.execute("SELECT stock, price FROM products WHERE id = %s", (product_id,))
            product_in_db = cursor.fetchone()
            if not product_in_db or product_in_db['stock'] < item['quantity']:
                flash(f"Not enough stock for {item['name']}. Transaction cancelled.", 'danger')
                conn.rollback()
                return redirect(url_for('billing'))
            total_amount += float(product_in_db['price']) * item['quantity'] # FIX: Cast Decimal to float

        TAX_RATE = 0.18
        final_total_with_tax = total_amount * (1 + TAX_RATE)
        
        # FIX: Changed from lastrowid to RETURNING id
        cursor.execute('INSERT INTO invoices (customer_name, payment_mode, total_amount, cashier_username) VALUES (%s, %s, %s, %s) RETURNING id', 
                       (customer_name, payment_mode, final_total_with_tax, session['username']))
        invoice_id = cursor.fetchone()['id']
        
        for product_id, item in cart.items():
            cursor.execute("SELECT price FROM products WHERE id = %s", (product_id,))
            price_at_sale = cursor.fetchone()['price']
            line_total = float(price_at_sale) * item['quantity'] # FIX: Cast Decimal to float
            cursor.execute('INSERT INTO invoice_items (invoice_id, product_id, quantity, price_at_sale, line_total) VALUES (%s, %s, %s, %s, %s)', 
                           (invoice_id, product_id, item['quantity'], price_at_sale, line_total))
            
            cursor.execute("UPDATE products SET stock = stock - %s WHERE id = %s", (item['quantity'], product_id))
            
            cursor.execute('INSERT INTO sales (product_id, quantity, total_price, customer_name, payment_mode) VALUES (%s, %s, %s, %s, %s)', 
                           (product_id, item['quantity'], line_total, customer_name, payment_mode))
        
        conn.commit()
        flash(f'Invoice #{invoice_id} created successfully! Sales history updated.', 'success')
        return redirect(url_for('receipt', invoice_id=invoice_id))
        
    except psycopg2.Error as e: # FIX: Changed from sqlite3.Error
        conn.rollback()
        flash(f'A database error occurred: {e}. Transaction cancelled.', 'danger')
        return redirect(url_for('billing'))

@app.route('/receipt/<int:invoice_id>')
@login_required
def receipt(invoice_id):
    cursor = get_db().cursor(cursor_factory=DictCursor)

    cursor.execute("""
        SELECT *,
               to_char(created_on, 'YYYY-MM-DD') AS formatted_date,
               to_char(created_on, 'HH12:MI:SS PM') AS formatted_time
        FROM invoices WHERE id = %s
    """, (invoice_id,))

    invoice = cursor.fetchone()
    if not invoice:
        flash('Invoice not found.', 'danger')
        return redirect(url_for('dashboard'))

    cursor.execute('SELECT p.name, ii.quantity, ii.price_at_sale, ii.line_total FROM invoice_items ii JOIN products p ON ii.product_id = p.id WHERE ii.invoice_id = %s', (invoice_id,))
    items = cursor.fetchall()

    total_amount = float(invoice['total_amount'])
    subtotal = total_amount / 1.18
    cgst_amount = subtotal * 0.09
    sgst_amount = subtotal * 0.09


    return render_template('receipt.html', 
                           invoice=invoice, 
                           items=items,
                           subtotal=subtotal,
                           cgst_amount=cgst_amount,
                           sgst_amount=sgst_amount,
                           invoice_date=invoice['formatted_date'],
                           invoice_time=invoice['formatted_time'])

if __name__ == '__main__':
    app.run(debug=True)
