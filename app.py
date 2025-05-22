import os
import json
from datetime import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, AudioMessage, FollowEvent
from utils import detect_emotion, suggest_music
from dotenv import load_dotenv
from openai import OpenAI
import openai
import tempfile

# 載入環境變數
load_dotenv()

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

MEMORY_FILE = "memory.json"
LOG_FILE = "logs.txt"
STUDENTS_FILE = "students.json"

for file in [MEMORY_FILE, STUDENTS_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        pass

def load_memory():
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f)

def load_students():
    with open(STUDENTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_students(data):
    with open(STUDENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_interaction(user_id, user_input, ai_reply, emotion):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] User: {user_id}\nInput: {user_input}\nEmotion: {emotion}\nAI: {ai_reply}\n---\n")

def check_emotion_alert(user_id):
    emotion_count = {"sad": 0, "anger": 0, "fear": 0}
    if not os.path.exists(LOG_FILE):
        return False
    with open(LOG_FILE, encoding="utf-8") as f:
        lines = f.readlines()
    current_user_lines = []
    for i in range(len(lines)):
        if f"User: {user_id}" in lines[i]:
            log_block = lines[i:i+4]
            current_user_lines.append(log_block)
    recent_logs = current_user_lines[-7:]
    for block in recent_logs:
        for line in block:
            for emo in emotion_count:
                if f"Emotion: {emo}" in line:
                    emotion_count[emo] += 1
    return sum(emotion_count.values()) >= 5

def notify_teacher(user_id):
    students = load_students()
    for sid, info in students.items():
        if info["line_user_id"] == user_id:
            teacher_id = info.get("teacher_id")
            student_name = info["name"]
            if teacher_id:
                msg = f"⚠️ [警示] 您的學生 {student_name}（{sid}）最近 7 次互動中出現過多負面情緒，請特別關注。"
                line_bot_api.push_message(teacher_id, TextSendMessage(text=msg))
            break

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

@handler.add(FollowEvent)
def handle_follow(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=(
                "🎓 歡迎加入情緒偵測 AI！\n"
                "請輸入你的學號與姓名來完成註冊或修改或刪除\n"
                "格式：註冊 學號 姓名\n"
                "      修改 學號 姓名\n"
                "      刪除 學號 姓名\n"
                "例如：註冊 A1111111 王小明"
            )
        )
    )

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_id = event.source.user_id
    user_input = event.message.text.strip()

    students = load_students()
    sid_found = None
    for sid, info in students.items():
        if info.get("line_user_id") == user_id:
            sid_found = sid
            break

    if any(x in user_input for x in ["我要修改", "更改學號", "更換姓名"]):
        reply = "✏️ 請提供您希望修改成什麼名字和學號，我會協助您完成修改的。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    if any(x in user_input for x in ["我要刪除", "刪除註冊", "取消註冊"]):
        if sid_found:
            del students[sid_found]
            save_students(students)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="🗑️ 已刪除您的註冊紀錄，如需重新使用請再次註冊。"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 找不到您的註冊資料，無法刪除。"))
        return

    if user_input.startswith("註冊") or user_input.startswith("修改") or (len(user_input.split()) == 2 and sid_found):
        parts = user_input.split()
        if len(parts) == 3:
            _, sid, name = parts
        elif len(parts) == 2:
            sid, name = parts
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入正確格式：註冊 學號 姓名"))
            return
        students[sid] = {
            "name": name,
            "line_user_id": user_id,
            "teacher_id": ""
        }
        save_students(students)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅ 已註冊學號 {sid}，姓名 {name}。請開始使用情緒偵測服務。"))
        return

    if "查詢註冊" in user_input or "查詢我的註冊" in user_input or "我的註冊內容" in user_input:
        for sid, info in students.items():
            if info.get("line_user_id") == user_id:
                msg = f"📄 讓我幫您確認一下。您目前的註冊資料包括：\n\n{sid} {info['name']}\n\n如果有任何其他需要修改的地方，或想查詢其他資訊，請告訴我。"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
                return

    if not sid_found:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=(
                    "🎓 您尚未註冊，請輸入：\n"
                    "註冊 學號 姓名\n"
                    "以完成登入\n"
                    "例如 : 註冊 A1111111 王小明"
                )
            )
        )
        return

    memory = load_memory()
    user_history = memory.get(user_id, [])
    emotion = detect_emotion(user_input)

    prompt = f"你是一位貼心的 AI 室友，用自然語言回答使用者：\n{chr(10).join(user_history[-3:])}\n使用者：{user_input}\nAI："

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

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=full_reply))
    user_history.append(user_input)
    user_history.append(ai_reply)
    memory[user_id] = user_history[-10:]
    save_memory(memory)
    log_interaction(user_id, user_input, ai_reply, emotion)

    if check_emotion_alert(user_id):
        notify_teacher(user_id)

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

    event.message.text = user_input
    handle_text_message(event)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
