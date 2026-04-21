import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="junction.proxy.rlwy.net",
        port=37604,
        user="root",
        password="LtvqydRohNxyXdZZQhtZPqEAgfiZuvsy",
        database="railway",
        connection_timeout=10,   # ✅ ป้องกัน hang ถ้า Railway หลุด
    )

# alias
get_conn = get_connection

def search_place(keyword):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM place WHERE place_name LIKE %s LIMIT 1",
            (f"%{keyword}%",)
        )
        result = cursor.fetchone()
        cursor.close()
        return result
    finally:
        conn.close()   # ✅ ปิดเสมอ แม้เกิด error

def get_places_by_category(category):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM place WHERE category = %s ORDER BY place_id",
            (category,)
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        conn.close()

def get_all_place_names():
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT place_name FROM place ORDER BY place_id")
        rows = cursor.fetchall()
        cursor.close()
        return [r["place_name"] for r in rows]
    finally:
        conn.close()

def get_all_restaurants():
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM restaurant ORDER BY restaurant_id")
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        conn.close()

def get_all_souvenirs():
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM souvenir_shop ORDER BY shop_id")
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        conn.close()

def query_one(sql, args=()):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, args)
        result = cursor.fetchone()
        cursor.close()
        return result
    finally:
        conn.close()
