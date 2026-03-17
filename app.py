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
import difflib
import os

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = "4daQ2JUnEe+vEmbDJhOmn48fWc7d/Kb6+iWXIm05H8ngOFqDPLyNpgdTO58cKvHyfcL/q/gytkIljJiMSjAQCvN5wmahGaLKoVocuepLo5tyQq7q33YfsPZPhxpO8kPOrpnECFRdZPB0JjHKaKaPOQdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "a97e9e9977b3aac81ca9af33e59bde55"

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


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
# 🧠 SMART SEARCH (ไม่ใช้ AI)
# =========================
def smart_search(user_text):

    keywords_map = {
        "วัด": ["วัด", "ไหว้พระ", "ทำบุญ"],
        "อาหาร": ["กิน", "หิว", "ร้าน", "อาหาร"],
        "เที่ยว": ["เที่ยว", "ที่เที่ยว", "พักผ่อน"],
        "ถ่ายรูป": ["ถ่ายรูป", "วิว", "สวย", "เช็คอิน"]
    }

    scores = {}

    for name, p in places.items():
        score = 0

        # ชื่อตรง
        if name in user_text:
            score += 5

        # keyword
        for words in keywords_map.values():
            if any(w in user_text for w in words):
                if any(w in name for w in words):
                    score += 3

        # highlight
        highlight = p.get("highlight", "")
        if any(word in highlight for word in user_text.split()):
            score += 2

        scores[name] = score

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


# =========================
# 🎨 FLEX MESSAGE TOP 3
# =========================
def create_flex_top3(results):

    bubbles = []

    for name, score in results[:3]:

        place = places[name]

        bubble = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": place.get("image"),
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": name,
                        "weight": "bold",
                        "size": "lg"
                    },
                    {
                        "type": "text",
                        "text": place.get("highlight", "-"),
                        "wrap": True,
                        "size": "sm"
                    },
                    {
                        "type": "text",
                        "text": f"⏰ {place.get('time','-')}",
                        "size": "sm"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "uri",
                            "label": "🧭 นำทาง",
                            "uri": place.get("map")
                        }
                    }
                ]
            }
        }

        bubbles.append(bubble)

    return {
        "type": "carousel",
        "contents": bubbles
    }


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):

    text = event.message.text.strip()

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        # =========================
        # 🏝 สถานที่ท่องเที่ยว
        # =========================
        if text in ["สถานที่เที่ยว", "สถานที่ท่องเที่ยว"]:

            items = [
                QuickReplyItem(action=MessageAction(label=name, text=name))
                for name in places
            ]

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(
                            text="📍 เลือกสถานที่ในท่ายาง",
                            quick_reply=QuickReply(items=items)
                        )
                    ]
                )
            )

        # =========================
        # 📍 แผนที่ 2 ชั้น
        # =========================
        elif text == "แผนที่ท่ายาง":

            items = [
                QuickReplyItem(action=MessageAction(label="🗺 แผนที่รวม", text="แผนที่รวม")),
                QuickReplyItem(action=MessageAction(label="📍 รายสถานที่", text="แผนที่รายสถานที่")),
            ]

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(
                            text="📍 เลือกประเภทแผนที่",
                            quick_reply=QuickReply(items=items)
                        )
                    ]
                )
            )

        elif text == "แผนที่รวม":
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text="📍 https://maps.google.com/?q=Tha+Yang+Phetchaburi")
                    ]
                )
            )

        elif text == "แผนที่รายสถานที่":

            items = [
                QuickReplyItem(action=MessageAction(label=name, text=f"map_{name}"))
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

        elif text.startswith("map_"):

            name = text.replace("map_", "")

            if name in places:
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            TextMessage(text=f"📍 {name}\n{places[name].get('map','-')}")
                        ]
                    )
                )

        # =========================
        # 📍 แสดงข้อมูลสถานที่
        # =========================
        elif text in places:

            place = places[text]

            reply_text = f"""
📍 {text}

⭐ {place.get('highlight','-')}
⏰ {place.get('time','-')}
📍 {place.get('map','-')}
"""

            messages = []

            if place.get("image"):
                messages.append(
                    ImageMessage(
                        original_content_url=place["image"],
                        preview_image_url=place["image"]
                    )
                )

            messages.append(TextMessage(text=reply_text))

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=messages
                )
            )

        # =========================
        # 🤖 SMART REPLY (TOP 3)
        # =========================
        else:

            results = smart_search(text)
            top_score = results[0][1]

            if top_score > 0:

                flex = create_flex_top3(results)

                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            FlexMessage(
                                alt_text="แนะนำสถานที่ท่องเที่ยว",
                                contents=flex
                            )
                        ]
                    )
                )

            else:
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            TextMessage(text="ลองพิมพ์ เช่น 'ไปวัดไหนดี' หรือ 'มีร้านอาหารแนะนำไหม'")
                        ]
                    )
                )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)