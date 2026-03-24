from flask import Flask, request, send_from_directory
from linebot.v3.messaging import *
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from rapidfuzz import process

from places import places
from info import info
from questions import questions
from food import food

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
# 🎁 SOUVENIRS DATA (ย้ายมาจาก souvenirs.py)
# =========================
souvenirs = {
    "ขนมหม้อแกง": {
        "description": "ขนมหวานขึ้นชื่อของจังหวัดเพชรบุรี ทำจากไข่ กะทิ น้ำตาลโตนด รสชาติหวานมัน หอม",
        "location": "อำเภอท่ายาง จังหวัดเพชรบุรี"
    },
    "น้ำตาลโตนด": {
        "description": "ผลิตจากต้นตาลโตนด เป็นของดีของเพชรบุรี ใช้ทำอาหารและขนมหวาน มีกลิ่นหอมเฉพาะตัว",
        "location": "อำเภอท่ายาง จังหวัดเพชรบุรี"
    },
    "ขนมตาล": {
        "description": "ขนมพื้นบ้าน ทำจากเนื้อลูกตาล มีรสหวานหอม เนื้อนุ่มฟู",
        "location": "อำเภอท่ายาง จังหวัดเพชรบุรี"
    },
    "ทองม้วน": {
        "description": "ขนมกรอบ หอมกะทิ ม้วนเป็นแท่ง เก็บได้นาน เหมาะเป็นของฝาก",
        "location": "อำเภอท่ายาง จังหวัดเพชรบุรี"
    },
    "กล้วยฉาบ": {
        "description": "กล้วยทอดกรอบ รสหวานหรือเค็ม เป็นของกินเล่นยอดนิยม",
        "location": "อำเภอท่ายาง จังหวัดเพชรบุรี"
    },
}

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
# 🧠 AI หาใกล้เคียง
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
# 📍 สถานที่
# =========================
def send_place_detail(api, event, name):
    p = places[name]
    messages = []

    if p.get("images"):
        messages.append(
            ImageMessage(
                original_content_url=p["images"][0],
                preview_image_url=p["images"][0]
            )
        )

    messages.append(
        TextMessage(
            text=f"""📍 {name}

📜 ประวัติ:
{p['history']}

⭐ จุดเด่น:
{p['highlight']}

⏰ เวลา:
{p['time']}
"""
        )
    )

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=messages[:2]
        )
    )

# =========================
# 🗺 MAP
# =========================
def send_map(api, event):
    names = list(places.keys())[:9]

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(
                    text="🗺 เลือกสถานที่",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyItem(action=MessageAction(label=n, text=f"map_{n}"))
                            for n in names
                        ] + [
                            QuickReplyItem(action=MessageAction(label="แผนที่ท่ายาง", text="map_all"))
                        ]
                    )
                )
            ]
        )
    )

# =========================
# 🏨 ACTIVITY
# =========================
def send_activity(api, event):
    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(text="🧭 กิจกรรมแนะนำในท่ายาง"),
                TextMessage(
                    text="เลือกกิจกรรมที่สนใจ",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyItem(action=MessageAction(label="🙏 ไหว้พระ", text="activity_pray")),
                            QuickReplyItem(action=MessageAction(label="📸 ถ่ายรูป", text="activity_photo")),
                            QuickReplyItem(action=MessageAction(label="🐟 ให้อาหารปลา", text="activity_fish")),
                            QuickReplyItem(action=MessageAction(label="🍜 ตะลอนกิน", text="activity_eat")),
                        ]
                    )
                )
            ]
        )
    )

activity_details = {
    "activity_pray": """🙏 ไหว้พระในท่ายาง

- วัดท่าคอย
- ศาลเจ้าพ่อกวนอู
- ศาลเจ้าแม่ทับทิม""",

    "activity_photo": """📸 จุดถ่ายรูปในท่ายาง

- วัดท่าคอย
- ศาลเจ้าพ่อกวนอู
- ศาลเจ้าแม่ทับทิม
- อุโบสถ 100 ปี""",

    "activity_fish": """🐟 ให้อาหารปลาในท่ายาง

- อุทยานปลาวัดท่าคอย""",

    "activity_eat": """🍜 ตะลอนกินในท่ายาง

- ตลาดสดท่ายาง
- ร้านทองม้วนแม่เล็ก
- ร้านผัดไทย 100 ปี
- ร้านข้าวแช่แม่เล็ก สกิดใจ""",
}

# =========================
# 📖 INFO
# =========================
def send_info(api, event):
    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(text="📖 เกี่ยวกับท่ายาง"),
                TextMessage(
                    text="เลือกหัวข้อ",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyItem(action=MessageAction(label="📜 ประวัติ", text="info_history")),
                            QuickReplyItem(action=MessageAction(label="⭐ จุดเด่น", text="info_highlight")),
                            QuickReplyItem(action=MessageAction(label="🌿 วิถีชีวิต", text="info_lifestyle")),
                            QuickReplyItem(action=MessageAction(label="🛕 วัฒนธรรม", text="info_culture"))
                        ]
                    )
                )
            ]
        )
    )

def send_culture(api, event):
    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(text="🏛️ วัฒนธรรมท่ายาง"),
                TextMessage(
                    text="เลือกสถานที่",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyItem(action=MessageAction(label="วัดท่าคอย", text="info_culture_wat_takhoi")),
                            QuickReplyItem(action=MessageAction(label="อุโบสถ 100 ปี", text="info_culture_ubosot")),
                            QuickReplyItem(action=MessageAction(label="อุทยานปลาวัดท่าคอย", text="info_culture_fish_park")),
                            QuickReplyItem(action=MessageAction(label="ตลาดสดท่ายาง", text="info_culture_market")),
                            QuickReplyItem(action=MessageAction(label="ร้านทองม้วนแม่เล็ก", text="info_culture_thong_muan")),
                            QuickReplyItem(action=MessageAction(label="ร้านผัดไทย 100 ปี", text="info_culture_padthai")),
                            QuickReplyItem(action=MessageAction(label="ศาลเจ้าพ่อกวนอู", text="info_culture_guanyu")),
                            QuickReplyItem(action=MessageAction(label="ข้าวแช่แม่เล็ก", text="info_culture_khao_chae")),
                            QuickReplyItem(action=MessageAction(label="ศาลเจ้าแม่ทับทิม", text="info_culture_tapthim"))
                        ]
                    )
                )
            ]
        )
    )

def send_places(api, event):
    names = list(places.keys())[:9]

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(
                    text="📍 เลือกสถานที่ท่องเที่ยว",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyItem(
                                action=MessageAction(label=name, text=name)
                            )
                            for name in names
                        ]
                    )
                )
            ]
        )
    )

def send_food(api, event):
    food_names = [name for name, p in places.items() if p.get("type") == "food"]
    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(
                    text="🍜 ร้านอาหารในท่ายาง",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyItem(
                                action=MessageAction(label=name, text=name)
                            )
                            for name in food_names[:10]
                        ]
                    )
                )
            ]
        )
    )

# =========================
# 🎁 SOUVENIRS
# =========================
def send_souvenirs(api, event):
    names = list(souvenirs.keys())[:10]

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(
                    text="🎁 ของฝากขึ้นชื่อในท่ายาง",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyItem(
                                action=MessageAction(label=name, text=f"souvenir_{name}")
                            )
                            for name in names
                        ]
                    )
                )
            ]
        )
    )

def send_souvenir_detail(api, event, name):
    s = souvenirs[name]
    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(
                    text=f"""🎁 {name}

📜 รายละเอียด:
{s['description']}

📍 แหล่งที่มา:
{s['location']}
"""
                )
            ]
        )
    )


def send_food_detail(api, event, name):
    f = food[name]

    location_text, map_url = f["location"].split("|")

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(
                    text=f"""🍜 {name}

📜 รายละเอียด:
{f['description']}

⭐ จุดเด่น:
{f['highlight']}

📍 {location_text.strip()}

🗺 แผนที่:
{map_url.strip()}
"""
                )
            ]
        )
    )

# =========================
# 📩 HANDLE
# =========================
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()
    match = None
    is_question = False

    with ApiClient(configuration) as api_client:
        api = MessagingApi(api_client)

        # 🔹 ตอบสวัสดีแบบสุ่ม
        if text.lower() in ["สวัสดี", "สวัสดีค่ะ", "สวัสดีครับ", "สวัสดีค่า", "สวัสดีคับ", "หวัดดีค่ะ", "หวัดดีงับ", "ดี", "ดีจ้า", "หวัดดีคับ", "หวัดดี", "hi", "hello"]:
            greetings = [
                "สวัสดีค่ะน้องเพชรผู้ช่วยตอบคำถามในอำเภอท่ายาง ยินดีให้บริการค่ะ",
                "สวัสดีค่ะ น้องเพชรพร้อมช่วยแนะนำสถานที่ท่องเที่ยวในท่ายางแล้วค่ะ",
                "สวัสดีค่ะ! น้องเพชรผู้ช่วยของคุณอยู่ที่นี่ พร้อมให้คำตอบทุกคำถามค่ะ",
                "สวัสดีค่า น้องเพชรมาแล้วค่ะ! วันนี้มีอะไรให้ช่วยดูแลในท่ายาง บอกน้องเพชรได้เลยนะ",
                "ยินดีต้อนรับสู่ท่ายางนะคะ น้องเพชรพร้อมเป็นไกด์ส่วนตัวให้คุณแล้วค่ะ"
            ]
            reply_text = random.choice(greetings)
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )
            return

        # 🔹 ตรวจสอบ ใช่_ ก่อน fuzzy
        if text.startswith("ใช่_"):
            name = text.replace("ใช่_", "")
            if name in places:
                send_place_detail(api, event, name)
            elif name in souvenirs:
                send_souvenir_detail(api, event, name)
            elif name in questions:
                api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=questions[name])]
                    )
                )
            elif text.startswith("food_"):
                name = text.replace("food_", "")
                if name in food:
                    send_food_flex(event, name)
            else:
                api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="ขอโทษค่ะ ไม่พบข้อมูล")]
                    )
                )
            return

        # 🔹 ตรวจสอบคำสั่งต่างๆ
        elif text in ["souvenir", "ของฝาก", "ของฝากในอำเภอท่ายาง"]:
            send_souvenirs(api, event)

        elif text.startswith("souvenir_"):
            name = text.replace("souvenir_", "")
            if name in souvenirs:
                send_souvenir_detail(api, event, name)
            else:
                api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="ขอโทษค่ะ ไม่พบข้อมูลของฝากนี้ค่ะ")]
                    )
                )

        elif text in ["travel", "สถานที่ท่องเที่ยว"]:
            send_places(api, event)

        elif text in places:
            send_place_detail(api, event, text)

        elif text in ["map", "แผนที่ภายในอำเภอท่ายาง"]:
            send_map(api, event)

        elif text.startswith("map_"):
            name = text.replace("map_", "")
            if name == "all":
                url = places["แผนที่อำเภอท่ายาง"]["map_all"]
            else:
                url = places[name]["map"]
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f"🗺 {url}")]
                )
            )

        elif text in ["activity", "กิจกรรมภายในอำเภอท่ายาง"]:
            send_activity(api, event)
        
        elif text.startswith("food_"):
            name = text.replace("food_", "")
            if name in food:
                send_food_detail(api, event, name)

        elif text in ["info", "เกี่ยวกับเรา"]:
            send_info(api, event)

        elif text == "info_culture":
            send_culture(api, event)

        elif text.startswith("info_"):
            key = text.replace("info_", "")
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=info[key])]
                )
            )

        elif text in activity_details:
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=activity_details[text])]
                )
            )

        elif text in ["ขอบคุณ", "ขอบคุณค่ะ", "ขอบคุณครับ", "ขอบคุณค่า", "ขอบคุณนะ", "thank you", "thanks"]:
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="ยินดีให้บริการค่ะ 🗺️💖 ขอบคุณที่แวะมาสอบถามนะคะ หวังว่าจะได้ช่วยให้การเที่ยวของคุณสนุกขึ้นนะคะ 😊")]
                )
            )

        else:
            # 🔹 fuzzy search ทั้ง places และ questions
            match_place = fuzzy_search_place(text)
            match_question = None

            if not match_place:
                match_question = process.extractOne(text, list(questions.keys()))
                if match_question and match_question[1] > 60:
                    match = match_question[0]
                    is_question = True
            else:
                match = match_place

            if match:
                api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(
                            text=f"คุณหมายถึง {match} ใช่ไหม",
                            quick_reply=QuickReply(
                                items=[
                                    QuickReplyItem(action=MessageAction(label="ใช่", text=f"ใช่_{match}")),
                                    QuickReplyItem(action=MessageAction(label="ไม่ใช่", text="ไม่ใช่"))
                                ]
                            )
                        )]
                    )
                )
            elif text == "ไม่ใช่":
                api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="ขอโทษค่ะ ลองพิมพ์ใหม่อีกครั้งนะคะ")]
                    )
                )
            else:
                api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="ขอโทษค่ะ ไม่เข้าใจคำถาม กรุณาพิมพ์ใหม่")]
                    )
                )

# =========================
# 🚀 RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)