import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, date
import uuid


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


# ---------- REGISTER RESIDENT ----------
def register_resident():
    def get_non_empty_input(prompt):
        while True:
            value = input(prompt).strip()
            if value:
                return value
            else:
                print("❌ This field is required. Please enter a value.")

    def get_valid_int_input(prompt):
        while True:
            value = input(prompt).strip()
            if value.isdigit():
                return int(value)
            else:
                print("❌ Please enter a valid number.")

    def get_details():
        print("\n📝 Please enter the following details:")
        name = get_non_empty_input("Name: ")
        flat_no = get_non_empty_input("Flat Number: ")
        phone = get_non_empty_input("Phone Number: ")
        age = get_valid_int_input("Age: ")
        number_of_members = get_valid_int_input("Number of Members in Flat: ")
        gender = get_non_empty_input("Gender: ")
        designation = get_non_empty_input("Designation: ")

        return (name, flat_no, phone, age, number_of_members, gender, designation)

    name, flat_no, phone, age, members, gender, designation = get_details()

    resident_id = str(uuid.uuid4())[:8]

    query = """
        INSERT INTO residents (resident_id, name, flat_no, phone, age, number_of_members, gender, designation, approved)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE);
    """
    execute_query(query, (resident_id, name, flat_no, phone, age, members, gender, designation))
    print(f"\n✅ Registered successfully! Your resident ID is: {resident_id}")
    print("⏳ Please wait for admin approval.\n")
    return resident_id


# ---------- LOGIN RESIDENT ----------
def login_resident(flat_no, resident_id):
    query = """
        SELECT * FROM residents
        WHERE flat_no = %s AND resident_id = %s AND approved = TRUE;
    """
    resident = execute_query(query, (flat_no, resident_id), fetch=True)
    if resident:
        print(f"Welcome, {resident[0]['name']}!")
        return resident[0]
    else:
        print("❌ Login failed. Please check credentials or wait for approval.")
        return None


# ---------- RAISE COMPLAINT ----------
def raise_complaint(logged_in_flat_no, entered_flat_no, category, description, complaint_date):
    if entered_flat_no != logged_in_flat_no:
        print("❌ Flat number mismatch.")
        return False

    try:
        complaint_date_obj = datetime.strptime(complaint_date.strip(), "%Y-%m-%d").date()
        today = datetime.today().date()
        if complaint_date_obj != today:
            print(f"❌ Complaint date must be today's date ({today}).")
            return False
    except ValueError:
        print("❌ Invalid date format. Use YYYY-MM-DD.")
        return False

    query = """
        INSERT INTO complaints (flat_no, category, description, date, status)
        VALUES (%s, %s, %s, %s, 'Pending');
    """
    execute_query(query, (entered_flat_no, category, description, complaint_date))
    print("✅ Complaint submitted successfully!")
    return True


# ---------- VIEW MY COMPLAINTS ----------
def view_my_complaints(flat_no):
    query = "SELECT * FROM complaints WHERE flat_no = %s;"
    complaints = execute_query(query, (flat_no,), fetch=True)
    print(f"\n--- Complaints for Flat {flat_no} ---")
    if not complaints:
        print("ℹ️ No complaints found.")
        return
    for c in complaints:
        print(
            f"📅 Date: {c.get('date')} | "
            f"📂 Category: {c.get('category')} | "
            f"📝 Issue: {c.get('description')} | "
            f"⚙️ Status: {c.get('status', 'Pending')}"
        )


# ---------- SKIP DELIVERY ----------
def skip_delivery(logged_in_flat_no, entered_flat_no, item, skip_date):
    if entered_flat_no != logged_in_flat_no:
        print("❌ Entered flat number doesn't match your logged-in flat number.")
        return False

    try:
        skip_date_obj = datetime.strptime(skip_date.strip(), "%Y-%m-%d").date()
        today = datetime.today().date()
        if skip_date_obj <= today:
            print("❌ Skip date must be a future date.")
            return False
    except ValueError:
        print("❌ Invalid date format. Use YYYY-MM-DD.")
        return False

    query = """
        INSERT INTO skip_delivery (flat_no, item, skip_date)
        VALUES (%s, %s, %s);
    """
    execute_query(query, (entered_flat_no, item, skip_date))
    print("✅ Delivery skipped successfully.")
    return True


# ---------- PARTICIPATE IN POLL ----------
def participate_poll(flat_no):
    poll_query = "SELECT * FROM polls WHERE status = 'open' LIMIT 1;"
    polls = execute_query(poll_query, fetch=True)
    if not polls:
        print("ℹ️ No active polls available.")
        return
    poll = polls[0]

    # Check if already voted
    vote_check = "SELECT * FROM votes WHERE flat_no = %s AND poll_id = %s;"
    voted = execute_query(vote_check, (flat_no, poll['id']), fetch=True)
    if voted:
        print("⚠️ You have already voted in this poll.")
        return

    print(f"\n🗳️ Poll: {poll['question']}")
    options = poll['options']
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")

    try:
        choice = int(input("Enter your choice number: "))
        if 1 <= choice <= len(options):
            selected_option = options[choice - 1]

            # Update poll votes
            update_query = f"""
                UPDATE polls SET votes = jsonb_set(votes, '{{{selected_option}}}', 
                (COALESCE(votes->>'{selected_option}','0')::int + 1)::text::jsonb) 
                WHERE id = %s;
            """
            execute_query(update_query, (poll['id'],))

            # Record vote
            insert_vote = "INSERT INTO votes (flat_no, poll_id) VALUES (%s, %s);"
            execute_query(insert_vote, (flat_no, poll['id']))

            print("✅ Your vote has been recorded. Thank you!")
        else:
            print("❌ Invalid choice.")
    except ValueError:
        print("❌ Please enter a valid number.")


# ---------- VIEW ANNOUNCEMENTS ----------
def view_announcements():
    print("\n📢 Announcements")
    query = "SELECT * FROM announcements ORDER BY created_at DESC;"
    announcements = execute_query(query, fetch=True)
    if not announcements:
        print("ℹ️ No announcements available.")
        return
    for a in announcements:
        created_time = a['created_at'].strftime("%Y-%m-%d %H:%M")
        print("\n-------------------------")
        print(f"🕒 Date: {created_time}")
        print(f"📢 Message: {a['message']}")
