import sqlite3

def show_table_schema(cursor, table_name):
    print(f"\n🔍 Schema of '{table_name}' table:")
    cursor.execute(f"PRAGMA table_info({table_name})")
    for col in cursor.fetchall():
        print(f"- {col[1]} ({col[2]}){' PRIMARY KEY' if col[5] else ''}")

def main():
    conn = sqlite3.connect('POS.db')
    cursor = conn.cursor()

    # Show tables
    print("📂 Tables in POS.db:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        print(f"- {table}")

    # Show schema of 'products' table
    if 'products' in tables:
        show_table_schema(cursor, 'products')

    # Show schema of 'users' table
    if 'users' in tables:
        show_table_schema(cursor, 'users')
    # Show schema of 'sales' table
    if 'sales' in tables:
        show_table_schema(cursor, 'sales')    
        

    conn.close()

if __name__ == "__main__":
    main()
