from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, AudioMessage, StickerMessage
from transformers import pipeline
from langdetect import detect
from youtube_search import YoutubeSearch
import openai
import os
import tempfile

app = Flask(__name__)

# 環境變數初始化
line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])
openai.api_key = os.environ['OPENAI_API_KEY']

# 記憶儲存（記錄使用者聊天歷史）
user_memory = {}

# 情緒分類器
classifier = pipeline("text-classification", model="bhadresh-savani/bert-base-uncased-emotion")

# 情緒對應建議
emotion_response = {
    'joy': "你看起來心情很好！可以試著挑戰新任務哦！✨",
    'anger': "你似乎有點生氣，試試深呼吸或聽音樂放鬆一下 🎧",
    'sadness': "我在這陪你～建議聽聽輕音樂放鬆一下 🎵",
    'fear': "感到害怕時可以找人聊聊，也可以聽冥想音樂 🧘",
    'love': "喜歡的感覺真好！可以把喜歡的事記錄下來喔 📝",
    'surprise': "驚訝嗎？今天有什麼新鮮事？可以分享給我聽 😯",
    'neutral': "平穩的一天也很棒，別忘了喝水與休息 💧"
}

# GPT 對話函數
def chat_response(history):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=history
    )
    return response.choices[0].message.content.strip()

# YouTube 搜尋推薦音樂連結
def search_youtube_link(query):
    results = YoutubeSearch(query, max_results=1).to_dict()
    if results:
        return f"https://www.youtube.com{results[0]['url_suffix']}"
    return "https://www.youtube.com"

# Whisper 語音轉文字
def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    return transcript["text"]

# 處理 LINE Webhook
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理文字訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_id = event.source.user_id
    user_input = event.message.text.strip()

    # 初始化對話記憶
    if user_id not in user_memory:
        user_memory[user_id] = [
            {"role": "system", "content": "你是一位貼心的 AI 室友，會根據使用者的情緒與需求自然聊天，提供安慰、音樂建議與互動。"}
        ]

    # 儲存用戶輸入
    user_memory[user_id].append({"role": "user", "content": user_input})

    # 判斷是否是詢問或 AI 模式
    keywords = ["怎麼辦", "可以和我聊", "為什麼", "我最近", "你是誰", "我該", "聊聊", "你覺得", "我很"]
    if any(k in user_input for k in keywords):
        reply = chat_response(user_memory[user_id])
        user_memory[user_id].append({"role": "assistant", "content": reply})
        return line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

    # 情緒分析模式
    result = classifier(user_input)[0]
    emotion = result['label'].lower()
    suggestion = emotion_response.get(emotion, "我還不太確定你的情緒，但我會一直陪著你喔 💡")

    # 語言偵測
    lang = detect(user_input)
    pref = "中文" if "zh" in lang else "英文"
    yt_query = f"{pref} {emotion} 音樂"
    youtube_link = search_youtube_link(yt_query)

    reply_text = f"你的情緒是：{emotion}\n👉 {suggestion}\n🎵 推薦音樂：{youtube_link}"
    user_memory[user_id].append({"role": "assistant", "content": reply_text})
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

# 處理語音訊息
@handler.add(MessageEvent, message=AudioMessage)
def handle_audio(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as tf:
        for chunk in message_content.iter_content(chunk_size=1024):
            tf.write(chunk)
        tf_path = tf.name

    try:
        text = transcribe_audio(tf_path)
        result = classifier(text)[0]
        emotion = result['label'].lower()
        suggestion = emotion_response.get(emotion, "我還不太確定你的情緒，但我會一直陪著你喔 💡")
        lang = detect(text)
        pref = "中文" if "zh" in lang else "英文"
        yt_query = f"{pref} {emotion} 音樂"
        youtube_link = search_youtube_link(yt_query)

        reply = f"🎧 語音內容為：{text}\n你的情緒是：{emotion}\n👉 {suggestion}\n🎵 推薦音樂：{youtube_link}"
    except Exception as e:
        reply = f"語音處理失敗：{str(e)}"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# 處理貼圖訊息
@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker(event):
    sticker_id = event.message.sticker_id
    reply = f"😄 你傳了一個貼圖（ID：{sticker_id}），好可愛！"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
