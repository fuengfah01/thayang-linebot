import mysql.connector
import os

def get_connection():
    return mysql.connector.connect(
        host="junction.proxy.rlwy.net",
        port=37604,
        user="root",
        password="LtvqydRohNxyXdZZQhtZPqEAgfiZuvsy",
        database="railway",
    )

def search_place(keyword):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT place_name, place_description, category, open_time, close_time FROM place WHERE place_name LIKE %s LIMIT 1",
        (f"%{keyword}%",)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def get_places_by_category(category):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT place_name FROM place WHERE category = %s",
        (category,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def get_all_place_names():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT place_name FROM place")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [r["place_name"] for r in rows]