from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from transformers import pipeline

import os  # 若你改用環境變數也可以使用

app = Flask(__name__)

line_bot_api = LineBotApi('rc5MlSvrXcnjmbdB68PggoiG47+mj8LL/jEhjT+Gaj9dVkvR7mi0OQ2DngYvDnB0tfo+KU3h2T12cskbECKnXB3NTKG3tgDJ6B7PlREkINdLmXCKJFkcz/TU42Jgp6VoWonxvQMQENPTc8Q11zrQbAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('3ab6df516a940cfe65f2fbc163147dc3')

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
    suggestion = emotion_response.get(emotion, "我還不太確定你的情緒，但我會一直陪著你喔！💡")
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"你的情緒是：{emotion}\n👉 {suggestion}")
    )

if __name__ == "__main__":
    app.run()
