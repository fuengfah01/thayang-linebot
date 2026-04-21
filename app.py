from flask import Flask, request, send_from_directory, jsonify
from linebot.v3.messaging import (
    ApiClient, Configuration, MessagingApi,
    ReplyMessageRequest,
    TextMessage, ImageMessage, FlexMessage,
    QuickReply, QuickReplyItem, MessageAction,
)
from linebot.v3.messaging.models import FlexContainer
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from db import (
    search_place, get_places_by_category, get_all_place_names,
    get_all_restaurants, get_all_souvenirs, get_conn
)
from info import info
from food import food
from places import places
from ai_helper import ask_ai
from dialogflow_handler import detect_intent

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
# 🎁 SOUVENIRS DATA (fallback)
# =========================
souvenirs = {
    "ขนมหม้อแกง": {
        "description": "ขนมหวานขึ้นชื่อของจังหวัดเพชรบุรี ทำจากไข่ กะทิ น้ำตาลโตนด รสชาติหวานมัน หอม",
        "shops": [
            {"name": "แม่บุญล้น", "address": "ซอยข้างธนาคารกรุงเทพ ถนนราษฎร์บำรุง ต.ท่ายาง", "tel": "032 771 125", "time": "07:00 - 17:30 น.", "map": "https://maps.google.com/?q=12.9715847,99.8938471"},
            {"name": "แอนขนมหวาน", "address": "ตรงข้ามร้านผัดไทย ย่านศาลเจ้าพ่อกวนอู", "tel": "064 838 8709", "time": "08:00 - 18:00 น.", "map": "https://maps.google.com/?q=12.973429,99.889248"},
        ]
    },
    "น้ำตาลโตนด": {
        "description": "ผลิตจากต้นตาลโตนด เป็นของดีของเพชรบุรี มีกลิ่นหอมเฉพาะตัว",
        "shops": [
            {"name": "ชมนาถขนมไทย", "address": "88 ม.4 ถ.เพชรเกษม ต.ท่ายาง", "tel": "086 393 4968", "time": "จ-พฤ 08:00-18:00 / ศ-อา 07:00-18:00", "map": "https://maps.google.com/?q=13.0011882,99.9107277"},
        ]
    },
    "ขนมตาล": {
        "description": "ขนมพื้นบ้าน ทำจากเนื้อลูกตาล มีรสหวานหอม เนื้อนุ่มฟู",
        "shops": [
            {"name": "แม่บุญล้น", "address": "ซอยข้างธนาคารกรุงเทพ ถนนราษฎร์บำรุง ต.ท่ายาง", "tel": "032 771 125", "time": "07:00 - 17:30 น.", "map": "https://maps.google.com/?q=12.9715847,99.8938471"},
        ]
    },
    "ทองม้วน": {
        "description": "ขนมกรอบ หอมกะทิและน้ำตาลโตนด ม้วนเป็นแท่ง เก็บได้นาน มีทั้งแบบนิ่มและกรอบ",
        "shops": [
            {"name": "ทองม้วนแม่เล็ก", "address": "592 หลังตลาดสดเทศบาล ถ.ราษฎร์บำรุง ต.ท่ายาง", "tel": "090 974 5764", "time": "07:30 - 17:30 น.", "map": "https://maps.google.com/?q=12.9731808,99.8891799"},
            {"name": "ทองม้วนทิพย์ (บ้านเปี่ยมเพชร)", "address": "322/52 ซอย ธ ต.ท่ายาง", "tel": "092 479 4545", "time": "07:00 - 18:00 น.", "map": "https://maps.google.com/?q=12.9713536,99.8939792"},
        ]
    },
    "กล้วยฉาบ": {
        "description": "กล้วยทอดกรอบ รสหวานหรือเค็ม เป็นของกินเล่นยอดนิยม",
        "shops": [
            {"name": "เจ๊ณี ของฝากเมืองเพชรบุรี", "address": "1/1 ม.7 ต.ท่ายาง", "tel": "063 642 5965", "time": "08:00 - 18:00 น.", "map": "https://maps.google.com/?q=12.9577529,99.8932537"},
        ]
    },
    "อาหารทะเลแห้ง": {
        "description": "กุ้งแห้ง หมึกบด ปลาเค็ม และอาหารทะเลแปรรูปอื่นๆ จากทะเลเพชรบุรี",
        "shops": [
            {"name": "เจ๊ยบ ของฝากอาหารทะเลแห้ง", "address": "ต.ท่ายาง (ในตัวอำเภอ)", "tel": "085 704 1480", "time": "08:30 - 18:00 น.", "map": "https://maps.google.com/?q=12.91068,99.9075148"},
        ]
    },
}

# =========================
# 🛠 HELPERS
# =========================
def _reply(api, event, messages: list):
    api.reply_message(
        ReplyMessageRequest(reply_token=event.reply_token, messages=messages[:5])
    )

def _text(msg: str) -> TextMessage:
    return TextMessage(text=msg)

def _image(url: str) -> ImageMessage:
    return ImageMessage(original_content_url=url, preview_image_url=url)

def _valid_url(url) -> bool:
    """เช็คว่า URL ใช้ได้จริง ต้องขึ้นต้นด้วย http:// หรือ https://"""
    if not url:
        return False
    s = str(url).strip()
    return s.startswith("http://") or s.startswith("https://")

def _s(val, fallback: str = "") -> str:
    """แปลง None/NULL จาก DB ให้เป็น string ปลอดภัย"""
    if val is None:
        return fallback
    s = str(val).strip()
    return s if s else fallback

def _safe_time(val) -> str:
    """แปลง timedelta/time object หรือ string เป็น HH:MM ปลอดภัย"""
    if val is None:
        return ""
    import datetime
    if isinstance(val, datetime.timedelta):
        total = int(val.total_seconds())
        h, m = divmod(total // 60, 60)
        return f"{h:02d}:{m:02d}"
    return str(val)[:5]

def _fmt_time_range(open_val, close_val, fallback: str = "ไม่ระบุ") -> str:
    """สร้างช่วงเวลา HH:MM – HH:MM หรือ fallback ถ้าไม่มีข้อมูล"""
    ot = _safe_time(open_val)
    ct = _safe_time(close_val)
    if ot and ct:
        return f"{ot} – {ct} น."
    if ot:
        return f"เปิด {ot} น."
    return fallback

# =========================
# 💬 FLEX MESSAGE BUILDERS
# =========================
def _flex_place_bubble(name, highlight, image_url, open_time, close_time, map_url):
    desc = _s(highlight, "สถานที่ท่องเที่ยวในอำเภอท่ายาง")
    body_contents = [
        {"type": "text", "text": _s(name, "สถานที่"), "weight": "bold", "size": "lg", "wrap": True, "color": "#1a1a2e"},
        {"type": "text", "text": desc,
         "size": "sm", "color": "#555555", "wrap": True, "margin": "sm"},
    ]
    time_str = _fmt_time_range(open_time, close_time, "")
    if time_str:
        body_contents.append({
            "type": "text",
            "text": f"⏰ {time_str}",
            "size": "sm", "color": "#777777", "margin": "md"
        })

    footer_contents = []
    if _valid_url(map_url):
        footer_contents.append({
            "type": "button", "style": "primary", "color": "#2d7a3a", "height": "sm",
            "action": {"type": "uri", "label": "🗺 ดูแผนที่", "uri": str(map_url).strip()}
        })
    footer_contents.append({
        "type": "button", "style": "secondary", "height": "sm",
        "action": {"type": "message", "label": "📖 ดูรายละเอียด", "text": name}
    })

    bubble = {
        "type": "bubble",
        "body": {"type": "box", "layout": "vertical", "contents": body_contents, "paddingAll": "16px"},
        "footer": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": footer_contents, "paddingAll": "12px"}
    }
    if _valid_url(image_url):
        bubble["hero"] = {
            "type": "image", "url": str(image_url).strip(),
            "size": "full", "aspectRatio": "20:13", "aspectMode": "cover"
        }
    return bubble


def _flex_restaurant_bubble(name, highlight, image_url, open_hours, close_hours, map_url):
    body_contents = [
        {"type": "text", "text": _s(name, "ร้านอาหาร"), "weight": "bold", "size": "lg", "wrap": True, "color": "#1a1a2e"},
        {"type": "text", "text": _s(highlight, "ร้านอาหารในอำเภอท่ายาง"),
         "size": "sm", "color": "#555555", "wrap": True, "margin": "sm"},
    ]
    time_str = _fmt_time_range(open_hours, close_hours, "")
    if time_str:
        body_contents.append({
            "type": "text",
            "text": f"⏰ {time_str}",
            "size": "sm", "color": "#777777", "margin": "md"
        })

    footer_contents = []
    if _valid_url(map_url):
        footer_contents.append({
            "type": "button", "style": "primary", "color": "#d97706", "height": "sm",
            "action": {"type": "uri", "label": "🗺 ดูแผนที่", "uri": str(map_url).strip()}
        })

    bubble = {
        "type": "bubble",
        "body": {"type": "box", "layout": "vertical", "contents": body_contents, "paddingAll": "16px"}
    }
    if _valid_url(image_url):
        bubble["hero"] = {
            "type": "image", "url": str(image_url).strip(),
            "size": "full", "aspectRatio": "20:13", "aspectMode": "cover"
        }
    if footer_contents:
        bubble["footer"] = {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": footer_contents, "paddingAll": "12px"
        }
    return bubble


def _flex_souvenir_bubble(name, description, phone, time_str, map_url):
    body_contents = [
        {"type": "text", "text": name, "weight": "bold", "size": "md", "wrap": True, "color": "#0369a1"},
        {"type": "text", "text": description or "", "size": "sm", "color": "#555555",
         "wrap": True, "margin": "sm", "maxLines": 3},
    ]
    if phone:
        body_contents.append({"type": "text", "text": f"📞 {phone}", "size": "xs", "color": "#555555", "margin": "sm"})
    if time_str:
        body_contents.append({"type": "text", "text": f"⏰ {time_str}", "size": "xs", "color": "#777777", "margin": "sm"})

    footer_contents = [
        {
            "type": "button", "style": "secondary", "height": "sm",
            "action": {"type": "message", "label": "📖 ดูรายละเอียด", "text": f"รายละเอียดของฝาก {name}"}
        }
    ]
    if _valid_url(map_url):
        footer_contents.append({
            "type": "button", "style": "primary", "color": "#0369a1", "height": "sm",
            "action": {"type": "uri", "label": "🗺 ดูแผนที่", "uri": str(map_url).strip()}
        })

    return {
        "type": "bubble", "size": "kilo",
        "body": {"type": "box", "layout": "vertical", "contents": body_contents, "paddingAll": "16px"},
        "footer": {"type": "box", "layout": "vertical", "spacing": "sm", "contents": footer_contents, "paddingAll": "10px"}
    }


def _send_flex_carousel(api, event, alt_text, bubbles):
    bubbles = [b for b in bubbles if b][:10]
    if not bubbles:
        return
    container = bubbles[0] if len(bubbles) == 1 else {"type": "carousel", "contents": bubbles}
    _reply(api, event, [
        FlexMessage(alt_text=alt_text, contents=FlexContainer.from_dict(container))
    ])

# =========================
# 🖼 ROUTES
# =========================
@app.route('/image/<path:filename>')
def serve_image(filename):
    return send_from_directory('image', filename)

@app.route("/")
def home():
    return "LINE BOT RUNNING ✅"

# =========================
# 🎛 SETUP RICH MENU
# =========================
@app.route("/setup-richmenu")
def setup_richmenu():
    headers_json = {"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}", "Content-Type": "application/json"}
    headers_auth = {"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"}

    res_list = req.get("https://api.line.me/v2/bot/richmenu/list", headers=headers_auth)
    for menu in res_list.json().get("richmenus", []):
        req.delete(f"https://api.line.me/v2/bot/richmenu/{menu['richMenuId']}", headers=headers_auth)

    body = {
        "size": {"width": 2500, "height": 1686},
        "selected": True,
        "name": "Main Menu",
        "chatBarText": "ผู้ช่วยเที่ยวท่ายาง",
        "areas": [
            {"bounds": {"x": 0,    "y": 0,   "width": 833, "height": 843}, "action": {"type": "message", "text": "สถานที่ท่องเที่ยว"}},
            {"bounds": {"x": 833,  "y": 0,   "width": 834, "height": 843}, "action": {"type": "message", "text": "ร้านอาหาร"}},
            {"bounds": {"x": 1667, "y": 0,   "width": 833, "height": 843}, "action": {"type": "message", "text": "กิจกรรมภายในอำเภอท่ายาง"}},
            {"bounds": {"x": 0,    "y": 843, "width": 833, "height": 843}, "action": {"type": "message", "text": "แผนที่ภายในอำเภอท่ายาง"}},
            {"bounds": {"x": 833,  "y": 843, "width": 834, "height": 843}, "action": {"type": "message", "text": "ของฝาก"}},
            {"bounds": {"x": 1667, "y": 843, "width": 833, "height": 843}, "action": {"type": "message", "text": "เกี่ยวกับเรา"}},
        ]
    }

    res = req.post("https://api.line.me/v2/bot/richmenu", headers=headers_json, json=body)
    rich_menu_id = res.json().get("richMenuId")
    if not rich_menu_id:
        return f"❌ สร้าง Rich Menu ไม่สำเร็จ: {res.json()}", 500

    img_path = os.path.join(os.path.dirname(__file__), "richmenu.jpg")
    if os.path.exists(img_path):
        with open(img_path, "rb") as f:
            req.post(
                f"https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content",
                headers={"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}", "Content-Type": "image/jpeg"},
                data=f.read()
            )
    else:
        return f"⚠️ Rich Menu ID: {rich_menu_id} สำเร็จ แต่ไม่พบไฟล์ richmenu.jpg", 200

    req.post(f"https://api.line.me/v2/bot/richmenu/default/{rich_menu_id}", headers=headers_auth)
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
        rows = get_all_restaurants()
        if rows:
            msg = "🍽️ ร้านอาหารในท่ายาง\n\n"
            for i, r in enumerate(rows, 1):
                msg += f"{i}. {r['name']}\n"
        else:
            msg = "ขอโทษค่ะ ยังไม่มีข้อมูลร้านอาหารค่ะ"
    elif intent == "place.search":
        p = search_place(place_name)
        if p:
            msg = f"📍 {_s(p.get('place_name'), place_name)}\n\n📖 {_s(p.get('place_description'), 'ยังไม่มีรายละเอียดค่ะ')}"
            time_str = _fmt_time_range(p.get("open_time"), p.get("close_time"), "")
            if time_str:
                msg += f"\n\n🕐 {time_str}"
        else:
            msg = f"ขอโทษค่ะ ไม่พบข้อมูลของ {place_name} ค่ะ"
    elif intent == "place.opentime":
        if not place_name:
            msg = "ต้องการทราบเวลาเปิด-ปิดของที่ไหนคะ? 🕐"
        else:
            p = search_place(place_name)
            if p:
                ot = _safe_time(p.get("open_time"))
                ct = _safe_time(p.get("close_time"))
                if ot or ct:
                    msg = f"🕐 {_s(p.get('place_name'), place_name)} เปิด {ot or 'ไม่ระบุ'} – {ct or 'ไม่ระบุ'} น.ค่ะ"
                else:
                    msg = f"ขอโทษค่ะ ยังไม่มีข้อมูลเวลาของ {_s(p.get('place_name'), place_name)} ค่ะ"
            else:
                msg = f"ขอโทษค่ะ ไม่พบข้อมูลของ {place_name} ค่ะ"
    else:
        msg = "ขอโทษค่ะ ไม่เข้าใจคำถาม ลองถามใหม่ได้เลยค่ะ 😊"

    return jsonify({"fulfillmentText": msg})

# =========================
# 📍 PLACE FUNCTIONS
# =========================
def send_place_detail(api, event, name):
    if name in places:
        p = places[name]
        msgs = []
        if p.get("images") and _valid_url(p["images"][0]):
            msgs.append(_image(p["images"][0]))
        msgs.append(_text(f"📍 {name}\n\n📖 {p.get('history', '')}"))
        detail = f"⭐ จุดเด่น\n{p.get('highlight', '')}"
        if p.get("time"):
            detail += f"\n\n🕐 เวลา {p['time']} น."
        if p.get("map"):
            detail += f"\n\n🗺 {p['map']}"
        msgs.append(_text(detail))
        _reply(api, event, msgs)
        return

    p = search_place(name)
    if not p:
        _reply(api, event, [_text(f"ขอโทษค่ะ ไม่พบข้อมูลของ {name} ค่ะ")])
        return
    cat = "🏛️ สถานที่ท่องเที่ยว" if p.get("category") == "travel" else "🍽️ ร้านอาหาร"
    desc = _s(p.get("place_description"), "ยังไม่มีข้อมูลรายละเอียดค่ะ")
    msg = f"{cat}\n\n📍 {_s(p.get('place_name'), name)}\n\n📖 {desc}"
    time_str = _fmt_time_range(p.get("open_time"), p.get("close_time"), "")
    if time_str:
        msg += f"\n\n🕐 {time_str}"
    _reply(api, event, [_text(msg)])


def send_places(api, event):
    rows = get_places_by_category("travel")
    if not rows:
        _reply(api, event, [_text("ขอโทษค่ะ ยังไม่มีข้อมูลสถานที่ค่ะ")])
        return
    bubbles = [_flex_place_bubble(
        r["place_name"], r.get("highlight"), r.get("cover_image"),
        r.get("open_time"), r.get("close_time"),
        r.get("map_url") if _valid_url(r.get("map_url")) else None
    ) for r in rows]
    _send_flex_carousel(api, event, "สถานที่ท่องเที่ยวในท่ายาง", bubbles)


def send_restaurants(api, event):
    rows = get_all_restaurants()
    if not rows:
        _reply(api, event, [_text("ขอโทษค่ะ ยังไม่มีข้อมูลร้านอาหารค่ะ")])
        return
    bubbles = [_flex_restaurant_bubble(
        r["name"], r.get("highlight"), r.get("cover_image"),
        r.get("open_hours"), r.get("close_hours"),
        r.get("map_url") if _valid_url(r.get("map_url")) else None
    ) for r in rows]
    _send_flex_carousel(api, event, "ร้านอาหารในท่ายาง", bubbles)


def send_souvenirs(api, event):
    rows = get_all_souvenirs()
    if not rows:
        _reply(api, event, [_text("ขอโทษค่ะ ยังไม่มีข้อมูลของฝากค่ะ")])
        return
    bubbles = []
    for r in rows:
        time_str = _fmt_time_range(r.get("open_hours"), r.get("close_hours"), "")
        map_url = r.get("map_url") if _valid_url(r.get("map_url")) else None
        bubbles.append(_flex_souvenir_bubble(
            _s(r.get("name"), "ร้านของฝาก"),
            _s(r.get("description")),
            _s(r.get("phone")),
            time_str, map_url
        ))
    _send_flex_carousel(api, event, "ของฝากในท่ายาง", bubbles)


def send_map(api, event):
    names = get_all_place_names()[:9]
    _reply(api, event, [
        TextMessage(
            text="🗺 เลือกสถานที่ที่ต้องการดูแผนที่ค่ะ",
            quick_reply=QuickReply(items=[
                QuickReplyItem(action=MessageAction(label=n[:20], text=f"แผนที่ {n}"))
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
                QuickReplyItem(action=MessageAction(label="🙏 ไหว้พระ",     text="ไหว้พระในท่ายาง")),
                QuickReplyItem(action=MessageAction(label="📸 ถ่ายรูป",      text="ถ่ายรูปในท่ายาง")),
                QuickReplyItem(action=MessageAction(label="🐟 ให้อาหารปลา", text="ให้อาหารปลาในท่ายาง")),
                QuickReplyItem(action=MessageAction(label="🍜 ตะลอนกิน",    text="ตะลอนกินในท่ายาง")),
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
# 🎁 SOUVENIR DETAIL (fallback dict)
# =========================
def send_souvenir_detail(api, event, name):
    s = souvenirs[name]
    msgs = [_text(f"🎁 {name}\n\n📜 {s['description']}")]
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
# 🍽 FOOD FUNCTIONS
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
    names = list(food[category].keys())
    quick_items = [
        QuickReplyItem(action=MessageAction(label=n[:20], text=f"เมนู {category} {n}"))
        for n in names[:13]
    ]
    _reply(api, event, [TextMessage(
        text=f"🍴 {category} ในท่ายาง\n\n" + "\n".join(f"• {n}" for n in names) + "\n\n👆 กดเลือกเมนูที่สนใจได้เลยค่ะ",
        quick_reply=QuickReply(items=quick_items)
    )])

def send_food_detail(api, event, category, name):
    item = food[category][name]
    msgs = []
    if item.get("image") and _valid_url(item["image"]):
        msgs.append(_image(item["image"]))
    msgs.append(_text(f"🍽 {name}\n\n📜 {item['description']}\n\n⭐ {item['highlight']}"))
    msgs.append(_text(f"📍 สถานที่\n{item['location']}"))
    _reply(api, event, msgs)

# =========================
# 🕐 TIME HELPERS
# =========================
def _reply_time_by_mode(api, event, p: dict, mode: str):
    name = _s(p.get("place_name"), "สถานที่นี้")
    ot = _safe_time(p.get("open_time"))
    ct = _safe_time(p.get("close_time"))
    if not ot and not ct:
        _reply(api, event, [_text(f"ขอโทษค่ะ ยังไม่มีข้อมูลเวลาของ {name} ค่ะ")])
        return
    if mode == "open":
        _reply(api, event, [_text(f"🕐 {name} เปิด {ot or 'ไม่ระบุ'} น.ค่ะ")])
    elif mode == "close":
        _reply(api, event, [_text(f"🕐 {name} ปิด {ct or 'ไม่ระบุ'} น.ค่ะ")])
    else:
        _reply(api, event, [_text(f"🕐 {name} เปิด {ot or 'ไม่ระบุ'} – {ct or 'ไม่ระบุ'} น.ค่ะ")])

def _detect_time_mode(text: str) -> str:
    has_open  = any(kw in text for kw in ["เปิดกี่โมง","เปิดไหม","เปิดยัง","เปิดกี่","เปิดเวลา","เปิดตอน","ยังเปิด","เปิดอยู่"])
    has_close = any(kw in text for kw in ["ปิดกี่โมง","ปิดไหม","ปิดยัง","ปิดกี่","ปิดเวลา","ปิดตอน","ร้านปิด","ปิดแล้วยัง","ปิดอยู่"])
    has_both  = any(kw in text for kw in ["เวลาเปิดปิด","เปิดปิด","เวลาทำการ"])
    if has_both or (has_open and has_close): return "both"
    if has_open:  return "open"
    if has_close: return "close"
    return "both"

def _detect_category_from_text(text: str) -> str:
    if any(kw in text for kw in ["ร้านปิด","ร้านยังปิด","ร้านเปิด","ร้านยังเปิด","ร้านอาหารปิด","ร้านอาหารเปิด"]):
        return "eat"
    return "all"

def send_time_picker(api, event, mode: str, category: str = "all"):
    if category == "eat":
        rows = get_places_by_category("eat"); names = [r["place_name"] for r in rows] if rows else []
    elif category == "travel":
        rows = get_places_by_category("travel"); names = [r["place_name"] for r in rows] if rows else []
    else:
        names = get_all_place_names()
    if not names:
        _reply(api, event, [_text("ขอโทษค่ะ ยังไม่มีข้อมูลค่ะ")]); return
    prefix_map   = {"open": "เวลาเปิดของ", "close": "เวลาปิดของ", "both": "เวลาเปิดปิดของ"}
    question_map = {"open": "ต้องการทราบเวลาเปิดของที่ไหนคะ? 🕐", "close": "ต้องการทราบเวลาปิดของที่ไหนคะ? 🕐", "both": "ต้องการทราบเวลาเปิด-ปิดของที่ไหนคะ? 🕐"}
    _reply(api, event, [TextMessage(
        text=question_map[mode] + "\nกดเลือกได้เลยค่ะ",
        quick_reply=QuickReply(items=[
            QuickReplyItem(action=MessageAction(label=n[:20], text=f"{prefix_map[mode]}{n}"))
            for n in names[:13]
        ])
    )])

# =========================
# 📩 HANDLE MESSAGE
# =========================
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()

    with ApiClient(configuration) as api_client:
        api = MessagingApi(api_client)

        # ── ทักทาย ──
        if text.lower() in ["สวัสดี","สวัสดีค่ะ","สวัสดีครับ","สวัสดีค่า","สวัสดีคับ",
                             "หวัดดีค่ะ","หวัดดีงับ","ดี","ดีจ้า","หวัดดีคับ","หวัดดี","hi","hello"]:
            greetings = [
                "สวัสดีค่ะ น้องเพชรผู้ช่วยตอบคำถามในอำเภอท่ายาง ยินดีให้บริการค่ะ 😊",
                "สวัสดีค่ะ น้องเพชรพร้อมช่วยแนะนำสถานที่ท่องเที่ยวในท่ายางแล้วค่ะ ✨",
                "สวัสดีค่ะ! น้องเพชรผู้ช่วยของคุณอยู่ที่นี่ พร้อมให้คำตอบทุกคำถามค่ะ 🌟",
                "สวัสดีค่า น้องเพชรมาแล้วค่ะ! วันนี้มีอะไรให้ช่วยดูแลในท่ายาง บอกน้องเพชรได้เลยนะ 💎",
            ]
            _reply(api, event, [_text(random.choice(greetings))])

        elif text in ["ขอบคุณ","ขอบคุณค่ะ","ขอบคุณครับ","ขอบคุณค่า","ขอบคุณนะ","thank you","thanks"]:
            _reply(api, event, [_text("ยินดีให้บริการค่ะ 🗺️💖 หวังว่าจะได้ช่วยให้การเที่ยวสนุกขึ้นนะคะ 😊")])

        # ── Rich Menu ──
        elif text in ["travel", "สถานที่ท่องเที่ยว"]:
            send_places(api, event)

        elif text in ["food", "ร้านอาหาร", "ร้านอาหารในอำเภอท่ายาง", "อาหาร", "กินอะไรดี", "อาหารแนะนำ"]:
            send_restaurants(api, event)

        elif text in ["activity", "กิจกรรมภายในอำเภอท่ายาง"]:
            send_activity(api, event)

        elif text in ["map", "แผนที่ภายในอำเภอท่ายาง"]:
            send_map(api, event)

        elif text in ["souvenir", "ของฝาก", "ของฝากในอำเภอท่ายาง"]:
            send_souvenirs(api, event)

        elif text in ["info", "เกี่ยวกับเรา"]:
            send_info(api, event)

        # ── หมวดอาหาร ──
        elif text.startswith("หมวดอาหาร "):
            send_food_category_list(api, event, text.replace("หมวดอาหาร ", "", 1))

        elif text.startswith("เมนู "):
            rest = text[len("เมนู "):]
            matched_cat = matched_name = None
            for cat in food:
                if rest.startswith(cat + " "):
                    matched_cat = cat; matched_name = rest[len(cat) + 1:]; break
            if matched_cat and matched_name in food[matched_cat]:
                send_food_detail(api, event, matched_cat, matched_name)
            else:
                _reply(api, event, [_text("ขอโทษค่ะ ไม่พบข้อมูลเมนูนี้ค่ะ")])

        # ── รายละเอียดของฝาก (ดึงจาก DB) ──
        elif text.startswith("รายละเอียดของฝาก "):
            name = text.replace("รายละเอียดของฝาก ", "", 1).strip()
            conn = get_conn()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM souvenir_shop WHERE name = %s LIMIT 1", (name,))
            r = cur.fetchone()
            cur.close(); conn.close()
            if r:
                ot = _safe_time(r.get("open_hours")) or "ไม่ระบุ"
                ct = _safe_time(r.get("close_hours")) or "ไม่ระบุ"
                time_str = _fmt_time_range(r.get("open_hours"), r.get("close_hours"), "ไม่ระบุ")
                msg = (
                    f"🎁 {_s(r.get('name'))}\n\n"
                    f"📜 {_s(r.get('description'), 'ยังไม่มีรายละเอียดค่ะ')}\n\n"
                    f"📞 {_s(r.get('phone'), 'ไม่ระบุ')}\n"
                    f"⏰ {time_str}"
                )
                if _valid_url(r.get("map_url")):
                    msg += f"\n🗺 {r['map_url']}"
                _reply(api, event, [_text(msg)])
            else:
                _reply(api, event, [_text(f"ขอโทษค่ะ ไม่พบข้อมูลของ {name} ค่ะ")])

        # ── ของฝาก detail (fallback dict) ──
        elif text.startswith("ของฝาก "):
            name = text.replace("ของฝาก ", "", 1)
            if name in souvenirs:
                send_souvenir_detail(api, event, name)
            else:
                _reply(api, event, [_text("ขอโทษค่ะ ไม่พบข้อมูลของฝากนี้ค่ะ")])

        # ── แผนที่สถานที่ ──
        elif text.startswith("แผนที่ "):
            place_name = text.replace("แผนที่ ", "", 1)
            p = search_place(place_name)
            if p and _valid_url(p.get("map_url")):
                _reply(api, event, [_text(f"🗺 แผนที่ {p['place_name']}\n{p['map_url']}")])
            else:
                _reply(api, event, [_text("ขอโทษค่ะ ไม่พบข้อมูลแผนที่ค่ะ")])

        # ── กิจกรรม detail ──
        elif text in activity_details:
            _reply(api, event, [_text(activity_details[text])])

        # ── INFO ──
        elif text == "วัฒนธรรมท่ายาง":
            send_culture(api, event)

        elif text in INFO_KEY_MAP:
            _reply(api, event, [_text(info.get(INFO_KEY_MAP[text], "ขอโทษค่ะ ไม่พบข้อมูลนี้ค่ะ"))])

        elif text.startswith("วัฒนธรรม "):
            place_name = text.replace("วัฒนธรรม ", "", 1)
            key = CULTURE_KEY_MAP.get(place_name)
            _reply(api, event, [_text(info[key] if key and key in info else "ขอโทษค่ะ ไม่พบข้อมูลนี้ค่ะ")])

        # ── สถานที่ใน places.py ──
        elif text in places and text != "แผนที่อำเภอท่ายาง":
            send_place_detail(api, event, text)

        # ── เวลา (quick reply response) ──
        elif text.startswith("เวลาเปิดปิดของ"):
            pname = text.replace("เวลาเปิดปิดของ", "", 1).strip()
            p = search_place(pname)
            if p: _reply_time_by_mode(api, event, p, "both")
            else: _reply(api, event, [_text(f"ขอโทษค่ะ ไม่พบข้อมูลของ {pname} ค่ะ")])

        elif text.startswith("เวลาเปิดของ"):
            pname = text.replace("เวลาเปิดของ", "", 1).strip()
            p = search_place(pname)
            if p: _reply_time_by_mode(api, event, p, "open")
            else: _reply(api, event, [_text(f"ขอโทษค่ะ ไม่พบข้อมูลของ {pname} ค่ะ")])

        elif text.startswith("เวลาปิดของ"):
            pname = text.replace("เวลาปิดของ", "", 1).strip()
            p = search_place(pname)
            if p: _reply_time_by_mode(api, event, p, "close")
            else: _reply(api, event, [_text(f"ขอโทษค่ะ ไม่พบข้อมูลของ {pname} ค่ะ")])

        # ── ตรวจจับคำถามเวลา ──
        elif any(kw in text for kw in [
            "เปิดกี่โมง","เปิดไหม","เปิดยัง","ปิดกี่โมง","ปิดไหม","ปิดยัง","เวลาเปิดปิด","เวลาทำการ"
        ]):
            mode = _detect_time_mode(text)
            matched_place = next((n for n in get_all_place_names() if n in text), None)
            if matched_place:
                p = search_place(matched_place)
                if p: _reply_time_by_mode(api, event, p, mode)
                else: _reply(api, event, [_text(f"ขอโทษค่ะ ไม่พบข้อมูลของ {matched_place} ค่ะ")])
            else:
                send_time_picker(api, event, mode, _detect_category_from_text(text))

        # ── แนะนำที่เที่ยว/ร้านอาหาร ──
        elif any(kw in text for kw in ["แนะนำที่เที่ยว","ที่เที่ยวแนะนำ","มีที่เที่ยวอะไรบ้าง","สถานที่น่าเที่ยว","แนะนำสถานที่"]):
            send_places(api, event)

        elif any(kw in text for kw in ["แนะนำที่กิน","แนะนำร้านอาหาร","ร้านอาหารแนะนำ","มีร้านอาหารอะไรบ้าง","ร้านไหนอร่อย"]):
            send_restaurants(api, event)

        elif any(kw in text for kw in ["ไปไหนดี","อยากเที่ยว","เที่ยวไหนดี","น่าเที่ยว","เที่ยวที่ไหนดี"]):
            _reply(api, event, [
                _text("น้องเพชรมีกิจกรรมแนะนำในท่ายางเลยค่ะ 🗺️"),
                TextMessage(
                    text="อยากทำอะไรคะ? กดเลือกได้เลยนะคะ 👇",
                    quick_reply=QuickReply(items=[
                        QuickReplyItem(action=MessageAction(label="🙏 ไหว้พระทำบุญ",     text="ไหว้พระในท่ายาง")),
                        QuickReplyItem(action=MessageAction(label="📸 ถ่ายรูปเช็คอิน",   text="ถ่ายรูปในท่ายาง")),
                        QuickReplyItem(action=MessageAction(label="🐟 ให้อาหารปลา",      text="ให้อาหารปลาในท่ายาง")),
                        QuickReplyItem(action=MessageAction(label="🍜 ตะลอนกิน",         text="ตะลอนกินในท่ายาง")),
                        QuickReplyItem(action=MessageAction(label="🏛️ ดูสถานที่ทั้งหมด", text="สถานที่ท่องเที่ยว")),
                    ])
                )
            ])

        # ── Dialogflow fallback ──
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
                        send_restaurants(api, event)
                    elif intent == "place.search" and place_name:
                        p = search_place(place_name)
                        if p:
                            msg = f"📍 {_s(p.get('place_name'), place_name)}\n\n📖 {_s(p.get('place_description'), 'ยังไม่มีรายละเอียดค่ะ')}"
                            time_str = _fmt_time_range(p.get("open_time"), p.get("close_time"), "")
                            if time_str:
                                msg += f"\n\n🕐 {time_str}"
                            _reply(api, event, [_text(msg)])
                        elif place_name in places:
                            send_place_detail(api, event, place_name)
                        else:
                            _reply(api, event, [_text(f"ขอโทษค่ะ ไม่พบข้อมูลของ {place_name} ค่ะ")])
                    elif intent == "place.opentime":
                        mode = _detect_time_mode(text)
                        if place_name:
                            p = search_place(place_name)
                            if p: _reply_time_by_mode(api, event, p, mode)
                            else: _reply(api, event, [_text(f"ขอโทษค่ะ ไม่พบข้อมูลของ {place_name} ค่ะ")])
                        else:
                            send_time_picker(api, event, mode, _detect_category_from_text(text))
                    else:
                        p = search_place(text)
                        if p: send_place_detail(api, event, text)
                        else: _reply(api, event, [_text(ask_ai(text))])
                else:
                    p = search_place(text)
                    if p: send_place_detail(api, event, text)
                    else: _reply(api, event, [_text(ask_ai(text))])

            except Exception as e:
                print("Dialogflow error:", e)
                p = search_place(text)
                if p: send_place_detail(api, event, text)
                else: _reply(api, event, [_text(ask_ai(text))])

# =========================
# 🚀 RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
