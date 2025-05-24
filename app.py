
import os
import re
import random
import urllib.parse
import requests
from flask import Flask, request, abort
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

load_dotenv()

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# ✅ YouTube 搜尋第一筆影片連結
def search_youtube_link(query):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        html = requests.get(url, headers=headers).text
        match = re.search(r'"url":"/watch\?v=(.{11})"', html)
        if match:
            return f"https://www.youtube.com/watch?v={match.group(1)}"
    except Exception as e:
        print("YouTube 查詢失敗：", e)
    return "（找不到連結）"

# ✅ 音樂請求處理（處理我想聽 xxx、播放 xxx）
def handle_music_request(user_message):
    keywords = user_message
    for word in ["我想聽", "播放", "想聽", "來點", "給我", "音樂", "歌曲", "歌"]:
        keywords = keywords.replace(word, "")
    keywords = keywords.strip()
    if not keywords:
        keywords = "熱門音樂"
    link = search_youtube_link(keywords)
    return TextSendMessage(text=f"🎵 這是你可能會喜歡的音樂：\n{link}")

# ✅ 動態推薦歌手歌曲（不限歌手）+ 自動附連結
def auto_recommend_artist(user_message):
    artist_match = re.search(r"(推薦.*?)([\u4e00-\u9fa5A-Za-z0-9]+)(的歌|的歌曲)", user_message)
    if artist_match:
        artist = artist_match.group(2)
        common_titles = ["代表作", "經典歌曲", "熱門歌曲", "必聽歌曲", "傳唱歌曲"]
        msg = f"這裡是為你推薦的「{artist}」熱門歌曲：\n\n"
        for idx in range(1, 6):
            fake_title = f"{artist} {random.choice(common_titles)} {idx}"
            link = search_youtube_link(fake_title)
            msg += f"{idx}. {fake_title} 👉 {link}\n"
        msg += "\n以上推薦為自動搜尋結果，如想指定歌曲可直接輸入『我想聽 + 歌名』"
        return TextSendMessage(text=msg)

    return TextSendMessage(text="請告訴我你想聽哪位歌手的歌，例如：推薦幾首周杰倫的歌")

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
    print(f"[使用者訊息] {user_message}")

    if "推薦" in user_message and "歌" in user_message:
        reply = auto_recommend_artist(user_message)
    elif "聽" in user_message or "播放" in user_message:
        reply = handle_music_request(user_message)
    else:
        reply = TextSendMessage(text="你可以說：『推薦幾首某某歌手的歌』或『我想聽 xxx』來試試 🎶")

    line_bot_api.reply_message(event.reply_token, reply)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
