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
story_topics = ["冒險", "友情", "溫馨", "奇幻", "動物", "勇氣"]


# 🎵 搜尋 YouTube 音樂連結
def search_youtube_link(query):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        html = requests.get(url, headers=headers).text
        video_ids = re.findall(r"watch\?v=(.{11})", html)
        seen = set()
        for vid in video_ids:
            if vid not in seen:
                seen.add(vid)
                return f"https://www.youtube.com/watch?v={vid}"
    except Exception as e:
        print("YouTube 查詢失敗：", e)
    return "⚠️ 找不到音樂連結，請換個關鍵字再試一次。"

# 🎧 音樂推薦邏輯
def handle_music_request(user_message):
    stop_words = ["我想聽", "播放", "想聽", "來點", "給我", "聽一下", "音樂", "歌曲", "首歌", "聽聽", "歌"]
    cleaned = user_message
    for word in stop_words:
        cleaned = cleaned.replace(word, "")
    keywords = cleaned.strip()

    mood_map = {
        "放鬆": "輕音樂 放鬆 身心靈",
        "運動": "動感 音樂 運動 撥放清單",
        "悲傷": "療癒 情歌 抒情",
        "開心": "快樂 音樂 熱門",
        "焦慮": "自然 音樂 放鬆",
        "睡不著": "助眠 音樂 白噪音"
    }

    for mood, query in mood_map.items():
        if mood in user_message:
            link = search_youtube_link(query)
            return TextSendMessage(text=f"🎵 給你推薦的 {mood} 音樂：{link}")

    if re.match(r".+的$", keywords):
        return TextSendMessage(text="請告訴我完整歌名，例如：周杰倫的青花瓷")

    if "中文" in user_message:
        search_query = "中文 熱門 歌曲 site:youtube.com"
    elif "英文" in user_message:
        search_query = "英文 熱門 歌曲 site:youtube.com"
    elif keywords:
        search_query = f"{keywords} 官方 MV site:youtube.com"
    else:
        search_query = "熱門 歌曲 site:youtube.com"

    link = search_youtube_link(search_query)
    return TextSendMessage(text=f"🎵 推薦音樂：{link}")


# 🧚‍♀️ 故事生成
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


# 🤖 GPT 聊天
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


# 😂 Yahoo 梗圖搜尋
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


# 🐶 梗圖處理
def handle_fun_image(user_message, user_id):
    global last_meme_theme
    theme_keywords = ["動物", "狗", "貓", "熊", "老虎", "貓咪", "狗狗", "鯊魚", "食物", "人類", "日常", "漫畫", "梗"]
    matched_theme = next((word for word in theme_keywords if word in user_message), None)

    if "再來一張" in user_message or "再一張" in user_message:
        theme = last_meme_theme.get(user_id, "梗圖")
    else:
        theme = f"{matched_theme}梗圖" if matched_theme else "梗圖"
        last_meme_theme[user_id] = theme

    if re.search(r"(三|3|幾|多).*張", user_message):
        results = []
        for _ in range(3):
            image_url = search_meme_image_by_yahoo(theme)
            if image_url:
                results.append(ImageSendMessage(original_content_url=image_url, preview_image_url=image_url))
        return results if results else [TextSendMessage(text=f"❌ 找不到與「{theme}」相關的梗圖 😢")]

    image_url = search_meme_image_by_yahoo(theme)
    if image_url:
        return ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
    else:
        return TextSendMessage(text=f"❌ 找不到與「{theme}」相關的梗圖 😢")


# 🔍 健康檢查
@app.route("/")
def health_check():
    return "OK"


# 📩 LINE Webhook
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


# 📥 主訊息邏輯處理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    user_id = event.source.user_id
    print(f"[使用者訊息] {user_message}")

    if user_message in story_topics:
        reply = TextSendMessage(text=generate_story_by_topic(user_message))
    elif "說故事" in user_message or "講故事" in user_message or "故事" in user_message:
        reply = TextSendMessage(text="你想聽什麼主題的故事呢？請輸入主題，例如：冒險、友情、溫馨、奇幻")
    elif "梗圖" in user_message or "再來一張" in user_message or "三張" in user_message or "3張" in user_message:
        reply = handle_fun_image(user_message, user_id)
        if isinstance(reply, list):
            for r in reply:
                line_bot_api.push_message(user_id, r)
            return
    elif "聽" in user_message or "播放" in user_message or "歌曲" in user_message or "音樂" in user_message:
        reply = handle_music_request(user_message)
    else:
        reply = TextSendMessage(text=chat_with_gpt(user_message))

    line_bot_api.reply_message(event.reply_token, reply)


# 🚀 啟動伺服器
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
