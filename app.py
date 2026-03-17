from flask import Flask, request
from linebot.v3.messaging import (
    MessagingApi,
    Configuration,
    ApiClient,
    ReplyMessageRequest,
    TextMessage,
    ImageMessage,
    QuickReply,
    QuickReplyItem,
    MessageAction,
    FlexMessage
)
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from places import places
from activities import activities

import os

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = "4daQ2JUnEe+vEmbDJhOmn48fWc7d/Kb6+iWXIm05H8ngOFqDPLyNpgdTO58cKvHyfcL/q/gytkIljJiMSjAQCvN5wmahGaLKoVocuepLo5tyQq7q33YfsPZPhxpO8kPOrpnECFRdZPB0JjHKaKaPOQdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "a97e9e9977b3aac81ca9af33e59bde55"

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# จำสถานะ user
user_state = {}


@app.route("/")
def home():
    return "LINE BOT RUNNING"


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
# 🧠 Smart Search
# =========================
def smart_search(user_text):

    keywords_map = {
        "วัด": ["วัด", "ไหว้พระ"],
        "อาหาร": ["กิน", "หิว", "ร้าน"],
        "เที่ยว": ["เที่ยว"],
        "ถ่ายรูป": ["ถ่ายรูป", "วิว"]
    }

    scores = {}

    for name, p in places.items():
        score = 0

        if name in user_text:
            score += 5

        for words in keywords_map.values():
            if any(w in user_text for w in words):
                if any(w in name for w in words):
                    score += 3

        scores[name] = score

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


# =========================
# 📍 Filter ร้านอาหาร
# =========================
def get_food():
    return [name for name, p in places.items() if p.get("type") == "food"]


# =========================
# 📍 ส่งรายละเอียดสถานที่
# =========================
def send_place_detail(line_bot_api, event, name):

    place = places[name]

    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                ImageMessage(
                    original_content_url=place["image"],
                    preview_image_url=place["image"]
                ),
                TextMessage(
                    text=f"""
📍 {name}

⭐ {place.get('highlight','-')}
⏰ {place.get('time','-')}
📍 {place.get('map','-')}
""",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyItem(action=MessageAction(label="🔙 กลับเมนู", text="เมนู")),
                            QuickReplyItem(action=MessageAction(label="📍 สถานที่อื่น", text="สถานที่ท่องเที่ยว"))
                        ]
                    )
                )
            ]
        )
    )


# =========================
# 📍 ส่งรายละเอียดกิจกรรม
# =========================
def send_activity_detail(line_bot_api, event, name):

    act = activities[name]

    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                ImageMessage(
                    original_content_url=act["image"],
                    preview_image_url=act["image"]
                ),
                TextMessage(
                    text=f"""
🏨 {name}

⭐ {act.get('highlight','-')}
⏰ {act.get('time','-')}
📍 {act.get('map','-')}
""",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyItem(action=MessageAction(label="🔙 กลับเมนู", text="เมนู"))
                        ]
                    )
                )
            ]
        )
    )


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):

    text = event.message.text.strip()
    user_id = event.source.user_id

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        # =========================
        # 🔙 เมนู
        # =========================
        if text == "เมนู":
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="พิมพ์ 'สถานที่ท่องเที่ยว' เพื่อเริ่ม")]
                )
            )

        # =========================
        # 🍜 FOOD
        # =========================
        elif text.lower() in ["food", "ร้านอาหาร", "อาหาร"]:

            food_list = get_food()

            items = [
                QuickReplyItem(action=MessageAction(label=name, text=name))
                for name in food_list
            ]

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(
                            text="🍜 เลือกร้านอาหาร",
                            quick_reply=QuickReply(items=items)
                        )
                    ]
                )
            )

        # =========================
        # 🏨 ACTIVITY
        # =========================
        elif text.lower() in ["activity", "กิจกรรม"]:

            items = [
                QuickReplyItem(action=MessageAction(label=name, text=f"act_{name}"))
                for name in activities
            ]

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(
                            text="🏨 เลือกกิจกรรม",
                            quick_reply=QuickReply(items=items)
                        )
                    ]
                )
            )

        elif text.startswith("act_"):
            name = text.replace("act_", "")
            if name in activities:
                send_activity_detail(line_bot_api, event, name)

        # =========================
        # 📍 สถานที่
        # =========================
        elif text in places:
            send_place_detail(line_bot_api, event, text)

        elif text.startswith("detail_"):
            name = text.replace("detail_", "")
            if name in places:
                send_place_detail(line_bot_api, event, name)

        elif text in ["สถานที่เที่ยว", "สถานที่ท่องเที่ยว"]:
            items = [
                QuickReplyItem(action=MessageAction(label=name, text=name))
                for name in places
            ]

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(
                            text="📍 เลือกสถานที่",
                            quick_reply=QuickReply(items=items)
                        )
                    ]
                )
            )

        # =========================
        # 🤖 SMART (ถาม → ใช่)
        # =========================
        elif text == "ใช่":
            if user_id in user_state:
                send_place_detail(line_bot_api, event, user_state[user_id])

        else:

            results = smart_search(text)
            best_name, best_score = results[0]

            if best_score > 0:
                user_state[user_id] = best_name

                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            TextMessage(
                                text=f"คุณหมายถึง {best_name} ใช่ไหม",
                                quick_reply=QuickReply(
                                    items=[
                                        QuickReplyItem(action=MessageAction(label="ใช่", text="ใช่")),
                                        QuickReplyItem(action=MessageAction(label="ไม่ใช่", text="ไม่ใช่"))
                                    ]
                                )
                            )
                        ]
                    )
                )

            else:
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            TextMessage(text="ลองพิมพ์ เช่น 'ไปวัดไหนดี' หรือ 'หิวแล้ว'")
                        ]
                    )
                )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)