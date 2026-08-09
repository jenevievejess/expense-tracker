import sqlite3

DB_NAME = "tracker.db"

CURRENCY_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CNY": "¥",
    "IDR": "Rp", "SGD": "S$", "MYR": "RM", "HKD": "HK$", "AUD": "A$",
    "INR": "₹", "KRW": "₩",
}


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_settings_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_setting(key, default=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default


def set_setting(key, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, value))
    conn.commit()
    conn.close()


def get_currency_code():
    return get_setting("currency", "USD")


def get_currency_symbol():
    return CURRENCY_SYMBOLS.get(get_currency_code(), "$")


def set_currency(code):
    set_setting("currency", code)
