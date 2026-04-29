import mysql.connector
from mysql.connector import Error
from urllib.parse import quote

DB_CONFIG = {
    "host": "sql7.freesqldatabase.com",
    "port": 3306,
    "user": "sql7824635",
    "password": "iUz24J2d6E",
    "database": "sql7824635",
    "connection_timeout": 10,
}

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] get_connection failed: {e}")
        raise

# alias
get_conn = get_connection

def _fix_map_url(row):
    """Ensure map_url is a valid URI (encode Thai characters if present)."""
    if not row:
        return row
    url = row.get("map_url") or ""
    if url and "q=" in url:
        base, q = url.split("q=", 1)
        row["map_url"] = base + "q=" + quote(q, safe=",+&:/")
    elif not url:
        row["map_url"] = "https://www.google.com/maps/search/?api=1&query=Tha+Yang+Phetchaburi"
    return row

def search_place(keyword):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM chatbot_place WHERE place_name LIKE %s LIMIT 1",
            (f"%{keyword}%",)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return _fix_map_url(result)
    except Error as e:
        print(f"[DB ERROR] search_place({keyword}): {e}")
        return None

def get_places_by_category(category):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM chatbot_place WHERE category = %s ORDER BY place_id",
            (category,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [_fix_map_url(r) for r in rows]
    except Error as e:
        print(f"[DB ERROR] get_places_by_category({category}): {e}")
        return []

def get_all_place_names():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT place_name FROM chatbot_place ORDER BY place_id")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [r["place_name"] for r in rows]
    except Error as e:
        print(f"[DB ERROR] get_all_place_names: {e}")
        return []

def get_all_restaurants():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM restaurant ORDER BY restaurant_id")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [_fix_map_url(r) for r in rows]
    except Error as e:
        print(f"[DB ERROR] get_all_restaurants: {e}")
        return []

def get_all_souvenirs():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM souvenir_shop ORDER BY shop_id")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [_fix_map_url(r) for r in rows]
    except Error as e:
        print(f"[DB ERROR] get_all_souvenirs: {e}")
        return []

def query_one(sql, args=()):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, args)
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return _fix_map_url(result)
    except Error as e:
        print(f"[DB ERROR] query_one: {e}")
        return None
