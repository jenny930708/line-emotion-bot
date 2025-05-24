
import os
import re
import random
import urllib.parse
import requests
from flask import Flask, request, abort
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage

# ✅ 載入 .env 環境變數
load_dotenv()

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# ✅ YouTube 音樂搜尋功能
def search_youtube_link(query):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        html = requests.get(search_url, headers=headers).text
        match = re.search(r'"url":"/watch\?v=(.{11})"', html)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"
    except Exception as e:
        print("❌ YouTube 查詢失敗：", e)
    return "（找不到連結）"

# ✅ 音樂請求處理
def handle_music_request(user_message):
    keywords = user_message.replace("我想聽", "").replace("播放", "").replace("音樂", "").replace("歌", "").strip()
    if not keywords:
        default_choices = [
            "chill music playlist", "happy music", "focus study music",
            "lofi chillhop", "ambient relaxing music"
        ]
        keywords = random.choice(default_choices)
    link = search_youtube_link(keywords)
    return TextSendMessage(text=f"🎵 這是你可能會喜歡的音樂：\n{link}")

# ✅ 梗圖與影片處理
def search_meme_image_by_yahoo(query="梗圖"):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://tw.images.search.yahoo.com/search/images?p={query}"
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        img_tags = soup.select("img")
        img_urls = [img["src"] for img in img_tags if img.get("src") and img["src"].startswith("http")]
        if img_urls:
            return random.choice(img_urls)
    except Exception as e:
        print(f"[Yahoo 搜圖錯誤] {e}")
    return None

def handle_fun(user_message):
    if "梗圖" in user_message:
        theme_keywords = ["動物", "狗", "貓", "熊", "老虎", "貓咪", "狗狗", "鯊魚", "食物", "人類", "日常", "漫畫", "梗"]
        matched_theme = next((word for word in theme_keywords if word in user_message), None)
        search_query = f"{matched_theme}梗圖" if matched_theme else "梗圖"
        image_url = search_meme_image_by_yahoo(search_query)
        if image_url:
            return ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
        else:
            return TextSendMessage(text=f"❌ 沒找到與「{search_query}」相關的梗圖 😥")
    elif "影片" in user_message:
        return TextSendMessage(text="這支短影片讓你笑一笑：https://www.youtube.com/shorts/abc123xyz")
    return TextSendMessage(text="你可以說：播放影片、來張梗圖等等喔！")

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
    print(f"[使用者訊息] {user_message}")

    if ("聽" in user_message) and ("音樂" in user_message or "歌" in user_message):
        reply = handle_music_request(user_message)
    elif "梗圖" in user_message or "影片" in user_message:
        reply = handle_fun(user_message)
    else:
        reply = TextSendMessage(text="你可以說『我想聽音樂』或『給我梗圖』來試試看喔！")

    line_bot_api.reply_message(event.reply_token, reply)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
