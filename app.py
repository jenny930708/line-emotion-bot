你說：
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

# ✅ 用來記住每位使用者最近看的梗圖主題
last_meme_theme = {}


def search_youtube_link(query):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        html = requests.get(url, headers=headers).text
        video_ids = re.findall(r'"url":"/watch\?v=(.{11})"', html)
        seen = set()
        for vid in video_ids:
            if vid not in seen:
                seen.add(vid)
                return f"https://www.youtube.com/watch?v={vid}"
    except Exception as e:
        print("YouTube 查詢失敗：", e)
    return "（找不到連結）"

def handle_music_request(user_message):
    cleaned = user_message
    for word in ["我想聽", "播放", "想聽", "來點", "給我", "音樂", "歌曲", "歌"]:
        cleaned = cleaned.replace(word, "")
    keywords = cleaned.strip()

    if re.match(r".+的$", keywords):
        return TextSendMessage(text="請告訴我想聽哪一首歌，例如：周杰倫的青花瓷")

    # 如果沒有明確歌手名稱，預設補強周杰倫匹配
    if "周杰倫" not in keywords and "Jay" not in keywords:
        search_query = f'"{keywords}" 周杰倫 官方 MV site:youtube.com'
    else:
        search_query = f'"{keywords}" 官方 MV site:youtube.com'

    link = search_youtube_link(search_query)
    return TextSendMessage(text=f"🎵 這是你可能會喜歡的音樂：{link}")

def auto_recommend_artist(user_message):
    artist_match = re.search(r"(推薦.*?)([\u4e00-\u9fa5A-Za-z0-9]+)(的歌|的歌曲)", user_message)
    if not artist_match:
        return TextSendMessage(text="請告訴我你想聽哪位歌手的歌，例如：推薦幾首周杰倫的歌")

    artist = artist_match.group(2)
    search_query = f"{artist} 熱門歌曲 官方 MV"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_query)}"
        res = requests.get(url, headers=headers)
        video_ids = re.findall(r'"url":"/watch\?v=(.{11})"', res.text)
        seen = set()
        links = []
        for vid in video_ids:
            if vid not in seen:
                seen.add(vid)
                links.append(f"https://www.youtube.com/watch?v={vid}")
            if len(links) >= 5:
                break

        if not links:
            return TextSendMessage(text="找不到熱門歌曲影片 😢")

        msg = f"這裡是為你推薦的「{artist}」熱門歌曲：\n\n"
        for idx, link in enumerate(links, 1):
            msg += f"{idx}. 👉 {link}\n"

        return TextSendMessage(text=msg)

    except Exception as e:
        return TextSendMessage(text=f"⚠️ 無法推薦歌曲：{str(e)}")

def generate_story_by_topic(topic):
    try:
        variation = random.choice(["小狐狸", "獨角獸", "小女孩", "探險隊", "魔法師", "未來世界"])
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

@app.route("/")
def health_check():
    return "OK"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    theme_reply = handle_theme_recommendation(event.message.text.strip())
    if theme_reply:
        line_bot_api.reply_message(event.reply_token, theme_reply)
        return
    else:
        if "推薦" in user_message and "歌" in user_message:
            reply = auto_recommend_artist(user_message)
        elif user_message in story_topics:
            reply = TextSendMessage(text=generate_story_by_topic(user_message))
        elif "說故事" in user_message or "講故事" in user_message or "故事" in user_message:
            reply = TextSendMessage(text="你想聽什麼主題的故事呢？請輸入主題，例如：冒險、友情、溫馨、奇幻")
        elif "聽" in user_message or "播放" in user_message:
            reply = handle_music_request(user_message)
        elif "梗圖" in user_message or "再來一張" in user_message or "三張" in user_message or "3張" in user_message:
            reply = handle_fun_image(user_message, user_id)
            if isinstance(reply, list):
                for r in reply:
                    line_bot_api.push_message(user_id, r)
                return
        else:
            reply = TextSendMessage(text=chat_with_gpt(user_message))
        line_bot_api.reply_message(event.reply_token, reply)

    user_message = event.message.text.strip()
    user_id = event.source.user_id
    print(f"[使用者訊息] {user_message}")

    story_topics = ["冒險", "友情", "溫馨", "奇幻", "動物", "勇氣"]

    if "推薦" in user_message and "歌" in user_message:
        reply = auto_recommend_artist(user_message)
    elif user_message in story_topics:
        reply = TextSendMessage(text=generate_story_by_topic(user_message))
    elif "說故事" in user_message or "講故事" in user_message or "故事" in user_message:
        reply = TextSendMessage(text="你想聽什麼主題的故事呢？請輸入主題，例如：冒險、友情、溫馨、奇幻")
    elif "聽" in user_message or "播放" in user_message:
        reply = handle_music_request(user_message)
    elif "梗圖" in user_message or "再來一張" in user_message or "三張" in user_message or "3張" in user_message:
        reply = handle_fun_image(user_message, user_id)
        if isinstance(reply, list):
            for r in reply:
                line_bot_api.push_message(user_id, r)
            return
    else:
        reply = TextSendMessage(text=chat_with_gpt(user_message))

    line_bot_api.reply_message(event.reply_token, reply)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
