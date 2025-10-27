import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date


# ---------- DATABASE CONNECTION ----------
def get_db():
    """Connect to PostgreSQL database."""
    return psycopg2.connect(
        host="localhost",      # change this to your host
        database="society_db", # change this to your DB name
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


# ---------- VIEW TODAY'S DELIVERY ----------
def view_todays_delivery(service_type):
    today = str(date.today())

    # Get skipped flats for today
    query_skips = "SELECT flat_no FROM skip_delivery WHERE skip_date=%s AND item=%s;"
    skipped = execute_query(query_skips, (today, service_type), fetch=True)
    skipped_flats = [s['flat_no'] for s in skipped] if skipped else []

    # Get approved residents
    query_residents = "SELECT flat_no, name FROM residents WHERE approved=TRUE;"
    residents = execute_query(query_residents, fetch=True)

    print(f"\n📦 Delivery list for {service_type} - {today}:")
    for res in residents:
        if res['flat_no'] not in skipped_flats:
            print(f"Flat {res['flat_no']} - {res['name']}")
    if not skipped_flats:
        print("✅ No skips today!")


# ---------- VIEW SKIPPED DELIVERIES ----------
def view_skipped_deliveries(service_type):
    today = str(date.today())
    query_skips = "SELECT flat_no FROM skip_delivery WHERE skip_date=%s AND item=%s;"
    skips = execute_query(query_skips, (today, service_type), fetch=True)

    print(f"\n📌 Skipped {service_type} deliveries for {today}:")
    if not skips:
        print("✅ No skips today.")
    else:
        for s in skips:
            print(f"Flat {s['flat_no']}")


# ---------- DELIVERY MENU ----------
def delivery_menu(username):
    while True:
        print("\n--- Delivery Staff Menu ---")
        print("1. View today's full delivery list")
        print("2. View skipped deliveries")
        print("3. Logout")

        choice = input("Enter choice: ")

        if choice == "1":
            service = input("Enter service (milk/water/newspaper): ")
            view_todays_delivery(service)

        elif choice == "2":
            service = input("Enter service (milk/water/newspaper): ")
            view_skipped_deliveries(service)

        elif choice == "3":
            print("Logging out...")
            break

        else:
            print("❌ Invalid choice. Try again.")
