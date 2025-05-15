from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from transformers import pipeline
import openai
import os

app = Flask(__name__)

# 將你的 Key 放進環境變數或直接放這（開發用）
line_bot_api = LineBotApi('你的 Line Channel Access Token')
handler = WebhookHandler('你的 Line Channel Secret')
openai.api_key = os.environ['OPENAI_API_KEY']

classifier = pipeline("text-classification", model="bhadresh-savani/bert-base-uncased-emotion")

emotion_response = {
    'joy': "你看起來心情很好！可以試著挑戰新任務哦！✨",
    'anger': "你似乎有點生氣，試著做深呼吸，或出去走走吧 🌳",
    'sadness': "我在這陪你～建議聽聽輕音樂放鬆一下 🎧",
    'fear': "感到害怕時可以找人聊聊，也可以聽冥想音樂 🧘",
    'love': "喜歡的感覺真好！可以把喜歡的事記錄下來喔 📝",
    'surprise': "驚訝嗎？今天有什麼新鮮事？可以分享給我聽 😯",
    'neutral': "平穩的一天也很棒，別忘了喝水與休息 💧"
}

# 🧠 GPT 聊天邏輯
def chat_response(user_text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一位貼心、溫柔又幽默的 AI 室友，會根據使用者的話做自然回應。"},
            {"role": "user", "content": user_text}
        ]
    )
    return response.choices[0].message.content.strip()

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
    user_input = event.message.text
    result = classifier(user_input)[0]
    emotion = result['label']

    if emotion in emotion_response:
        response_text = f"你的情緒是：{emotion}\n👉 {emotion_response[emotion]}"
    else:
        response_text = chat_response(user_input)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
