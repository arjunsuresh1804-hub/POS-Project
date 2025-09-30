import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def show_table_schema(cursor, table_name):
    """Prints the schema for a given table in PostgreSQL."""
    print(f"\n🔍 Schema of '{table_name}' table:")
    # Query the information_schema for column details
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position;
    """, (table_name,))
    
    for col in cursor.fetchall():
        print(f"- {col['column_name']} ({col['data_type']}) {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")

def main():
    """Connects to the PostgreSQL database and prints the schema of all tables."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found in .env file. Please ensure it is set correctly.")
        return

    conn = None
    try:
        conn = psycopg2.connect(db_url)
        # Use DictCursor to access columns by name
        cursor = conn.cursor(cursor_factory=DictCursor)

        # Get all tables in the public schema
        print("📂 Tables in the database:")
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = [row['table_name'] for row in cursor.fetchall()]
        for table in tables:
            print(f"- {table}")
        
        # Show the schema for each table found
        for table in tables:
            show_table_schema(cursor, table)

        cursor.close()

    except psycopg2.OperationalError as e:
        print(f"❌ Could not connect to the database: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()