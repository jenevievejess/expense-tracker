import sqlite3
import calendar
from datetime import date

from expenses import add_expense
from earnings import add_earning

DB_NAME = "tracker.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_recurring_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recurring (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            method TEXT NOT NULL,
            note TEXT,
            day_of_month INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            last_generated TEXT,
            active INTEGER NOT NULL DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()


def add_recurring(entry_type, category, amount, method, note, day_of_month, start_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO recurring (type, category, amount, method, note, day_of_month, start_date, last_generated, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, NULL, 1)
    """, (entry_type, category, amount, method, note, day_of_month, start_date))
    conn.commit()
    conn.close()


def view_recurring():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recurring ORDER BY day_of_month")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recurring(recurring_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recurring WHERE id=?", (recurring_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def edit_recurring(recurring_id, category, amount, method, note, day_of_month):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE recurring SET category=?, amount=?, method=?, note=?, day_of_month=? WHERE id=?
    """, (category, amount, method, note, day_of_month, recurring_id))
    conn.commit()
    conn.close()


def set_active(recurring_id, active):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE recurring SET active=? WHERE id=?", (int(active), recurring_id))
    conn.commit()
    conn.close()


def delete_recurring(recurring_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recurring WHERE id=?", (recurring_id,))
    conn.commit()
    conn.close()


def _add_months(y, m, delta):
    total = (y * 12 + (m - 1)) + delta
    return total // 12, total % 12 + 1


def generate_due():
    """Checks every active recurring entry and creates the real expense/
    earning rows for any month that's due (from where it last left off,
    through today), then remembers where it stopped so it never duplicates.
    Safe to call on every page load - does nothing if nothing is due."""
    today = date.today()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recurring WHERE active=1")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    for r in rows:
        start = date.fromisoformat(r["start_date"])
        if r["last_generated"]:
            last = date.fromisoformat(r["last_generated"])
            y, m = _add_months(last.year, last.month, 1)
        else:
            y, m = start.year, start.month

        last_generated_date = r["last_generated"]

        while True:
            last_day_of_month = calendar.monthrange(y, m)[1]
            day = min(r["day_of_month"], last_day_of_month)
            occurrence = date(y, m, day)

            if occurrence > today:
                break
            if occurrence < start:
                y, m = _add_months(y, m, 1)
                continue

            if r["type"] == "expense":
                add_expense(str(occurrence), r["category"], r["amount"], r["method"], r["note"] or "")
            else:
                add_earning(str(occurrence), r["category"], r["amount"], r["method"], r["note"] or "")

            last_generated_date = str(occurrence)
            y, m = _add_months(y, m, 1)

        if last_generated_date != r["last_generated"]:
            conn2 = get_connection()
            cursor2 = conn2.cursor()
            cursor2.execute("UPDATE recurring SET last_generated=? WHERE id=?", (last_generated_date, r["id"]))
            conn2.commit()
            conn2.close()
