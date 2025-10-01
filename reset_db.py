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
        role TEXT DEFAULT 'user',
        session_token TEXT NULL  
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

print("Inserting default admin user...")
hashed_admin_pass = generate_password_hash('admin123')

# Manually insert the Root Admin with ID 1000
cursor.execute("INSERT INTO users (id, username, password, role) VALUES (%s, %s, %s, %s)", 
               (1000, 'Admin', hashed_admin_pass, 'admin'))

# Set the NEXT user ID to start from 1001
cursor.execute("ALTER SEQUENCE users_id_seq RESTART WITH 1001;")

print("Inserting New Refined International Menu...")

# --- French Cuisine ---
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Escargots de Bourgogne', 'Appetizer', 950.00, 40))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Seared Foie Gras with Fig Jam', 'Appetizer', 1200.00, 30))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Duck Confit with Cherry Sauce', 'Main Dish', 1850.00, 35))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Sole Meunière', 'Main Dish', 1750.00, 30))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Lobster Thermidor', 'Main Dish', 2500.00, 25))

# --- British Cuisine ---
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Scotch Egg with Piccalilli', 'Appetizer', 750.00, 50))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Potted Shrimp with Melba Toast', 'Appetizer', 800.00, 45))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Beef Wellington', 'Main Dish', 2100.00, 25))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Pan-Seared Scallops with Black Pudding', 'Main Dish', 1900.00, 30))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Roasted Lamb Rack with Mint Jus', 'Main Dish', 2000.00, 30))

# --- Italian Cuisine ---
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Beef Carpaccio with Arugula & Parmesan', 'Appetizer', 900.00, 40))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Fried Zucchini Flowers with Truffle', 'Appetizer', 850.00, 35))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Osso Buco with Saffron Risotto', 'Main Dish', 1950.00, 30))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Cacio e Pepe with Fresh Truffles', 'Main Dish', 1600.00, 40))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Saltimbocca alla Romana', 'Main Dish', 1700.00, 35))

# --- Mexican Cuisine ---
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Scallop Aguachile with Serrano', 'Appetizer', 880.00, 35))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Duck Carnitas Tacos', 'Appetizer', 820.00, 40))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Mole Poblano with Roasted Chicken', 'Main Dish', 1750.00, 35))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Chile en Nogada', 'Main Dish', 1800.00, 30))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Pescado a la Veracruzana', 'Main Dish', 1650.00, 35))

# --- Indian Cuisine ---
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Galouti Kebab', 'Appetizer', 850.00, 45))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Amritsari Macchi', 'Appetizer', 780.00, 50))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Nalli Nihari (Lamb Shank Curry)', 'Main Dish', 1900.00, 30))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Malabar Prawn Curry', 'Main Dish', 1700.00, 35))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Dum Pukht Biryani', 'Main Dish', 1600.00, 40))

# --- Mocktails (Beverages) ---
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Rosemary Blueberry Smash', 'Beverage', 480.00, 55))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Spicy Mango Tango', 'Beverage', 420.00, 70))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Virgin Cucumber Gimlet', 'Beverage', 450.00, 60))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Grapefruit and Thyme Spritzer', 'Beverage', 400.00, 65))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Passion Fruit No-jito', 'Beverage', 460.00, 60))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Lavender Lemonade', 'Beverage', 430.00, 70))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Ginger-Pear Fizz', 'Beverage', 470.00, 60))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Hibiscus Iced Tea Sparkler', 'Beverage', 390.00, 80))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Watermelon-Mint Cooler', 'Beverage', 410.00, 75))
cursor.execute("INSERT INTO products (name, category, price, stock) VALUES (%s, %s, %s, %s)", ('Blackberry & Sage Soda', 'Beverage', 490.00, 55))

conn.commit()
cursor.close()
conn.close()

print("\n✅ PostgreSQL reset script is ready!")
print("   The next step is to configure Render and deploy.")