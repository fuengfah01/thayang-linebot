from flask import Flask, request, send_from_directory
from linebot.v3.messaging import *
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from rapidfuzz import process

from places import places
from info import info

import os
import threading

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

# ✅ ป้องกัน Render สลีป — ให้ UptimeRobot หรือบริการอื่น ping ที่ /ping ทุก 5 นาที
@app.route("/ping")
def ping():
    return "pong"

# =========================
# 🔗 WEBHOOK
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_data(as_text=True)
    signature = request.headers.get("X-Line-Signature", "")

    # ✅ ตอบ LINE กลับทันทีก่อน แล้วค่อยประมวลผลใน background
    def process_event():
        try:
            handler.handle(body, signature)
        except Exception as e:
            print("Webhook error:", e)

    thread = threading.Thread(target=process_event)
    thread.start()

    return "OK"

# =========================
# 🧠 Fuzzy Search
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
# 📍 สถานที่ — แสดงรายการ (Quick Reply)
# =========================
def send_places(api, event):
    names = list(places.keys())[:9]

    # ✅ ใช้ "place_0", "place_1" เป็น text แทนชื่อเต็ม
    # เพราะ label ใน Quick Reply ถูกตัดที่ 20 ตัวอักษร ทำให้ text ที่ส่งมาไม่ตรงกับชื่อใน places
    items = []
    for i, n in enumerate(names):
        label = n[:20]  # label แสดงผลตัดที่ 20 ตัว
        items.append(
            QuickReplyItem(
                action=MessageAction(label=label, text=f"place_{i}")
            )
        )

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(
                    text="📍 เลือกสถานที่ท่องเที่ยวในอำเภอท่ายาง",
                    quick_reply=QuickReply(items=items)
                )
            ]
        )
    )

# =========================
# 📍 สถานที่ — แสดงรายละเอียด (Flex Message)
# =========================
def send_place_detail(api, event, name):
    p = places[name]

    flex = FlexMessage(
        alt_text=name,
        contents=Bubble(
            hero=ImageComponent(
                url=p["images"][0],
                size="full",
                aspect_ratio="20:13",
                aspect_mode="cover"
            ),
            body=BoxComponent(
                layout="vertical",
                spacing="sm",
                contents=[
                    TextComponent(
                        text=name,
                        weight="bold",
                        size="xl",
                        color="#1a1a1a"
                    ),
                    SeparatorComponent(margin="sm"),
                    BoxComponent(
                        layout="vertical",
                        margin="md",
                        spacing="sm",
                        contents=[
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(text="📜", flex=0, size="sm"),
                                    TextComponent(
                                        text=p["history"],
                                        wrap=True,
                                        size="sm",
                                        color="#555555",
                                        flex=1,
                                        margin="sm"
                                    )
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(text="⭐", flex=0, size="sm"),
                                    TextComponent(
                                        text=p["highlight"],
                                        wrap=True,
                                        size="sm",
                                        color="#555555",
                                        flex=1,
                                        margin="sm"
                                    )
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(text="⏰", flex=0, size="sm"),
                                    TextComponent(
                                        text=p["time"],
                                        size="sm",
                                        color="#888888",
                                        flex=1,
                                        margin="sm"
                                    )
                                ]
                            )
                        ]
                    )
                ]
            ),
            footer=BoxComponent(
                layout="vertical",
                contents=[
                    ButtonComponent(
                        action=URIAction(
                            label="🗺 ดูแผนที่",
                            uri=p["map"]
                        ),
                        style="primary",
                        color="#4A90D9"
                    )
                ]
            )
        )
    )

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[flex]
        )
    )

# =========================
# 🗺 แผนที่
# =========================
def send_map(api, event):
    names = list(places.keys())[:9]

    items = []
    for i, n in enumerate(names):
        items.append(
            QuickReplyItem(
                action=MessageAction(label=n[:20], text=f"map_{i}")
            )
        )
    items.append(
        QuickReplyItem(
            action=MessageAction(label="📍 แผนที่อำเภอ", text="map_all")
        )
    )

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(
                    text="🗺 เลือกสถานที่เพื่อดูเส้นทาง",
                    quick_reply=QuickReply(items=items)
                )
            ]
        )
    )

# =========================
# 🏃 กิจกรรม — Flex Carousel 4 หมวด
# =========================
def send_activity(api, event):
    categories = [
        {
            "emoji": "🙏",
            "title": "ไหว้พระ / ทำบุญ",
            "color": "#F5A623",
            "places_list": [
                "• วัดท่าคอย",
                "• ศาลเจ้าพ่อกวนอู",
                "• ศาลเจ้าแม่ทับทิม"
            ]
        },
        {
            "emoji": "📸",
            "title": "ถ่ายรูปสถานที่วัฒนธรรม",
            "color": "#7B68EE",
            "places_list": [
                "• วัดท่าคอย",
                "• อุโบสถ 100 ปี",
                "• ศาลเจ้าพ่อกวนอู",
                "• ศาลเจ้าแม่ทับทิม"
            ]
        },
        {
            "emoji": "🐟",
            "title": "ให้อาหารปลา",
            "color": "#4A90D9",
            "places_list": [
                "• อุทยานปลาวัดท่าคอย"
            ]
        },
        {
            "emoji": "🍜",
            "title": "ตะลอนกิน",
            "color": "#E85D30",
            "places_list": [
                "• ตลาดสดท่ายาง",
                "• ร้านทองม้วนแม่เล็ก",
                "• ร้านผัดไทย 100 ปี",
                "• ข้าวแช่แม่เล็ก สกิดใจ"
            ]
        }
    ]

    bubbles = []
    for cat in categories:
        place_texts = [
            TextComponent(
                text=p,
                size="sm",
                color="#555555",
                wrap=True
            ) for p in cat["places_list"]
        ]

        bubble = Bubble(
            body=BoxComponent(
                layout="vertical",
                spacing="sm",
                contents=[
                    TextComponent(
                        text=cat["emoji"],
                        size="xxl",
                        align="center"
                    ),
                    TextComponent(
                        text=cat["title"],
                        weight="bold",
                        size="md",
                        align="center",
                        color=cat["color"],
                        wrap=True
                    ),
                    SeparatorComponent(margin="md"),
                    BoxComponent(
                        layout="vertical",
                        margin="md",
                        spacing="xs",
                        contents=place_texts
                    )
                ]
            )
        )
        bubbles.append(bubble)

    carousel = FlexMessage(
        alt_text="กิจกรรมแนะนำในอำเภอท่ายาง",
        contents=Carousel(contents=bubbles)
    )

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[carousel]
        )
    )

# =========================
# 📖 เกี่ยวกับท่ายาง
# =========================
def send_info(api, event):
    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(text="📖 เกี่ยวกับอำเภอท่ายาง\nเลือกหัวข้อที่สนใจ"),
                TextMessage(
                    text="เลือกหัวข้อ",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyItem(
                                action=MessageAction(
                                    label="📜 ประวัติความเป็นมา",
                                    text="info_history"
                                )
                            ),
                            QuickReplyItem(
                                action=MessageAction(
                                    label="⭐ จุดเด่นของพื้นที่",
                                    text="info_highlight"
                                )
                            ),
                            QuickReplyItem(
                                action=MessageAction(
                                    label="🏡 วิถีชีวิตชุมชน",
                                    text="info_lifestyle"
                                )
                            )
                        ]
                    )
                )
            ]
        )
    )

# =========================
# 📩 HANDLE MESSAGE
# =========================
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()
    print(f"[DEBUG] received: '{text}'")

    place_names = list(places.keys())

    with ApiClient(configuration) as api_client:
        api = MessagingApi(api_client)

        # --- สถานที่ท่องเที่ยว ---
        if text in ["travel", "สถานที่ท่องเที่ยว"]:
            send_places(api, event)

        # --- กดจาก Quick Reply place_0 .. place_8 ---
        elif text.startswith("place_"):
            try:
                idx = int(text.replace("place_", ""))
                name = place_names[idx]
                print(f"[DEBUG] place index {idx} = {name}")
                send_place_detail(api, event, name)
            except (ValueError, IndexError):
                send_places(api, event)

        # --- พิมพ์ชื่อสถานที่ตรงๆ ---
        elif text in places:
            send_place_detail(api, event, text)

        # --- แผนที่ ---
        elif text in ["map", "แผนที่", "แผนที่อำเภอ", "แผนที่ภายในอำเภอท่ายาง"]:
            send_map(api, event)

        elif text.startswith("map_"):
            suffix = text.replace("map_", "")

            if suffix == "all":
                url = "https://maps.google.com/?q=อำเภอท่ายาง+เพชรบุรี"
                label = "อำเภอท่ายาง"
            else:
                try:
                    idx = int(suffix)
                    name = place_names[idx]
                    url = places[name]["map"]
                    label = name
                except (ValueError, IndexError):
                    url = "https://maps.google.com/?q=อำเภอท่ายาง"
                    label = "อำเภอท่ายาง"

            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f"🗺 เส้นทางไป {label}\n{url}")]
                )
            )

        # --- กิจกรรม ---
        elif text in ["activity", "กิจกรรมภายในอำเภอท่ายาง"]:
            send_activity(api, event)

        # --- เกี่ยวกับท่ายาง ---
        elif text in ["info", "เกี่ยวกับอำเภอท่ายาง"]:
            send_info(api, event)

        elif text.startswith("info_"):
            key = text.replace("info_", "")
            if key in info:
                titles = {
                    "history": "📜 ประวัติความเป็นมา",
                    "highlight": "⭐ จุดเด่นของพื้นที่",
                    "lifestyle": "🏡 วิถีชีวิตชุมชน"
                }
                title = titles.get(key, "")
                api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            TextMessage(text=f"{title}\n\n{info[key]}")
                        ]
                    )
                )
            else:
                send_info(api, event)

        # --- Fuzzy Search ---
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
