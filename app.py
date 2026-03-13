from flask import Flask, request, abort
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

CHANNEL_ACCESS_TOKEN = "ใส่ access token"
CHANNEL_SECRET = "ใส่ channel secret"

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


@app.route("/")
def home():
    return "LINE BOT RUNNING"


@app.route("/webhook", methods=["POST"])
def webhook():

    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):

    text = event.message.text.strip()

    with ApiClient(configuration) as api_client:

        line_bot_api = MessagingApi(api_client)

        # -------------------------
        # แสดงรายการสถานที่
        # -------------------------
        if text == "สถานที่ท่องเที่ยว":

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
        # ถ้าพิมพ์ชื่อสถานที่ตรง
        # -------------------------
        elif text in places:

            place = places[text]

            reply_text = f"""
📍 {text}

📖 ประวัติ
{place['history']}

⭐ จุดเด่น
{place['highlight']}

⏰ เวลาเปิด
{place['time']}

📍 ที่อยู่
{place['address']}

🗺 แผนที่
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
        # ค้นหาคำใกล้เคียง
        # -------------------------
        else:

            match = difflib.get_close_matches(text, places.keys(), n=1, cutoff=0.5)

            if match:

                name = match[0]
                place = places[name]

                reply = f"""
คุณหมายถึง {name} ใช่ไหม

{place['history']}
"""

            else:

                reply = """
พิมพ์คำว่า

สถานที่ท่องเที่ยว

เพื่อดูสถานที่ในท่ายาง
"""

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply)]
                )
            )


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)