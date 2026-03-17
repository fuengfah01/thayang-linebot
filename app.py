from flask import Flask, request
from linebot.v3.messaging import *
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from places import places
from activities import activities
from foods import foods

import os

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = "4daQ2JUnEe+vEmbDJhOmn48fWc7d/Kb6+iWXIm05H8ngOFqDPLyNpgdTO58cKvHyfcL/q/gytkIljJiMSjAQCvN5wmahGaLKoVocuepLo5tyQq7q33YfsPZPhxpO8kPOrpnECFRdZPB0JjHKaKaPOQdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "a97e9e9977b3aac81ca9af33e59bde55"

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 🔥 เก็บ history
user_state = {}

def push_state(user_id, state):
    user_state.setdefault(user_id, []).append(state)

def pop_state(user_id):
    if user_id in user_state and len(user_state[user_id]) > 1:
        user_state[user_id].pop()
        return user_state[user_id][-1]
    return "menu"

# =========================
# 🧠 SMART SEARCH
# =========================
def smart_search(text):
    for name in places:
        if name in text:
            return name
    return None

# =========================
# 📍 เมนูหลัก
# =========================
def send_main_menu(api, event):
    push_state(event.source.user_id, "menu")

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(
                    text="📍 เมนูหลัก",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyItem(action=MessageAction(label="📍 Travel", text="travel")),
                            QuickReplyItem(action=MessageAction(label="🍜 Food", text="food")),
                            QuickReplyItem(action=MessageAction(label="🏨 Activity", text="activity")),
                            QuickReplyItem(action=MessageAction(label="🗺 Map", text="map"))
                        ]
                    )
                )
            ]
        )
    )

# =========================
# 🔙 ปุ่ม
# =========================
def back_buttons():
    return [
        QuickReplyItem(action=MessageAction(label="🔙 กลับ", text="back")),
        QuickReplyItem(action=MessageAction(label="🏠 เมนู", text="menu"))
    ]

# =========================
# 📍 TRAVEL
# =========================
def send_places(api, event):
    push_state(event.source.user_id, "travel")

    items = [
        QuickReplyItem(action=MessageAction(label=name, text=f"place_{name}"))
        for name in places
    ] + back_buttons()

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text="📍 เลือกสถานที่", quick_reply=QuickReply(items=items))]
        )
    )

def send_place_detail(api, event, name):
    push_state(event.source.user_id, f"place_{name}")
    p = places[name]

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                ImageMessage(original_content_url=p["image"], preview_image_url=p["image"]),
                TextMessage(
                    text=f"""📍 {name}
⭐ {p.get('highlight','-')}
⏰ {p.get('time','-')}""",
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyItem(action=MessageAction(label="🎯 กิจกรรม", text=f"act_{name}")),
                            QuickReplyItem(action=MessageAction(label="🍜 อาหาร", text=f"food_{name}")),
                            QuickReplyItem(action=MessageAction(label="🗺 แผนที่", text=f"map_place_{name}")),
                        ] + back_buttons()
                    )
                )
            ]
        )
    )

# =========================
# 🍜 FOOD
# =========================
def send_food(api, event, place=None):
    push_state(event.source.user_id, "food")

    if place and place in foods:
        items = [
            QuickReplyItem(action=MessageAction(label=f["name"], text=f["map"]))
            for f in foods[place]
        ] + back_buttons()

        api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"🍜 {place}", quick_reply=QuickReply(items=items))]
            )
        )
    else:
        items = []
        for p in foods:
            items.append(QuickReplyItem(action=MessageAction(label=p, text=f"food_{p}")))

        items += back_buttons()

        api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="🍜 เลือกสถานที่กิน", quick_reply=QuickReply(items=items))]
            )
        )

# =========================
# 🏨 ACTIVITY
# =========================
def send_activity(api, event, place=None):
    push_state(event.source.user_id, "activity")

    if place and place in activities:
        items = [
            QuickReplyItem(action=MessageAction(label=a["name"], text=f"act_detail_{a['name']}"))
            for a in activities[place]
        ] + back_buttons()
    else:
        items = [
            QuickReplyItem(action=MessageAction(label=p, text=f"act_{p}"))
            for p in activities
        ] + back_buttons()

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text="🏨 เลือกกิจกรรม", quick_reply=QuickReply(items=items))]
        )
    )

def send_activity_detail(api, event, name):
    push_state(event.source.user_id, f"act_detail_{name}")

    for p in activities:
        for a in activities[p]:
            if a["name"] == name:
                api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            ImageMessage(original_content_url=a["image"], preview_image_url=a["image"]),
                            TextMessage(
                                text=f"{a['name']}\n⭐ {a['highlight']}\n⏰ {a['time']}",
                                quick_reply=QuickReply(items=back_buttons())
                            )
                        ]
                    )
                )
                return

# =========================
# 🗺 MAP
# =========================
def send_map(api, event):
    push_state(event.source.user_id, "map")

    items = [
        QuickReplyItem(action=MessageAction(label="📍 ไปท่ายาง", text="https://maps.google.com/?q=ท่ายาง"))
    ]

    for p in places:
        items.append(
            QuickReplyItem(action=MessageAction(label=p, text=places[p]["map"]))
        )

    items += back_buttons()

    api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text="🗺 เลือกแผนที่", quick_reply=QuickReply(items=items))]
        )
    )

# =========================
# 📩 HANDLE
# =========================
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()
    user_id = event.source.user_id

    with ApiClient(configuration) as api_client:
        api = MessagingApi(api_client)

        if text == "menu":
            send_main_menu(api, event)

        elif text == "back":
            last = pop_state(user_id)

            if last == "menu":
                send_main_menu(api, event)
            elif last == "travel":
                send_places(api, event)
            elif last == "food":
                send_food(api, event)
            elif last == "activity":
                send_activity(api, event)
            elif last == "map":
                send_map(api, event)
            elif last.startswith("place_"):
                send_place_detail(api, event, last.replace("place_", ""))

        elif text == "travel":
            send_places(api, event)

        elif text.startswith("place_"):
            send_place_detail(api, event, text.replace("place_", ""))

        elif text == "food":
            send_food(api, event)

        elif text.startswith("food_"):
            send_food(api, event, text.replace("food_", ""))

        elif text == "activity":
            send_activity(api, event)

        elif text.startswith("act_detail_"):
            send_activity_detail(api, event, text.replace("act_detail_", ""))

        elif text.startswith("act_"):
            send_activity(api, event, text.replace("act_", ""))

        elif text == "map":
            send_map(api, event)

        elif text.startswith("http"):
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f"🗺 เปิดแผนที่:\n{text}")]
                )
            )

        else:
            found = smart_search(text)
            if found:
                send_place_detail(api, event, found)
            else:
                send_main_menu(api, event)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)