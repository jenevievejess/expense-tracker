import sqlite3
from datetime import date

from expenses import get_total_for_method as get_expense_total_for_method
from earnings import get_total_for_method as get_earning_total_for_method
from transfers import get_transfers_in_total, get_transfers_out_total

DB_NAME = "tracker.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_accounts_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            method_name TEXT NOT NULL UNIQUE,
            starting_balance REAL NOT NULL,
            start_date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def set_account_balance(method_name, starting_balance, start_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO accounts (method_name, starting_balance, start_date) VALUES (?, ?, ?)
        ON CONFLICT(method_name) DO UPDATE SET starting_balance=excluded.starting_balance, start_date=excluded.start_date
    """, (method_name, starting_balance, start_date))
    conn.commit()
    conn.close()


def get_account(method_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE method_name=?", (method_name,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_accounts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts ORDER BY method_name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_account(method_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM accounts WHERE method_name=?", (method_name,))
    conn.commit()
    conn.close()


def get_balance_as_of(method_name, as_of_date):
    """Balance at the end of a specific date - starting balance + activity
    from the account's start_date through as_of_date (inclusive)."""
    account = get_account(method_name)
    if not account:
        return None

    start_date = account["start_date"]
    earnings = get_earning_total_for_method(method_name, start_date, as_of_date)
    expenses = get_expense_total_for_method(method_name, start_date, as_of_date)
    transfers_in = get_transfers_in_total(method_name, start_date, as_of_date)
    transfers_out = get_transfers_out_total(method_name, start_date, as_of_date)

    return account["starting_balance"] + earnings - expenses + transfers_in - transfers_out


def get_balance(method_name):
    """Current balance, as of today."""
    return get_balance_as_of(method_name, str(date.today()))


def get_total_balance():
    """Sum of every configured account's current balance."""
    accounts = get_all_accounts()
    return sum(get_balance(a["method_name"]) for a in accounts)


def get_account_dates(method_name, start_date):
    """Every distinct date (>= start_date) with any activity - expense,
    earning, or transfer - involving this method, most recent first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date FROM expenses WHERE method=? AND date>=?
        UNION
        SELECT date FROM earnings WHERE method=? AND date>=?
        UNION
        SELECT date FROM transfers WHERE (from_method=? OR to_method=?) AND date>=?
        ORDER BY date DESC
    """, (method_name, start_date, method_name, start_date, method_name, method_name, start_date))
    rows = [r[0] for r in cursor.fetchall()]
    conn.close()
    return rows


def get_account_activity_for_date(method_name, date_str):
    """Every transaction touching this method on a specific date, shaped so
    it can render with the same category+method bubble format used in
    Expenses/Earnings. For transfers, 'category' becomes 'Transfer' and
    'method' becomes whichever account is on the other side."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    activity = []

    cursor.execute("SELECT id, category, amount, note FROM expenses WHERE method=? AND date=?", (method_name, date_str))
    for row in cursor.fetchall():
        activity.append({"type": "expense", "category": row["category"], "method": method_name, "note": row["note"], "amount": -row["amount"]})

    cursor.execute("SELECT id, category, amount, note FROM earnings WHERE method=? AND date=?", (method_name, date_str))
    for row in cursor.fetchall():
        activity.append({"type": "earning", "category": row["category"], "method": method_name, "note": row["note"], "amount": row["amount"]})

    cursor.execute(
        "SELECT id, from_method, to_method, amount, note FROM transfers WHERE (from_method=? OR to_method=?) AND date=?",
        (method_name, method_name, date_str)
    )
    for row in cursor.fetchall():
        if row["from_method"] == method_name:
            activity.append({"type": "transfer", "category": "Transfer", "method": row["to_method"], "note": row["note"], "amount": -row["amount"]})
        else:
            activity.append({"type": "transfer", "category": "Transfer", "method": row["from_method"], "note": row["note"], "amount": row["amount"]})

    conn.close()
    return activity
