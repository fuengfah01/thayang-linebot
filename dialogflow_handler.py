from google.cloud import dialogflow
from google.oauth2 import service_account
import json, os
import mysql.connector

# ── DB connection ──────────────────────────────────────────────────
def get_conn():
    return mysql.connector.connect(
        host="junction.proxy.rlwy.net",
        port=37604,
        user="root",
        password="LtvqydRohNxyXdZZQhtZPqEAgfiZuvsy",
        database="railway",
    )

def q(sql, args=()):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, args)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

# ── Dialogflow detect intent ───────────────────────────────────────
def detect_intent(text, session_id="user123", language_code="th"):
    credentials_json = os.environ.get("GOOGLE_CREDENTIALS")
    credentials_dict = json.loads(credentials_json)
    project_id = credentials_dict["project_id"]
    credentials = service_account.Credentials.from_service_account_info(
        credentials_dict,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    session_client = dialogflow.SessionsClient(credentials=credentials)
    session = session_client.session_path(project_id, session_id)
    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)
    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )
    return {
        "intent": response.query_result.intent.display_name,
        "parameters": dict(response.query_result.parameters),
        "fulfillment_text": response.query_result.fulfillment_text,
        "confidence": response.query_result.intent_detection_confidence,
    }

# ── Main handler ───────────────────────────────────────────────────
def handle_dialogflow(body):
    qr = body.get("queryResult", {})
    intent = qr.get("intent", {}).get("displayName", "")
    params = qr.get("parameters", {})

    # ── greeting ──────────────────────────────────────────────────
    if intent == "greeting":
        return {"fulfillmentText": (
            "สวัสดีครับ 🌿 ยินดีต้อนรับสู่อำเภอท่ายาง!\n"
            "ผมช่วยแนะนำสิ่งต่าง ๆ ได้เลยครับ เช่น\n"
            "• สถานที่ท่องเที่ยว\n"
            "• ร้านอาหาร\n"
            "• ของฝาก\n"
            "• กิจกรรมน่าทำ"
        )}

    # ── recommend_place ───────────────────────────────────────────
    elif intent == "recommend_place":
        rows = q("SELECT place_name, highlight FROM place WHERE category='travel' ORDER BY place_id")
        if not rows:
            return {"fulfillmentText": "ขณะนี้ยังไม่มีข้อมูลสถานที่ครับ"}
        lines = ["🏛 สถานที่ท่องเที่ยวในอำเภอท่ายาง\n"]
        for r in rows:
            lines.append(f"📍 {r['place_name']}\n   {r['highlight'] or ''}")
        return {"fulfillmentText": "\n".join(lines)}

    # ── place.eat ─────────────────────────────────────────────────
    elif intent == "place.eat":
        rows = q("SELECT name, highlight, open_hours, close_hours FROM restaurant ORDER BY restaurant_id")
        if not rows:
            return {"fulfillmentText": "ขณะนี้ยังไม่มีข้อมูลร้านอาหารครับ"}
        lines = ["🍽 ร้านอาหารในอำเภอท่ายาง\n"]
        for r in rows:
            t = f"{r['open_hours'][:5]}–{r['close_hours'][:5]}" if r['open_hours'] else ""
            lines.append(f"🍴 {r['name']}\n   {r['highlight'] or ''}\n   ⏰ {t}")
        return {"fulfillmentText": "\n".join(lines)}

    # ── place.search ──────────────────────────────────────────────
    elif intent == "place.search":
        keyword = params.get("place_name") or params.get("any") or ""
        if not keyword:
            return {"fulfillmentText": "กรุณาบอกชื่อสถานที่ที่ต้องการค้นหาครับ"}
        rows = q(
            "SELECT place_name, place_description, highlight, open_time, close_time, map_url "
            "FROM place WHERE place_name LIKE %s LIMIT 1",
            (f"%{keyword}%",)
        )
        if not rows:
            return {"fulfillmentText": f"ขอโทษครับ ไม่พบสถานที่ที่มีชื่อว่า '{keyword}'"}
        r = rows[0]
        t = f"{r['open_time'][:5]}–{r['close_time'][:5]}" if r['open_time'] else "ไม่ระบุ"
        text = (
            f"📍 {r['place_name']}\n\n"
            f"{r['place_description'] or ''}\n\n"
            f"✨ จุดเด่น: {r['highlight'] or 'ไม่ระบุ'}\n"
            f"⏰ เวลาเปิด: {t}\n"
        )
        if r['map_url']:
            text += f"🗺 แผนที่: {r['map_url']}"
        return {"fulfillmentText": text}

    # ── place.opentime ────────────────────────────────────────────
    elif intent == "place.opentime":
        keyword = params.get("place_name") or params.get("any") or ""
        if not keyword:
            return {"fulfillmentText": "กรุณาบอกชื่อสถานที่ที่ต้องการทราบเวลาเปิดครับ"}
        rows = q(
            "SELECT place_name, open_time, close_time FROM place WHERE place_name LIKE %s LIMIT 1",
            (f"%{keyword}%",)
        )
        if not rows:
            # ลองหาในร้านอาหารด้วย
            rows = q(
                "SELECT name AS place_name, open_hours AS open_time, close_hours AS close_time "
                "FROM restaurant WHERE name LIKE %s LIMIT 1",
                (f"%{keyword}%",)
            )
        if not rows:
            return {"fulfillmentText": f"ไม่พบข้อมูลเวลาเปิดของ '{keyword}' ครับ"}
        r = rows[0]
        t = f"{r['open_time'][:5]} – {r['close_time'][:5]}" if r['open_time'] else "ไม่ระบุ"
        return {"fulfillmentText": f"⏰ {r['place_name']}\nเปิดเวลา {t} ครับ"}

    # ── fallback ──────────────────────────────────────────────────
    else:
        fallback = qr.get("fulfillmentText", "")
        return {"fulfillmentText": fallback or "ขออภัยครับ ไม่เข้าใจคำถาม ลองถามใหม่ได้เลยนะครับ 🙏"}