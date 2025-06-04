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

# 記住每位使用者是否剛說過情緒
last_emotion_status = {}

# 抓取歌手名稱的簡易方法
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

# YouTube 搜尋函式
def search_youtube_link(query):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    
    try:
        html = requests.get(url, headers=headers).text
        # 更廣泛地抓取影片ID（適應更多格式）
        video_ids = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', html)
        video_ids = list(dict.fromkeys(video_ids))  # 去除重複
        
        if video_ids:
            return f"https://www.youtube.com/watch?v={video_ids[0]}"
        else:
            # fallback: 把關鍵字縮短（例如：王力宏 療癒歌曲 → 王力宏）
            fallback_query = query.split()[0]
            fallback_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(fallback_query)}"
            fallback_html = requests.get(fallback_url, headers=headers).text
            fallback_ids = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', fallback_html)
            fallback_ids = list(dict.fromkeys(fallback_ids))
            
            if fallback_ids:
                return f"https://www.youtube.com/watch?v={fallback_ids[0]}"
    except Exception as e:
        print(f"🔴 YouTube search error: {e}")
    
    return None  # 若兩階段都沒結果

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

# 主處理邏輯
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_msg = event.message.text.lower()
    keyword = None

    is_negative = any(word in user_msg for word in negative_keywords)

    # 使用者明確說出情緒
    if is_negative:
        last_emotion_status[user_id] = True

        # 語言偏好處理
        if any(kw in user_msg for kw in chinese_keywords):
            keyword = random.choice(["療癒中文歌", "中文抒情歌", "華語放鬆音樂"])
        elif any(kw in user_msg for kw in english_keywords):
            keyword = random.choice(["英文療癒歌", "英文放鬆音樂", "英文情歌"])
        else:
            # 試著擷取歌手
            singer = extract_singer(user_msg)
            if singer:
                keyword = f"{singer} 療癒歌曲"

        if not keyword:
            keyword = random.choice(recommend_keywords)

    # 使用者沒明說情緒，但前面說過 → 試著延續
    elif last_emotion_status.get(user_id):
        singer = extract_singer(user_msg)
        if singer:
            keyword = f"{singer} 療癒歌曲"

    # 若有推薦關鍵字就送出音樂
    if keyword:
        video_link = search_youtube_link(keyword)
        reply = f"聽聽這首「{keyword}」，希望能讓你心情好一點 🎵\n{video_link}" if video_link else "目前找不到合適的音樂連結，稍後再試試看喔～"
        last_emotion_status[user_id] = False  # 清除情緒記憶
    else:
        # 引導提示
        reply = "你可以說「我心情不好，我想聽〇〇的歌」，我會幫你推薦療癒音樂 🎧"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# Render 運行設定
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
