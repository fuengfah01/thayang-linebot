import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "junction.proxy.rlwy.net",
    "port": 37604,
    "user": "root",
    "password": "LtvqydRohNxyXdZZQhtZPqEAgfiZuvsy",
    "database": "railway",
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
        return result
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
        return rows
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
        return rows
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
        return rows
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