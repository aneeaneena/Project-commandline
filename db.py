import psycopg2
from psycopg2.extras import RealDictCursor

def get_db():
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host="localhost",         # change this to your PostgreSQL host
            database="society_db",    # change this to your database name
            user="postgres",          # change this to your username
            password="admin",         # change this to your password
            port=5432                 # default PostgreSQL port
        )
        return conn
    except Exception as e:
        print("❌ Error connecting to PostgreSQL:", e)
        return None
