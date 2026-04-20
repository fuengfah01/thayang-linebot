# app.py — Main Flask server
import os
import logging
from flask import Flask, request, jsonify, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dialogflow_handler import handle_dialogflow

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "PNOGvfmIWQ3/BcVmw2rLjWwhWCVKe+ZMQl12nn4Dd/1aX0eAdxY9Q2pPPI/XMXgXfcL/q/gytkIljJiMSjAQCvN5wmahGaLKoVocuepLo5s98q0hD6fF6yGE9U8xfnPI9ayXKt13DQ/Tp1mV7MtYLgdB04t89/1O/w1cDnyilFU=")
LINE_CHANNEL_SECRET       = os.environ.get("LINE_CHANNEL_SECRET", "ca7f131ffbb010718720d8bb21230a23")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler      = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route("/", methods=["GET"])
def index():
    return "Thayang LINE Bot is running ✅", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body      = request.get_data(as_text=True)
    app.logger.info(f"[WEBHOOK] {body[:200]}")
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.warning("[WEBHOOK] Invalid signature")
        abort(400)
    return "OK", 200


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    user_id   = event.source.user_id
    app.logger.info(f"[LINE] user={user_id} msg={user_text}")

    try:
        from dialogflow_handler import detect_intent
        result = detect_intent(user_text, session_id=user_id)
        reply  = result["fulfillment_text"] or "ขออภัย ไม่เข้าใจคำถามครับ"
    except Exception as e:
        app.logger.error(f"[DIALOGFLOW ERROR] {e}")
        reply = "ขออภัย เกิดข้อผิดพลาดครับ"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

@app.route("/dialogflow", methods=["POST"])
def dialogflow_webhook():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"fulfillmentText": "ไม่ได้รับข้อมูลครับ"}), 200
    intent = body.get("queryResult", {}).get("intent", {}).get("displayName", "unknown")
    app.logger.info(f"[DIALOGFLOW] intent={intent}")
    response = handle_dialogflow(body)
    return jsonify(response), 200


@app.route("/health", methods=["GET"])
def health():
    try:
        from db import query_one
        query_one("SELECT 1")
        return jsonify({"status": "ok", "db": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "error", "db": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)