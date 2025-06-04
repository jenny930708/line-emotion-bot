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

# 環境設定
load_dotenv()
app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# 使用者狀態
user_states = {}

# 心情關鍵字與推薦詞對照
MOOD_KEYWORDS = {
    "negative": ["心情不好", "難過", "不開心", "想哭", "崩潰", "低落", "焦慮", "沮喪", "憂鬱", "失落"],
    "positive": ["開心", "快樂", "興奮", "愉快"],
    "relaxed": ["放鬆", "輕鬆", "平靜", "舒服"],
    "energetic": ["運動", "健身", "跑步", "活力"]
}

MOOD_MUSIC_SUGGESTIONS = {
    "negative": ["療癒音樂", "抒情歌曲", "輕音樂"],
    "positive": ["快樂音樂", "熱門歌曲"],
    "relaxed": ["放鬆音樂", "自然音樂", "冥想音樂"],
    "energetic": ["運動音樂", "動感音樂", "電音"]
}

# 偵測心情
def detect_mood(text):
    for mood, keywords in MOOD_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return mood
    return None

# 擷取歌手或歌曲關鍵字
def extract_keywords(text):
    patterns = [
        r"我想聽(.+?)的(歌|音樂)?",
        r"可以聽(.+?)的(歌|音樂)?",
        r"聽(.+?)的(歌|音樂)?",
        r"我想聽(.+)",
        r"可以聽(.+)",
        r"聽(.+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            keyword = match.group(1).strip()
            keyword = re.sub(r"[的歌音樂\s]+$", "", keyword)
            if keyword:
                return keyword
    return None

# YouTube 搜尋
def search_youtube_link(query):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8"
        }
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        for a_tag in soup.find_all("a"):
            title = a_tag.get("title")
            href = a_tag.get("href")
            if title and href and "/watch?v=" in href:
                if any(word in title for word in query.split()):
                    video_id = href.split("v=")[-1].split("&")[0]
                    return f"https://www.youtube.com/watch?v={video_id}"

        # fallback：第一個影片
        video_ids = re.findall(r'href="/watch\?v=([a-zA-Z0-9_-]{11})"', response.text)
        if video_ids:
            return f"https://www.youtube.com/watch?v={video_ids[0]}"
    except Exception as e:
        print("YouTube 查詢失敗：", e)

    return None

# LINE Webhook 接收
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# 主邏輯
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_msg = event.message.text.strip()

    if user_id not in user_states:
        user_states[user_id] = {"mood": None, "waiting": False}

    mood = detect_mood(user_msg)
    if mood:
        user_states[user_id]["mood"] = mood
        user_states[user_id]["waiting"] = True

    keywords = extract_keywords(user_msg)

    if keywords:
        if user_states[user_id]["mood"] in MOOD_MUSIC_SUGGESTIONS:
            mood_query = MOOD_MUSIC_SUGGESTIONS[user_states[user_id]["mood"]][0]
            search_query = f"{keywords} {mood_query}"
        else:
            search_query = keywords

        video_url = search_youtube_link(search_query)
        if video_url:
            reply = f"🎵 推薦音樂：{keywords} - {video_url}"
        else:
            reply = "⚠️ 找不到相關音樂，試試其他關鍵字看看～"
        user_states[user_id]["waiting"] = False
    elif user_states[user_id]["waiting"]:
        reply = "你想聽誰的歌呢？例如：我想聽周杰倫的歌。"
    elif mood:
        reply = "你心情不錯～要我推薦一首音樂嗎？🎶"
    else:
        reply = "想聽音樂嗎？可以說：「我心情不好，我想聽周杰倫的歌」🎧"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# 健康檢查頁面
@app.route("/")
def health_check():
    return "LINE Bot is running!"

# 啟動伺服器（適用 Render）
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
