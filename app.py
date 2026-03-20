from flask import Flask, request, send_from_directory
from linebot.v3.messaging import *
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from rapidfuzz import process

from places import places
from info import info
from questions import questions

import random  # 🔹 เพิ่มด้านบนไฟล์
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
        # ชื่อหลัก
        all_choices.append(name)
        mapping[name] = name

        # keywords
        for k in data.get("keywords", []):
            all_choices.append(k)
            mapping[k] = name

        # synonyms
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

    # 🔹 สร้าง carousel เฉพาะถ้ามีรูป
    if p["images"]:
        bubbles = []
        for img in p["images"]:
            bubble = BubbleContainer(
                hero=ImageComponent(
                    url=img,
                    size="full",
                    aspect_ratio="20:13",
                    aspect_mode="cover"
                )
            )
            bubbles.append(bubble)

        flex = FlexMessage(
            alt_text=f"{name}",
            contents=CarouselContainer(contents=bubbles)
        )
        messages.append(flex)

    # 🔹 ข้อมูลข้อความ
    text = TextMessage(
        text=f"""📍 {name}

📜 ประวัติ:
{p['history']}

⭐ จุดเด่น:
{p['highlight']}

⏰ เวลา:
{p['time']}
"""
    )
    messages.append(text)

    # 🔹 ส่งข้อความทั้งหมด
    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=messages
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
                            QuickReplyItem(action=MessageAction(label="แผนที่อำเภอ", text="map_all"))
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
                TextMessage(text="🏨 กิจกรรมแนะนำในท่ายาง"),
                TextMessage(
                    text="เลือกกิจกรรมที่สนใจ",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyItem(action=MessageAction(label="🙏 ไหว้พระ", text="กิจกรรม_ไหว้พระ")),
                            QuickReplyItem(action=MessageAction(label="📸 ถ่ายรูป", text="กิจกรรม_ถ่ายรูป")),
                            QuickReplyItem(action=MessageAction(label="🐟 ให้อาหารปลา", text="กิจกรรม_ให้อาหารปลา")),
                            QuickReplyItem(action=MessageAction(label="🍜 ตะลอนกิน", text="กิจกรรม_ตะลอนกิน")),
                        ]
                    )
                )
            ]
        )
    )


activity_details = {
    "กิจกรรม_ไหว้พระ": """🙏 ไหว้พระในท่ายาง

- วัดท่าคอย
- ศาลเจ้าพ่อกวนอู
- ศาลเจ้าแม่ทับทิม""",

    "กิจกรรม_ถ่ายรูป": """📸 จุดถ่ายรูปในท่ายาง

- วัดท่าคอย
- ศาลเจ้าพ่อกวนอู
- ศาลเจ้าแม่ทับทิม
- อุโบสถ 100 ปี""",

    "กิจกรรม_ให้อาหารปลา": """🐟 ให้อาหารปลาในท่ายาง

- อุทยานปลาวัดท่าคอย""",

    "กิจกรรม_ตะลอนกิน": """🍜 ตะลอนกินในท่ายาง

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
                            QuickReplyItem(action=MessageAction(label="📜 ประวัติ", text="ข้อมูล_ประวัติ")),
                            QuickReplyItem(action=MessageAction(label="⭐ จุดเด่น", text="ข้อมูล_จุดเด่น")),
                            QuickReplyItem(action=MessageAction(label="🌿 วิถีชีวิต", text="ข้อมูล_วิถีชีวิต")),
                            QuickReplyItem(action=MessageAction(label="🛕 วัฒนธรรม", text="ข้อมูล_วัฒนธรรม"))
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
                            QuickReplyItem(action=MessageAction(label="วัดท่าคอย",          text="ข้อมูล_วัฒนธรรม_วัดท่าคอย")),
                            QuickReplyItem(action=MessageAction(label="อุโบสถ 100 ปี",      text="ข้อมูล_วัฒนธรรม_อุโบสถ")),
                            QuickReplyItem(action=MessageAction(label="อุทยานปลาวัดท่าคอย", text="ข้อมูล_วัฒนธรรม_อุทยานปลา")),
                            QuickReplyItem(action=MessageAction(label="ตลาดสดท่ายาง",       text="ข้อมูล_วัฒนธรรม_ตลาดสด")),
                            QuickReplyItem(action=MessageAction(label="ร้านทองม้วนแม่เล็ก",  text="ข้อมูล_วัฒนธรรม_ทองม้วน")),
                            QuickReplyItem(action=MessageAction(label="ร้านผัดไทย 100 ปี",   text="ข้อมูล_วัฒนธรรม_ผัดไทย")),
                            QuickReplyItem(action=MessageAction(label="ศาลเจ้าพ่อกวนอู",    text="ข้อมูล_วัฒนธรรม_กวนอู")),
                            QuickReplyItem(action=MessageAction(label="ข้าวแช่แม่เล็ก",     text="ข้อมูล_วัฒนธรรม_ข้าวแช่")),
                            QuickReplyItem(action=MessageAction(label="สกิดใจ",             text="ข้อมูล_วัฒนธรรม_สกิดใจ")),
                            QuickReplyItem(action=MessageAction(label="ศาลเจ้าแม่ทับทิม",   text="ข้อมูล_วัฒนธรรม_ทับทิม"))
                        ]
                    )
                )
            ]
        )
    )

def send_places(api, event):
    names = list(places.keys())[:9]  # เอา 9 ที่

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(
                    text="📍 เลือกสถานที่ท่องเที่ยว",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyItem(
                                action=MessageAction(
                                    label=name,
                                    text=name
                                )
                            )
                            for name in names
                        ]
                    )
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
    match = None  # 🔹 กำหนดค่าเริ่มต้น
    is_question = False  # ตรวจสอบว่าเป็นคำถาม

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
            elif name in questions:
                api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=questions[name])]
                    )
                )
            else:
                api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="ขอโทษค่ะ ไม่พบข้อมูล")]
                    )
                )
            return

        # 🔹 ตรวจสอบคำสั่งอื่นๆ
        elif text in ["สถานที่", "สถานที่ท่องเที่ยว"]:
            send_places(api, event)
        elif text in places:
            send_place_detail(api, event, text)
        elif text in ["map", "แผนที่ภายในอำเภอท่ายาง"]:
            send_map(api, event)
        elif text.startswith("แผนที่_"):
            name = text.replace("แผนที่_", "")
            url = "https://maps.google.com" if name == "ทั้งหมด" else places[name]["map"]
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f"🗺 {url}")]
                )
            )
        elif text in ["กิจกรรม", "กิจกรรมภายในอำเภอท่ายาง"]:
            send_activity(api, event)
        elif text in ["ข้อมูล", "เกี่ยวกับอำเภอท่ายาง"]:
            send_info(api, event)
        elif text == "ข้อมูล_วัฒนธรรม":
            send_culture(api, event)
        elif text.startswith("ข้อมูล_"):
            key = text.replace("ข้อมูล_", "")
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
        else:
            # 🔹 fuzzy search ทั้ง places และ questions
            match_place = fuzzy_search_place(text)
            match_question = None
            # ตรวจสอบคำถามใกล้เคียง
            if not match_place:
                match_question = process.extractOne(text, list(questions.keys()))
                if match_question and match_question[1] > 60:
                    match = match_question[0]
                    is_question = True
            else:
                match = match_place

            if match:
                # 🔹 quick reply ใช้เหมือนกัน
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