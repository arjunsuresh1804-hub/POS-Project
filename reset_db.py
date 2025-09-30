import os
import psycopg2
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# This line loads the DATABASE_URL from your .env file
load_dotenv()

DB_URL = os.environ.get('DATABASE_URL')
if not DB_URL:
    raise Exception("DATABASE_URL is not set in the .env file.")

conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

print("Dropping existing tables...")
# Use CASCADE to handle dependencies (foreign keys)
cursor.execute("DROP TABLE IF EXISTS invoice_items, invoices, sales, products, users CASCADE;")

print("Recreating all tables for PostgreSQL...")

# Use SERIAL PRIMARY KEY for auto-incrementing IDs in PostgreSQL
cursor.execute('''
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user'
    )
''')

# Use NUMERIC for prices and TIMESTAMPTZ for timezone-aware timestamps
cursor.execute('''
    CREATE TABLE products (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        price NUMERIC(10, 2) NOT NULL,
        stock INTEGER NOT NULL,
        created_on TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE invoices (
        id SERIAL PRIMARY KEY,
        customer_name TEXT,
        payment_mode TEXT NOT NULL,
        total_amount NUMERIC(10, 2) NOT NULL,
        created_on TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        cashier_username TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE invoice_items (
        id SERIAL PRIMARY KEY,
        invoice_id INTEGER NOT NULL REFERENCES invoices(id),
        product_id INTEGER NOT NULL REFERENCES products(id),
        quantity INTEGER NOT NULL,
        price_at_sale NUMERIC(10, 2) NOT NULL,
        line_total NUMERIC(10, 2) NOT NULL
    )
''')

# Legacy sales table
cursor.execute('''
    CREATE TABLE sales (
        id SERIAL PRIMARY KEY,
        product_id INTEGER NOT NULL REFERENCES products(id),
        quantity INTEGER NOT NULL,
        total_price NUMERIC(10, 2),
        customer_name TEXT,
        payment_mode TEXT,
        created_on TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    )
''')

print("Inserting default admin user and sample products...")
hashed_admin_pass = generate_password_hash('admin123')
# Note: psycopg2 uses %s for placeholders, not ?
cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", ('admin', hashed_admin_pass, 'admin'))

print("Inserting Existing Menu...")
# Beverages
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Matcha Latte', 'Beverage', 180.00, 60))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Hojicha Latte', 'Beverage', 170.00, 55))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Sakura Cappuccino', 'Beverage', 200.00, 40))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Kyoto Cold Brew', 'Beverage', 220.00, 50))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Royal Milk Tea', 'Beverage', 160.00, 70))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Yuzu Lemonade Sparkler', 'Beverage', 140.00, 65))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Azuki Red Bean Frappé', 'Beverage', 210.00, 45))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Brown Sugar Bubble Latte', 'Beverage', 190.00, 50))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Genmaicha Tea', 'Beverage', 130.00, 80))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Ume Plum Iced Tea', 'Beverage', 150.00, 60))

# Food
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Onigiri Trio', 'Food', 120.00, 40))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Tamago Sando', 'Food', 110.00, 50))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Katsu Sando', 'Food', 180.00, 35))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Teriyaki Chicken Don', 'Food', 250.00, 30))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Miso Soup Set', 'Food', 90.00, 60))

# Desserts
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Mochi Ice Cream', 'Dessert', 130.00, 70))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Dorayaki Pancakes', 'Dessert', 100.00, 55))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Matcha Cheesecake', 'Dessert', 220.00, 40))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Taiyaki', 'Dessert', 120.00, 50))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Kuro Goma Parfait', 'Dessert', 200.00, 45))

conn.commit()
cursor.close()
conn.close()

print("\n✅ PostgreSQL reset script is ready!")
print("   The next step is to configure Render and deploy.")