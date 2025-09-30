import sqlite3
from werkzeug.security import generate_password_hash

# --- ACTION REQUIRED ---
# 1. DELETE your old 'POS.db' file.
# 2. RUN this script once from your terminal: python reset_db.py
# This will create a new, clean POS.db file with the new table structure.

DB_NAME = 'POS.db'

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

print("Dropping existing tables...")
cursor.execute("DROP TABLE IF EXISTS users")
cursor.execute("DROP TABLE IF EXISTS products")
cursor.execute("DROP TABLE IF EXISTS sales") # Old sales table
cursor.execute("DROP TABLE IF EXISTS invoices") # New
cursor.execute("DROP TABLE IF EXISTS invoice_items") # New

# --- Recreate core tables ---
print("Recreating users and products tables...")
# Recreate users table
cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user'
    )
''')

# Recreate products table
cursor.execute('''
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        price REAL NOT NULL,
        stock INTEGER NOT NULL,
        created_on TEXT DEFAULT CURRENT_TIMESTAMP
    )
''')

# --- Recreate legacy sales table (for historical data) ---
print("Recreating legacy sales table...")
cursor.execute('''
    CREATE TABLE sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        total_price REAL,
        customer_name TEXT,
        payment_mode TEXT,
        created_on TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
''')


# --- NEW: Create invoice tables for multi-item sales ---
print("Creating new invoice tables...")
# This table holds the summary of one entire transaction.
cursor.execute('''
    CREATE TABLE invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        payment_mode TEXT NOT NULL,
        total_amount REAL NOT NULL,
        created_on TEXT DEFAULT CURRENT_TIMESTAMP,
        cashier_username TEXT NOT NULL
    )
''')

# This table holds each individual line item for an invoice.
cursor.execute('''
    CREATE TABLE invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price_at_sale REAL NOT NULL,
        line_total REAL NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
''')


# Insert default admin user
print("Inserting default admin user...")
# Hash the default password
hashed_admin_pass = generate_password_hash('admin123')
cursor.execute('''
    INSERT INTO users (username, password, role)
    VALUES (?, ?, ?)
''', ('admin', hashed_admin_pass, 'admin'))

# Optional: Insert some sample products for testing
print("Inserting Existing Menu...")

cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Matcha Latte', 'Beverage', 180.00, 60))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Hojicha Latte', 'Beverage', 170.00, 55))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Sakura Cappuccino', 'Beverage', 200.00, 40))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Kyoto Cold Brew', 'Beverage', 220.00, 50))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Royal Milk Tea', 'Beverage', 160.00, 70))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Yuzu Lemonade Sparkler', 'Beverage', 140.00, 65))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Azuki Red Bean Frappé', 'Beverage', 210.00, 45))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Brown Sugar Bubble Latte', 'Beverage', 190.00, 50))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Genmaicha Tea', 'Beverage', 130.00, 80))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Ume Plum Iced Tea', 'Beverage', 150.00, 60))

cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Onigiri Trio', 'Food', 120.00, 40))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Tamago Sando', 'Food', 110.00, 50))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Katsu Sando', 'Food', 180.00, 35))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Teriyaki Chicken Don', 'Food', 250.00, 30))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Miso Soup Set', 'Food', 90.00, 60))

cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Mochi Ice Cream', 'Dessert', 130.00, 70))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Dorayaki Pancakes', 'Dessert', 100.00, 55))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Matcha Cheesecake', 'Dessert', 220.00, 40))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Taiyaki', 'Dessert', 120.00, 50))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)", ('Kuro Goma Parfait', 'Dessert', 200.00, 45))


conn.commit()
conn.close()

print("\n✅ Database reset successfully!")
print("   New tables 'invoices' and 'invoice_items' have been created.")
print("   Run your Flask app now.")
