import os
import random
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from dotenv import load_dotenv
from openai import OpenAI
from agents.meditation_agent import handle_meditation
from agents.story_agent import handle_story
from bs4 import BeautifulSoup

# 載入環境變數
load_dotenv()
app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chat_with_gpt(user_message):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一位溫柔的 AI 好朋友，擅長安撫使用者情緒、傾聽與聊天。"},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ OpenAI 發生錯誤：{str(e)}"

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
        print(f"[Yahoo 搜圖錯誤] {e}")
    return None

def handle_music_request(user_message):
    search_terms = {
        "周杰倫": "周杰倫 音樂",
        "林俊傑": "林俊傑 歌曲",
        "白噪音": "white noise music",
        "輕音樂": "relaxing instrumental music",
        "水晶音樂": "crystal healing music"
    }

    for keyword, query in search_terms.items():
        if keyword in user_message:
            return TextSendMessage(text=search_youtube_music(query))

    default_choices = [
        "chill music playlist",
        "happy music",
        "focus study music",
        "lofi chillhop",
        "ambient relaxing music"
    ]
    return TextSendMessage(text=search_youtube_music(random.choice(default_choices)))

def search_youtube_music(query):
    try:
        search_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        html = requests.get(search_url, headers=headers).text
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.select("a"):
            href = a.get("href")
            if href and href.startswith("/watch?v="):
                return f"🎵 這是我為你挑選的音樂： https://www.youtube.com{href}"
    except Exception as e:
        print("搜尋 YouTube 音樂時出錯：", e)
    return "抱歉，目前找不到合適的音樂影片 😢"

@app.route("/")
def health_check():
    return "OK"

@app.route("/test-image")
def test_image():
    keyword = request.args.get("q", "梗圖")
    image_url = search_meme_image_by_yahoo(keyword)
    if image_url:
        return f"<img src='{image_url}' style='max-width: 400px;'><br><code>{image_url}</code>"
    else:
        return "❌ 找不到梗圖"

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
    user_message = event.message.text
    user_id = event.source.user_id

    if "心情不好" in user_message or "不開心" in user_message or "難過" in user_message:
        reply = TextSendMessage(text="聽起來你今天過得不太好，我在這裡陪你。這首音樂也許能陪伴你：https://www.youtube.com/watch?v=inpok4MKVLM")
    elif "我想聽" in user_message and "歌" in user_message:
        reply = handle_music_request(user_message)  # ✅ 修正這行
    elif "冥想" in user_message or "靜心" in user_message:
        reply = TextSendMessage(text=handle_meditation(user_message))
    elif "故事" in user_message:
        reply = TextSendMessage(text=handle_story(user_message, user_id))
    elif "梗圖" in user_message:
        image_url = search_meme_image_by_yahoo()
        if image_url:
            reply = ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
        else:
            reply = TextSendMessage(text="❌ 找不到梗圖 😥")
    elif "音樂" in user_message or "影片" in user_message:
        reply = handle_music_request(user_message)  # ✅ 修正這行
    else:
        reply = TextSendMessage(text=chat_with_gpt(user_message))

    line_bot_api.reply_message(event.reply_token, reply)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
