import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
from agents.meditation_agent import handle_meditation
from agents.story_agent import handle_story
from agents.fun_agent import handle_fun

load_dotenv()
app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

@app.route("/")
def health_check():
    return "OK"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id

    if "冥想" in user_message or "靜心" in user_message:
        reply = handle_meditation(user_message)
    elif "故事" in user_message:
        reply = handle_story(user_message, user_id)
    elif "梗圖" in user_message or "音樂" in user_message or "影片" in user_message:
        reply = handle_fun(user_message)
    else:
        reply = "我是你的AI朋友，可以陪你聊天、說故事、或幫你放鬆一下～
輸入：冥想、故事、梗圖、音樂、影片"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))