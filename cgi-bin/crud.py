from db import get_db

def get_items(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM items WHERE user_id = ?",
        (user_id,)
    )
    items = cursor.fetchall()
    conn.close()
    return items

def add_item(user_id, name, description, price):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO items (name, description, price, user_id) VALUES (?, ?, ?, ?)",
        (name, description, price, user_id)
    )
    conn.commit()
    conn.close()

def update_item(item_id, user_id, name, description, price):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE items SET name = ?, description = ?, price = ? WHERE id = ? AND user_id = ?",
        (name, description, price, item_id, user_id)
    )
    conn.commit()
    conn.close()

def delete_item(item_id, user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM items WHERE id = ? AND user_id = ?",
        (item_id, user_id)
    )
    conn.commit()
    conn.close()
