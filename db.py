import mysql.connector
from mysql.connector import Error
from urllib.parse import quote

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

get_conn = None  # legacy alias, set below


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


def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] get_connection failed: {e}")
        raise


get_conn = get_connection


def _execute(sql, args=()):
    """Central helper: open → query → close, always."""
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

def get_all_restaurants():
    print("[DB] get_all_restaurants query start")
    rows = _execute("SELECT * FROM restaurant ORDER BY restaurant_id")
    print(f"[DB] get_all_restaurants got {len(rows)} rows")
    return [_fix_map_url(r) for r in rows]


# =========================
# souvenir_shop
# =========================

def get_all_souvenirs():
    rows = _execute("SELECT * FROM souvenir_shop ORDER BY shop_id")
    return [_fix_map_url(r) for r in rows]


# =========================
# about_us  (แทน info.py)
# =========================

def get_about(section: str) -> str:
    """
    section: 'highlight' | 'lifestyle' | 'culture' | 'contact'
    Returns content string or empty string.
    """
    rows = _execute(
        "SELECT content FROM about_us WHERE section = %s LIMIT 1",
        (section,)
    )
    return rows[0]["content"] if rows else ""


def get_history() -> str:
    """ประวัติท่ายาง — ดึงจาก chatbot_place ทุก travel รวมกัน (fallback)"""
    rows = _execute(
        "SELECT place_name, place_description FROM chatbot_place WHERE category='travel' ORDER BY place_id LIMIT 3"
    )
    if not rows:
        return "ขอโทษค่ะ ยังไม่มีข้อมูลประวัติค่ะ"
    return "📜 ประวัติสถานที่สำคัญในท่ายาง\n\n" + "\n\n".join(
        f"📍 {r['place_name']}\n{r['place_description'][:200]}..." for r in rows
    )


# =========================
# activity  (แทน activity_details dict)
# =========================

def get_activity_detail(name: str) -> str:
    """
    name: ชื่อกิจกรรม เช่น 'ไหว้พระในท่ายาง'
    Returns formatted string.
    """
    rows = _execute(
        "SELECT * FROM activity WHERE name = %s LIMIT 1",
        (name,)
    )
    if not rows:
        return None
    a = rows[0]
    emoji_map = {
        "ไหว้พระ":    "🙏",
        "ถ่ายรูป":    "📸",
        "ให้อาหารปลา": "🐟",
        "ตะลอนกิน":   "🍜",
    }
    emoji = emoji_map.get(a.get("type", ""), "🧭")
    places_list = "\n".join(f"• {p.strip()}" for p in (a.get("description") or "").split(","))
    return f"{emoji} {a['name']}\n\n{places_list}"


def get_all_activities():
    return _execute("SELECT * FROM activity ORDER BY activity_id")


# =========================
# misc
# =========================

def query_one(sql, args=()):
    rows = _execute(sql, args)
    return _fix_map_url(rows[0]) if rows else None
