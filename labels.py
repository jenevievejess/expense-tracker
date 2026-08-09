import sqlite3

DB_NAME = "tracker.db"

CATEGORY_COLORS = ["#6B8E6F", "#C77B6B", "#D9A441", "#8E6B9E", "#4A7A8C", "#B5533C"]
METHOD_COLORS = ["#D8C3A5", "#E8B4BC", "#B8D4C4", "#C9D6E3", "#E3D1C4", "#D6C9E3"]


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_labels_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            color TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_label(label_type, name, color=None):
    conn = get_connection()
    cursor = conn.cursor()
    if color is None:
        color = CATEGORY_COLORS[0] if label_type == "category" else METHOD_COLORS[0]
    cursor.execute(
        "INSERT INTO labels (type, name, color) VALUES (?, ?, ?)",
        (label_type, name, color)
    )
    conn.commit()
    conn.close()


def add_category(name, color=None):
    add_label("category", name, color)


def add_method(name, color=None):
    add_label("method", name, color)


def view_labels(label_type):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, color FROM labels WHERE type=?", (label_type,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_label(label_id):
    """Fetch a single label (id, type, name, color) - used for the edit form."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, type, name, color FROM labels WHERE id=?", (label_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def view_categories():
    return view_labels("category")


def view_methods():
    return view_labels("method")


def get_category_colors():
    """{name: color} lookup - used to color the bubbles in entry lists."""
    return {name: color for id, name, color in view_categories()}


def get_method_colors():
    return {name: color for id, name, color in view_methods()}


def edit_label(label_id, new_name, new_color=None):
    conn = get_connection()
    cursor = conn.cursor()
    if new_color is not None:
        cursor.execute("UPDATE labels SET name=?, color=? WHERE id=?", (new_name, new_color, label_id))
    else:
        cursor.execute("UPDATE labels SET name=? WHERE id=?", (new_name, label_id))
    conn.commit()
    conn.close()


def delete_label(label_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM labels WHERE id=?", (label_id,))
    conn.commit()
    conn.close()
