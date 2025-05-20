import os
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from utils import detect_emotion, suggest_music
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

app = Flask(__name__)

# 初始化 LINE API
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 對話記憶（可用檔案記錄）
MEMORY_FILE = "memory.json"
if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "w") as f:
        json.dump({}, f)

def load_memory():
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f)

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
def handle_message(event):
    user_id = event.source.user_id
    user_input = event.message.text

    # 載入對話記憶
    memory = load_memory()
    user_history = memory.get(user_id, [])

    # 情緒分析
    emotion = detect_emotion(user_input)
    music_link = suggest_music(emotion, user_input)

    # 組合 prompt（簡化範例）
    history_text = "\n".join(user_history[-3:])  # 保留近三句
    prompt = f"你是一位貼心的 AI 室友，用自然語言回答使用者：\n{history_text}\n使用者：{user_input}\nAI："

    # 呼叫 OpenAI
    import openai
    openai.api_key = OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "你是一個友善的情緒偵測 AI 室友。"},
            {"role": "user", "content": prompt}
        ]
    )
    ai_reply = response['choices'][0]['message']['content']

    # 回覆訊息
    full_reply = f"{ai_reply}\n\n🌈 目前情緒：{emotion}\n🎵 推薦音樂：{music_link}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=full_reply)
    )

    # 更新對話記憶
    user_history.append(user_input)
    user_history.append(ai_reply)
    memory[user_id] = user_history[-10:]  # 最多保留10句
    save_memory(memory)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
