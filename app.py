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

load_dotenv()
app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 關鍵字設定
negative_keywords = ["難過", "不開心", "心情不好", "低落", "不爽", "崩潰", "沮喪", "想哭", "壓力", "焦慮"]
recommend_keywords = ["療癒音樂", "放鬆音樂", "抒情歌曲", "希望的音樂", "安靜的音樂"]
chinese_keywords = ["中文", "華語", "中文歌", "聽中文"]
english_keywords = ["英文", "英語", "英文歌", "英文音樂"]
jay_keywords = ["周杰倫", "jay", "jay chou"]

# YouTube 爬蟲
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

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.lower()

    keyword = None

    if any(neg in user_msg for neg in negative_keywords):
        if any(kw in user_msg for kw in chinese_keywords):
            keyword = random.choice(["療癒中文歌", "中文抒情歌", "華語放鬆音樂"])
        elif any(kw in user_msg for kw in english_keywords):
            keyword = random.choice(["英文療癒歌", "英文安靜音樂", "英文放鬆歌單"])
        elif any(kw in user_msg for kw in jay_keywords):
            keyword = "周杰倫 療癒歌曲"
        else:
            keyword = random.choice(recommend_keywords)
    else:
        if "中文" in user_msg:
            reply = "你可以說「我心情不好，我想聽中文歌」，我會幫你推薦療癒的中文音樂 🎵"
        elif "英文" in user_msg:
            reply = "你可以說「我心情不好，我想聽英文歌」，我會幫你推薦療癒的英文歌 🎧"
        elif "周杰倫" in user_msg:
            reply = "你可以說「我心情不好，我想聽周杰倫」，我就知道你是老粉啦 😎"
        else:
            reply = "你可以說「我心情不好」，我會幫你推薦療癒的音樂 🎧"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # 執行搜尋
    video_link = search_youtube_link(keyword)
    if video_link:
        reply = f"聽聽這首「{keyword}」，希望能讓你心情好一點 🎵\n{video_link}"
    else:
        reply = "目前找不到合適的音樂連結，稍後再試試看喔～"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# 正確綁定 PORT 給 Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
