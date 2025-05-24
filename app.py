
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

load_dotenv()

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

def search_youtube_link(query):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        html = requests.get(url, headers=headers).text
        match = re.search(r'"url":"/watch\?v=(.{11})"', html)
        if match:
            return f"https://www.youtube.com/watch?v={match.group(1)}"
    except Exception as e:
        print("YouTube 查詢失敗：", e)
    return "（找不到連結）"

def handle_music_request(user_message):
    keywords = user_message
    for word in ["我想聽", "播放", "想聽", "來點", "給我", "音樂", "歌曲", "歌"]:
        keywords = keywords.replace(word, "")
    keywords = keywords.strip()
    if not keywords:
        keywords = "熱門音樂"
    link = search_youtube_link(keywords)
    return TextSendMessage(text=f"🎵 這是你可能會喜歡的音樂：\n{link}")

def auto_recommend_artist(user_message):
    artist_match = re.search(r"(推薦.*?)([\u4e00-\u9fa5A-Za-z0-9]+)(的歌|的歌曲)", user_message)
    if artist_match:
        artist = artist_match.group(2)
        common_titles = ["代表作", "經典歌曲", "熱門歌曲", "必聽歌曲", "傳唱歌曲"]
        msg = f"這裡是為你推薦的「{artist}」熱門歌曲：\n\n"
        for idx in range(1, 6):
            fake_title = f"{artist} {random.choice(common_titles)} {idx}"
            link = search_youtube_link(fake_title)
            msg += f"{idx}. {fake_title} 👉 {link}\n"
        msg += "\n以上推薦為自動搜尋結果，如想指定歌曲可直接輸入『我想聽 + 歌名』"
        return TextSendMessage(text=msg)
    return TextSendMessage(text="請告訴我你想聽哪位歌手的歌，例如：推薦幾首周杰倫的歌")

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

def handle_story(user_message):
    story = (
        "從前從前，有一隻小狐狸住在山林裡，他每天都會幫森林裡的動物送信。\n"
        "有一天，他收到了一封奇怪的信，上面什麼都沒寫，只畫了一顆星星...\n"
        "你想知道接下來發生了什麼嗎？"
    )
    return story

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
    user_message = event.message.text
    print(f"[使用者訊息] {user_message}")

    if "推薦" in user_message and "歌" in user_message:
    reply = auto_recommend_artist(user_message)
elif "說故事" in user_message or "講故事" in user_message or "故事" in user_message:
    reply = TextSendMessage(text=handle_story(user_message))
        reply = auto_recommend_artist(user_message)
    elif "聽" in user_message or "播放" in user_message:
        reply = handle_music_request(user_message)
    elif "梗圖" in user_message or "再來一張" in user_message or "換一張" in user_message or "再給我一張" in user_message:
        image_url = search_meme_image_by_yahoo()
        if image_url:
            reply = ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
        else:
            reply = TextSendMessage(text="❌ 找不到梗圖 😢")
        else:
        reply = TextSendMessage(text="你可以說：『我想聽 xxx』、『推薦某某歌手的歌』或『來張梗圖』、『說個故事』來試試看 🎵🦊")

    line_bot_api.reply_message(event.reply_token, reply)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
