import psycopg2
from psycopg2.extras import RealDictCursor



def get_db():
    """Connect to PostgreSQL database."""
    return psycopg2.connect(
        host="localhost",      
        database="society_db", 
        user="postgres",       
        password="admin",      
        port=5432
    )



def execute_query(query, params=None, fetch=False):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(query, params)
        if fetch:
            data = cur.fetchall()
        else:
            data = None
        conn.commit()
        return data
    finally:
        cur.close()
        conn.close()



def register_staff():
    print("\n--- Staff Registration ---")
    username = input("Enter staff username: ").strip()
    password = input("Enter password: ").strip()
    role = input("Enter role (delivery/maintenance/security): ").strip().lower()

    valid_roles = {"delivery", "maintenance", "security"}
    if role not in valid_roles:
        print("⚠️ Invalid role. Choose from: delivery, maintenance, or security.")
        return

   
    query_check = "SELECT * FROM staff WHERE username = %s;"
    existing = execute_query(query_check, (username,), fetch=True)
    if existing:
        print("⚠️ Username already exists. Try again.")
        return

    
    query_insert = """
        INSERT INTO staff (username, password, role, approved)
        VALUES (%s, %s, %s, %s);
    """
    execute_query(query_insert, (username, password, role, False))
    print(f"✅ Registered successfully: {username} ({role})\n⏳ Awaiting admin approval.")



def staff_login():
    print("\n--- Staff Login ---")
    username = input("Enter staff username: ").strip()
    password = input("Enter staff password: ").strip()

    query = "SELECT * FROM staff WHERE username = %s AND password = %s;"
    staff = execute_query(query, (username, password), fetch=True)

    if staff:
        staff_member = staff[0]
        if not staff_member.get("approved", False):
            print("⏳ Your account is not yet approved by admin.")
            return None

        print(f"✅ Login successful! Welcome {staff_member['username']} ({staff_member['role']})")
        return staff_member
    else:
        print("❌ Invalid credentials. Try again.")
        return None
