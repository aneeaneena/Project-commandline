import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime


# ---------- DATABASE CONNECTION ----------
def get_db():
    """Connect to PostgreSQL database."""
    return psycopg2.connect(
        host="localhost",      # change this to your host
        database="society_db", # change this to your database name
        user="postgres",       # change this to your username
        password="admin",      # change this to your password
        port=5432
    )


# ---------- HELPER FUNCTION ----------
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


# ---------- VIEW COMMON TASKS ----------
def view_common_tasks():
    print("\n--- Common Society Maintenance Tasks ---")
    query = "SELECT * FROM maintenance_tasks WHERE is_common = TRUE;"
    tasks = execute_query(query, fetch=True)
    if not tasks:
        print("No common tasks found.")
        return
    for task in tasks:
        print(f"🛠 Task: {task['task_name']} | Description: {task['description']} | "
              f"Status: {task['status']} | Created At: {task['created_at']}")


# ---------- VIEW TASKS ASSIGNED TO STAFF ----------
def view_assigned_tasks_for_staff(staff_username):
    print(f"\n📋 Tasks assigned to: {staff_username}")
    query = "SELECT * FROM maintenance_tasks WHERE assigned_to = %s;"
    tasks = execute_query(query, (staff_username,), fetch=True)

    if not tasks:
        print("ℹ️ No tasks assigned yet.")
        return

    for task in tasks:
        print("\n-----------------------------")
        print(f"🏢 Flat No     : {task.get('flat_no')}")
        print(f"📝 Issue       : {task.get('issue')}")
        print(f"📅 Due Date    : {task.get('due_date')}")
        print(f"⏱️ Status      : {task.get('status')}")
        print(f"🕒 Created At  : {task.get('created_at')}")

# ---------- VIEW MAINTENANCE TASKS (FOR STAFF) ----------
def view_maintenance_tasks(staff_name):
    """View maintenance tasks assigned to a specific staff member."""
    print(f"\n🧰 Maintenance Tasks assigned to: {staff_name}")
    query = "SELECT * FROM maintenance_tasks WHERE assigned_to = %s;"
    tasks = execute_query(query, (staff_name,), fetch=True)

    if not tasks:
        print("ℹ️ No maintenance tasks found.")
        return

    for task in tasks:
        print("\n-----------------------------")
        print(f"🆔 Task ID     : {task.get('id')}")
        print(f"🏢 Flat No     : {task.get('flat_no')}")
        print(f"📝 Issue       : {task.get('issue')}")
        print(f"📅 Due Date    : {task.get('due_date')}")
        print(f"⚙️ Status      : {task.get('status')}")
        print(f"👷 Assigned To : {task.get('assigned_to')}")
        print(f"🕒 Created At  : {task.get('created_at')}")


# ---------- UPDATE TASK STATUS ----------
def update_task_status(task_id, new_status):
    """Update the status of a maintenance task."""
    query = "UPDATE maintenance_tasks SET status = %s WHERE id = %s;"
    execute_query(query, (new_status, task_id))
    print(f"✅ Task {task_id} updated to status '{new_status}'.")


# ---------- UPDATE COMMON TASK STATUS ----------
def update_common_task_status():
    task_name = input("Enter the task name: ").strip()
    staff_name = input("Enter the staff name: ").strip()
    new_status = input("Enter the new status (Pending/In Progress/Completed): ").strip()

    query = """
        UPDATE maintenance_tasks
        SET status = %s
        WHERE task_name = %s AND assigned_to = %s AND is_common = TRUE;
    """
    execute_query(query, (new_status, task_name, staff_name))
    print(f"✅ Task '{task_name}' updated to {new_status}")


# ---------- VIEW COMPLAINTS BY DATE ----------
def view_complaints(complaint_date):
    query = "SELECT * FROM complaints WHERE date = %s;"
    complaints = execute_query(query, (complaint_date,), fetch=True)
    print(f"\n--- Complaints on {complaint_date} ---")

    if not complaints:
        print("❌ No complaints found on this date.")
        return

    for c in complaints:
        print(f"Flat: {c['flat_no']} | Category: {c['category']} | "
              f"Issue: {c['description']} | Status: {c['status']}")


# ---------- UPDATE COMPLAINT STATUS ----------
def update_complaint_status():
    flat_no = input("Enter Flat No of the complaint: ").strip()
    complaint_date = input("Enter Date of complaint (YYYY-MM-DD): ").strip()

    query_find = "SELECT * FROM complaints WHERE flat_no = %s AND date = %s;"
    complaints = execute_query(query_find, (flat_no, complaint_date), fetch=True)

    if not complaints:
        print("❌ No complaint found for given flat and date.")
        return

    complaint = complaints[0]
    print(f"\nComplaint Found:")
    print(f"Category: {complaint['category']}")
    print(f"Issue: {complaint['description']}")
    print(f"Status: {complaint['status']}")

    new_status = input("Enter new status (Pending / In Progress / Resolved): ").strip()
    query_update = """
        UPDATE complaints
        SET status = %s, updated_at = %s
        WHERE id = %s;
    """
    execute_query(query_update, (new_status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), complaint['id']))
    print(f"✅ Complaint status updated to '{new_status}'")


# ---------- MAIN MENU FOR MAINTENANCE STAFF ----------
def maintenance_menu(staff_name):
    while True:
        print("\n--- Maintenance Staff Menu ---")
        print("1. View Common Tasks")
        print("2. View Assigned Tasks by Admin")
        print("3. View All Complaints (By Date)")
        print("4. Update Complaint Status")
        print("5. Update Common Task Status")
        print("6. Logout")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            view_common_tasks()
        elif choice == "2":
            view_assigned_tasks_for_staff(staff_name)
        elif choice == "3":
            date = input("Enter date (YYYY-MM-DD): ").strip()
            view_complaints(date)
        elif choice == "4":
            update_complaint_status()
        elif choice == "5":
            update_common_task_status()
        elif choice == "6":
            print("Logging out...")
            break
        else:
            print("Invalid choice, try again.")
