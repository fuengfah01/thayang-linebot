from flask import Flask, request, send_from_directory
from linebot.v3.messaging import *
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from rapidfuzz import process

from places import places
from info import info
from questions import questions
from intents import intents   # ⭐ เพิ่มตรงนี้

import os
import random

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
# 🧠 INTENT DETECTION
# =========================
def detect_intent(text):
    text = text.lower()

    best_intent = None
    best_score = 0

    for intent, data in intents.items():
        result = process.extractOne(text, data["keywords"])
        if result:
            _, score, _ = result
            if score > best_score and score > 60:
                best_score = score
                best_intent = intent

    return best_intent

# =========================
# 🧠 FUZZY SEARCH (PLACE)
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
# 🧠 FUZZY SEARCH (QUESTION)
# =========================
def fuzzy_search_question(text):
    text = text.lower()

    choices = list(questions.keys())
    result = process.extractOne(text, choices)

    if result:
        word, score, _ = result
        if score > 60:
            return word

    return None

# =========================
# 📍 PLACE DETAIL
# =========================
def send_place_detail(api, event, name):
    p = places[name]
    messages = []

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
            alt_text=name,
            contents=CarouselContainer(contents=bubbles)
        )
        messages.append(flex)

    text_msg = TextMessage(
        text=f"""📍 {name}

📜 ประวัติ:
{p['history']}

⭐ จุดเด่น:
{p['highlight']}

⏰ เวลา:
{p['time']}
"""
    )
    messages.append(text_msg)

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
    text = """🏨 กิจกรรมแนะนำ

🙏 ไหว้พระ
- วัดท่าคอย
- ศาลเจ้าพ่อกวนอู
- ศาลเจ้าแม่ทับทิม

📸 ถ่ายรูป
- วัดท่าคอย
- ศาลเจ้าพ่อกวนอู
- ศาลเจ้าแม่ทับทิม
- อุโบสถ 100 ปี

🐟 ให้อาหารปลา
- อุทยานปลาวัดท่าคอย

🍜 ตะลอนกิน
- ตลาดสดท่ายาง
- ร้านทองม้วนแม่เล็ก
- ร้านผัดไทย 100 ปี
- ร้านข้าวแช่แม่เล็ก สกิดใจ
"""

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=text)]
        )
    )


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
                            QuickReplyItem(action=MessageAction(label="ประวัติ", text="info_history")),
                            QuickReplyItem(action=MessageAction(label="จุดเด่น", text="info_highlight")),
                            QuickReplyItem(action=MessageAction(label="วิถีชีวิต", text="info_lifestyle"))
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
# 📩 HANDLE MESSAGE
# =========================
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()

    with ApiClient(configuration) as api_client:
        api = MessagingApi(api_client)

        # ✅ confirm
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
            return

        # ✅ intent ก่อนเลย
        intent = detect_intent(text)

        if intent == "greeting":
            reply = random.choice([
                "สวัสดีค่ะ มีอะไรให้ช่วยไหมคะ",
                "สวัสดีค่ะ ยินดีให้บริการค่ะ"
            ])
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply)]
                )
            )
            return

        elif intent == "map":
            send_map(api, event)
            return

        elif intent == "travel":
            send_places(api, event)
            return

        elif intent == "activity":
            send_activity(api, event)
            return

        elif intent == "info":
            send_info(api, event)
            return

        # ✅ ตรงตัว
        if text in places:
            send_place_detail(api, event, text)
            return

        # ✅ fuzzy
        match_place = fuzzy_search_place(text)
        match_question = fuzzy_search_question(text)

        if match_place:
            match = match_place
        elif match_question:
            match = match_question
        else:
            match = None

        if match:
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(
                            text=f"คุณหมายถึง {match} ใช่ไหม",
                            quick_reply=QuickReply(
                                items=[
                                    QuickReplyItem(action=MessageAction(label="ใช่", text=f"ใช่_{match}")),
                                    QuickReplyItem(action=MessageAction(label="ไม่ใช่", text="กลับหน้าหลัก"))
                                ]
                            )
                        )
                    ]
                )
            )
        else:
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="ไม่เข้าใจคำถาม ลองใหม่ค่ะ")]
                )
            )

# =========================
# 🚀 RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)