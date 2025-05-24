import os
import random
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
from openai import OpenAI

from agents.meditation_agent import handle_meditation
from agents.story_agent import handle_story
from agents.fun_agent import handle_fun, handle_music_request, search_meme_image  # 加入 search_meme_image

# 載入環境變數
load_dotenv()
app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chat_with_gpt(user_message):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一位溫柔的 AI 好朋友，擅長安撫使用者情緒、傾聽與聊天。"},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ OpenAI 發生錯誤：{str(e)}"

@app.route("/")
def health_check():
    return "OK"

@app.route("/test-image")
def test_image():
    keyword = request.args.get("q", "梗圖")
    image_url = search_meme_image(keyword)
    if image_url:
        return f"<img src='{image_url}' style='max-width: 400px;'><br><code>{image_url}</code>"
    else:
        return "❌ 找不到梗圖"

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

    if "心情不好" in user_message or "不開心" in user_message or "難過" in user_message:
        reply = TextSendMessage(text="聽起來你今天過得不太好，我在這裡陪你。這首音樂也許能陪伴你：https://www.youtube.com/watch?v=inpok4MKVLM")

    elif "我想聽" in user_message and "歌" in user_message:
        reply = TextSendMessage(text=handle_music_request(user_message))

    elif "冥想" in user_message or "靜心" in user_message:
        reply = TextSendMessage(text=handle_meditation(user_message))

    elif "故事" in user_message:
        reply = TextSendMessage(text=handle_story(user_message, user_id))

    elif "梗圖" in user_message or "音樂" in user_message or "影片" in user_message:
        reply = handle_fun(user_message)

    else:
        reply = TextSendMessage(text=chat_with_gpt(user_message))

    line_bot_api.reply_message(event.reply_token, reply)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
