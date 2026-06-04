import os
import mysql.connector
from mysql.connector import Error
from urllib.parse import quote_plus

def _get_db_config():
    return {
        "host":               os.environ.get("DB_HOST", "sql12.freesqldatabase.com"),
        "port":               int(os.environ.get("DB_PORT", 3306)),
        "user":               os.environ.get("DB_USER", "sql12825543"),
        "password":           os.environ.get("DB_PASSWORD", "BiDtrBXwmJ"),
        "database":           os.environ.get("DB_NAME", "sql12825543"),
        "connection_timeout": 10,
        "connect_timeout":    10,
        "autocommit":         True,
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
        conn = mysql.connector.connect(**_get_db_config())
        print("[DB] connection OK")
        return conn
    except Error as e:
        print(f"[DB ERROR] get_connection failed: {e}")
        raise

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
    except Exception as e:
        print(f"[DB ERROR] unexpected: {e}")
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
def get_restaurants_by_category(category, limit=50, offset=0):
    print(f"[DB] get_restaurants_by_category: category={repr(category)} limit={limit} offset={offset}")
    rows = _execute(
        "SELECT * FROM restaurant WHERE category = %s ORDER BY restaurant_id LIMIT %s OFFSET %s",
        (category, limit, offset)
    )
    print(f"[DB] got {len(rows)} rows")
    return [_fix_map_url(r) for r in rows]

def count_restaurants_by_category(category):
    rows = _execute(
        "SELECT COUNT(*) as total FROM restaurant WHERE category = %s",
        (category,)
    )
    return rows[0]["total"] if rows else 0

def get_restaurant_detail(name: str):
    rows = _execute(
        "SELECT * FROM restaurant WHERE name = %s LIMIT 1",
        (name,)
    )
    return _fix_map_url(rows[0]) if rows else None

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
# activity
# =========================
def get_all_activities():
    rows = _execute("SELECT * FROM activity ORDER BY activity_id")
    return rows

# =========================
# misc
# =========================
def query_one(sql, args=()):
    rows = _execute(sql, args)
    return _fix_map_url(rows[0]) if rows else None
