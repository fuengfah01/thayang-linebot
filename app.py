from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient, ReplyMessageRequest, TextMessage
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from places import places

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = "4daQ2JUnEe+vEmbDJhOmn48fWc7d/Kb6+iWXIm05H8ngOFqDPLyNpgdTO58cKvHyfcL/q/gytkIljJiMSjAQCvN5wmahGaLKoVocuepLo5tyQq7q33YfsPZPhxpO8kPOrpnECFRdZPB0JjHKaKaPOQdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "a97e9e9977b3aac81ca9af33e59bde55"

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


@app.route("/")
def home():
    return "LINE BOT RUNNING"


@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):

    text = event.message.text

    # แสดงรายการสถานที่
    if text == "สถานที่ท่องเที่ยว":

        reply = "📍 สถานที่ท่องเที่ยวในท่ายาง\n\n"

        for name in places:
            reply += f"• {name}\n"

        reply += "\nพิมพ์ชื่อสถานที่เพื่อดูรายละเอียด"

    # แสดงรายละเอียดสถานที่
    elif text in places:

        place = places[text]

        reply = f"""
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

    else:

        reply = """
สวัสดี 👋

พิมพ์คำว่า

สถานที่ท่องเที่ยว

เพื่อดูสถานที่ในท่ายาง
"""

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )


if __name__ == "__main__":
    app.run()