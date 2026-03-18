from flask import Flask, request, send_from_directory
import os
from rapidfuzz import process

# นำเข้าคลาสหลักที่จำเป็นสำหรับ Messaging API
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    FlexMessage,
    QuickReply,
    QuickReplyItem,
    MessageAction,
    URIAction,
    # นำเข้าคลาสสำหรับสร้าง Flex Message ไว้ที่นี่ที่เดียวเพื่อความเสถียร
    Bubble, 
    ImageComponent, 
    BoxComponent, 
    TextComponent, 
    SeparatorComponent, 
    ButtonComponent,
    Carousel
)
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from places import places
from info import info

app = Flask(__name__)

# แนะนำให้ใช้ Environment Variable ในหน้า Render Settings แทนการใส่ในโค้ด
CHANNEL_ACCESS_TOKEN = "4daQ2JUnEe+vEmbDJhOmn48fWc7d/Kb6+iWXIm05H8ngOFqDPLyNpgdTO58cKvHyfcL/q/gytkIljJiMSjAQCvN5wmahGaLKoVocuepLo5tyQq7q33YfsPZPhxpO8kPOrpnECFRdZPB0JjHKaKaPOQdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "a97e9e9977b3aac81ca9af33e59bde55"

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route('/image/<path:filename>')
def serve_image(filename):
    return send_from_directory('image', filename)

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
        print(f"[DEBUG] handler error: {e}")
    return "OK", 200

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
        if score > 70:
            return mapping[word]
    return None

def send_places(api, event):
    names = list(places.keys())[:12]
    items = []
    for n in names:
        items.append(QuickReplyItem(action=MessageAction(label=n[:20], text=n)))
    
    api.reply_message(ReplyMessageRequest(
        reply_token=event.reply_token,
        messages=[TextMessage(text="📍 เลือกสถานที่ท่องเที่ยวที่คุณสนใจในท่ายาง", quick_reply=QuickReply(items=items))]
    ))

def send_place_detail(api, event, name):
    if name not in places:
        return
    
    p = places[name]
    flex = FlexMessage(
        alt_text=f"ข้อมูล {name}",
        contents=Bubble(
            hero=ImageComponent(url=p["images"][0], size="full", aspect_ratio="20:13", aspect_mode="cover"),
            body=BoxComponent(
                layout="vertical", spacing="sm",
                contents=[
                    TextComponent(text=name, weight="bold", size="xl", color="#1a1a1a"),
                    SeparatorComponent(margin="sm"),
                    BoxComponent(layout="vertical", margin="md", spacing="sm", contents=[
                        BoxComponent(layout="horizontal", contents=[
                            TextComponent(text="📜", flex=0, size="sm"),
                            TextComponent(text=p["history"], wrap=True, size="sm", color="#555555", flex=1, margin="sm")
                        ]),
                        BoxComponent(layout="horizontal", contents=[
                            TextComponent(text="⭐", flex=0, size="sm"),
                            TextComponent(text=p["highlight"], wrap=True, size="sm", color="#555555", flex=1, margin="sm")
                        ]),
                        BoxComponent(layout="horizontal", contents=[
                            TextComponent(text="⏰", flex=0, size="sm"),
                            TextComponent(text=p["time"], size="sm", color="#888888", flex=1, margin="sm")
                        ])
                    ])
                ]
            ),
            footer=BoxComponent(layout="vertical", contents=[
                ButtonComponent(action=URIAction(label="🗺 ดูแผนที่ / นำทาง", uri=p["map"]), style="primary", color="#4A90D9")
            ])
        )
    )
    api.reply_message(ReplyMessageRequest(reply_token=event.reply_token, messages=[flex]))

def send_map(api, event):
    names = list(places.keys())[:10]
    items = []
    for i, n in enumerate(names):
        items.append(QuickReplyItem(action=MessageAction(label=f"แผนที่ {n[:15]}", text=f"map_{i}")))
    items.append(QuickReplyItem(action=MessageAction(label="📍 แผนที่ท่ายางทั้งหมด", text="map_all")))
    
    api.reply_message(ReplyMessageRequest(
        reply_token=event.reply_token,
        messages=[TextMessage(text="🗺 เลือกสถานที่เพื่อดูเส้นทาง หรือดูแผนที่รวม", quick_reply=QuickReply(items=items))]
    ))

def send_activity(api, event):
    categories = [
        {"emoji": "🙏", "title": "ไหว้พระ / ทำบุญ", "color": "#F5A623", "places_list": ["• วัดท่าคอย", "• ศาลเจ้าพ่อกวนอู"]},
        {"emoji": "📸", "title": "ถ่ายรูปวัฒนธรรม", "color": "#7B68EE", "places_list": ["• อุโบสถ 100 ปี", "• ตลาดเก่า"]},
        {"emoji": "🐟", "title": "พักผ่อนหย่อนใจ", "color": "#4A90D9", "places_list": ["• อุทยานปลาวัดท่าคอย"]},
        {"emoji": "🍜", "title": "ตะลอนกิน", "color": "#E85D30", "places_list": ["• ผัดไทย 100 ปี", "• ข้าวแช่แม่เล็ก"]}
    ]
    bubbles = []
    for cat in categories:
        bubbles.append(Bubble(body=BoxComponent(layout="vertical", spacing="sm", contents=[
            TextComponent(text=cat["emoji"], size="xxl", align="center"),
            TextComponent(text=cat["title"], weight="bold", size="md", align="center", color=cat["color"], wrap=True),
            SeparatorComponent(margin="md"),
            BoxComponent(layout="vertical", margin="md", spacing="xs",
                contents=[TextComponent(text=p, size="sm", color="#555555", wrap=True) for p in cat["places_list"]])
        ])))
    
    api.reply_message(ReplyMessageRequest(
        reply_token=event.reply_token,
        messages=[FlexMessage(alt_text="กิจกรรมแนะนำ", contents=Carousel(contents=bubbles))]
    ))

def send_info(api, event):
    api.reply_message(ReplyMessageRequest(
        reply_token=event.reply_token,
        messages=[
            TextMessage(text="📖 เกี่ยวกับอำเภอท่ายาง\nเลือกหัวข้อที่สนใจได้เลยครับ", 
                        quick_reply=QuickReply(items=[
                            QuickReplyItem(action=MessageAction(label="📜 ประวัติ", text="info_history")),
                            QuickReplyItem(action=MessageAction(label="⭐ จุดเด่น", text="info_highlight")),
                            QuickReplyItem(action=MessageAction(label="🏡 วิถีชีวิต", text="info_lifestyle"))
                        ]))
        ]
    ))

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()
    place_names = list(places.keys())

    with ApiClient(configuration) as api_client:
        api = MessagingApi(api_client)

        if text in ["สถานที่ท่องเที่ยว", "travel"]:
            send_places(api, event)
        elif text in ["แผนที่อำเภอท่ายาง", "แผนที่", "map"]:
            send_map(api, event)
        elif text in ["กิจกรรม", "activity"]:
            send_activity(api, event)
        elif text in ["เกี่ยวกับอำเภอท่ายาง", "info"]:
            send_info(api, event)
        elif text in places:
            send_place_detail(api, event, text)
        elif text.startswith("map_"):
            suffix = text.replace("map_", "")
            if suffix == "all":
                url = "https://www.google.com/maps/search/อำเภอท่ายาง"
                label = "อำเภอท่ายาง"
            else:
                try:
                    idx = int(suffix)
                    name = place_names[idx]
                    url = places[name]["map"]
                    label = name
                except:
                    url = "https://www.google.com/maps"
                    label = "ท่ายาง"
            api.reply_message(ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"🗺 เส้นทางไป {label}\n{url}")]
            ))
        elif text.startswith("info_"):
            key = text.replace("info_", "")
            if key in info:
                api.reply_message(ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=info[key])]
                ))
        else:
            match = fuzzy_search_place(text)
            if match:
                send_place_detail(api, event, match)
            else:
                send_places(api, event)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)