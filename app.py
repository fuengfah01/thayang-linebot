from flask import Flask, request, send_from_directory, jsonify
from linebot.v3.messaging import (
    ApiClient, Configuration, MessagingApi,
    ReplyMessageRequest,
    TextMessage, ImageMessage,
    QuickReply, QuickReplyItem, MessageAction,
)
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from rapidfuzz import process

from db import search_place, get_places_by_category, get_all_place_names
from info import info
from food import food
from ai_helper import ask_ai
from dialogflow_helper import detect_intent

import random
import os
import requests as req

app = Flask(__name__)

# =========================
# 🔑 CONFIG
# =========================
CHANNEL_ACCESS_TOKEN = "PNOGvfmIWQ3/BcVmw2rLjWwhWCVKe+ZMQl12nn4Dd/1aX0eAdxY9Q2pPPI/XMXgXfcL/q/gytkIljJiMSjAQCvN5wmahGaLKoVocuepLo5s98q0hD6fF6yGE9U8xfnPI9ayXKt13DQ/Tp1mV7MtYLgdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "ca7f131ffbb010718720d8bb21230a23"

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# =========================
# 🎁 SOUVENIRS DATA
# =========================
souvenirs = {
    "ขนมหม้อแกง": {
        "description": "ขนมหวานขึ้นชื่อของจังหวัดเพชรบุรี ทำจากไข่ กะทิ น้ำตาลโตนด รสชาติหวานมัน หอม",
        "shops": [
            {
                "name": "แม่บุญล้น",
                "address": "ซอยข้างธนาคารกรุงเทพ ถนนราษฎร์บำรุง ต.ท่ายาง อ.ท่ายาง",
                "tel": "032 771 125",
                "time": "07:00 - 17:30 น. (ทุกวัน)",
                "map": "https://maps.google.com/?q=12.9715847,99.8938471"
            },
            {
                "name": "แอนขนมหวาน",
                "address": "ตรงข้ามร้านผัดไทย ย่านศาลเจ้าพ่อกวนอู ต.ท่ายาง อ.ท่ายาง",
                "tel": "064 838 8709",
                "time": "08:00 - 18:00 น. (ทุกวัน)",
                "map": "https://maps.google.com/?q=12.973429,99.889248"
            },
        ]
    },
    "น้ำตาลโตนด": {
        "description": "ผลิตจากต้นตาลโตนด เป็นของดีของเพชรบุรี ใช้ทำอาหารและขนมหวาน มีกลิ่นหอมเฉพาะตัว",
        "shops": [
            {
                "name": "ชมนาถขนมไทย",
                "address": "88 หมู่ 4 ถ.เพชรเกษม ต.ท่ายาง อ.ท่ายาง (กม.165.5 ริมถนนขาลงใต้)",
                "tel": "086 393 4968",
                "time": "จ-พฤ 08:00-18:00 / ศ-อา 07:00-18:00 น.",
                "map": "https://maps.google.com/?q=13.0011882,99.9107277"
            },
        ]
    },
    "ขนมตาล": {
        "description": "ขนมพื้นบ้าน ทำจากเนื้อลูกตาล มีรสหวานหอม เนื้อนุ่มฟู",
        "shops": [
            {
                "name": "แม่บุญล้น",
                "address": "ซอยข้างธนาคารกรุงเทพ ถนนราษฎร์บำรุง ต.ท่ายาง อ.ท่ายาง",
                "tel": "032 771 125",
                "time": "07:00 - 17:30 น. (ทุกวัน)",
                "map": "https://maps.google.com/?q=12.9715847,99.8938471"
            },
        ]
    },
    "ทองม้วน": {
        "description": "ขนมกรอบ หอมกะทิและน้ำตาลโตนด ม้วนเป็นแท่ง เก็บได้นาน มีทั้งแบบนิ่มและกรอบ หลายรสชาติ",
        "shops": [
            {
                "name": "ทองม้วนแม่เล็ก",
                "address": "592 หลังตลาดสดเทศบาล ถ.ราษฎร์บำรุง ต.ท่ายาง อ.ท่ายาง",
                "tel": "090 974 5764",
                "time": "07:30 - 17:30 น. (ทุกวัน)",
                "map": "https://maps.google.com/?q=12.9731808,99.8891799"
            },
            {
                "name": "ทองม้วนทิพย์ (บ้านเปี่ยมเพชร)",
                "address": "322/52 ซอย ธ ต.ท่ายาง อ.ท่ายาง",
                "tel": "092 479 4545",
                "time": "07:00 - 18:00 น. (ทุกวัน)",
                "map": "https://maps.google.com/?q=12.9713536,99.8939792"
            },
        ]
    },
    "กล้วยฉาบ": {
        "description": "กล้วยทอดกรอบ รสหวานหรือเค็ม เป็นของกินเล่นยอดนิยม",
        "shops": [
            {
                "name": "เจ๊ณี ของฝากเมืองเพชรบุรี",
                "address": "1/1 ม.7 ต.ท่ายาง อ.ท่ายาง",
                "tel": "063 642 5965",
                "time": "08:00 - 18:00 น. (จ-ส / อา หยุด)",
                "map": "https://maps.google.com/?q=12.9577529,99.8932537"
            },
        ]
    },
    "อาหารทะเลแห้ง": {
        "description": "กุ้งแห้ง หมึกบด ปลาเค็ม และอาหารทะเลแปรรูปอื่นๆ จากทะเลเพชรบุรี รสชาติเข้มข้น เก็บได้นาน",
        "shops": [
            {
                "name": "เจ๊ยบ ของฝากอาหารทะเลแห้ง",
                "address": "ต.ท่ายาง อ.ท่ายาง (ในตัวอำเภอ)",
                "tel": "085 704 1480",
                "time": "08:30 - 18:00 น. (จ-ศ) / 08:30 - 20:00 น. (ส-อา)",
                "map": "https://maps.google.com/?q=12.91068,99.9075148"
            },
        ]
    },
}

# =========================
# 🛠 HELPERS
# =========================
def _reply(api, event, messages: list):
    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=messages[:5],
        )
    )

def _text(msg: str) -> TextMessage:
    return TextMessage(text=msg)

def _image(url: str) -> ImageMessage:
    return ImageMessage(original_content_url=url, preview_image_url=url)


# =========================
# 🖼 ROUTE — รูปภาพ
# =========================
@app.route('/image/<path:filename>')
def serve_image(filename):
    return send_from_directory('image', filename)


# =========================
# 🌐 HOME
# =========================
@app.route("/")
def home():
    return "LINE BOT RUNNING"


# =========================
# 🎛 SETUP RICH MENU
# =========================
@app.route("/setup-richmenu")
def setup_richmenu():
    headers_json = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    headers_auth = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }

    # 1. ลบ Rich Menu เก่าทั้งหมดก่อน
    res_list = req.get("https://api.line.me/v2/bot/richmenu/list", headers=headers_auth)
    for menu in res_list.json().get("richmenus", []):
        req.delete(f"https://api.line.me/v2/bot/richmenu/{menu['richMenuId']}", headers=headers_auth)

    # 2. สร้าง Rich Menu ใหม่ (6 ปุ่ม 2 แถว x 3 คอลัมน์)
    body = {
        "size": {"width": 2500, "height": 1686},
        "selected": True,
        "name": "Main Menu",
        "chatBarText": "ผู้ช่วยเที่ยวท่ายาง",
        "areas": [
            # แถวบน
            {
                "bounds": {"x": 0,    "y": 0, "width": 833, "height": 843},
                "action": {"type": "message", "text": "สถานที่ท่องเที่ยว"}
            },
            {
                "bounds": {"x": 833,  "y": 0, "width": 834, "height": 843},
                "action": {"type": "message", "text": "ร้านอาหาร"}
            },
            {
                "bounds": {"x": 1667, "y": 0, "width": 833, "height": 843},
                "action": {"type": "message", "text": "กิจกรรมภายในอำเภอท่ายาง"}
            },
            # แถวล่าง
            {
                "bounds": {"x": 0,    "y": 843, "width": 833, "height": 843},
                "action": {"type": "message", "text": "แผนที่ภายในอำเภอท่ายาง"}
            },
            {
                "bounds": {"x": 833,  "y": 843, "width": 834, "height": 843},
                "action": {"type": "message", "text": "ของฝาก"}
            },
            {
                "bounds": {"x": 1667, "y": 843, "width": 833, "height": 843},
                "action": {"type": "message", "text": "เกี่ยวกับเรา"}
            },
        ]
    }

    res = req.post(
        "https://api.line.me/v2/bot/richmenu",
        headers=headers_json,
        json=body
    )
    rich_menu_id = res.json().get("richMenuId")

    if not rich_menu_id:
        return f"❌ สร้าง Rich Menu ไม่สำเร็จ: {res.json()}", 500

    # 3. อัพโหลดรูป (วางไฟล์ richmenu.jpg ไว้ใน folder เดียวกับ app.py)
    img_path = os.path.join(os.path.dirname(__file__), "richmenu.jpg")
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            req.post(
                f"https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content",
                headers={
                    "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
                    "Content-Type": "image/jpeg"
                },
                data=f.read()
            )
    else:
        return f"⚠️ สร้าง Rich Menu ID: {rich_menu_id} สำเร็จ แต่ไม่พบไฟล์ richmenu.jpg กรุณาอัพโหลดรูปด้วยค่ะ", 200

    # 4. ตั้งเป็น Default Rich Menu
    req.post(
        f"https://api.line.me/v2/bot/richmenu/default/{rich_menu_id}",
        headers=headers_auth
    )

    return f"✅ Rich Menu สร้างสำเร็จ! ID: {rich_menu_id}"


# =========================
# 🔗 WEBHOOK — LINE
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_data(as_text=True)
    signature = request.headers.get("X-Line-Signature", "")
    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Webhook error:", e)
    return "OK"


# =========================
# 🔗 WEBHOOK — DIALOGFLOW
# =========================
@app.route("/dialogflow", methods=["POST"])
def dialogflow_webhook():
    data = request.get_json()
    intent = data["queryResult"]["intent"]["displayName"]
    parameters = data["queryResult"].get("parameters", {})
    place_name = parameters.get("place-name", "")

    if intent in ["recommend_place", "place.travel"]:
        rows = get_places_by_category("travel")
        if rows:
            msg = "🏛️ สถานที่ท่องเที่ยวในท่ายาง\n\n"
            for i, r in enumerate(rows, 1):
                msg += f"{i}. {r['place_name']}\n"
        else:
            msg = "ขอโทษค่ะ ยังไม่มีข้อมูลสถานที่ค่ะ"

    elif intent == "place.eat":
        rows = get_places_by_category("eat")
        if rows:
            msg = "🍽️ ร้านอาหารในท่ายาง\n\n"
            for i, r in enumerate(rows, 1):
                msg += f"{i}. {r['place_name']}\n"
        else:
            msg = "ขอโทษค่ะ ยังไม่มีข้อมูลร้านอาหารค่ะ"

    elif intent == "place.search":
        p = search_place(place_name)
        if p:
            cat = "🏛️ สถานที่ท่องเที่ยว" if p["category"] == "travel" else "🍽️ ร้านอาหาร"
            msg = f"{cat}\n\n📍 {p['place_name']}\n\n📖 {p['place_description']}"
            if p.get("open_time") and p.get("close_time"):
                msg += f"\n\n🕐 เปิด {p['open_time']} - {p['close_time']} น."
        else:
            msg = f"ขอโทษค่ะ ไม่พบข้อมูลของ {place_name} ค่ะ"

    elif intent == "place.opentime":
        p = search_place(place_name)
        if p and p.get("open_time") and p.get("close_time"):
            msg = f"🕐 {p['place_name']} เปิด {p['open_time']} - {p['close_time']} น.ค่ะ"
        elif p:
            msg = f"ขอโทษค่ะ ยังไม่มีข้อมูลเวลาของ {p['place_name']} ค่ะ"
        else:
            msg = f"ขอโทษค่ะ ไม่พบข้อมูลของ {place_name} ค่ะ"

    else:
        msg = "ขอโทษค่ะ ไม่เข้าใจคำถาม ลองถามใหม่ได้เลยค่ะ 😊"

    return jsonify({"fulfillmentText": msg})


# =========================
# 📍 สถานที่ — ดึงจาก DB
# =========================
def send_place_detail(api, event, name):
    p = search_place(name)
    if not p:
        _reply(api, event, [_text(f"ขอโทษค่ะ ไม่พบข้อมูลของ {name} ค่ะ")])
        return

    cat = "🏛️ สถานที่ท่องเที่ยว" if p["category"] == "travel" else "🍽️ ร้านอาหาร"
    msg = f"{cat}\n\n📍 {p['place_name']}\n\n📖 {p['place_description']}"
    if p.get("open_time") and p.get("close_time"):
        msg += f"\n\n🕐 เปิด {p['open_time']} - {p['close_time']} น."
    else:
        msg += "\n\n🕐 ยังไม่มีข้อมูลเวลาเปิด-ปิดค่ะ"

    _reply(api, event, [_text(msg)])


def send_places(api, event):
    rows = get_places_by_category("travel")
    if not rows:
        _reply(api, event, [_text("ขอโทษค่ะ ยังไม่มีข้อมูลสถานที่ค่ะ")])
        return
    names = [r["place_name"] for r in rows[:9]]
    _reply(api, event, [
        TextMessage(
            text="📍 เลือกสถานที่ท่องเที่ยวในท่ายางค่ะ",
            quick_reply=QuickReply(items=[
                QuickReplyItem(action=MessageAction(label=name, text=name))
                for name in names
            ])
        )
    ])


# =========================
# 🗺 MAP
# =========================
def send_map(api, event):
    rows = get_all_place_names()
    names = rows[:9]
    _reply(api, event, [
        TextMessage(
            text="🗺 เลือกสถานที่ที่ต้องการดูแผนที่ค่ะ",
            quick_reply=QuickReply(items=[
                QuickReplyItem(action=MessageAction(label=n, text=f"แผนที่ {n}"))
                for n in names
            ])
        )
    ])


# =========================
# 🏃 ACTIVITY
# =========================
activity_details = {
    "ไหว้พระในท่ายาง":     "🙏 ไหว้พระในท่ายาง\n\n• วัดท่าคอย\n• ศาลเจ้าพ่อกวนอู\n• ศาลเจ้าแม่ทับทิม",
    "ถ่ายรูปในท่ายาง":     "📸 จุดถ่ายรูปในท่ายาง\n\n• วัดท่าคอย\n• ศาลเจ้าพ่อกวนอู\n• ศาลเจ้าแม่ทับทิม\n• อุโบสถ 100 ปี",
    "ให้อาหารปลาในท่ายาง": "🐟 ให้อาหารปลาในท่ายาง\n\n• อุทยานปลาวัดท่าคอย",
    "ตะลอนกินในท่ายาง":    "🍜 ตะลอนกินในท่ายาง\n\n• ตลาดสดท่ายาง\n• ร้านทองม้วนแม่เล็ก\n• ร้านผัดไทย 100 ปี\n• ร้านข้าวแช่แม่เล็ก สกิดใจ",
}

def send_activity(api, event):
    _reply(api, event, [
        _text("🧭 กิจกรรมแนะนำในท่ายาง"),
        TextMessage(
            text="👇 กดเลือกกิจกรรมที่สนใจได้เลยค่ะ",
            quick_reply=QuickReply(items=[
                QuickReplyItem(action=MessageAction(label="🙏 ไหว้พระ",      text="ไหว้พระในท่ายาง")),
                QuickReplyItem(action=MessageAction(label="📸 ถ่ายรูป",       text="ถ่ายรูปในท่ายาง")),
                QuickReplyItem(action=MessageAction(label="🐟 ให้อาหารปลา",  text="ให้อาหารปลาในท่ายาง")),
                QuickReplyItem(action=MessageAction(label="🍜 ตะลอนกิน",     text="ตะลอนกินในท่ายาง")),
            ])
        )
    ])


# =========================
# 📖 INFO
# =========================
INFO_KEY_MAP = {
    "ประวัติท่ายาง":   "history",
    "จุดเด่นท่ายาง":   "highlight",
    "วิถีชีวิตท่ายาง": "lifestyle",
    "ติดต่อท่ายาง":    "contact",
}

CULTURE_KEY_MAP = {
    "วัดท่าคอย":            "culture_wat_takhoi",
    "อุโบสถ 100 ปี":       "culture_ubosot",
    "อุทยานปลาวัดท่าคอย": "culture_fish_park",
    "ตลาดสดท่ายาง":        "culture_market",
    "ร้านทองม้วนแม่เล็ก":  "culture_thong_muan",
    "ร้านผัดไทย 100 ปี":   "culture_padthai",
    "ศาลเจ้าพ่อกวนอู":     "culture_guanyu",
    "ข้าวแช่แม่เล็ก":       "culture_khao_chae",
    "ศาลเจ้าแม่ทับทิม":    "culture_tapthim",
}

def send_info(api, event):
    _reply(api, event, [
        _text("📖 เกี่ยวกับอำเภอท่ายาง"),
        TextMessage(
            text="👇 กดเลือกหัวข้อที่สนใจได้เลยค่ะ",
            quick_reply=QuickReply(items=[
                QuickReplyItem(action=MessageAction(label="📜 ประวัติ",   text="ประวัติท่ายาง")),
                QuickReplyItem(action=MessageAction(label="⭐ จุดเด่น",   text="จุดเด่นท่ายาง")),
                QuickReplyItem(action=MessageAction(label="🌿 วิถีชีวิต", text="วิถีชีวิตท่ายาง")),
                QuickReplyItem(action=MessageAction(label="🛕 วัฒนธรรม", text="วัฒนธรรมท่ายาง")),
                QuickReplyItem(action=MessageAction(label="📞 ติดต่อเรา", text="ติดต่อท่ายาง")),
            ])
        )
    ])

def send_culture(api, event):
    _reply(api, event, [
        _text("🏛️ วัฒนธรรมท่ายาง"),
        TextMessage(
            text="👇 กดเลือกสถานที่/ร้านที่สนใจค่ะ",
            quick_reply=QuickReply(items=[
                QuickReplyItem(action=MessageAction(label="วัดท่าคอย",         text="วัฒนธรรม วัดท่าคอย")),
                QuickReplyItem(action=MessageAction(label="อุโบสถ 100 ปี",     text="วัฒนธรรม อุโบสถ 100 ปี")),
                QuickReplyItem(action=MessageAction(label="อุทยานปลา",         text="วัฒนธรรม อุทยานปลาวัดท่าคอย")),
                QuickReplyItem(action=MessageAction(label="ตลาดสดท่ายาง",     text="วัฒนธรรม ตลาดสดท่ายาง")),
                QuickReplyItem(action=MessageAction(label="ทองม้วนแม่เล็ก",   text="วัฒนธรรม ร้านทองม้วนแม่เล็ก")),
                QuickReplyItem(action=MessageAction(label="ผัดไทย 100 ปี",    text="วัฒนธรรม ร้านผัดไทย 100 ปี")),
                QuickReplyItem(action=MessageAction(label="ศาลเจ้าพ่อกวนอู",  text="วัฒนธรรม ศาลเจ้าพ่อกวนอู")),
                QuickReplyItem(action=MessageAction(label="ข้าวแช่แม่เล็ก",   text="วัฒนธรรม ข้าวแช่แม่เล็ก")),
                QuickReplyItem(action=MessageAction(label="ศาลเจ้าแม่ทับทิม", text="วัฒนธรรม ศาลเจ้าแม่ทับทิม")),
            ])
        )
    ])


# =========================
# 🎁 SOUVENIRS
# =========================
def send_souvenirs(api, event):
    names = list(souvenirs.keys())[:10]
    _reply(api, event, [
        TextMessage(
            text="🎁 ของฝากขึ้นชื่อในท่ายาง\nกดเลือกรายการได้เลยค่ะ",
            quick_reply=QuickReply(items=[
                QuickReplyItem(action=MessageAction(label=name, text=f"ของฝาก {name}"))
                for name in names
            ])
        )
    ])

def send_souvenir_detail(api, event, name):
    s = souvenirs[name]
    msgs = []
    msgs.append(_text(f"🎁 {name}\n\n📜 {s['description']}"))
    shop_text = "🏪 ร้านแนะนำในอำเภอท่ายาง\n"
    for i, shop in enumerate(s["shops"], 1):
        shop_text += (
            f"\n{i}. {shop['name']}\n"
            f"   📍 {shop['address']}\n"
            f"   📞 {shop['tel']}\n"
            f"   ⏰ {shop['time']}\n"
            f"   🗺 {shop['map']}"
        )
    msgs.append(_text(shop_text))
    _reply(api, event, msgs)


# =========================
# 🍽 FOOD
# =========================
def send_food_categories(api, event):
    _reply(api, event, [
        TextMessage(
            text="🍽 อาหารในอำเภอท่ายาง\nเลือกหมวดที่สนใจได้เลยค่ะ",
            quick_reply=QuickReply(items=[
                QuickReplyItem(action=MessageAction(label="🍛 อาหารคาว",     text="หมวดอาหาร อาหารคาว")),
                QuickReplyItem(action=MessageAction(label="🍮 ขนม/ของหวาน", text="หมวดอาหาร ขนม/ของหวาน")),
            ])
        )
    ])

def send_food_category_list(api, event, category):
    if category not in food:
        _reply(api, event, [_text("ขอโทษค่ะ ไม่พบหมวดนี้ค่ะ")])
        return
    items_in_category = food[category]
    names = list(items_in_category.keys())
    quick_items = []
    for name in names[:13]:
        label = name if len(name) <= 20 else name[:19] + "…"
        quick_items.append(
            QuickReplyItem(action=MessageAction(label=label, text=f"เมนู {category} {name}"))
        )
    _reply(api, event, [
        TextMessage(
            text=(
                f"🍴 {category} ในท่ายาง\n\n" +
                "\n".join(f"• {n}" for n in names) +
                "\n\n👆 กดเลือกเมนูที่สนใจได้เลยค่ะ"
            ),
            quick_reply=QuickReply(items=quick_items)
        )
    ])

def send_food_detail(api, event, category, name):
    item = food[category][name]
    msgs = []
    if item.get("image"):
        msgs.append(_image(item["image"]))
    msgs.append(_text(
        f"🍽 {name}\n\n"
        f"📜 {item['description']}\n\n"
        f"⭐ {item['highlight']}"
    ))
    msgs.append(_text(f"📍 สถานที่\n{item['location']}"))
    if item.get("image_credit"):
        msgs.append(_text(item["image_credit"]))
    _reply(api, event, msgs)


# =========================
# 📩 HANDLE MESSAGE
# =========================
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()

    with ApiClient(configuration) as api_client:
        api = MessagingApi(api_client)

        if text.lower() in ["สวัสดี", "สวัสดีค่ะ", "สวัสดีครับ", "สวัสดีค่า", "สวัสดีคับ",
                             "หวัดดีค่ะ", "หวัดดีงับ", "ดี", "ดีจ้า", "หวัดดีคับ", "หวัดดี", "hi", "hello"]:
            greetings = [
                "สวัสดีค่ะ น้องเพชรผู้ช่วยตอบคำถามในอำเภอท่ายาง ยินดีให้บริการค่ะ 😊",
                "สวัสดีค่ะ น้องเพชรพร้อมช่วยแนะนำสถานที่ท่องเที่ยวในท่ายางแล้วค่ะ ✨",
                "สวัสดีค่ะ! น้องเพชรผู้ช่วยของคุณอยู่ที่นี่ พร้อมให้คำตอบทุกคำถามค่ะ 🌟",
                "สวัสดีค่า น้องเพชรมาแล้วค่ะ! วันนี้มีอะไรให้ช่วยดูแลในท่ายาง บอกน้องเพชรได้เลยนะ 💎",
                "ยินดีต้อนรับสู่ท่ายางนะคะ น้องเพชรพร้อมเป็นไกด์ส่วนตัวให้คุณแล้วค่ะ 🗺️",
            ]
            _reply(api, event, [_text(random.choice(greetings))])

        elif text in ["ขอบคุณ", "ขอบคุณค่ะ", "ขอบคุณครับ", "ขอบคุณค่า", "ขอบคุณนะ", "thank you", "thanks"]:
            _reply(api, event, [_text(
                "ยินดีให้บริการค่ะ 🗺️💖 ขอบคุณที่แวะมาสอบถามนะคะ "
                "หวังว่าจะได้ช่วยให้การเที่ยวของคุณสนุกขึ้นนะคะ 😊"
            )])

        elif text in ["food", "ร้านอาหาร", "อาหาร", "ร้านอาหารในอำเภอท่ายาง", "กินอะไรดี", "อาหารแนะนำ"]:
            send_food_categories(api, event)

        elif text.startswith("หมวดอาหาร "):
            category = text.replace("หมวดอาหาร ", "", 1)
            send_food_category_list(api, event, category)

        elif text.startswith("เมนู "):
            rest = text[len("เมนู "):]
            matched_cat = None
            matched_name = None
            for cat in food:
                prefix = cat + " "
                if rest.startswith(prefix):
                    matched_cat = cat
                    matched_name = rest[len(prefix):]
                    break
            if matched_cat and matched_name in food[matched_cat]:
                send_food_detail(api, event, matched_cat, matched_name)
            else:
                _reply(api, event, [_text("ขอโทษค่ะ ไม่พบข้อมูลเมนูนี้ค่ะ")])

        elif text in ["souvenir", "ของฝาก", "ของฝากในอำเภอท่ายาง"]:
            send_souvenirs(api, event)

        elif text.startswith("ของฝาก "):
            name = text.replace("ของฝาก ", "", 1)
            if name in souvenirs:
                send_souvenir_detail(api, event, name)
            else:
                _reply(api, event, [_text("ขอโทษค่ะ ไม่พบข้อมูลของฝากนี้ค่ะ")])

        elif text in ["travel", "สถานที่ท่องเที่ยว"]:
            send_places(api, event)

        elif text in ["map", "แผนที่ภายในอำเภอท่ายาง"]:
            send_map(api, event)

        elif text.startswith("แผนที่ "):
            place_name = text.replace("แผนที่ ", "", 1)
            p = search_place(place_name)
            if p and p.get("map_url"):
                _reply(api, event, [_text(f"🗺 แผนที่ {p['place_name']}\n{p['map_url']}")])
            else:
                _reply(api, event, [_text("ขอโทษค่ะ ไม่พบข้อมูลแผนที่ของสถานที่นี้ค่ะ")])

        elif text in ["activity", "กิจกรรมภายในอำเภอท่ายาง"]:
            send_activity(api, event)

        elif text in activity_details:
            _reply(api, event, [_text(activity_details[text])])

        elif text in ["info", "เกี่ยวกับเรา"]:
            send_info(api, event)

        elif text == "วัฒนธรรมท่ายาง":
            send_culture(api, event)

        elif text in INFO_KEY_MAP:
            key = INFO_KEY_MAP[text]
            _reply(api, event, [_text(info.get(key, "ขอโทษค่ะ ไม่พบข้อมูลนี้ค่ะ"))])

        elif text.startswith("วัฒนธรรม "):
            place_name = text.replace("วัฒนธรรม ", "", 1)
            key = CULTURE_KEY_MAP.get(place_name)
            if key and key in info:
                _reply(api, event, [_text(info[key])])
            else:
                _reply(api, event, [_text("ขอโทษค่ะ ไม่พบข้อมูลนี้ค่ะ")])

        elif text.startswith("ใช่_"):
            name = text.replace("ใช่_", "", 1)
            p = search_place(name)
            if p:
                send_place_detail(api, event, name)
            elif name in souvenirs:
                send_souvenir_detail(api, event, name)
            else:
                _reply(api, event, [_text("ขอโทษค่ะ ไม่พบข้อมูล")])

        elif text == "ไม่ใช่":
            _reply(api, event, [_text("ขอโทษค่ะ ลองพิมพ์ใหม่อีกครั้งนะคะ 😊")])

        # ─── ส่งให้ Dialogflow แปล Intent ────────────────────────────────
        else:
            try:
                result = detect_intent(text, session_id=event.source.user_id)
                intent = result["intent"]
                params = result["parameters"]
                place_name = str(params.get("place-name", "")).strip()
                confidence = result["confidence"]

                if confidence > 0.5:
                    if intent == "recommend_place":
                        send_places(api, event)

                    elif intent == "place.eat":
                        rows = get_places_by_category("eat")
                        if rows:
                            msg = "🍽️ ร้านอาหารในท่ายาง\n\n"
                            for i, r in enumerate(rows, 1):
                                msg += f"{i}. {r['place_name']}\n"
                            _reply(api, event, [_text(msg)])
                        else:
                            _reply(api, event, [_text("ขอโทษค่ะ ยังไม่มีข้อมูลร้านอาหารค่ะ")])

                    elif intent == "place.search" and place_name:
                        p = search_place(place_name)
                        if p:
                            send_place_detail(api, event, place_name)
                        else:
                            _reply(api, event, [_text(f"ขอโทษค่ะ ไม่พบข้อมูลของ {place_name} ค่ะ")])

                    elif intent == "place.opentime" and place_name:
                        p = search_place(place_name)
                        if p and p.get("open_time") and p.get("close_time"):
                            _reply(api, event, [_text(f"🕐 {p['place_name']} เปิด {p['open_time']} - {p['close_time']} น.ค่ะ")])
                        elif p:
                            _reply(api, event, [_text(f"ขอโทษค่ะ ยังไม่มีข้อมูลเวลาของ {p['place_name']} ค่ะ")])
                        else:
                            _reply(api, event, [_text(f"ขอโทษค่ะ ไม่พบข้อมูลของ {place_name} ค่ะ")])

                    else:
                        p = search_place(text)
                        if p:
                            send_place_detail(api, event, text)
                        else:
                            ai_answer = ask_ai(text)
                            _reply(api, event, [_text(ai_answer)])
                else:
                    p = search_place(text)
                    if p:
                        send_place_detail(api, event, text)
                    else:
                        ai_answer = ask_ai(text)
                        _reply(api, event, [_text(ai_answer)])

            except Exception as e:
                print("Dialogflow error:", e)
                p = search_place(text)
                if p:
                    send_place_detail(api, event, text)
                else:
                    ai_answer = ask_ai(text)
                    _reply(api, event, [_text(ai_answer)])


# =========================
# 🚀 RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
