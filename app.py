import os
import random
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from dotenv import load_dotenv
from openai import OpenAI

from agents.meditation_agent import handle_meditation
from agents.story_agent import handle_story
from agents.fun_agent import handle_fun, handle_music_request

load_dotenv()
app = Flask(__name__)

# 驗證變數是否有成功讀取
REQUIRED_ENV = ["LINE_CHANNEL_ACCESS_TOKEN", "LINE_CHANNEL_SECRET", "OPENAI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_CSE_ID"]
for var in REQUIRED_ENV:
    if not os.getenv(var):
        print(f"❗️環境變數 {var} 沒有正確設置，請確認 .env")

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 搜尋梗圖
def search_meme_image(query):
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&cx={cse_id}&searchType=image&key={api_key}"

    try:
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
        items = data.get("items", [])
        if items:
            chosen = random.choice(items)
            return chosen.get("link")
        else:
            print("⚠️ 沒有搜尋到圖片")
    except Exception as e:
        print(f"[錯誤] 搜尋圖片失敗: {e}")
    return None

# GPT 聊天功能
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
        print(f"[OpenAI 錯誤] {e}")
        return "⚠️ 抱歉，我暫時無法回覆你的訊息喔～"

@app.route("/")
def health_check():
    return "OK"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
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
    print(f"[使用者訊息] {user_id}: {user_message}")

    try:
        if "心情不好" in user_message or "不開心" in user_message or "難過" in user_message:
            reply = TextSendMessage(text="聽起來你今天過得不太好，我在這裡陪你。這首音樂也許能陪伴你：https://www.youtube.com/watch?v=inpok4MKVLM")
        elif "我想聽" in user_message and "歌" in user_message:
            reply = TextSendMessage(text=handle_music_request(user_message))
        elif "冥想" in user_message or "靜心" in user_message:
            reply = TextSendMessage(text=handle_meditation(user_message))
        elif "故事" in user_message:
            reply = TextSendMessage(text=handle_story(user_message, user_id))
        elif "梗圖" in user_message:
            keywords = ["療癒梗圖", "心情不好梗圖", "搞笑梗圖", "中文梗圖"]
            image_url = search_meme_image(random.choice(keywords))
            if image_url:
                reply = ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
            else:
                reply = TextSendMessage(text="目前找不到梗圖 😥")
        elif "音樂" in user_message or "影片" in user_message:
            reply = TextSendMessage(text=handle_fun(user_message))
        else:
            reply = TextSendMessage(text=chat_with_gpt(user_message))
    except Exception as e:
        print(f"[訊息處理錯誤] {e}")
        reply = TextSendMessage(text="⚠️ 系統忙碌中，稍後再試看看好嗎？")

    line_bot_api.reply_message(event.reply_token, reply)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
