from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient, ReplyMessageRequest, TextMessage
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import random

from places import places

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = "YOUR_CHANNEL_ACCESS_TOKEN"
CHANNEL_SECRET = "YOUR_CHANNEL_SECRET"

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


# =========================
# alias คำค้นหา
# =========================
aliases = {

    "วัด": "วัดท่าคอย",
    "ท่าคอย": "วัดท่าคอย",

    "อุโบสถ": "อุโบสถ 100 ปี",
    "100 ปี": "อุโบสถ 100 ปี",

    "อุทยาน": "อุทยานปลาวัดท่าคอย",
    "ปลา": "อุทยานปลาวัดท่าคอย",

    "ตลาด": "ตลาดสดท่ายาง",
    "ตลาดสด": "ตลาดสดท่ายาง",
    "ตลาดท่ายาง": "ตลาดสดท่ายาง",

    "ทองม้วน": "ร้านทองม้วนแม่เล็ก",
    "ร้านทองม้วน": "ร้านทองม้วนแม่เล็ก",

    "ผัดไทย": "ร้านผัดไทย 100 ปี",
    "ร้านผัดไทย": "ร้านผัดไทย 100 ปี",

    "กวนอู": "ศาลเจ้าพ่อกวนอู",
    "เจ้าพ่อกวนอู": "ศาลเจ้าพ่อกวนอู",

    "ข้าวแช่": "ข้าวแช่แม่เล็ก สกิดใจ",

    "ทับทิม": "ศาลเจ้าแม่ทับทิม",
    "เจ้าแม่ทับทิม": "ศาลเจ้าแม่ทับทิม"
}


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

    text = event.message.text.strip()

    # แปลง alias
    if text in aliases:
        text = aliases[text]

    # ======================
    # แสดงรายการสถานที่
    # ======================
    if text == "สถานที่ท่องเที่ยว":

        reply = "📍 สถานที่ท่องเที่ยวในท่ายาง\n\n"

        for name in places:
            reply += f"• {name}\n"

        reply += "\nพิมพ์ชื่อสถานที่เพื่อดูรายละเอียด"

    # ======================
    # แนะนำสถานที่
    # ======================
    elif text == "แนะนำสถานที่":

        name = random.choice(list(places.keys()))
        place = places[name]

        reply = f"""
💡 สถานที่แนะนำ

📍 {name}

⭐ {place.get('highlight','')}
"""

    # ======================
    # แสดงรายละเอียดสถานที่
    # ======================
    elif text in places:

        place = places[text]

        reply = f"""
📍 {text}

📖 ประวัติความเป็นมา
{place.get('history','-')}

⭐ จุดเด่นของสถานที่
{place.get('highlight','-')}

🎯 กิจกรรมที่สามารถทำได้
{place.get('activities','-')}

🏛 ความสำคัญทางวัฒนธรรม
{place.get('culture','-')}

💡 คำแนะนำสำหรับผู้มาเยือน
{place.get('tips','-')}

⏰ เวลาเปิดให้เข้าชม
{place.get('time','-')}

📍 ที่อยู่
{place.get('address','-')}

🗺 แผนที่
{place.get('map','-')}
"""

    # ======================
    # เมนูช่วยเหลือ
    # ======================
    else:

        reply = """
สวัสดี 👋 ยินดีต้อนรับสู่แชทบอทท่องเที่ยวท่ายาง

คุณสามารถพิมพ์คำต่อไปนี้เพื่อดูข้อมูลได้

📍 สถานที่ท่องเที่ยว
ดูรายชื่อสถานที่ท่องเที่ยวในท่ายาง

💡 แนะนำสถานที่
ให้แชทบอทแนะนำสถานที่น่าเที่ยว

หรือพิมพ์ชื่อสถานที่ เช่น

• วัดท่าคอย , วัด , ท่าคอย
• อุโบสถ 100 ปี , อุโบสถ , 100 ปี
• อุทยานปลาวัดท่าคอย , อุทยาน , ปลา
• ตลาดสดท่ายาง , ตลาดสด , ตลาด
• ร้านทองม้วนแม่เล็ก , ทองม้วน
• ร้านผัดไทย 100 ปี , ผัดไทย
• ศาลเจ้าพ่อกวนอู , กวนอู
• ข้าวแช่แม่เล็ก สกิดใจ , ข้าวแช่
• ศาลเจ้าแม่ทับทิม , ทับทิม

พิมพ์ชื่อสถานที่เพื่อดูรายละเอียดได้ทันที 😊
"""

    # ======================
    # ส่งข้อความกลับ LINE
    # ======================
    with ApiClient(configuration) as api_client:

        line_bot_api = MessagingApi(api_client)

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply.strip())]
            )
        )


if __name__ == "__main__":
    app.run()