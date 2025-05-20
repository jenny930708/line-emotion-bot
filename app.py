from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, AudioMessage, StickerMessage
from transformers import pipeline
from langdetect import detect
import openai
import os
import tempfile
import datetime

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])
openai.api_key = os.environ['OPENAI_API_KEY']

classifier = pipeline("text-classification", model="bhadresh-savani/bert-base-uncased-emotion")

user_context = {}  # 使用者偏好與對話上下文記憶

emotion_response = {
    'joy': "你看起來心情很好！可以試著挑戰新任務哦！✨",
    'anger': "你似乎有點生氣，試著做深呼吸，或出去走走吧 🌳",
    'sadness': "我在這陪你～建議聽聽輕音樂放鬆一下 🎧",
    'fear': "感到害怕時可以找人聊聊，也可以聽冥想音樂 🧘",
    'love': "喜歡的感覺真好！可以把喜歡的事記錄下來喔 📝",
    'surprise': "驚訝嗎？今天有什麼新鮮事？可以分享給我聽 😯",
    'neutral': "平穩的一天也很棒，別忘了喝水與休息 💧"
}

def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

def get_music_suggestion(emotion, language="zh", preference=""):
    base = "https://www.youtube.com/results?search_query="
    if language == "zh":
        query = f"{preference} 情緒 {emotion} 音樂"
    elif language == "en":
        query = f"{emotion} music {preference}"
    else:
        query = f"{emotion} music"
    return base + query.replace(" ", "+")

def chat_response(user_id, user_text):
    messages = user_context.get(user_id, [])
    messages.append({"role": "user", "content": user_text})
    messages = messages[-10:]  # 限制記憶長度

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一位貼心的 AI 室友，會根據使用者的訊息做自然、溫暖、個性化的回應。"},
            *messages
        ]
    )
    reply = response.choices[0].message.content.strip()
    messages.append({"role": "assistant", "content": reply})
    user_context[user_id] = messages
    return reply

def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    return transcript["text"]

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_input = event.message.text
    user_id = event.source.user_id
    lang = detect_language(user_input)

    result = classifier(user_input)[0]
    emotion = result['label'].lower()
    music_link = get_music_suggestion(emotion, lang, user_input)

    suggestion = emotion_response.get(emotion, "我還不太確定你的情緒，但我會一直陪著你喔 💡")
    ai_reply = chat_response(user_id, user_input)

    reply = f"你的情緒是：{emotion}\n👉 {suggestion}\n🎵 推薦音樂：{music_link}\n🧠 {ai_reply}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@handler.add(MessageEvent, message=AudioMessage)
def handle_audio(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as tf:
        for chunk in message_content.iter_content(chunk_size=1024):
            tf.write(chunk)
        tf_path = tf.name

    try:
        text = transcribe_audio(tf_path)
        user_id = event.source.user_id
        lang = detect_language(text)

        result = classifier(text)[0]
        emotion = result['label'].lower()
        suggestion = emotion_response.get(emotion, "我還不太確定你的情緒，但我會一直陪著你喔 💡")
        music_link = get_music_suggestion(emotion, lang, text)
        ai_reply = chat_response(user_id, text)

        reply = f"🎧 語音內容為：{text}\n你的情緒是：{emotion}\n👉 {suggestion}\n🎵 推薦音樂：{music_link}\n🧠 {ai_reply}"
    except Exception as e:
        reply = f"語音處理失敗：{str(e)}"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker(event):
    sticker_id = event.message.sticker_id
    reply = f"😄 你傳了一個貼圖（ID：{sticker_id}），好可愛！"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
