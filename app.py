import os
import re
import urllib.parse
import requests
from flask import Flask, request, abort
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 載入 .env 變數
load_dotenv()
app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 紀錄每個使用者是否進入情緒推薦模式
last_emotion_status = {}

# ⛏ 修正後的歌手 / 歌名擷取函式
def extract_singer(text):
    patterns = [
        r"我想聽(.*?)(的)?(歌|音樂)?",
        r"可以聽(.*?)(的)?(歌|音樂)?",
        r"聽(.*?)(的)?(歌|音樂)?"
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(1).strip()
            return re.sub(r"[的歌音樂\s]+$", "", candidate)
    return None

# 透過歌手名搜尋 YouTube，回傳標題含關鍵字的影片
def search_youtube_by_singer(singer_name):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(singer_name)}"
    html = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")

    for a_tag in soup.find_all("a"):
        title = a_tag.get("title")
        href = a_tag.get("href")
        if title and href and "/watch?v=" in href:
            if singer_name in title:
                video_id = href.split("v=")[-1].split("&")[0]
                return f"https://www.youtube.com/watch?v={video_id}"
    return None

# LINE webhook 入口
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# 文字訊息處理主體
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_msg = event.message.text.lower()

    # 偵測情緒關鍵字
    negative_keywords = ["心情不好", "難過", "不開心", "想哭", "崩潰", "低落", "焦慮", "沮喪"]
    is_negative = any(word in user_msg for word in negative_keywords)

    if is_negative:
        last_emotion_status[user_id] = True

    # 若進入情緒推薦模式
    if last_emotion_status.get(user_id, False):
        singer = extract_singer(user_msg)
        if singer:
            video_url = search_youtube_by_singer(singer)
            if video_url:
                reply = f"聽聽這首「{singer}」的歌，希望能讓你心情好一點 🎵\n{video_url}"
            else:
                reply = "目前找不到合適的音樂連結，稍後再試試看喔～"
            last_emotion_status[user_id] = False
        else:
            reply = "你可以說「我想聽〇〇的歌」，我會推薦一首影片給你 🎧"
    else:
        reply = "你可以說「我心情不好，我想聽〇〇的歌」，我會幫你推薦音樂 🎵"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# 適配 Render 的埠口
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
