import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tracker.db")

EVENT_COLORS = [
    "#D8C3A5", "#E8B4BC", "#B8D4C4", "#C9D6E3", "#E3D1C4", "#D6C9E3",
    "#F0D9A8", "#C9E3D6", "#D6E3C9", "#E3C9D6",
]


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_events_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            color TEXT NOT NULL,
            start_date TEXT,
            end_date TEXT,
            budget REAL,
            notes TEXT
        )
    """)
    try:
        cursor.execute("ALTER TABLE events ADD COLUMN budget REAL")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE events ADD COLUMN notes TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


def apply_band_tagging(event_id):
    """Retroactively tags any pre-existing, untagged transaction that falls
    inside this event's date range - covers transactions logged BEFORE the
    event existed, or before its date range was set/widened."""
    event = get_event(event_id)
    if not event or not event["start_date"] or not event["end_date"]:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE expenses SET event_id = ? WHERE event_id IS NULL AND date BETWEEN ? AND ?",
        (event_id, event["start_date"], event["end_date"]),
    )
    cursor.execute(
        "UPDATE earnings SET event_id = ? WHERE event_id IS NULL AND date BETWEEN ? AND ?",
        (event_id, event["start_date"], event["end_date"]),
    )
    conn.commit()
    conn.close()


def add_event(name, color, start_date=None, end_date=None, budget=None, notes=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO events (name, color, start_date, end_date, budget, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (name, color, start_date or None, end_date or None, budget, notes or None),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    apply_band_tagging(new_id)
    return new_id


def edit_event(event_id, name, color, start_date=None, end_date=None, budget=None, notes=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE events SET name = ?, color = ?, start_date = ?, end_date = ?, budget = ?, notes = ? WHERE id = ?",
        (name, color, start_date or None, end_date or None, budget, notes or None, event_id),
    )
    conn.commit()
    conn.close()
    apply_band_tagging(event_id)


def delete_event(event_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE expenses SET event_id = NULL WHERE event_id = ?", (event_id,))
    cursor.execute("UPDATE earnings SET event_id = NULL WHERE event_id = ?", (event_id,))
    cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()


def get_event(event_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_events():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY start_date DESC, id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_band_map(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM events
        WHERE start_date IS NOT NULL AND end_date IS NOT NULL
        AND start_date <= ? AND end_date >= ?
        """,
        (end_date, start_date),
    )
    events = [dict(r) for r in cursor.fetchall()]
    conn.close()

    result = {}
    for e in events:
        d = max(e["start_date"], start_date)
        stop = min(e["end_date"], end_date)
        from datetime import date, timedelta
        cur = date.fromisoformat(d)
        stop_d = date.fromisoformat(stop)
        while cur <= stop_d:
            result[str(cur)] = e
            cur += timedelta(days=1)
    return result


def get_tag_map(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT expenses.date AS date, events.* FROM expenses
        JOIN events ON events.id = expenses.event_id
        WHERE expenses.date BETWEEN ? AND ?
        AND (events.start_date IS NULL OR events.end_date IS NULL
             OR expenses.date < events.start_date OR expenses.date > events.end_date)
        """,
        (start_date, end_date),
    )
    rows = [dict(r) for r in cursor.fetchall()]
    cursor.execute(
        """
        SELECT earnings.date AS date, events.* FROM earnings
        JOIN events ON events.id = earnings.event_id
        WHERE earnings.date BETWEEN ? AND ?
        AND (events.start_date IS NULL OR events.end_date IS NULL
             OR earnings.date < events.start_date OR earnings.date > events.end_date)
        """,
        (start_date, end_date),
    )
    rows += [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {r["date"]: r for r in rows}


def get_event_for_date(entry_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM events
        WHERE start_date IS NOT NULL AND end_date IS NOT NULL
        AND start_date <= ? AND end_date >= ?
        LIMIT 1
        """,
        (entry_date, entry_date),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def untag_expense(expense_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE expenses SET event_id = NULL WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()


def untag_earning(earning_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE earnings SET event_id = NULL WHERE id = ?", (earning_id,))
    conn.commit()
    conn.close()


def get_transactions_for_event(event_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, date, category, amount, method, note, 'expense' AS kind "
        "FROM expenses WHERE event_id = ?",
        (event_id,),
    )
    expense_rows = [dict(r) for r in cursor.fetchall()]

    cursor.execute(
        "SELECT id, date, category, amount, method, note, 'earning' AS kind "
        "FROM earnings WHERE event_id = ?",
        (event_id,),
    )
    earning_rows = [dict(r) for r in cursor.fetchall()]

    conn.close()
    all_rows = expense_rows + earning_rows
    all_rows.sort(key=lambda r: r["date"])
    return all_rows


def get_event_totals(event_id):
    transactions = get_transactions_for_event(event_id)
    total_expenses = sum(t["amount"] for t in transactions if t["kind"] == "expense")
    total_earnings = sum(t["amount"] for t in transactions if t["kind"] == "earning")
    net = total_expenses - total_earnings

    by_category = {}
    by_method = {}
    for t in transactions:
        if t["kind"] == "expense":
            by_category[t["category"]] = by_category.get(t["category"], 0) + t["amount"]
            by_method[t["method"]] = by_method.get(t["method"], 0) + t["amount"]

    return {
        "total_expenses": total_expenses,
        "total_earnings": total_earnings,
        "net": net,
        "by_category": list(by_category.items()),
        "by_method": list(by_method.items()),
    }


def get_band_total(event_id):
    event = get_event(event_id)
    if not event or not event["start_date"] or not event["end_date"]:
        return 0
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT SUM(amount) FROM expenses WHERE event_id=? AND date BETWEEN ? AND ?",
        (event_id, event["start_date"], event["end_date"]),
    )
    total = cursor.fetchone()[0]
    conn.close()
    return total if total else 0


def get_band_total_earnings(event_id):
    event = get_event(event_id)
    if not event or not event["start_date"] or not event["end_date"]:
        return 0
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT SUM(amount) FROM earnings WHERE event_id=? AND date BETWEEN ? AND ?",
        (event_id, event["start_date"], event["end_date"]),
    )
    total = cursor.fetchone()[0]
    conn.close()
    return total if total else 0


def get_daily_tag_totals(start_date, end_date):
    """{date_str: {event_id: total}} for expense spending tagged to an event,
    per day, within this range - used for per-day hover totals."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT expenses.date AS date, events.id AS event_id, SUM(expenses.amount) AS total
        FROM expenses JOIN events ON events.id = expenses.event_id
        WHERE expenses.date BETWEEN ? AND ?
        GROUP BY expenses.date, events.id
        """,
        (start_date, end_date),
    )
    result = {}
    for row in cursor.fetchall():
        result.setdefault(row["date"], {})[row["event_id"]] = row["total"]
    conn.close()
    return result


def get_daily_tag_totals_earnings(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT earnings.date AS date, events.id AS event_id, SUM(earnings.amount) AS total
        FROM earnings JOIN events ON events.id = earnings.event_id
        WHERE earnings.date BETWEEN ? AND ?
        GROUP BY earnings.date, events.id
        """,
        (start_date, end_date),
    )
    result = {}
    for row in cursor.fetchall():
        result.setdefault(row["date"], {})[row["event_id"]] = row["total"]
    conn.close()
    return result


def get_tag_totals_for_range(start_date, end_date):
    """One event per row, with its total expense spending tagged to it within
    this date range. Used for month/week/day 'tag total' summaries, and for
    per-day hover totals (call with start_date == end_date)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT events.id, events.name, events.color, SUM(expenses.amount) AS total
        FROM expenses JOIN events ON events.id = expenses.event_id
        WHERE expenses.date BETWEEN ? AND ?
        GROUP BY events.id
        """,
        (start_date, end_date),
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_tag_totals_for_range_earnings(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT events.id, events.name, events.color, SUM(earnings.amount) AS total
        FROM earnings JOIN events ON events.id = earnings.event_id
        WHERE earnings.date BETWEEN ? AND ?
        GROUP BY events.id
        """,
        (start_date, end_date),
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows