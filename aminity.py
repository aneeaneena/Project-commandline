import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date


# ---------- DATABASE CONNECTION ----------
def get_db():
    """Connect to PostgreSQL database."""
    return psycopg2.connect(
        host="localhost",      # change this to your PostgreSQL host
        database="society_db", # change this to your database name
        user="postgres",       # change this to your username
        password="admin",      # change this to your password
        port=5432
    )


# ---------- HELPER FUNCTION ----------
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


# ---------- AMENITY SELECTION ----------
def select_amenity():
    print("\n📋 Available Amenities:")
    print("1. Clubhouse")
    print("2. Tennis Court")
    print("3. Gym")

    choice = input("Select an amenity by number (1-3): ").strip()

    if choice == "1":
        return "Clubhouse"
    elif choice == "2":
        return "Tennis Court"
    elif choice == "3":
        return "Gym"
    else:
        print("❌ Invalid choice.")
        return None


# ---------- BOOK AMENITY ----------
def book_amenity(resident_id, amenity_name, booking_date_str, booking_time):
    """Book an amenity for a resident."""
    try:
        booking_date = datetime.strptime(booking_date_str, "%Y-%m-%d").date()
        if booking_date < date.today():
            print("⚠️ That date has already passed. Please choose a future date.")
            return
    except ValueError:
        print("❌ Invalid date format. Use YYYY-MM-DD.")
        return

    query = """
        INSERT INTO amenity_bookings (resident_id, amenity, date, time, status)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """
    result = execute_query(query, (resident_id, amenity_name, str(booking_date), booking_time, "pending"), fetch=True)

    if result:
        print(f"✅ {amenity_name} booking request submitted.")
        print(f"🆔 Your Booking ID: {result[0]['id']}")
    else:
        print("⚠️ Failed to create booking.")
