from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, AudioMessage, StickerMessage
from transformers import pipeline
import openai
import os
import tempfile
import sqlite3
import datetime
from linebot.models import FlexSendMessage
from collections import Counter

def create_weekly_chart(data):
    counter = Counter([row[3] for row in data])
    bars = []
    for label in ['joy','anger','sadness','fear','love','surprise','neutral']:
        count = counter.get(label, 0)
        bars.append({
            "type": "box",
            "layout": "baseline",
            "spacing": "sm",
            "contents": [
                {"type": "text", "text": label, "size": "sm", "color": "#555555", "flex": 2},
                {"type": "text", "text": str(count), "size": "sm", "color": "#111111", "align": "end", "flex": 1}
            ]
        })
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "上週情緒統計", "weight": "bold", "size": "lg", "margin": "md"},
                {"type": "separator", "margin": "md"},
                *bars
            ]
        }
    }


app = Flask(__name__)

line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])
openai.api_key = os.environ['OPENAI_API_KEY']

classifier = pipeline("text-classification", model="bhadresh-savani/bert-base-uncased-emotion")

emotion_response = {
    'joy': ("你看起來心情很好！可以試著挑戰新任務哦！✨", "https://www.youtube.com/watch?v=ZbZSe6N_BXs"),
    'anger': ("你似乎有點生氣，試著做深呼吸，或出去走走吧 🌳", "https://www.youtube.com/watch?v=2bj2ERB7iB4"),
    'sadness': ("我在這陪你～建議聽聽輕音樂放鬆一下 🎧", "https://www.youtube.com/watch?v=2OEL4P1Rz04"),
    'fear': ("感到害怕時可以找人聊聊，也可以聽冥想音樂 🧘", "https://www.youtube.com/watch?v=2OEL4P1Rz04"),
    'love': ("喜歡的感覺真好！可以把喜歡的事記錄下來喔 📝", "https://www.youtube.com/watch?v=3JWTaaS7LdU"),
    'surprise': ("驚訝嗎？今天有什麼新鮮事？可以分享給我聽 😯", "https://www.youtube.com/watch?v=Zi_XLOBDo_Y"),
    'neutral': ("平穩的一天也很棒，別忘了喝水與休息 💧", "https://www.youtube.com/watch?v=y6Sxv-sUYtM")
}

conn = sqlite3.connect("memory.db", check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS memory (user_id TEXT, datetime TEXT, message TEXT, emotion TEXT)")
conn.commit()

user_styles = {}

def chat_response(user_text, style="一般"):
    prompt = {
        "一般": "你是一位貼心的 AI 室友，會自然溫暖地回應使用者。",
        "中二風": "你是中二病爆發的 AI 夥伴，說話風格誇張有趣，像動漫角色。",
        "老師風": "你是冷靜且理性的導師型 AI，會給出中肯建議。",
    }.get(style, "你是一位貼心的 AI 室友。")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_text}
        ]
    )
    return response.choices[0].message.content.strip()

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
    user_id = event.source.user_id
    user_input = event.message.text.strip()
    if user_input == "/上週情緒":
        one_week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
        c.execute("SELECT * FROM memory WHERE user_id = ? AND datetime >= ?", (user_id, one_week_ago))
        records = c.fetchall()
        if records:
            flex = create_weekly_chart(records)
            line_bot_api.reply_message(event.reply_token, FlexSendMessage("統計", flex))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="上週尚無紀錄 😅"))
        return

    if user_input.startswith("/角色 "):
        new_style = user_input.replace("/角色 ", "")
        user_styles[user_id] = new_style
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅ 已切換為「{new_style}」語氣模式"))
        return
    if user_input.startswith("/提醒 "):
        c.execute("INSERT INTO memory VALUES (?, ?, ?, ?)", (user_id, str(datetime.datetime.now()), user_input, "remind"))
        conn.commit()
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 已記下提醒！"))
        return
    result = classifier(user_input)[0]
    emotion = result['label']
    c.execute("INSERT INTO memory VALUES (?, ?, ?, ?)", (user_id, str(datetime.datetime.now()), user_input, emotion))
    conn.commit()
    suggestion, music = emotion_response.get(emotion, ("我還不太確定你的情緒，但我會一直陪著你喔 💡", ""))
    reply = f"你的情緒是：{emotion}\n👉 {suggestion}\n🎵 音樂推薦：{music}"
    
    c.execute("SELECT emotion FROM memory WHERE user_id = ? ORDER BY datetime DESC LIMIT 3", (user_id,))
    last3 = [r[0] for r in c.fetchall()]
    if len(last3) == 3 and all(e == emotion for e in last3):
        reply += f"\n我注意到你連續 {emotion} 幾次了，需要幫忙聊聊嗎？"

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
        emotion = result['label']
        suggestion, music = emotion_response.get(emotion, ("我還不太確定你的情緒", ""))
        reply = f"🎧 語音轉文字為：{text}\n你的情緒是：{emotion}\n👉 {suggestion}\n🎵 音樂推薦：{music}"
        user_id = event.source.user_id
        c.execute("INSERT INTO memory VALUES (?, ?, ?, ?)", (user_id, str(datetime.datetime.now()), text, emotion))
        conn.commit()
    except Exception as e:
        reply = f"語音處理失敗：{str(e)}"
    
    c.execute("SELECT emotion FROM memory WHERE user_id = ? ORDER BY datetime DESC LIMIT 3", (user_id,))
    last3 = [r[0] for r in c.fetchall()]
    if len(last3) == 3 and all(e == emotion for e in last3):
        reply += f"\n我注意到你連續 {emotion} 幾次了，需要幫忙聊聊嗎？"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker(event):
    sticker_id = event.message.sticker_id
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"😆 你傳了貼圖 ID：{sticker_id}"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)