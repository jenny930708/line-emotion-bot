from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, AudioMessage, StickerMessage, FlexSendMessage
from transformers import pipeline
from openai import OpenAI
import os
import tempfile
import datetime
import json

app = Flask(__name__)

# 初始化 API
line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# 情緒分類器
classifier = pipeline("text-classification", model="bhadresh-savani/bert-base-uncased-emotion")

# 簡單的記憶儲存（可改為資料庫）
user_memory = {}

# 情緒對應建議與音樂
emotion_response = {
    'joy': "你看起來心情很好！可以試著挑戰新任務哦！✨\n🎵 推薦音樂：https://www.youtube.com/watch?v=ZbZSe6N_BXs",
    'anger': "你似乎有點生氣，試著做深呼吸，或出去走走吧 🌳\n🎵 推薦音樂：https://www.youtube.com/watch?v=IYzlVDlE72w",
    'sadness': "我在這陪你～建議聽聽輕音樂放鬆一下 🎧\n🎵 推薦音樂：https://www.youtube.com/watch?v=2OEL4P1Rz04",
    'fear': "感到害怕時可以找人聊聊，也可以聽冥想音樂 🧘\n🎵 推薦音樂：https://www.youtube.com/watch?v=Mk7-GRWq7wA",
    'love': "喜歡的感覺真好！可以把喜歡的事記錄下來喔 📝\n🎵 推薦音樂：https://www.youtube.com/watch?v=450p7goxZqg",
    'surprise': "驚訝嗎？今天有什麼新鮮事？可以分享給我聽 😯\n🎵 推薦音樂：https://www.youtube.com/watch?v=euCqAq6BRa4",
    'neutral': "平穩的一天也很棒，別忘了喝水與休息 💧\n🎵 推薦音樂：https://www.youtube.com/watch?v=WUXQzz2FKqk"
}

def chat_response(user_id, user_text):
    history = user_memory.get(user_id, [])[-5:]
    messages = [
        {"role": "system", "content": "你是一位貼心的 AI 室友，會根據使用者的情緒與訊息進行溫暖的交談。"},
    ] + history + [{"role": "user", "content": user_text}]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    reply = response.choices[0].message.content.strip()
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": reply})
    user_memory[user_id] = history
    return reply

def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

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
    user_id = event.source.user_id
    user_input = event.message.text
    result = classifier(user_input)[0]
    emotion = result['label'].lower()

    if emotion in emotion_response:
        msg = emotion_response[emotion]
        suggestion = msg['suggest']
        music_url = msg['music']
        reply = f"你的情緒是：{emotion}\n👉 {suggestion}\n🎵 推薦音樂：{music_url}"
    else:
        reply = chat_response(user_id, user_input)

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
        result = classifier(text)[0]
        emotion = result['label'].lower()
        msg = emotion_response.get(emotion, {"suggest": "我還不太確定你的情緒，但我會一直陪著你喔 💡", "music": ""})
        reply = f"🎧 語音內容為：{text}\n你的情緒是：{emotion}\n👉 {msg['suggest']}\n🎵 音樂建議：{msg['music']}"
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
