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

CHANNEL_ACCESS_TOKEN = "ใส่ของฟ้า"
CHANNEL_SECRET = "ใส่ของฟ้า"

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

        # -------------------------
        # 🏝 สถานที่ท่องเที่ยว (รองรับ 2 คำ)
        # -------------------------
        if text in ["สถานที่เที่ยว", "สถานที่ท่องเที่ยว"]:

            items = []

            for name in places:
                items.append(
                    QuickReplyItem(
                        action=MessageAction(
                            label=name,
                            text=name
                        )
                    )
                )

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(
                            text="📍 เลือกสถานที่ท่องเที่ยวในท่ายาง",
                            quick_reply=QuickReply(items=items)
                        )
                    ]
                )
            )

        # -------------------------
        # 📍 แผนที่ท่ายาง
        # -------------------------
        elif text == "แผนที่ท่ายาง":

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(
                            text="📍 แผนที่อำเภอท่ายาง\nhttps://maps.google.com/?q=Thayang"
                        )
                    ]
                )
            )

        # -------------------------
        # 🎯 กิจกรรม
        # -------------------------
        elif text == "กิจกรรม":

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(
                            text="🎯 กิจกรรมในท่ายาง\n- ไหว้พระ\n- เที่ยววัด\n- ชิมอาหารพื้นบ้าน\n- ถ่ายรูปธรรมชาติ"
                        )
                    ]
                )
            )

        # -------------------------
        # 🍜 ร้านอาหาร
        # -------------------------
        elif text == "ร้านอาหาร":

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(
                            text="🍜 ร้านอาหารแนะนำในท่ายาง (กำลังอัปเดต...)"
                        )
                    ]
                )
            )

        # -------------------------
        # 🏝 แสดงข้อมูลสถานที่
        # -------------------------
        elif text in places:

            place = places[text]

            reply_text = f"""
📍 {text}

⭐ จุดเด่น
{place['highlight']}

⏰ เวลาเปิด
{place['time']}

📍 แผนที่
{place['map']}

🧭 นำทาง
{place['map']}
"""

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        ImageMessage(
                            original_content_url=place["image"],
                            preview_image_url=place["image"]
                        ),
                        TextMessage(text=reply_text)
                    ]
                )
            )

        # -------------------------
        # 🔍 ค้นหาคำใกล้เคียง
        # -------------------------
        else:

            match = difflib.get_close_matches(text, places.keys(), n=1, cutoff=0.5)

            if match:
                name = match[0]
                place = places[name]

                reply = f"""
คุณหมายถึง {name} ใช่ไหม

{place.get('highlight','')}
"""
            else:
                reply = "พิมพ์คำว่า 'สถานที่เที่ยว' เพื่อดูสถานที่ในท่ายาง"

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply)]
                )
            )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)