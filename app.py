import os
import re
import random
import urllib.parse
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, abort
from dotenv import load_dotenv
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

# 記憶每位使用者最近是否處於情緒狀態
last_emotion_status = {}

# 從訊息中擷取歌手名稱
def extract_singer(text):
    patterns = [
        r"想聽(.*?)(的)?(歌|音樂)?",
        r"可以聽(.*?)(的)?(歌|音樂)?",
        r"聽(.*?)(的)?(歌|音樂)?"
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None

# 更聰明的 YouTube 搜尋：抓標題+ID，篩選符合的
def search_youtube_link(query):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # 找出所有包含影片連結的 <a> 標籤
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            title = a_tag.get("title", "")
            if "/watch?v=" in href and len(href) >= 20:
                video_id = href.split("v=")[-1][:11]
                if query.split()[0] in title:  # 篩選標題包含歌手名的
                    return f"https://www.youtube.com/watch?v={video_id}"

        # fallback：只抓 video ID（防萬一）
        html = response.text
        video_ids = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', html)
        video_ids = list(dict.fromkeys(video_ids))
        if video_ids:
            return f"https://www.youtube.com/watch?v={video_ids[0]}"
    except Exception as e:
        print(f"❌ YouTube search error: {e}")

    return None

# webhook 路由
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# 處理訊息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_msg = event.message.text.lower()
    keyword = None

    is_negative = any(word in user_msg for word in negative_keywords)

    # 使用者表達情緒
    if is_negative:
        last_emotion_status[user_id] = True
        if any(kw in user_msg for kw in chinese_keywords):
            keyword = random.choice(["療癒中文歌", "中文抒情歌", "華語放鬆音樂"])
        elif any(kw in user_msg for kw in english_keywords):
            keyword = random.choice(["英文療癒歌", "英文放鬆音樂", "英文情歌"])
        else:
            singer = extract_singer(user_msg)
            if singer:
                keyword = f"{singer} 療癒歌曲"
        if not keyword:
            keyword = random.choice(recommend_keywords)

    # 沒有情緒詞，但使用者之前表達過情緒（延續）
    elif last_emotion_status.get(user_id):
        singer = extract_singer(user_msg)
        if singer:
            keyword = f"{singer} 療癒歌曲"

    # 執行推薦
    if keyword:
        video_link = search_youtube_link(keyword)
        reply = f"聽聽這首「{keyword}」，希望能讓你心情好一點 🎵\n{video_link}" if video_link else "目前找不到合適的音樂連結，稍後再試試看喔～"
        last_emotion_status[user_id] = False
    else:
        reply = "你可以說「我心情不好，我想聽〇〇的歌」，我會幫你推薦療癒音樂 🎧"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# 部署設定（Render 用）
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
