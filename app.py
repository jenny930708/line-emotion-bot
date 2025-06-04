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
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 載入 .env 的環境變數
load_dotenv()

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 偵測負面情緒的關鍵字
negative_keywords = ["難過", "不開心", "心情不好", "低落", "不爽", "崩潰", "沮喪", "想哭", "壓力", "焦慮"]

# 隨機選幾個推薦關鍵字
recommend_keywords = ["療癒中文歌", "放鬆音樂", "抒情中文歌", "安靜的音樂", "希望的音樂", "台灣療癒歌曲"]

# 搜尋 YouTube 並取得第一個影片連結
def search_youtube_link(query):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    html = requests.get(url, headers=headers).text
    video_ids = re.findall(r'"url":"/watch\?v=(.{11})"', html)
    if video_ids:
        return f"https://www.youtube.com/watch?v={video_ids[0]}"
    return None

# 主 webhook
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# 處理文字訊息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text

    if any(word in user_msg for word in negative_keywords):
        # 隨機挑一個推薦主題
        keyword = random.choice(recommend_keywords)
        video_link = search_youtube_link(keyword)
        if video_link:
            reply = f"聽聽這首「{keyword}」，希望能讓你心情好一點 🎵\n{video_link}"
        else:
            reply = "目前找不到合適的音樂連結，稍後再試試看喔～"
    else:
        reply = "你可以說「我心情不好」，我會幫你推薦療癒的音樂 🎧"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run()
