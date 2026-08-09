import sqlite3

DB_NAME = "tracker.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_expenses_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            method TEXT,
            note TEXT,
            reimbursed REAL NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def add_expense(expense_date, category, amount, method, note, reimbursed=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (date, category, amount, method, note, reimbursed) VALUES (?, ?, ?, ?, ?, ?)",
        (expense_date, category, amount, method, note, reimbursed)
    )
    conn.commit()
    conn.close()


def get_expense(expense_id):
    """Fetch a single expense by id - used to pre-fill the edit form.
    Row shape: (id, date, category, amount, method, note, reimbursed)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, date, category, amount, method, note, reimbursed FROM expenses WHERE id=?",
        (expense_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return row


def view_expenses(start_date=None, end_date=None):
    """If start_date and end_date are given, only returns expenses in that range
    (inclusive). Leave both blank to get everything. This one function covers
    day (start == end), week, month, or any custom range.
    Row shape: (id, date, category, amount, method, note, reimbursed)."""
    conn = get_connection()
    cursor = conn.cursor()
    if start_date and end_date:
        cursor.execute(
            "SELECT id, date, category, amount, method, note, reimbursed FROM expenses "
            "WHERE date BETWEEN ? AND ? ORDER BY date",
            (start_date, end_date)
        )
    else:
        cursor.execute(
            "SELECT id, date, category, amount, method, note, reimbursed FROM expenses ORDER BY date"
        )
    rows = cursor.fetchall()
    conn.close()
    return rows


def edit_expense(expense_id, date, category, amount, method, note, reimbursed=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE expenses SET date=?, category=?, amount=?, method=?, note=?, reimbursed=? WHERE id=?",
        (date, category, amount, method, note, reimbursed, expense_id)
    )
    conn.commit()
    conn.close()


def delete_expense(expense_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id=?", (expense_id,))
    conn.commit()
    conn.close()


def get_total_expenses(start_date=None, end_date=None):
    """Raw total - the full amount that actually left your account,
    unaffected by reimbursements. Used for account balances and general
    reporting where you want to match your bank statement exactly."""
    conn = get_connection()
    cursor = conn.cursor()
    if start_date and end_date:
        cursor.execute(
            "SELECT SUM(amount) FROM expenses WHERE date BETWEEN ? AND ?",
            (start_date, end_date)
        )
    else:
        cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0]
    conn.close()
    return total if total else 0


def get_total_expenses_net(start_date=None, end_date=None):
    """Total minus whatever's marked as reimbursed on each entry - this is
    what actually counts against a budget, since money you got back isn't
    really money you spent."""
    conn = get_connection()
    cursor = conn.cursor()
    if start_date and end_date:
        cursor.execute(
            "SELECT SUM(amount - reimbursed) FROM expenses WHERE date BETWEEN ? AND ?",
            (start_date, end_date)
        )
    else:
        cursor.execute("SELECT SUM(amount - reimbursed) FROM expenses")
    total = cursor.fetchone()[0]
    conn.close()
    return total if total else 0


def get_total_by_category(start_date=None, end_date=None):
    conn = get_connection()
    cursor = conn.cursor()
    if start_date and end_date:
        cursor.execute(
            "SELECT category, SUM(amount) FROM expenses "
            "WHERE date BETWEEN ? AND ? GROUP BY category ORDER BY category",
            (start_date, end_date)
        )
    else:
        cursor.execute(
            "SELECT category, SUM(amount) FROM expenses GROUP BY category ORDER BY category"
        )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_total_by_method(start_date=None, end_date=None):
    conn = get_connection()
    cursor = conn.cursor()
    if start_date and end_date:
        cursor.execute(
            "SELECT method, SUM(amount) FROM expenses "
            "WHERE date BETWEEN ? AND ? GROUP BY method ORDER BY method",
            (start_date, end_date)
        )
    else:
        cursor.execute(
            "SELECT method, SUM(amount) FROM expenses GROUP BY method ORDER BY method"
        )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_total_for_method(method_name, start_date=None, end_date=None):
    """Total expenses for one specific method - used by accounts.py to
    calculate a running account balance."""
    conn = get_connection()
    cursor = conn.cursor()
    if start_date and end_date:
        cursor.execute(
            "SELECT SUM(amount) FROM expenses WHERE method=? AND date BETWEEN ? AND ?",
            (method_name, start_date, end_date)
        )
    else:
        cursor.execute("SELECT SUM(amount) FROM expenses WHERE method=?", (method_name,))
    total = cursor.fetchone()[0]
    conn.close()
    return total if total else 0
