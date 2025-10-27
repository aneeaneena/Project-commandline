import sys
from datetime import datetime, date
from db import get_db
from aminity import book_amenity, select_amenity
import psycopg2
from psycopg2.extras import RealDictCursor
from admin import approve_resident_by_id, admin_login, admin_menu
from staff import staff_login, register_staff
from maintainance import maintenance_menu, view_maintenance_tasks, update_task_status
from deliver_service import delivery_menu, view_todays_delivery
from resident import (
    register_resident,
    login_resident,
    raise_complaint,
    skip_delivery,
    participate_poll,
    view_my_complaints,
    view_announcements
)


# ---------- MAIN MENU ----------
def main_menu():
    while True:
        print("\n=== Main Menu ===")
        print("1. Resident Register")
        print("2. Resident Login")
        print("3. Staff Login")
        print("4. Staff Registration")
        print("5. Admin Login")
        print("6. Exit")

        choice = input("Choose an option (1-6): ")

        if choice == "1":
            register_flow()
        elif choice == "2":
            login_flow()
        elif choice == "3":
            staff = staff_login()
            if staff:
                role = staff.get("role")
                if role == "delivery":
                    delivery_menu(staff["username"])
                elif role == "maintenance":
                    maintenance_menu(staff["username"])
                elif role == "security":
                    print("🔒 Security module not implemented yet.")
                else:
                    print("⚠️ Unknown staff role.")
        elif choice == "4":
            register_staff()
        elif choice == "5":
            if admin_login():
                admin_menu()
        elif choice == "6":
            print("Exiting the system.")
            sys.exit()
        else:
            print("Invalid option. Please try again.")


# ---------- RESIDENT FLOWS ----------
def register_flow():
    print("\n🧾 Resident Registration")
    register_resident()
    print("✅ Registration complete. Please wait for admin approval.")


def login_flow():
    flat_no = input("Enter your flat number: ")
    resident_id = input("Enter your resident ID: ")

    resident = login_resident(flat_no, resident_id)
    if resident:
        print("✅ Login successful. You can now access the system.")
        resident_menu(flat_no, resident_id)
    else:
        print("❌ Login failed. Please check your credentials or wait for approval.")


def resident_menu(flat_no, resident_id):
    while True:
        print("\n--- Resident Menu ---")
        print("1. Raise Complaint")
        print("2. Skip Delivery")
        print("3. View My Complaints")
        print("4. Book Amenity")
        print("5. Participate in Poll")
        print("6. View Announcements")
        print("7. Log Out")

        option = input("Choose an option (1-7): ")

        if option == "1":
            complaint_flow(flat_no)
        elif option == "2":
            skip_delivery_flow(flat_no)
        elif option == "3":
            view_my_complaints(flat_no)
        elif option == "4":
            book_amenity_flow(resident_id)
        elif option == "5":
            participate_poll(flat_no)
        elif option == "6":
            view_announcements()
        elif option == "7":
            print("Logged out successfully.")
            break
        else:
            print("Invalid option. Please try again.")


def complaint_flow(logged_in_flat_no):
    while True:
        entered_flat_no = input("Enter the flat number for complaint: ").strip()
        if entered_flat_no != logged_in_flat_no:
            print(f"❌ Entered flat number '{entered_flat_no}' does not match your logged-in flat number '{logged_in_flat_no}'.")
            retry = input("Do you want to try again? (yes/no): ").strip().lower()
            if retry != "yes":
                print("Exiting complaint submission.")
                return
        else:
            category = input("Enter complaint category: ")
            description = input("Enter complaint description: ")
            complaint_date = input("Enter the complaint date (YYYY-MM-DD): ")
            raise_complaint(logged_in_flat_no, entered_flat_no, category, description, complaint_date)
            break


# ---------- ADMIN APPROVAL ----------
def admin_approval_flow():
    rid = input("Enter resident ID to approve: ")
    approve_resident_by_id(rid)
    print("Resident approved successfully.")


# ---------- DELIVERY SKIP ----------
def skip_delivery_flow(logged_in_flat_no=None):
    print("\n--- Skip Delivery ---")

    if not logged_in_flat_no:
        print("❌ Error: Logged-in flat number is required.")
        return

    while True:
        entered_flat_no = input("Confirm your flat number to skip delivery: ").strip()
        item = input("Enter the item to skip (milk/water/gas): ").strip()
        if not item:
            print("❌ Error: Item cannot be empty.")
            continue

        skip_date_str = input("Enter the date to skip (YYYY-MM-DD): ").strip()

        result = skip_delivery(
            logged_in_flat_no,
            entered_flat_no,
            item,
            skip_date_str
        )

        if result:
            print(f"✅ Delivery for '{item}' skipped on {skip_date_str}.")
            break
        else:
            retry = input("Do you want to try again? (yes/no): ").strip().lower()
            if retry != "yes":
                print("Exiting skip delivery process.")
                break


# ---------- AMENITY BOOKING ----------
def book_amenity_flow(resident_id):
    amenity = select_amenity()
    if not amenity:
        return

    booking_date = input("Enter booking date (YYYY-MM-DD): ").strip()
    booking_time = input("Enter booking time (e.g., 5PM or 17:00): ").strip()
    book_amenity(resident_id, amenity, booking_date, booking_time)
    print(f"✅ Amenity '{amenity}' booked for {booking_date} at {booking_time}.")


# ---------- DEFAULT AMENITIES (POSTGRESQL) ----------
def add_amenities():
    amenities = [
        ("Clubhouse",),
        ("Tennis Court",),
        ("Gym",)
    ]

    conn = get_db()
    cur = conn.cursor()
    try:
        query = "INSERT INTO amenities (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;"
        cur.executemany(query, amenities)
        conn.commit()
        print("✅ Default amenities added.")
    except Exception as e:
        print("❌ Error adding amenities:", e)
    finally:
        cur.close()
        conn.close()


# ---------- STAFF MENUS ----------
def staff_menu(staff_name):
    while True:
        print("\n--- Staff Menu ---")
        print("1. View My Maintenance Tasks")
        print("2. Update Task Status")
        print("3. Logout")

        choice = input("Enter choice: ")
        if choice == "1":
            view_maintenance_tasks(staff_name)
        elif choice == "2":
            task_id = input("Enter Task ID to update: ")
            new_status = input("Enter new status (Pending/In Progress/Completed): ")
            update_task_status(task_id, new_status)
        elif choice == "3":
            break
        else:
            print("❌ Invalid choice, try again.")

def view_skipped_deliveries(service_type):
    """Show all skipped deliveries for today's date."""
    today = str(date.today())

    query = """
        SELECT flat_no, item, skip_date
        FROM skip_delivery
        WHERE skip_date = %s AND item = %s;
    """

    skips = execute_query(query, (today, service_type), fetch=True)

    print(f"\n📌 Skipped {service_type} deliveries for {today}:")

    if not skips or len(skips) == 0:
        print("✅ No skips today.")
    else:
        for s in skips:
            flat_no = s.get("flat_no", "Unknown")
            print(f"🏠 Flat {flat_no}")

def execute_query(query, params=None, fetch=False, many=False):
    """Executes a SQL query safely and returns data if needed."""
    conn = None
    cur = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        if many:
            cur.executemany(query, params)
        else:
            cur.execute(query, params)

        data = None
        if fetch:
            try:
                data = cur.fetchall()
            except psycopg2.ProgrammingError:
                # Happens if query has no result set
                data = None

        conn.commit()
        return data

    except Exception as e:
        print(f"❌ Database Error: {e}")
        if conn:
            conn.rollback()
        return None

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# ---------- DELIVERY & SERVICE STAFF ----------
def delivery_service_menu(staff_name):
    while True:
        print("\n--- Delivery & Service Menu ---")
        print("1. View today’s delivery list")
        print("2. Mark items delivered")
        print("3. View skip requests")
        print("4. View assigned maintenance tasks")
        print("5. Update task status")
        print("6. Logout")

        choice = input("Enter your choice: ")

        if choice == "1":
            service = input("Enter service (milk/water/newspaper): ")
            view_todays_delivery(service)
        elif choice == "2":
           flat = input("Enter flat no: ")
           service = input("Enter service: ")
           print(f"✅ Marked {service} delivered to flat {flat}.")  # temporary message

        elif choice == "3":
         service = input("Enter service: ")
         view_skipped_deliveries(service)

        elif choice == "4":
            view_maintenance_tasks(staff_name)
        elif choice == "5":
            task_id = input("Enter Task ID: ")
            new_status = input("Enter new status (In Progress/Completed): ")
            update_task_status(task_id, new_status)
        elif choice == "6":
            print("Logging out...")
            break
        else:
            print("Invalid choice, try again.")


# ---------- START SYSTEM ----------
if __name__ == "__main__":
    main_menu()
