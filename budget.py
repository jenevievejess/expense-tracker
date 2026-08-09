import sqlite3
import calendar
from datetime import date as _date
from expenses import get_total_expenses, get_total_expenses_net, get_total_by_category, get_total_by_method

DB_NAME = "tracker.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_budget_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget_periods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            amount REAL NOT NULL,
            rollover INTEGER NOT NULL DEFAULT 0,
            label TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            UNIQUE(period_id, type, name),
            FOREIGN KEY (period_id) REFERENCES budget_periods(id)
        )
    """)
    conn.commit()
    conn.close()


# ---------- Periods ----------

def add_period(start_date, end_date, amount, rollover=False, label=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO budget_periods (start_date, end_date, amount, rollover, label) VALUES (?, ?, ?, ?, ?)",
        (start_date, end_date, amount, int(rollover), label)
    )
    conn.commit()
    period_id = cursor.lastrowid
    conn.close()
    return period_id


def edit_period(period_id, start_date, end_date, amount, rollover, label=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE budget_periods SET start_date=?, end_date=?, amount=?, rollover=?, label=? WHERE id=?",
        (start_date, end_date, amount, int(rollover), label, period_id)
    )
    conn.commit()
    conn.close()


def delete_period(period_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM budget_allocations WHERE period_id=?", (period_id,))
    cursor.execute("DELETE FROM budget_periods WHERE id=?", (period_id,))
    conn.commit()
    conn.close()


def get_period(period_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM budget_periods WHERE id=?", (period_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_periods():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM budget_periods ORDER BY start_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def find_period_by_dates(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM budget_periods WHERE start_date=? AND end_date=?",
        (start_date, end_date)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_previous_period(start_date):
    """Finds the most recent period that ended before this one starts -
    used for rollover calculations."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM budget_periods WHERE end_date < ? ORDER BY end_date DESC LIMIT 1",
        (start_date,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_current_period():
    """Finds whichever budget period's date range includes today, if any -
    used for the Home page's 'current period remaining' card."""
    today = str(_date.today())
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM budget_periods WHERE start_date <= ? AND end_date >= ? "
        "ORDER BY start_date DESC LIMIT 1",
        (today, today)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------- Allocations (budget by category / by method) ----------

def set_allocation(period_id, alloc_type, name, amount):
    """alloc_type is 'category' or 'method'. Calling this again for the same
    period+type+name updates the amount instead of creating a duplicate."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO budget_allocations (period_id, type, name, amount) VALUES (?, ?, ?, ?)
        ON CONFLICT(period_id, type, name) DO UPDATE SET amount=excluded.amount
    """, (period_id, alloc_type, name, amount))
    conn.commit()
    conn.close()


def get_allocations(period_id, alloc_type):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, amount FROM budget_allocations WHERE period_id=? AND type=? ORDER BY name",
        (period_id, alloc_type)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_allocation(allocation_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM budget_allocations WHERE id=?", (allocation_id,))
    conn.commit()
    conn.close()


def get_allocation_progress(period_id, alloc_type):
    """Compares each budgeted category/method against actual expense spending
    in that period. Returns a list of dicts: name, budgeted, spent, remaining."""
    period = get_period(period_id)
    if not period:
        return []

    allocations = get_allocations(period_id, alloc_type)

    if alloc_type == "category":
        spent_rows = get_total_by_category(period["start_date"], period["end_date"])
    else:
        spent_rows = get_total_by_method(period["start_date"], period["end_date"])

    spent_map = {name: total for name, total in spent_rows}

    progress = []
    for alloc in allocations:
        spent = spent_map.get(alloc["name"], 0)
        progress.append({
            "name": alloc["name"],
            "budgeted": alloc["amount"],
            "spent": spent,
            "remaining": alloc["amount"] - spent
        })
    return progress


# ---------- Remaining budget calculations ----------

def get_remaining_for_period(period_id):
    """budget for this period - net expenses (reimbursed amounts excluded),
    plus leftover rolled forward from the previous period if rollover is
    enabled. Earnings don't factor in - a budget is a spending cap, not a
    net balance (that's what Accounts is for)."""
    period = get_period(period_id)
    if not period:
        return 0

    total_expenses = get_total_expenses_net(period["start_date"], period["end_date"])
    remaining = period["amount"] - total_expenses

    if period["rollover"]:
        prev = get_previous_period(period["start_date"])
        if prev:
            remaining += get_remaining_for_period(prev["id"])

    return remaining


def get_all_time_remaining():
    """Sum of every period's budget, minus all-time net expenses. Rollover
    doesn't need special handling here since every period's amount is only
    counted once."""
    periods = get_all_periods()
    total_budgeted = sum(p["amount"] for p in periods)
    return total_budgeted - get_total_expenses_net()


# ---------- Helpers ----------

def calendar_month_range(period_str):
    """'2026-08' -> ('2026-08-01', '2026-08-31')"""
    year, month = map(int, period_str.split("-"))
    last_day = calendar.monthrange(year, month)[1]
    return f"{period_str}-01", f"{period_str}-{last_day:02d}"


# ---------- Legacy calendar-month helpers ----------

def set_month_budget(period_str, amount):
    """Convenience wrapper for the terminal app: sets/updates a budget for a
    whole calendar month, e.g. set_month_budget('2026-08', 1000)."""
    start, end = calendar_month_range(period_str)
    existing = find_period_by_dates(start, end)
    if existing:
        edit_period(existing["id"], start, end, amount, existing["rollover"], period_str)
        return existing["id"]
    return add_period(start, end, amount, rollover=False, label=period_str)


def get_month_remaining(period_str):
    """Convenience wrapper: remaining budget for a whole calendar month."""
    start, end = calendar_month_range(period_str)
    existing = find_period_by_dates(start, end)
    if not existing:
        return 0 - get_total_expenses_net(start, end)
    return get_remaining_for_period(existing["id"])
