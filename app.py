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
from openai import OpenAI

# 載入 .env 中的環境變數
load_dotenv()

# 初始化 Flask 與 LINE、OpenAI
app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 使用者狀態記憶
last_meme_theme = {}
last_emotion_status = {}

# 支援的主題與關鍵字
story_topics = ["冒險", "友情", "溫馨", "奇幻", "動物", "勇氣"]
negative_keywords = ["難過", "不開心", "心情不好", "低落", "不爽", "崩潰", "沮喪", "想哭", "壓力", "焦慮"]
recommend_keywords = ["療癒音樂", "放鬆音樂", "抒情歌曲", "希望的音樂", "安靜的音樂"]
chinese_keywords = ["中文", "華語", "中文歌", "聽中文"]
english_keywords = ["英文", "英語", "英文歌", "英文音樂"]

# 中文數字轉換表
num_word_map = {
    "一": 1, "二": 2, "兩": 2, "三": 3, "四": 4, "五": 5, "六": 6,
    "七": 7, "八": 8, "九": 9, "十": 10
}

# 擷取歌手名稱
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

# 擷取張數
def extract_meme_count(text):
    match = re.search(r"([一二兩三四五六七八九十0-9]+).*張", text)
    if match:
        val = match.group(1)
        if val.isdigit():
            return int(val)
        elif val in num_word_map:
            return num_word_map[val]
    return 1

# 搜尋 Yahoo 梗圖圖片
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
        print("Yahoo 梗圖搜尋錯誤：", e)
    return None

# 處理梗圖回應（含張數與主題）
def handle_fun_image(user_message, user_id):
    global last_meme_theme
    theme_keywords = ["動物", "狗", "貓", "熊", "老虎", "貓咪", "狗狗", "鯊魚", "食物", "人類", "日常", "漫畫", "梗"]
    matched_theme = next((word for word in theme_keywords if word in user_message), None)

    if "再來一張" in user_message or "再一張" in user_message:
        theme = last_meme_theme.get(user_id, "梗圖")
    else:
        theme = f"{matched_theme}梗圖" if matched_theme else "梗圖"
        last_meme_theme[user_id] = theme

    meme_count = extract_meme_count(user_message)
    results = []
    for _ in range(meme_count):
        image_url = search_meme_image_by_yahoo(theme)
        if image_url:
            results.append(ImageSendMessage(original_content_url=image_url, preview_image_url=image_url))

    return results if results else [TextSendMessage(text=f"❌ 找不到與「{theme}」相關的梗圖 😢")]

# Webhook 回呼路徑（接收 LINE 訊息）
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
    user_message = event.message.text.strip()
    user_id = event.source.user_id
    print(f"[使用者訊息] {user_message}")

    if "梗圖" in user_message:
        reply = handle_fun_image(user_message, user_id)
        # 如果有多張圖片，逐張推播
        if isinstance(reply, list):
            for r in reply:
                line_bot_api.push_message(user_id, r)
            return
        else:
            line_bot_api.reply_message(event.reply_token, reply)
            return
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入『梗圖』加上數量～例如：來四張梗圖！"))

# 健康檢查
@app.route("/")
def health_check():
    return "OK"

# Flask 啟動（給 Render 用）
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
