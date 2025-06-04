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

# 載入環境變數
load_dotenv()

# 初始化 Flask 與外部服務
app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 使用者狀態記憶
last_meme_theme = {}
last_emotion_status = {}

# 支援主題與關鍵字
story_topics = ["冒險", "友情", "溫馨", "奇幻", "動物", "勇氣"]
negative_keywords = ["難過", "不開心", "心情不好", "低落", "不爽", "崩潰", "沮喪", "想哭", "壓力", "焦慮"]
recommend_keywords = ["療癒音樂", "放鬆音樂", "抒情歌曲", "希望的音樂", "安靜的音樂"]
chinese_keywords = ["中文", "華語", "中文歌", "聽中文"]
english_keywords = ["英文", "英語", "英文歌", "英文音樂"]

# 中文數字轉換
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

# Yahoo 圖片搜尋

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

# YouTube 音樂搜尋

def search_youtube_link(query):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            title = a_tag.get("title", "")
            if "/watch?v=" in href and len(href) >= 20:
                video_id = href.split("v=")[-1][:11]
                if query.split()[0] in title:
                    return f"https://www.youtube.com/watch?v={video_id}"
        html = response.text
        video_ids = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', html)
        video_ids = list(dict.fromkeys(video_ids))
        if video_ids:
            return f"https://www.youtube.com/watch?v={video_ids[0]}"
    except Exception as e:
        print(f"YouTube search error: {e}")
    return None

# GPT 說故事

def generate_story_by_topic(topic):
    try:
        variation = random.choice(["小狐狸", "獨角獸", "小女孩", "探險隊", "魔法師"])
        prompt = f"請說一個以「{variation}」為主角，主題為「{topic}」的童話故事，長度約100~150字，不要標題。"
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一位會說故事的 AI，請用溫柔口吻講故事。"},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ 故事生成失敗：{str(e)}"

# GPT 聊天

def chat_with_gpt(user_message):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一位溫柔的 AI 好朋友，擅長安慰、傾聽、陪伴與聊天。"},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ 聊天出錯：{str(e)}"

# 梗圖處理器

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

# Webhook 路由

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# 訊息事件處理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    user_id = event.source.user_id
    print(f"[使用者訊息] {user_message}")

    # 梗圖回應
    if "梗圖" in user_message:
        reply = handle_fun_image(user_message, user_id)
        if isinstance(reply, list):
            for r in reply:
                line_bot_api.push_message(user_id, r)
            return
        else:
            line_bot_api.reply_message(event.reply_token, reply)
            return

    # 故事主題
    if user_message in story_topics:
        story = generate_story_by_topic(user_message)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=story))
        return

    if "故事" in user_message:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="你想聽什麼主題的故事呢？例如：冒險、友情、溫馨、奇幻"))
        return

    # 音樂推薦：情緒關鍵字
    if any(word in user_message for word in negative_keywords):
        last_emotion_status[user_id] = True
        if any(kw in user_message for kw in chinese_keywords):
            keyword = random.choice(["療癒中文歌", "中文抒情歌", "華語放鬆音樂"])
        elif any(kw in user_message for kw in english_keywords):
            keyword = random.choice(["英文療癒歌", "英文放鬆音樂", "英文情歌"])
        else:
            singer = extract_singer(user_message)
            keyword = f"{singer} 療癒歌曲" if singer else random.choice(recommend_keywords)

        video_link = search_youtube_link(keyword)
        reply = TextSendMessage(text=f"聽聽這首「{keyword}」，希望能讓你心情好一點 🎵\n{video_link}" if video_link else "目前找不到合適的音樂連結，稍後再試試看喔～")
        line_bot_api.reply_message(event.reply_token, reply)
        return

    # 使用者接續指定歌手
    if last_emotion_status.get(user_id):
        singer = extract_singer(user_message)
        if singer:
            keyword = f"{singer} 療癒歌曲"
            video_link = search_youtube_link(keyword)
            reply = TextSendMessage(text=f"這首「{keyword}」送給你 🎶\n{video_link}" if video_link else "目前找不到歌曲，稍後再試試看喔～")
            last_emotion_status[user_id] = False
            line_bot_api.reply_message(event.reply_token, reply)
            return

    # 預設 GPT 回應
    reply = chat_with_gpt(user_message)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# 健康檢查頁
@app.route("/")
def health_check():
    return "OK"

# 啟動 Flask（Render 專用）
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
