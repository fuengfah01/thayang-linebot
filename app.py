from flask import Flask, request, send_from_directory
from linebot.v3.messaging import *
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from places import places
from info import info

from rapidfuzz import process
import os

app = Flask(__name__)

# =========================
# 🔑 CONFIG
# =========================
CHANNEL_ACCESS_TOKEN = "YOUR_TOKEN"
CHANNEL_SECRET = "YOUR_SECRET"

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# =========================
# 🖼 ROUTE รูป
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
# 🧠 FUZZY SEARCH (เทพ)
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
# 📍 LIST สถานที่
# =========================
def send_places(api, event):
    names = list(places.keys())

    text_list = "\n".join([f"{i+1}. {n}" for i, n in enumerate(names)])

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(
                    text=f"""📍 สถานที่ท่องเที่ยว

{text_list}

👉 พิมพ์ชื่อสถานที่เพื่อดูรายละเอียด"""
                )
            ]
        )
    )

# =========================
# 📍 DETAIL
# =========================
def send_place_detail(api, event, name):
    p = places[name]

    bubbles = []
    for img in p["images"]:
        bubbles.append(
            Bubble(
                hero=ImageComponent(
                    url=img,
                    size="full",
                    aspect_ratio="20:13",
                    aspect_mode="cover"
                )
            )
        )

    flex = FlexMessage(
        alt_text=name,
        contents=Carousel(contents=bubbles)
    )

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
    names = list(places.keys())

    text_list = "\n".join([f"{i+1}. {n}" for i, n in enumerate(names)])

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(
                    text=f"""🗺 แผนที่

{text_list}

👉 พิมพ์ชื่อสถานที่เพื่อเปิดแผนที่"""
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
                TextMessage(text="📖 เกี่ยวกับท่ายาง\nพิมพ์: ประวัติ / จุดเด่น / วิถีชีวิต")
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

        # เมนูหลัก
        if text.lower() in ["menu", "เริ่ม", "start"]:
            send_places(api, event)

        elif text in ["travel", "สถานที่ท่องเที่ยว"]:
            send_places(api, event)

        elif text in ["map", "แผนที่"]:
            send_map(api, event)

        elif text in ["activity", "กิจกรรม"]:
            send_activity(api, event)

        elif text in ["info", "เกี่ยวกับ"]:
            send_info(api, event)

        elif text in ["ประวัติ", "history"]:
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=info["history"])]
                )
            )

        elif text in ["จุดเด่น", "highlight"]:
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=info["highlight"])]
                )
            )

        elif text in ["วิถีชีวิต", "lifestyle"]:
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=info["lifestyle"])]
                )
            )

        # =========================
        # 🔥 AI FUZZY SEARCH
        # =========================
        else:
            match = fuzzy_search_place(text)

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