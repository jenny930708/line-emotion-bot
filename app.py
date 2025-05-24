import os
import random
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    ImageSendMessage
)
from dotenv import load_dotenv
from openai import OpenAI

from agents.meditation_agent import handle_meditation
from agents.story_agent import handle_story

load_dotenv()
app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 👉 Google CSE 設定
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CSE_CX", "YOUR_CSE_CX")

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

def search_meme_image(query):
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": query + " 梗圖",
        "searchType": "image",
        "num": 10,
        "safe": "high",
    }
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        items = response.json().get("items", [])
        if not items:
            return None
        return random.choice(items)["link"]
    except Exception as e:
        print(f"[ERROR] 搜尋圖片失敗：{e}")
        return None

def handle_fun(user_message):
    if "梗圖" in user_message:
        keywords = ["台灣梗圖", "迷因圖", "搞笑圖片", "厭世梗圖"]
        image_url = search_meme_image(random.choice(keywords))
        if image_url:
            return {
                "type": "image",
                "originalContentUrl": image_url,
                "previewImageUrl": image_url
            }
        else:
            return {
                "type": "text",
                "text": "目前找不到梗圖 😢"
            }
    elif "音樂" in user_message:
        return {
            "type": "text",
            "text": "這首歌也許能振奮你的心情：https://www.youtube.com/watch?v=ZbZSe6N_BXs"
        }
    elif "影片" in user_message:
        return {
            "type": "text",
            "text": "這支短影片讓你笑一笑：https://www.youtube.com/shorts/abc123xyz"
        }
    return None

def handle_music_request(user_message):
    if "周杰倫" in user_message:
        return "這是周杰倫的經典歌曲，希望你喜歡～ https://www.youtube.com/watch?v=2jD5V8YVhJM"
    elif "別的" in user_message or "換一首" in user_message:
        return "試試這首新歌看看，也許會讓你感覺更放鬆：https://www.youtube.com/watch?v=UfcAVejslrU"
    else:
        return "這首歌也許能振奮你的心情：https://www.youtube.com/watch?v=ZbZSe6N_BXs"

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

    if "心情不好" in user_message or "不開心" in user_message or "難過" in user_message:
        reply = TextSendMessage(text="聽起來你今天過得不太好，我在這裡陪你。這首音樂也許能陪伴你：https://www.youtube.com/watch?v=inpok4MKVLM")
    elif "我想聽" in user_message and "歌" in user_message:
        reply = TextSendMessage(text=handle_music_request(user_message))
    elif "冥想" in user_message or "靜心" in user_message:
        reply = TextSendMessage(text=handle_meditation(user_message))
    elif "故事" in user_message:
        reply = TextSendMessage(text=handle_story(user_message, user_id))
    elif "梗圖" in user_message or "音樂" in user_message or "影片" in user_message:
        fun_result = handle_fun(user_message)
        if fun_result["type"] == "image":
            reply = ImageSendMessage(
                original_content_url=fun_result["originalContentUrl"],
                preview_image_url=fun_result["previewImageUrl"]
            )
        else:
            reply = TextSendMessage(text=fun_result["text"])
    else:
        reply = TextSendMessage(text=chat_with_gpt(user_message))

    line_bot_api.reply_message(event.reply_token, reply)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
