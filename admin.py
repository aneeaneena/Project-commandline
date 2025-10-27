import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from tabulate import tabulate


# ---------- DATABASE CONNECTION ----------
def get_db():
    """Connect to PostgreSQL database."""
    return psycopg2.connect(
        host="localhost",      # change to your host
        database="society_db", # change to your db name
        user="postgres",       # change to your username
        password="admin",      # change to your password
        port=5432
    )


# ---------- HELPER FUNCTIONS ----------
def execute_query(query, params=None, fetch=False, many=False):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        if many:
            cur.executemany(query, params)
        else:
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


# ---------- ADMIN SEED DATA ----------
def seed_admin():
    """Insert or update admin credentials."""
    query = """
        INSERT INTO admins (username, password)
        VALUES (%s, %s)
        ON CONFLICT (username)
        DO UPDATE SET password = EXCLUDED.password;
    """
    execute_query(query, ("admin", "admin123"))


def seed_staff():
    staff = [
        ("delivery1", "pass123", "delivery"),
        ("maintenance1", "pass456", "maintenance"),
        ("maintenance2", "pass890", "maintenance"),
        ("maintenance5", "pass234", "maintenance"),
        ("security1", "pass789", "security")
    ]
    query = """
        INSERT INTO staff (username, password, role)
        VALUES (%s, %s, %s)
        ON CONFLICT (username) DO NOTHING;
    """
    execute_query(query, staff, many=True)


# ---------- ADMIN LOGIN ----------
def admin_login():
    print("\n--- Admin Login ---")
    u = input("Enter admin username: ").strip()
    p = input("Enter admin password: ").strip()
    query = "SELECT * FROM admins WHERE username=%s AND password=%s;"
    admin = execute_query(query, (u, p), fetch=True)
    if admin:
        print("✅ Login successful.")
        return admin[0]
    print("❌ Invalid admin credentials.")
    return None


# ---------- RESIDENT APPROVAL ----------
def list_pending_residents():
    print("\n👥 Pending Residents:")
    query = "SELECT * FROM residents WHERE approved IS NOT TRUE;"
    rows = execute_query(query, fetch=True)

    if not rows:
        print("✅ No pending residents.")
        return

    for r in rows:
        print(f"""
        🆔 ID: {r['resident_id']}
        👤 Name: {r['name']}
        🏠 Flat No: {r['flat_no']}
        📞 Phone: {r['phone']}
        🎂 Age: {r['age']}
        👨‍👩‍👧 Members in Flat: {r['number_of_members']}
        🚻 Gender: {r['gender']}
        🏷️ Designation: {r['designation']}
        """)


def approve_resident_by_id(resident_id):
    query = "UPDATE residents SET approved = TRUE WHERE resident_id = %s;"
    execute_query(query, (resident_id,))
    print(f"✅ Approved resident {resident_id}")


# ---------- COMMON TASKS ----------
def assign_common_task():
    print("\n--- Assign Common Society Task ---")
    task_name = input("Enter task name: ")
    description = input("Enter task description: ")
    staff_name = input("Assign to staff name: ")

    query = """
        INSERT INTO maintenance_tasks (task_name, description, assigned_to, status, created_at, is_common)
        VALUES (%s, %s, %s, %s, %s, %s);
    """
    execute_query(query, (task_name, description, staff_name, "Pending",
                          datetime.now().strftime("%Y-%m-%d %H:%M:%S"), True))
    print(f"✅ Common task '{task_name}' assigned to {staff_name} successfully!\n")


# ---------- POLLS ----------
def create_poll():
    print("\n🗳️ Create Poll")
    question = input("Enter the poll question: ").strip()
    options = [o.strip() for o in input("Enter options (comma separated): ").split(",") if o.strip()]

    query = """
        INSERT INTO polls (question, options, status, created_at)
        VALUES (%s, %s, %s, %s);
    """
    execute_query(query, (question, options, "open", datetime.utcnow()))
    print("✅ Poll created.")


def delete_all_polls():
    confirm = input("⚠️ Are you sure you want to delete ALL polls? (yes/no): ")
    if confirm.lower() == "yes":
        execute_query("DELETE FROM polls;")
        print("🗑️ Deleted all polls successfully.")
    else:
        print("❌ Cancelled. Polls were not deleted.")


# ---------- AMENITY BOOKINGS ----------
def list_pending_bookings():
    print("\n📅 Pending Amenity Bookings:")
    query = "SELECT * FROM amenity_bookings WHERE status='pending';"
    rows = execute_query(query, fetch=True)

    if not rows:
        print("✅ No pending bookings.")
        return

    for b in rows:
        print(f"- id:{b['id']} | amenity:{b['amenity']} | date:{b['date']} {b['time']} | resident:{b['resident_id']}")


def decide_booking():
    list_pending_bookings()
    bid = input("Enter booking id: ").strip()
    decision = input("Approve or Reject (a/r): ").strip().lower()
    if decision not in ("a", "r"):
        print("❌ Invalid choice.")
        return
    status = "approved" if decision == "a" else "rejected"
    query = "UPDATE amenity_bookings SET status=%s WHERE id=%s;"
    execute_query(query, (status, bid))
    print("✅ Booking status updated.")


# ---------- COMPLAINT MANAGEMENT ----------
def view_and_assign_complaints():
    while True:
        print("\n=== Complaint Management Menu ===")
        print("1. View and Assign Complaints")
        print("2. Remove a Task")
        print("3. Back to Admin Menu")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            complaints = execute_query("SELECT * FROM complaints;", fetch=True)
            if not complaints:
                print("⚠️ No complaints found.")
                continue

            table = []
            for idx, c in enumerate(complaints, 1):
                table.append([idx, c['flat_no'], c['category'], c['description'], c['status']])
            print(tabulate(table, headers=["No.", "Flat No", "Category", "Description", "Status"], tablefmt="grid"))

            choice = input("\nEnter complaint number to assign (or 'q' to cancel): ").strip()
            if choice.lower() == 'q':
                continue

            idx = int(choice) - 1
            if idx < 0 or idx >= len(complaints):
                print("⚠️ Invalid choice.")
                continue

            selected_complaint = complaints[idx]
            assigned_to = input("👷 Assign to (staff username): ").strip()
            due_date = input("📅 Due Date (YYYY-MM-DD): ").strip()

            query_task = """
                INSERT INTO maintenance_tasks (flat_no, issue, assigned_to, status, created_at, due_date, source_complaint_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
            execute_query(query_task, (
                selected_complaint['flat_no'], selected_complaint['description'],
                assigned_to, "Pending", datetime.utcnow(), due_date, selected_complaint['id']
            ))

            execute_query("UPDATE complaints SET status='Assigned' WHERE id=%s;", (selected_complaint['id'],))
            print("✅ Task assigned.\n")

        elif choice == "2":
            tasks = execute_query("SELECT * FROM maintenance_tasks;", fetch=True)
            if not tasks:
                print("⚠️ No tasks found to remove.")
                continue

            table = [[i + 1, t['id'], t['flat_no'], t['issue'], t['assigned_to'], t['status']] for i, t in enumerate(tasks)]
            print(tabulate(table, headers=["No.", "Task ID", "Flat No", "Issue", "Assigned To", "Status"], tablefmt="grid"))

            choice = input("\nEnter task number to remove (or 'q' to cancel): ").strip()
            if choice.lower() == 'q':
                continue
            idx = int(choice) - 1
            if idx < 0 or idx >= len(tasks):
                print("⚠️ Invalid choice.")
                continue

            task_to_remove = tasks[idx]
            execute_query("DELETE FROM maintenance_tasks WHERE id=%s;", (task_to_remove['id'],))
            print("🗑️ Task removed successfully.\n")

        elif choice == "3":
            print("🔙 Returning to Admin Menu...")
            break
        else:
            print("⚠️ Invalid option, try again.")


# ---------- ANNOUNCEMENTS ----------
def post_announcement():
    print("\n📢 Post Announcement")
    msg = input("Message: ").strip()
    execute_query("INSERT INTO announcements (message, created_at) VALUES (%s, %s);", (msg, datetime.utcnow()))
    print("✅ Announcement posted.")


def delete_announcement():
    print("\n🗑️ Delete an Announcement by ID")
    announcements = execute_query("SELECT * FROM announcements ORDER BY created_at DESC LIMIT 10;", fetch=True)
    if not announcements:
        print("No announcements to delete.")
        return
    for a in announcements:
        print(f"- ID: {a['id']} | Message: {a['message']}")
    ann_id = input("\nEnter the ID to delete: ").strip()
    execute_query("DELETE FROM announcements WHERE id=%s;", (ann_id,))
    print("✅ Announcement deleted.")


# ---------- SKIP DELIVERY ----------
def view_skips_by_date():
    d = input("Enter date (YYYY-MM-DD) or leave blank for today: ").strip() or datetime.now().strftime("%Y-%m-%d")
    svc = input("Service (milk/water/newspaper): ").strip().lower()
    print(f"\n🚚 Skips for {svc} on {d}:")
    query = "SELECT flat_no FROM skip_delivery WHERE skip_date=%s AND item=%s;"
    skips = execute_query(query, (d, svc), fetch=True)
    if skips:
        for s in skips:
            print(f"- Flat {s['flat_no']}")
    else:
        print("✅ No skips.")


# ---------- POLL SUMMARY ----------
def view_poll_summary():
    polls = execute_query("SELECT * FROM polls;", fetch=True)
    if not polls:
        print("\n📊 No polls found.")
        return
    print("\n📊 === Poll Summary ===")
    for poll in polls:
        print(f"\n🗳️ Question: {poll['question']}")
        print(f" Options: {poll['options']}")


# ---------- MAIN MENU ----------
def admin_menu():
    seed_admin()
    seed_staff()
    while True:
        print("\n=== Admin Menu ===")
        print("1. List pending residents")
        print("2. Approve resident by ID")
        print("3. Assign common task")
        print("4. Create poll")
        print("5. Delete all polls")
        print("6. List pending amenity bookings")
        print("7. Decide booking (approve/reject)")
        print("8. View and Assign maintenance task")
        print("9. Post announcement")
        print("10. Delete announcements")
        print("11. View skips by date/service")
        print("12. View poll summary")
        print("13. Back")

        ch = input("Choose: ").strip()
        if ch == "1": list_pending_residents()
        elif ch == "2": approve_resident_by_id(input("Resident ID: ").strip())
        elif ch == "3": assign_common_task()
        elif ch == "4": create_poll()
        elif ch == "5": delete_all_polls()
        elif ch == "6": list_pending_bookings()
        elif ch == "7": decide_booking()
        elif ch == "8": view_and_assign_complaints()
        elif ch == "9": post_announcement()
        elif ch == "10": delete_announcement()
        elif ch == "11": view_skips_by_date()
        elif ch == "12": view_poll_summary()
        elif ch == "13": break
        else: print("Invalid choice.")
