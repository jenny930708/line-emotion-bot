import os
import json
from datetime import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, AudioMessage
from utils import detect_emotion, suggest_music
from dotenv import load_dotenv
from openai import OpenAI
import openai
import tempfile
import requests

# 載入環境變數
load_dotenv()

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

MEMORY_FILE = "memory.json"
LOG_FILE = "logs.txt"

if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w") as f:
        json.dump({}, f)

def load_memory():
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f)

def log_interaction(user_id, user_input, ai_reply, emotion):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] User: {user_id}\nInput: {user_input}\nEmotion: {emotion}\nAI: {ai_reply}\n---\n")

@app.route("/", methods=['GET'])
def health_check():
    return "Bot is running!"

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
def handle_text_message(event):
    user_id = event.source.user_id
    user_input = event.message.text

    memory = load_memory()
    user_history = memory.get(user_id, [])

    emotion = detect_emotion(user_input)

    history_text = "\n".join(user_history[-3:])
    prompt = f"你是一位貼心的 AI 室友，用自然語言回答使用者：\n{history_text}\n使用者：{user_input}\nAI："

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "你是一個友善的情緒偵測 AI 室友。"},
            {"role": "user", "content": prompt}
        ]
    )
    ai_reply = response.choices[0].message.content

    full_reply = ai_reply
    if "音樂" in user_input or "想聽歌" in user_input:
        music_link = suggest_music(emotion, user_input)
        full_reply += f"\n🎵 推薦音樂：{music_link}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=full_reply)
    )

    user_history.append(user_input)
    user_history.append(ai_reply)
    memory[user_id] = user_history[-10:]
    save_memory(memory)
    log_interaction(user_id, user_input, ai_reply, emotion)

@handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
    user_id = event.source.user_id
    message_id = event.message.id

    with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as tf:
        audio_content = line_bot_api.get_message_content(message_id)
        for chunk in audio_content.iter_content(chunk_size=1024):
            tf.write(chunk)
        audio_path = tf.name

    with open(audio_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file, api_key=OPENAI_API_KEY)
        user_input = transcript["text"]

    event.message.text = user_input  # reuse as text
    handle_text_message(event)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
