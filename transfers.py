import sqlite3

DB_NAME = "tracker.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_transfers_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            from_method TEXT NOT NULL,
            to_method TEXT NOT NULL,
            amount REAL NOT NULL,
            note TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_transfer(transfer_date, from_method, to_method, amount, note):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transfers (date, from_method, to_method, amount, note) VALUES (?, ?, ?, ?, ?)",
        (transfer_date, from_method, to_method, amount, note)
    )
    conn.commit()
    conn.close()


def view_transfers(start_date=None, end_date=None):
    conn = get_connection()
    cursor = conn.cursor()
    if start_date and end_date:
        cursor.execute(
            "SELECT id, date, from_method, to_method, amount, note FROM transfers "
            "WHERE date BETWEEN ? AND ? ORDER BY date DESC",
            (start_date, end_date)
        )
    else:
        cursor.execute(
            "SELECT id, date, from_method, to_method, amount, note FROM transfers ORDER BY date DESC"
        )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_transfer(transfer_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, date, from_method, to_method, amount, note FROM transfers WHERE id=?",
        (transfer_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return row


def edit_transfer(transfer_id, transfer_date, from_method, to_method, amount, note):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE transfers SET date=?, from_method=?, to_method=?, amount=?, note=? WHERE id=?",
        (transfer_date, from_method, to_method, amount, note, transfer_id)
    )
    conn.commit()
    conn.close()


def delete_transfer(transfer_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transfers WHERE id=?", (transfer_id,))
    conn.commit()
    conn.close()


def get_transfers_in_total(method_name, start_date=None, end_date=None):
    """Sum of transfers received INTO this method."""
    conn = get_connection()
    cursor = conn.cursor()
    if start_date and end_date:
        cursor.execute(
            "SELECT SUM(amount) FROM transfers WHERE to_method=? AND date BETWEEN ? AND ?",
            (method_name, start_date, end_date)
        )
    else:
        cursor.execute("SELECT SUM(amount) FROM transfers WHERE to_method=?", (method_name,))
    total = cursor.fetchone()[0]
    conn.close()
    return total if total else 0


def get_transfers_out_total(method_name, start_date=None, end_date=None):
    """Sum of transfers sent OUT of this method."""
    conn = get_connection()
    cursor = conn.cursor()
    if start_date and end_date:
        cursor.execute(
            "SELECT SUM(amount) FROM transfers WHERE from_method=? AND date BETWEEN ? AND ?",
            (method_name, start_date, end_date)
        )
    else:
        cursor.execute("SELECT SUM(amount) FROM transfers WHERE from_method=?", (method_name,))
    total = cursor.fetchone()[0]
    conn.close()
    return total if total else 0
