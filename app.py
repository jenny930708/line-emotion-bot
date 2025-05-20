
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, AudioMessage, StickerMessage
from transformers import pipeline
from openai import OpenAI
import os, tempfile

app = Flask(__name__)

# 環境變數讀取
line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# 使用者對話歷史記憶
user_sessions = {}

# 情緒分類模型
classifier = pipeline("text-classification", model="bhadresh-savani/bert-base-uncased-emotion")

# YouTube 音樂推薦（依情緒）
youtube_music = {
    'joy': 'https://www.youtube.com/watch?v=ZbZSe6N_BXs',
    'anger': 'https://www.youtube.com/watch?v=hTWKbfoikeg',
    'sadness': 'https://www.youtube.com/watch?v=ho9rZjlsyYY',
    'fear': 'https://www.youtube.com/watch?v=2ZIpFytCSVc',
    'love': 'https://www.youtube.com/watch?v=450p7goxZqg',
    'surprise': 'https://www.youtube.com/watch?v=y6120QOlsfU',
    'neutral': 'https://www.youtube.com/watch?v=5qap5aO4i9A'
}

# AI Agent 回應
def chat_response(user_id, user_text):
    history = user_sessions.get(user_id, [])
    messages = [{"role": "system", "content": "你是一位貼心的 AI 室友，會用自然溫暖的語氣與使用者聊天，幫助他們紓解情緒。"}]
    for entry in history[-10:]:
        messages.append({"role": "user", "content": entry})

    messages.append({"role": "user", "content": user_text})

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    reply = response.choices[0].message.content.strip()
    user_sessions.setdefault(user_id, []).append(user_text)
    user_sessions[user_id].append(reply)
    return reply

# 語音轉文字
def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
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
    music_link = youtube_music.get(emotion)
    agent_reply = chat_response(user_id, user_input)
    reply = f"你的情緒是：{emotion}\n🎵 推薦音樂：{music_link}\n🗣️ AI室友說：{agent_reply}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

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
        result = classifier(text)[0]
        emotion = result['label'].lower()
        music_link = youtube_music.get(emotion)
        agent_reply = chat_response(user_id, text)
        reply = f"🎧 語音內容為：{text}\n你的情緒是：{emotion}\n🎵 推薦音樂：{music_link}\n🗣️ AI室友說：{agent_reply}"
    except Exception as e:
        reply = f"語音處理失敗：{str(e)}"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker(event):
    sticker_id = event.message.sticker_id
    reply = f"你傳來貼圖（ID：{sticker_id}）真可愛～！貼圖也能療癒心情喔 💖"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
