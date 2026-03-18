from flask import Flask, request, send_from_directory
from linebot.v3.messaging import *
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from places import places
from info import info

import difflib
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
def find_place(text):
    names = list(places.keys())
    match = difflib.get_close_matches(text, names, n=1, cutoff=0.5)
    return match[0] if match else None

# =========================
# 📍 สถานที่
# =========================
def send_place_detail(api, event, name):
    p = places[name]

    # 🔥 สร้าง bubble 4 อัน (แต่ละรูป = 1 card)
    bubbles = []

    for img in p["images"]:
        bubble = Bubble(
            hero=ImageComponent(
                url=img,
                size="full",
                aspect_ratio="20:13",
                aspect_mode="cover"
            )
        )
        bubbles.append(bubble)

    # 🔥 carousel (เลื่อนรูปได้)
    flex = FlexMessage(
        alt_text=f"{name}",
        contents=Carousel(contents=bubbles)
    )

    # 🔥 ข้อมูลข้อความ
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

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[flex, text]
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

# =========================
# 📩 HANDLE
# =========================
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()

    with ApiClient(configuration) as api_client:
        api = MessagingApi(api_client)

        if text in ["travel", "สถานที่ท่องเที่ยว"]:
            send_places(api, event)

        elif text in places:
            send_place_detail(api, event, text)

        elif text in ["map", "แผนที่"]:
            send_map(api, event)

        elif text.startswith("map_"):
            name = text.replace("map_", "")

            if name == "all":
                url = "https://maps.google.com"
            else:
                url = places[name]["map"]

            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f"🗺 {url}")]
                )
            )

        elif text in ["activity", "กิจกรรม"]:
            send_activity(api, event)

        elif text in ["info", "เกี่ยวกับท่ายาง"]:
            send_info(api, event)

        elif text.startswith("info_"):
            key = text.replace("info_", "")
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=info[key])]
                )
            )

        else:
            match = find_place(text)
            if match:
                send_place_detail(api, event, match)
            else:
                send_places(api, event)

# =========================
# 🚀 RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)