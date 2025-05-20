from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, AudioMessage, StickerMessage
from transformers import pipeline
from openai import OpenAI
import openai
import os
import tempfile
import json
import datetime

app = Flask(__name__)

# 初始化 LINE Bot 與 OpenAI
line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# 情緒分類器（英文模型）
classifier = pipeline("text-classification", model="bhadresh-savani/bert-base-uncased-emotion")

# YouTube 音樂推薦對應表（情緒對應連結）
youtube_music = {
    'joy': 'https://www.youtube.com/watch?v=ZbZSe6N_BXs',        # Happy - Pharrell Williams
    'anger': 'https://www.youtube.com/watch?v=hTWKbfoikeg',      # Nirvana - Smells Like Teen Spirit
    'sadness': 'https://www.youtube.com/watch?v=Ho32Oh6b4jc',    # Adele - Easy On Me
    'fear': 'https://www.youtube.com/watch?v=2OEL4P1Rz04',       # Alan Walker - Faded
    'love': 'https://www.youtube.com/watch?v=450p7goxZqg',       # Ed Sheeran - Perfect
    'surprise': 'https://www.youtube.com/watch?v=JGwWNGJdvx8',   # Ed Sheeran - Shape of You
    'neutral': 'https://www.youtube.com/watch?v=kXYiU_JCYtU'     # Numb - Linkin Park
}

# 簡易聊天記憶儲存
def log_message(user_id, message):
    log_data = {}
    log_file = "chat_logs.json"
    if os.path.exists(log_file):
        with open(log_file, "r", encoding='utf-8') as f:
            log_data = json.load(f)
    if user_id not in log_data:
        log_data[user_id] = []
    log_data[user_id].append({
        "time": str(datetime.datetime.now()),
        "message": message
    })
    with open(log_file, "w", encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

# GPT 回應
def chat_response(user_text):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一位溫暖又有耐心的 AI 室友，會陪使用者聊天、關心他們的情緒，並給出有溫度的回應。"},
            {"role": "user", "content": user_text}
        ]
    )
    return response.choices[0].message.content.strip()

# 語音轉文字（Whisper）
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

# 文字訊息處理
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_input = event.message.text
    user_id = event.source.user_id
    log_message(user_id, user_input)

    try:
        result = classifier(user_input)[0]
        emotion = result['label'].lower()
        music_link = youtube_music.get(emotion)
        response_text = f"你的情緒是：{emotion}\n👉 {emotion_response(emotion)}"
        if music_link:
            response_text += f"\n🎵 推薦音樂：{music_link}"
    except Exception:
        # 若分類器出錯，轉為 GPT 對話
        response_text = chat_response(user_input)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_text))

# 音訊處理
@handler.add(MessageEvent, message=AudioMessage)
def handle_audio(event):
    user_id = event.source.user_id
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as tf:
        for chunk in message_content.iter_content(chunk_size=1024):
            tf.write(chunk)
        tf_path = tf.name

    try:
        text = transcribe_audio(tf_path)
        log_message(user_id, f"(語音轉文字)：{text}")
        result = classifier(text)[0]
        emotion = result['label'].lower()
        music_link = youtube_music.get(emotion)
        suggestion = emotion_response(emotion)
        response_text = f"🎧 語音內容：{text}\n你的情緒是：{emotion}\n👉 {suggestion}"
        if music_link:
            response_text += f"\n🎵 推薦音樂：{music_link}"
    except Exception as e:
        response_text = f"語音處理失敗：{str(e)}"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_text))

# 貼圖訊息
@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker(event):
    sticker_id = event.message.sticker_id
    reply = f"😄 你傳了一個貼圖（ID：{sticker_id}），好可愛！"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# 情緒回應文字
def emotion_response(emotion):
    responses = {
        'joy': "你看起來心情很好！可以試著挑戰新任務哦 ✨",
        'anger': "你似乎有點生氣，試試深呼吸或聽音樂放鬆一下 🌳",
        'sadness': "我在這陪你～建議聽聽輕音樂放鬆一下 🎧",
        'fear': "感到害怕時可以找人聊聊，也可以聽冥想音樂 🧘",
        'love': "喜歡的感覺真好！可以把喜歡的事記錄下來喔 📝",
        'surprise': "驚訝嗎？今天有什麼新鮮事？可以跟我說 😯",
        'neutral': "平穩的一天也很棒，別忘了喝水與休息 💧"
    }
    return responses.get(emotion, "我還不太確定你的情緒，但我會一直陪著你喔 💡")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
