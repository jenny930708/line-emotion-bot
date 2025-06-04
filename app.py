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

load_dotenv()

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

last_meme_theme = {}
last_emotion_status = {}
story_topics = ["冒險", "友情", "溫馨", "奇幻", "動物", "勇氣"]

negative_keywords = ["難過", "不開心", "心情不好", "低落", "不爽", "崩潰", "沮喪", "想哭", "壓力", "焦慮"]
recommend_keywords = ["療癒音樂", "放鬆音樂", "抒情歌曲", "希望的音樂", "安靜的音樂"]
chinese_keywords = ["中文", "華語", "中文歌", "聽中文"]
english_keywords = ["英文", "英語", "英文歌", "英文音樂"]

num_word_map = {
    "一": 1, "二": 2, "兩": 2, "三": 3, "四": 4, "五": 5, "六": 6,
    "七": 7, "八": 8, "九": 9, "十": 10
}

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

def extract_meme_count(text):
    match = re.search(r"([一二兩三四五六七八九十0-9]+).*張", text)
    if match:
        val = match.group(1)
        if val.isdigit():
            return int(val)
        elif val in num_word_map:
            return num_word_map[val]
    return 1

# 其他函式維持不變...
# 以下略，假設其餘函式與處理邏輯不變，只在 handle_fun_image 中替換張數判斷邏輯：

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

# 其餘程式碼保持一致，例如 callback、handle_message 等。
# 若你需要我也整合完整最終版（包含這些修改與其餘邏輯），也可以隨時告訴我！
