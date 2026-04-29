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

# fallback map URLs from places.py (used when DB has no map_url)
_PLACE_MAP_FALLBACK = {
    "วัดท่าคอย":           "https://www.google.com/maps/search/?api=1&query=%E0%B8%A7%E0%B8%B1%E0%B8%94%E0%B8%97%E0%B9%88%E0%B8%B2%E0%B8%84%E0%B8%AD%E0%B8%A2+%E0%B8%97%E0%B9%88%E0%B8%B2%E0%B8%A2%E0%B8%B2%E0%B8%87",
    "อุโบสถ 100 ปี":       "https://www.google.com/maps/search/?api=1&query=%E0%B8%AD%E0%B8%B8%E0%B9%82%E0%B8%9A%E0%B8%AA%E0%B8%96+100+%E0%B8%9B%E0%B8%B5+%E0%B8%A7%E0%B8%B1%E0%B8%94%E0%B8%97%E0%B9%88%E0%B8%B2%E0%B8%84%E0%B8%AD%E0%B8%A2",
    "อุทยานปลาวัดท่าคอย":  "https://www.google.com/maps/search/?api=1&query=%E0%B8%AD%E0%B8%B8%E0%B8%97%E0%B8%A2%E0%B8%B2%E0%B8%99%E0%B8%9B%E0%B8%A5%E0%B8%B2+%E0%B8%A7%E0%B8%B1%E0%B8%94%E0%B8%97%E0%B9%88%E0%B8%B2%E0%B8%84%E0%B8%AD%E0%B8%A2",
    "ตลาดสดท่ายาง":        "https://www.google.com/maps/search/?api=1&query=%E0%B8%95%E0%B8%A5%E0%B8%B2%E0%B8%94%E0%B8%AA%E0%B8%94%E0%B8%97%E0%B9%88%E0%B8%B2%E0%B8%A2%E0%B8%B2%E0%B8%87",
    "ร้านทองม้วนแม่เล็ก":  "https://www.google.com/maps/search/?api=1&query=%E0%B8%97%E0%B8%AD%E0%B8%87%E0%B8%A1%E0%B9%89%E0%B8%A7%E0%B8%99%E0%B9%81%E0%B8%A1%E0%B9%88%E0%B9%80%E0%B8%A5%E0%B9%87%E0%B8%81+%E0%B8%97%E0%B9%88%E0%B8%B2%E0%B8%A2%E0%B8%B2%E0%B8%87",
    "ร้านผัดไทย 100 ปี":   "https://www.google.com/maps/search/?api=1&query=%E0%B8%9C%E0%B8%B1%E0%B8%94%E0%B9%84%E0%B8%97%E0%B8%A2+100+%E0%B8%9B%E0%B8%B5+%E0%B8%97%E0%B9%88%E0%B8%B2%E0%B8%A2%E0%B8%B2%E0%B8%87",
    "ศาลเจ้าพ่อกวนอู":     "https://www.google.com/maps/search/?api=1&query=%E0%B8%A8%E0%B8%B2%E0%B8%A5%E0%B9%80%E0%B8%88%E0%B9%89%E0%B8%B2%E0%B8%9E%E0%B9%88%E0%B8%AD%E0%B8%81%E0%B8%A7%E0%B8%99%E0%B8%AD%E0%B8%B9+%E0%B8%97%E0%B9%88%E0%B8%B2%E0%B8%A2%E0%B8%B2%E0%B8%87",
    "ข้าวแช่แม่เล็ก สกิดใจ":"https://www.google.com/maps/search/?api=1&query=%E0%B8%82%E0%B9%89%E0%B8%B2%E0%B8%A7%E0%B9%81%E0%B8%8A%E0%B9%88%E0%B9%81%E0%B8%A1%E0%B9%88%E0%B9%80%E0%B8%A5%E0%B9%87%E0%B8%81+%E0%B8%AA%E0%B8%81%E0%B8%B4%E0%B8%94%E0%B9%83%E0%B8%88+%E0%B8%97%E0%B9%88%E0%B8%B2%E0%B8%A2%E0%B8%B2%E0%B8%87",
    "ศาลเจ้าแม่ทับทิม":    "https://www.google.com/maps/search/?api=1&query=%E0%B8%A8%E0%B8%B2%E0%B8%A5%E0%B9%80%E0%B8%88%E0%B9%89%E0%B8%B2%E0%B9%81%E0%B8%A1%E0%B9%88%E0%B8%97%E0%B8%B1%E0%B8%9A%E0%B8%97%E0%B8%B4%E0%B8%A1+%E0%B8%97%E0%B9%88%E0%B8%B2%E0%B8%A2%E0%B8%B2%E0%B8%87",
}

def _inject_map_fallback(row):
    """If map_url is missing from DB row, inject from places.py fallback dict."""
    if row and not row.get("map_url"):
        name = row.get("place_name") or row.get("name") or ""
        if name in _PLACE_MAP_FALLBACK:
            row["map_url"] = _PLACE_MAP_FALLBACK[name]
    return row

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] get_connection failed: {e}")
        raise

# alias
get_conn = get_connection

def search_place(keyword):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM place WHERE place_name LIKE %s LIMIT 1",
            (f"%{keyword}%",)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return _inject_map_fallback(result)
    except Error as e:
        print(f"[DB ERROR] search_place({keyword}): {e}")
        return None

def get_places_by_category(category):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM place WHERE category = %s ORDER BY place_id",
            (category,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [_inject_map_fallback(r) for r in rows]
    except Error as e:
        print(f"[DB ERROR] get_places_by_category({category}): {e}")
        return []

def get_all_place_names():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT place_name FROM place ORDER BY place_id")
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
        return [_inject_map_fallback(r) for r in rows]
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
        return [_inject_map_fallback(r) for r in rows]
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
        return result
    except Error as e:
        print(f"[DB ERROR] query_one: {e}")
        return None
