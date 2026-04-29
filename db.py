import mysql.connector
from mysql.connector import Error
from urllib.parse import quote_plus

DB_CONFIG = {
    "host": "sql7.freesqldatabase.com",
    "port": 3306,
    "user": "sql7824635",
    "password": "iUz24J2d6E",
    "database": "sql7824635",
    "connection_timeout": 8,
    "connect_timeout": 8,
    "autocommit": True,
}


def _fix_map_url(row):
    if not row:
        return row
    url = (row.get("map_url") or "").strip()
    if not url:
        row["map_url"] = "https://www.google.com/maps/search/?api=1&query=Tha+Yang+Phetchaburi"
        return row
    try:
        if "?q=" in url:
            base, q = url.split("?q=", 1)
            row["map_url"] = base + "?q=" + quote_plus(q)
        elif "query=" in url:
            base, q = url.split("query=", 1)
            row["map_url"] = base + "query=" + quote_plus(q)
    except Exception as e:
        print(f"[MAP URL ERROR] {e}")
    return row


def get_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"[DB ERROR] get_connection failed: {e}")
        raise

# legacy alias
get_conn = get_connection


def _execute(sql, args=()):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, args)
        rows = cursor.fetchall()
        cursor.close()
        return rows
    except Error as e:
        print(f"[DB ERROR] query failed: {e} | sql={sql!r}")
        return []
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


# =========================
# chatbot_place
# =========================

def search_place(keyword):
    rows = _execute(
        "SELECT * FROM chatbot_place WHERE place_name LIKE %s LIMIT 1",
        (f"%{keyword}%",)
    )
    return _fix_map_url(rows[0]) if rows else None


def get_places_by_category(category):
    rows = _execute(
        "SELECT * FROM chatbot_place WHERE category = %s ORDER BY place_id",
        (category,)
    )
    return [_fix_map_url(r) for r in rows]


def get_all_place_names():
    rows = _execute("SELECT place_name FROM chatbot_place ORDER BY place_id")
    return [r["place_name"] for r in rows]


# =========================
# restaurant
# =========================

def get_restaurants_by_category(category):
    rows = _execute(
        "SELECT * FROM restaurant WHERE category = %s ORDER BY restaurant_id LIMIT 5",
        (category,)
    )
    return [_fix_map_url(r) for r in rows]


# =========================
# souvenir_shop
# =========================

def get_all_souvenirs():
    rows = _execute("SELECT * FROM souvenir_shop ORDER BY shop_id")
    return [_fix_map_url(r) for r in rows]


# =========================
# about_us
# =========================

def get_about(section: str) -> str:
    rows = _execute(
        "SELECT content FROM about_us WHERE section = %s LIMIT 1",
        (section,)
    )
    return rows[0]["content"] if rows else ""


# =========================
# misc
# =========================

def query_one(sql, args=()):
    rows = _execute(sql, args)
    return _fix_map_url(rows[0]) if rows else None
