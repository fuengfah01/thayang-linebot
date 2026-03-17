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
    MessageAction
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
        # 📍 เมนูแผนที่ (2 ชั้น)
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
                        TextMessage(text="📍 https://maps.google.com/?q=Thayang")
                    ]
                )
            )

        elif text == "แผนที่รายสถานที่":

            items = [
                QuickReplyItem(
                    action=MessageAction(label=name, text=f"map_{name}")
                )
                for name in places
            ]

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(
                            text="📍 เลือกสถานที่เพื่อเปิดแผนที่",
                            quick_reply=QuickReply(items=items)
                        )
                    ]
                )
            )

        elif text.startswith("map_"):

            name = text.replace("map_", "")

            if name in places:
                map_url = places[name].get("map", "ไม่มีข้อมูลแผนที่")

                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            TextMessage(text=f"📍 {name}\n{map_url}")
                        ]
                    )
                )

        # =========================
        # 🎯 กิจกรรม (กรอง)
        # =========================
        elif text == "กิจกรรม":

            items = [
                QuickReplyItem(action=MessageAction(label="🛕 สายบุญ", text="สายบุญ")),
                QuickReplyItem(action=MessageAction(label="📸 ถ่ายรูป", text="ถ่ายรูป")),
                QuickReplyItem(action=MessageAction(label="🍜 กิน", text="กิน")),
            ]

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(
                            text="🎯 เลือกกิจกรรม",
                            quick_reply=QuickReply(items=items)
                        )
                    ]
                )
            )

        elif text in ["สายบุญ", "ถ่ายรูป", "กิน"]:

            keyword_map = {
                "สายบุญ": ["วัด", "ศาล"],
                "ถ่ายรูป": ["วัด", "ตลาด", "ศาล"],
                "กิน": ["ร้าน", "ตลาด"]
            }

            keywords = keyword_map[text]

            results = [
                name for name in places
                if any(k in name for k in keywords)
            ]

            if results:
                items = [
                    QuickReplyItem(action=MessageAction(label=name, text=name))
                    for name in results
                ]

                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            TextMessage(
                                text=f"🎯 สถานที่สำหรับ {text}",
                                quick_reply=QuickReply(items=items)
                            )
                        ]
                    )
                )
            else:
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="ไม่พบข้อมูล")]
                    )
                )

        # =========================
        # 🍜 ร้านอาหาร (placeholder)
        # =========================
        elif text == "ร้านอาหาร":

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text="🍜 เลือกจากเมนูกิจกรรม > กิน ได้เลย")
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

⭐ จุดเด่น
{place.get('highlight','-')}

⏰ เวลาเปิด
{place.get('time','-')}

📍 แผนที่
{place.get('map','-')}
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
        # 🔍 ค้นหาใกล้เคียง
        # =========================
        else:

            match = difflib.get_close_matches(text, places.keys(), n=1, cutoff=0.5)

            if match:
                reply = f"คุณหมายถึง {match[0]} ใช่ไหม"
            else:
                reply = "พิมพ์ 'สถานที่เที่ยว' เพื่อเริ่มต้น"

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply)]
                )
            )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)