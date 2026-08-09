import sqlite3

DB_NAME = "tracker.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def search_expenses(query):
    """Searches expenses only - by note, category, or method."""
    conn = get_connection()
    cursor = conn.cursor()
    like = f"%{query}%"
    cursor.execute("""
        SELECT id, date, category, amount, method, note FROM expenses
        WHERE note LIKE ? OR category LIKE ? OR method LIKE ?
        ORDER BY date DESC
    """, (like, like, like))
    rows = cursor.fetchall()
    conn.close()
    return rows


def search_earnings(query):
    """Searches earnings only - by note, category, or method."""
    conn = get_connection()
    cursor = conn.cursor()
    like = f"%{query}%"
    cursor.execute("""
        SELECT id, date, category, amount, method, note FROM earnings
        WHERE note LIKE ? OR category LIKE ? OR method LIKE ?
        ORDER BY date DESC
    """, (like, like, like))
    rows = cursor.fetchall()
    conn.close()
    return rows
