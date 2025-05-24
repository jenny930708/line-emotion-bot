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

# 載入 .env 設定
load_dotenv()
app = Flask(__name__)

# 初始化 LINE 與 OpenAI
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Google CSE 搜尋圖片
def search_meme_image(query):
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_CX")
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&cx={cse_id}&searchType=image&key={api_key}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        results = res.json().get("items", [])
        if results:
            return random.choice(results)["link"]
    except Exception as e:
        print("❌ 梗圖搜尋失敗：", e)
    return None

# GPT 回覆
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

# 健康檢查
@app.route("/")
def health_check():
    return "OK"

# 測試梗圖搜尋（直接瀏覽器看結果）
@app.route("/test-image")
def test_image():
    keywords = ["療癒梗圖", "搞笑梗圖", "心情不好梗圖", "台灣梗圖", "中文梗圖"]
    img_url = search_meme_image(random.choice(keywords))
    return f"<img src='{img_url}' width='300'>" if img_url else "❌ 找不到梗圖"

# LINE Webhook
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# 處理訊息
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
    elif "梗圖" in user_message:
        keywords = ["療癒梗圖", "搞笑梗圖", "中文梗圖", "台灣梗圖"]
        img_url = search_meme_image(random.choice(keywords))
        if img_url:
            reply = ImageSendMessage(original_content_url=img_url, preview_image_url=img_url)
        else:
            reply = TextSendMessage(text="❌ 目前找不到梗圖 😢")
    elif "音樂" in user_message or "影片" in user_message:
        reply = TextSendMessage(text=handle_fun(user_message))
    else:
        reply = TextSendMessage(text=chat_with_gpt(user_message))

    line_bot_api.reply_message(event.reply_token, reply)

# 啟動服務
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
