# 匯入必要模組
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

# 載入 .env 檔案中的環境變數（API 金鑰等）
load_dotenv()

# 初始化 Flask App
app = Flask(__name__)

# 初始化 LINE Bot 與 OpenAI 物件
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 記錄使用者最近查詢的梗圖主題、情緒狀態
last_meme_theme = {}
last_emotion_status = {}

# 支援的故事主題
story_topics = ["冒險", "友情", "溫馨", "奇幻", "動物", "勇氣"]

# 情緒與音樂相關關鍵字定義
negative_keywords = ["難過", "不開心", "心情不好", "低落", "不爽", "崩潰", "沮喪", "想哭", "壓力", "焦慮"]
recommend_keywords = ["療癒音樂", "放鬆音樂", "抒情歌曲", "希望的音樂", "安靜的音樂"]
chinese_keywords = ["中文", "華語", "中文歌", "聽中文"]
english_keywords = ["英文", "英語", "英文歌", "英文音樂"]

# 中文數字對應數值（用於張數判斷）
num_word_map = {
    "一": 1, "二": 2, "兩": 2, "三": 3, "四": 4, "五": 5, "六": 6,
    "七": 7, "八": 8, "九": 9, "十": 10
}

# 從句子中擷取使用者想聽的歌手名稱
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

# 從句子中提取使用者要求的梗圖數量（支援中文與數字）
def extract_meme_count(text):
    match = re.search(r"([一二兩三四五六七八九十0-9]+).*張", text)
    if match:
        val = match.group(1)
        if val.isdigit():
            return int(val)
        elif val in num_word_map:
            return num_word_map[val]
    return 1  # 預設為 1 張

# 使用 Yahoo 圖片搜尋擷取梗圖網址
def search_meme_image_by_yahoo(query="梗圖"):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://tw.images.search.yahoo.com/search/images?p={query}"
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        img_tags = soup.select("img")
        img_urls = [img["src"] for img in img_tags if img.get("src") and img["src"].startswith("http")]
        if img_urls:
            return random.choice(img_urls)  # 隨機挑一張
    except Exception as e:
        print("Yahoo 梗圖搜尋錯誤：", e)
    return None

# 處理使用者的梗圖請求（根據主題與張數）
def handle_fun_image(user_message, user_id):
    global last_meme_theme

    # 預設支援的主題關鍵字
    theme_keywords = ["動物", "狗", "貓", "熊", "老虎", "貓咪", "狗狗", "鯊魚", "食物", "人類", "日常", "漫畫", "梗"]
    matched_theme = next((word for word in theme_keywords if word in user_message), None)

    # 如果是「再來一張」，延用上一個主題
    if "再來一張" in user_message or "再一張" in user_message:
        theme = last_meme_theme.get(user_id, "梗圖")
    else:
        theme = f"{matched_theme}梗圖" if matched_theme else "梗圖"
        last_meme_theme[user_id] = theme

    # 判斷使用者想要幾張梗圖
    meme_count = extract_meme_count(user_message)

    # 產生圖片回應
    results = []
    for _ in range(meme_count):
