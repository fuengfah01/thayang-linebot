from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = "4daQ2JUnEe+vEmbDJhOmn48fWc7d/Kb6+iWXIm05H8ngOFqDPLyNpgdTO58cKvHyfcL/q/gytkIljJiMSjAQCvN5wmahGaLKoVocuepLo5tyQq7q33YfsPZPhxpO8kPOrpnECFRdZPB0JjHKaKaPOQdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "1e3188f604e923828426653c22ef34c8"

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    handler.handle(body, signature)
    return 'OK'


@handler.add(MessageEvent)
def handle_message(event):
    text = event.message.text

    if text == "สถานที่ท่องเที่ยว":
        reply = """
สถานที่ท่องเที่ยวท่ายาง

1. วัดท่าคอย
2. อุโบสถ 100 ปี
3. อุทยานปลาวัดท่าคอย
4. ตลาดสดท่ายาง
5. ร้านทองม้วนแม่เล็ก
6. ร้านผัดไทย 100 ปี
7. ศาลเจ้าพ่อกวนอู
8. ข้าวแช่แม่เล็ก สกิดใจ
9. ศาลเจ้าแม่ทับทิม
"""

    elif text == "วัดท่าคอย":
        reply = "วัดท่าคอย เป็นวัดเก่าแก่ในอำเภอท่ายาง จังหวัดเพชรบุรี"

    else:
        reply = "พิมพ์คำว่า สถานที่ท่องเที่ยว เพื่อดูรายการ"

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