import sqlite3

DB_NAME = "tracker.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_earnings_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS earnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            method TEXT,
            note TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_earning(earning_date, category, amount, method, note):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO earnings (date, category, amount, method, note) VALUES (?, ?, ?, ?, ?)",
        (earning_date, category, amount, method, note)
    )
    conn.commit()
    conn.close()


def get_earning(earning_id):
    """Fetch a single earning by id - used to pre-fill the edit form."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, date, category, amount, method, note FROM earnings WHERE id=?",
        (earning_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return row


def view_earnings(start_date=None, end_date=None):
    conn = get_connection()
    cursor = conn.cursor()
    if start_date and end_date:
        cursor.execute(
            "SELECT id, date, category, amount, method, note FROM earnings "
            "WHERE date BETWEEN ? AND ? ORDER BY date",
            (start_date, end_date)
        )
    else:
        cursor.execute(
            "SELECT id, date, category, amount, method, note FROM earnings ORDER BY date"
        )
    rows = cursor.fetchall()
    conn.close()
    return rows


def edit_earning(earning_id, date, category, amount, method, note):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE earnings SET date=?, category=?, amount=?, method=?, note=? WHERE id=?",
        (date, category, amount, method, note, earning_id)
    )
    conn.commit()
    conn.close()


def delete_earning(earning_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM earnings WHERE id=?", (earning_id,))
    conn.commit()
    conn.close()


def get_total_earnings(start_date=None, end_date=None):
    conn = get_connection()
    cursor = conn.cursor()
    if start_date and end_date:
        cursor.execute(
            "SELECT SUM(amount) FROM earnings WHERE date BETWEEN ? AND ?",
            (start_date, end_date)
        )
    else:
        cursor.execute("SELECT SUM(amount) FROM earnings")
    total = cursor.fetchone()[0]
    conn.close()
    return total if total else 0


def get_total_by_category(start_date=None, end_date=None):
    conn = get_connection()
    cursor = conn.cursor()
    if start_date and end_date:
        cursor.execute(
            "SELECT category, SUM(amount) FROM earnings "
            "WHERE date BETWEEN ? AND ? GROUP BY category ORDER BY category",
            (start_date, end_date)
        )
    else:
        cursor.execute(
            "SELECT category, SUM(amount) FROM earnings GROUP BY category ORDER BY category"
        )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_total_by_method(start_date=None, end_date=None):
    conn = get_connection()
    cursor = conn.cursor()
    if start_date and end_date:
        cursor.execute(
            "SELECT method, SUM(amount) FROM earnings "
            "WHERE date BETWEEN ? AND ? GROUP BY method ORDER BY method",
            (start_date, end_date)
        )
    else:
        cursor.execute(
            "SELECT method, SUM(amount) FROM earnings GROUP BY method ORDER BY method"
        )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_total_for_method(method_name, start_date=None, end_date=None):
    """Total earnings for one specific method - used by accounts.py to
    calculate a running account balance."""
    conn = get_connection()
    cursor = conn.cursor()
    if start_date and end_date:
        cursor.execute(
            "SELECT SUM(amount) FROM earnings WHERE method=? AND date BETWEEN ? AND ?",
            (method_name, start_date, end_date)
        )
    else:
        cursor.execute("SELECT SUM(amount) FROM earnings WHERE method=?", (method_name,))
    total = cursor.fetchone()[0]
    conn.close()
    return total if total else 0
