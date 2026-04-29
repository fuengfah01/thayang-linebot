import mysql.connector
from mysql.connector import Error, pooling
from urllib.parse import quote

DB_CONFIG = {
    "host": "sql7.freesqldatabase.com",
    "port": 3306,
    "user": "sql7824635",
    "password": "iUz24J2d6E",
    "database": "sql7824635",
    "connection_timeout": 5,   # ✅ ลดจาก 10 → 5
    "connect_timeout": 5,      # ✅ เพิ่ม (บางเวอร์ชันใช้ชื่อนี้)
    "autocommit": True,        # ✅ ไม่ต้อง commit ทุกครั้ง
}

# ✅ ใช้ connection pool แทนเปิด/ปิดทุกครั้ง
try:
    _pool = pooling.MySQLConnectionPool(
        pool_name="thayang_pool",
        pool_size=3,
        **DB_CONFIG
    )
    print("[DB] Connection pool created OK")
except Error as e:
    print(f"[DB ERROR] Pool creation failed: {e}")
    _pool = None


def get_connection():
    if _pool:
        try:
            return _pool.get_connection()
        except Error as e:
            print(f"[DB ERROR] pool.get_connection failed: {e}")
    # fallback: direct connect
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] get_connection failed: {e}")
        raise

get_conn = get_connection


def _fix_map_url(row):
    if not row:
        return row
    url = row.get("map_url") or ""
    if url and "q=" in url:
        base, q = url.split("q=", 1)
        row["map_url"] = base + "q=" + quote(q, safe=",+&:/")
    elif not url:
        row["map_url"] = "https://www.google.com/maps/search/?api=1&query=Tha+Yang+Phetchaburi"
    return row


def _execute(sql, args=()):
    """✅ Helper กลาง: เปิด conn → query → ปิด พร้อม error handling"""
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


def get_all_restaurants():
    print("[DB] get_all_restaurants query start")
    rows = _execute("SELECT * FROM restaurant ORDER BY restaurant_id")
    print(f"[DB] get_all_restaurants got {len(rows)} rows")
    return [_fix_map_url(r) for r in rows]


def get_all_souvenirs():
    rows = _execute("SELECT * FROM souvenir_shop ORDER BY shop_id")
    return [_fix_map_url(r) for r in rows]


def query_one(sql, args=()):
    rows = _execute(sql, args)
    return _fix_map_url(rows[0]) if rows else None