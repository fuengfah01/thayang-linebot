from flask import Flask, request, send_from_directory
from linebot.v3.messaging import (
    ApiClient, Configuration, MessagingApi,
    ReplyMessageRequest,
    TextMessage, ImageMessage,
    QuickReply, QuickReplyItem, MessageAction,
)
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from rapidfuzz import process

from places import places
from info import info
from questions import questions
from food import food
from ai_helper import ask_ai

import random
import os

app = Flask(__name__)

# =========================
# 🔑 CONFIG
# =========================
CHANNEL_ACCESS_TOKEN = "4daQ2JUnEe+vEmbDJhOmn48fWc7d/Kb6+iWXIm05H8ngOFqDPLyNpgdTO58cKvHyfcL/q/gytkIljJiMSjAQCvN5wmahGaLKoVocuepLo5tyQq7q33YfsPZPhxpO8kPOrpnECFRdZPB0JjHKaKaPOQdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "a97e9e9977b3aac81ca9af33e59bde55"

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# =========================
# 🎁 SOUVENIRS DATA (พร้อมพิกัดร้านในอำเภอท่ายาง)
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
    """ส่งข้อความตอบกลับ (รองรับสูงสุด 5 messages ต่อครั้ง)"""
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
# 🖼 ROUTE รูปภาพ
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
# 🔗 WEBHOOK
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
# 🧠 FUZZY SEARCH
# =========================
def fuzzy_search_place(text):
    text = text.lower()
    all_choices = []
    mapping = {}

    for name, data in places.items():
        all_choices.append(name)
        mapping[name] = name
        for k in data.get("keywords", []):
            all_choices.append(k)
            mapping[k] = name
        for s in data.get("synonyms", []):
            all_choices.append(s)
            mapping[s] = name

    result = process.extractOne(text, all_choices)
    if result:
        word, score, _ = result
        if score > 60:
            return mapping[word]
    return None


# =========================
# 📍 สถานที่ — แยก bubble
# =========================
def send_place_detail(api, event, name):
    p = places[name]
    msgs = []

    # 1) รูปภาพ
    if p.get("images"):
        msgs.append(_image(p["images"][0]))

    # 2) ประวัติ
    msgs.append(_text(f"📜 ประวัติ {name}\n\n{p['history']}"))

    # 3) จุดเด่น + เวลา
    msgs.append(_text(
        f"⭐ จุดเด่น\n{p['highlight']}\n\n"
        f"⏰ เวลาทำการ\n{p.get('time', 'ไม่ระบุ')}"
    ))

    _reply(api, event, msgs)


# =========================
# 🗺 MAP
# =========================
def send_map(api, event):
    # กรองเฉพาะสถานที่ที่มีข้อมูล map
    names = [n for n in list(places.keys()) if places[n].get("map")][:9]
    _reply(api, event, [
        TextMessage(
            text="🗺 เลือกสถานที่ที่ต้องการดูแผนที่ค่ะ",
            quick_reply=QuickReply(items=[
                QuickReplyItem(action=MessageAction(label=n, text=f"แผนที่ {n}"))
                for n in names
            ] + [
                QuickReplyItem(action=MessageAction(label="ภาพรวมท่ายาง", text="แผนที่ท่ายางทั้งหมด"))
            ])
        )
    ])


# =========================
# 🏃 ACTIVITY
# =========================
activity_details = {
    "ไหว้พระในท่ายาง":    "🙏 ไหว้พระในท่ายาง\n\n• วัดท่าคอย\n• ศาลเจ้าพ่อกวนอู\n• ศาลเจ้าแม่ทับทิม",
    "ถ่ายรูปในท่ายาง":    "📸 จุดถ่ายรูปในท่ายาง\n\n• วัดท่าคอย\n• ศาลเจ้าพ่อกวนอู\n• ศาลเจ้าแม่ทับทิม\n• อุโบสถ 100 ปี",
    "ให้อาหารปลาในท่ายาง": "🐟 ให้อาหารปลาในท่ายาง\n\n• อุทยานปลาวัดท่าคอย",
    "ตะลอนกินในท่ายาง":   "🍜 ตะลอนกินในท่ายาง\n\n• ตลาดสดท่ายาง\n• ร้านทองม้วนแม่เล็ก\n• ร้านผัดไทย 100 ปี\n• ร้านข้าวแช่แม่เล็ก สกิดใจ",
}


def send_activity(api, event):
    _reply(api, event, [
        _text("🧭 กิจกรรมแนะนำในท่ายาง"),
        TextMessage(
            text="👇 กดเลือกกิจกรรมที่สนใจได้เลยค่ะ",
            quick_reply=QuickReply(items=[
                QuickReplyItem(action=MessageAction(label="🙏 ไหว้พระ",       text="ไหว้พระในท่ายาง")),
                QuickReplyItem(action=MessageAction(label="📸 ถ่ายรูป",        text="ถ่ายรูปในท่ายาง")),
                QuickReplyItem(action=MessageAction(label="🐟 ให้อาหารปลา",   text="ให้อาหารปลาในท่ายาง")),
                QuickReplyItem(action=MessageAction(label="🍜 ตะลอนกิน",      text="ตะลอนกินในท่ายาง")),
            ])
        )
    ])


# =========================
# 📖 INFO
# =========================
# mapping ชื่อภาษาไทยที่ผู้ใช้กด → key ใน info dict
INFO_KEY_MAP = {
    "ประวัติท่ายาง":   "history",
    "จุดเด่นท่ายาง":   "highlight",
    "วิถีชีวิตท่ายาง": "lifestyle",
    "ติดต่อท่ายาง":    "contact",
}

# mapping ชื่อสถานที่ (หลัง "วัฒนธรรม ") → key ใน info dict
CULTURE_KEY_MAP = {
    "วัดท่าคอย":              "culture_wat_takhoi",
    "อุโบสถ 100 ปี":         "culture_ubosot",
    "อุทยานปลาวัดท่าคอย":   "culture_fish_park",
    "ตลาดสดท่ายาง":          "culture_market",
    "ร้านทองม้วนแม่เล็ก":    "culture_thong_muan",
    "ร้านผัดไทย 100 ปี":     "culture_padthai",
    "ศาลเจ้าพ่อกวนอู":       "culture_guanyu",
    "ข้าวแช่แม่เล็ก":         "culture_khao_chae",
    "ศาลเจ้าแม่ทับทิม":      "culture_tapthim",
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
                QuickReplyItem(action=MessageAction(label="วัดท่าคอย",           text="วัฒนธรรม วัดท่าคอย")),
                QuickReplyItem(action=MessageAction(label="อุโบสถ 100 ปี",       text="วัฒนธรรม อุโบสถ 100 ปี")),
                QuickReplyItem(action=MessageAction(label="อุทยานปลา",           text="วัฒนธรรม อุทยานปลาวัดท่าคอย")),
                QuickReplyItem(action=MessageAction(label="ตลาดสดท่ายาง",       text="วัฒนธรรม ตลาดสดท่ายาง")),
                QuickReplyItem(action=MessageAction(label="ทองม้วนแม่เล็ก",     text="วัฒนธรรม ร้านทองม้วนแม่เล็ก")),
                QuickReplyItem(action=MessageAction(label="ผัดไทย 100 ปี",      text="วัฒนธรรม ร้านผัดไทย 100 ปี")),
                QuickReplyItem(action=MessageAction(label="ศาลเจ้าพ่อกวนอู",    text="วัฒนธรรม ศาลเจ้าพ่อกวนอู")),
                QuickReplyItem(action=MessageAction(label="ข้าวแช่แม่เล็ก",     text="วัฒนธรรม ข้าวแช่แม่เล็ก")),
                QuickReplyItem(action=MessageAction(label="ศาลเจ้าแม่ทับทิม",   text="วัฒนธรรม ศาลเจ้าแม่ทับทิม")),
            ])
        )
    ])


def send_places(api, event):
    names = list(places.keys())[:9]
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
# 🎁 SOUVENIRS — แยก bubble
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

    # 1) ชื่อ + รายละเอียด
    msgs.append(_text(f"🎁 {name}\n\n📜 {s['description']}"))

    # 2) รายชื่อร้านพร้อมพิกัด
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
# 🍽 FOOD — แยก bubble
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

    # 1) รูปภาพ
    if item.get("image"):
        msgs.append(_image(item["image"]))

    # 2) ชื่อเมนู + รายละเอียด + จุดเด่น
    msgs.append(_text(
        f"🍽 {name}\n\n"
        f"📜 {item['description']}\n\n"
        f"⭐ {item['highlight']}"
    ))

    # 3) สถานที่
    msgs.append(_text(f"📍 สถานที่\n{item['location']}"))

    # 4) เครดิตภาพ (ถ้ามี)
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

        # ─── สวัสดี ───────────────────────────────────────────────────────
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

        # ─── ขอบคุณ ──────────────────────────────────────────────────────
        elif text in ["ขอบคุณ", "ขอบคุณค่ะ", "ขอบคุณครับ", "ขอบคุณค่า", "ขอบคุณนะ", "thank you", "thanks"]:
            _reply(api, event, [_text(
                "ยินดีให้บริการค่ะ 🗺️💖 ขอบคุณที่แวะมาสอบถามนะคะ "
                "หวังว่าจะได้ช่วยให้การเที่ยวของคุณสนุกขึ้นนะคะ 😊"
            )])

        # ─── อาหาร ───────────────────────────────────────────────────────
        elif text in ["food", "ร้านอาหาร", "อาหาร", "ร้านอาหารในอำเภอท่ายาง", "กินอะไรดี", "อาหารแนะนำ"]:
            send_food_categories(api, event)

        # ─── หมวดอาหาร xxx → รายการเมนู ─────────────────────────────────
        elif text.startswith("หมวดอาหาร "):
            category = text.replace("หมวดอาหาร ", "", 1)
            send_food_category_list(api, event, category)

        # ─── เมนู หมวด ชื่อ → รายละเอียด ────────────────────────────────
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

        # ─── ของฝาก ──────────────────────────────────────────────────────
        elif text in ["souvenir", "ของฝาก", "ของฝากในอำเภอท่ายาง"]:
            send_souvenirs(api, event)

        elif text.startswith("ของฝาก "):
            name = text.replace("ของฝาก ", "", 1)
            if name in souvenirs:
                send_souvenir_detail(api, event, name)
            else:
                _reply(api, event, [_text("ขอโทษค่ะ ไม่พบข้อมูลของฝากนี้ค่ะ")])

        # ─── สถานที่ ──────────────────────────────────────────────────────
        elif text in ["travel", "สถานที่ท่องเที่ยว"]:
            send_places(api, event)

        elif text in places:
            send_place_detail(api, event, text)

        # ─── แผนที่ ───────────────────────────────────────────────────────
        elif text in ["map", "แผนที่ภายในอำเภอท่ายาง"]:
            send_map(api, event)

        elif text == "แผนที่ท่ายางทั้งหมด":
            url = places["แผนที่อำเภอท่ายาง"]["map_all"]
            _reply(api, event, [_text(f"🗺 แผนที่อำเภอท่ายาง\n{url}")])

        elif text.startswith("แผนที่ "):
            place_name = text.replace("แผนที่ ", "", 1)
            if place_name in places and places[place_name].get("map"):
                _reply(api, event, [_text(f"🗺 แผนที่ {place_name}\n{places[place_name]['map']}")])
            else:
                _reply(api, event, [_text("ขอโทษค่ะ ไม่พบข้อมูลแผนที่ของสถานที่นี้ค่ะ")])

        # ─── กิจกรรม ──────────────────────────────────────────────────────
        elif text in ["activity", "กิจกรรมภายในอำเภอท่ายาง"]:
            send_activity(api, event)

        elif text in activity_details:
            _reply(api, event, [_text(activity_details[text])])

        # ─── info ─────────────────────────────────────────────────────────
        elif text in ["info", "เกี่ยวกับเรา"]:
            send_info(api, event)

        elif text == "วัฒนธรรมท่ายาง":
            send_culture(api, event)

        # ─── info หัวข้อ (ชื่อไทย) ─────────────────────────────────────
        elif text in INFO_KEY_MAP:
            key = INFO_KEY_MAP[text]
            _reply(api, event, [_text(info.get(key, "ขอโทษค่ะ ไม่พบข้อมูลนี้ค่ะ"))])

        # ─── วัฒนธรรม ชื่อสถานที่ ─────────────────────────────────────────
        elif text.startswith("วัฒนธรรม "):
            place_name = text.replace("วัฒนธรรม ", "", 1)
            key = CULTURE_KEY_MAP.get(place_name)
            if key and key in info:
                _reply(api, event, [_text(info[key])])
            else:
                _reply(api, event, [_text("ขอโทษค่ะ ไม่พบข้อมูลนี้ค่ะ")])

        # ─── ใช่_xxx → ยืนยัน fuzzy match ────────────────────────────────
        elif text.startswith("ใช่_"):
            name = text.replace("ใช่_", "", 1)
            if name in places:
                send_place_detail(api, event, name)
            elif name in souvenirs:
                send_souvenir_detail(api, event, name)
            elif name in questions:
                _reply(api, event, [_text(questions[name])])
            else:
                _reply(api, event, [_text("ขอโทษค่ะ ไม่พบข้อมูล")])

        # ─── ไม่ใช่ ───────────────────────────────────────────────────────
        elif text == "ไม่ใช่":
            _reply(api, event, [_text("ขอโทษค่ะ ลองพิมพ์ใหม่อีกครั้งนะคะ 😊")])

        # ─── Fuzzy → AI fallback ──────────────────────────────────────────
        else:
            match_place = fuzzy_search_place(text)
            match = None
            is_question = False

            if not match_place:
                match_question = process.extractOne(text, list(questions.keys()))
                if match_question and match_question[1] > 60:
                    match = match_question[0]
                    is_question = True
            else:
                match = match_place

            if match:
                _reply(api, event, [
                    TextMessage(
                        text=f"คุณหมายถึง {match} ใช่ไหมคะ?",
                        quick_reply=QuickReply(items=[
                            QuickReplyItem(action=MessageAction(label="✅ ใช่", text=f"ใช่_{match}")),
                            QuickReplyItem(action=MessageAction(label="❌ ไม่ใช่", text="ไม่ใช่")),
                        ])
                    )
                ])
            else:
                # 🤖 ส่งให้ AI ตอบอิสระ
                ai_answer = ask_ai(text)
                _reply(api, event, [_text(ai_answer)])


# =========================
# 🚀 RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)