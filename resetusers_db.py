import sqlite3
from werkzeug.security import generate_password_hash # Add this import

DB_NAME = 'POS.db'

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

print("Dropping existing tables...")
cursor.execute("DROP TABLE IF EXISTS users")
# --- Recreate core tables ---
print("Recreating users tables...")
# Recreate users table
cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user'
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

conn.commit()
conn.close()

print("\n✅ Database reset successfully!")
print("   Run your Flask app now.")