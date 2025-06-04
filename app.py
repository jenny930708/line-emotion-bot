import os
import re
import urllib.parse
import requests
from flask import Flask, request, abort
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 載入 .env 變數

load_dotenv()
app = Flask(**name**)
line_bot_api = LineBotApi(os.getenv(“LINE_CHANNEL_ACCESS_TOKEN”))
handler = WebhookHandler(os.getenv(“LINE_CHANNEL_SECRET”))

# 紀錄每個使用者的狀態

user_states = {}

# 改進的歌手/歌名擷取函式

def extract_keywords(text):
“”“從文字中擷取歌手名或歌名”””
# 移除常見的前綴詞
patterns = [
r”我想聽(.+?)的歌”,
r”我想聽(.+?)的音樂”,
r”我想聽(.+)”,
r”可以聽(.+?)的歌”,
r”可以聽(.+?)的音樂”,
r”可以聽(.+)”,
r”聽(.+?)的歌”,
r”聽(.+?)的音樂”,
r”聽(.+)”
]

for pattern in patterns:
    match = re.search(pattern, text)
    if match:
        keyword = match.group(1).strip()
        # 清理結尾的贅字
        keyword = re.sub(r"[的歌音樂\s]+$", "", keyword)
        if keyword:  # 確保有內容
            return keyword
return None

# 改進的 YouTube 搜尋函式

# 🎵 修正後的 YouTube 音樂連結搜尋函式

def search_youtube_link(query):
try:
headers = {
“User-Agent”: “Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36”,
“Accept-Language”: “zh-TW,zh;q=0.9,en;q=0.8”
}
url = f”https://www.youtube.com/results?search_query={urllib.parse.quote(query)}”
response = requests.get(url, headers=headers, timeout=10)

    # 方法1: 從 script 標籤找 JSON 資料
    soup = BeautifulSoup(response.text, "html.parser")
    scripts = soup.find_all("script")
    
    for script in scripts:
        if script.string and "var ytInitialData" in script.string:
            # 更嚴謹的正規表達式
            video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', script.string)
            seen = set()
            for vid in video_ids:
                if vid not in seen and len(vid) == 11:
                    seen.add(vid)
                    return f"https://www.youtube.com/watch?v={vid}"
    
    # 方法2: 備用方案
    video_ids = re.findall(r'href="/watch\?v=([a-zA-Z0-9_-]{11})"', response.text)
    if video_ids:
        return f"https://www.youtube.com/watch?v={video_ids[0]}"
        
except Exception as e:
    print("YouTube 查詢失敗：", e)

return "⚠️ 找不到音樂連結，請換個關鍵字再試一次。"

# 🎧 修正音樂推薦邏輯

def handle_music_request(user_message):
stop_words = [“我想聽”, “播放”, “想聽”, “來點”, “給我”, “聽一下”, “音樂”, “歌曲”, “首歌”, “聽聽”, “歌”]
cleaned = user_message
for word in stop_words:
cleaned = cleaned.replace(word, “”)
keywords = cleaned.strip()

mood_map = {
    "放鬆": "輕音樂 放鬆 身心靈",
    "運動": "動感 音樂 運動 播放清單",  # 修正錯字
    "悲傷": "療癒 情歌 抒情",
    "開心": "快樂 音樂 熱門",
    "焦慮": "自然 音樂 放鬆",
    "睡不著": "助眠 音樂 白噪音"
}

for mood, query in mood_map.items():
    if mood in user_message:
        link = search_youtube_link(query)
        return TextSendMessage(text=f"🎵 給你推薦的 {mood} 音樂：{link}")

if re.match(r".+的$", keywords):
    return TextSendMessage(text="請告訴我完整歌名，例如：周杰倫的青花瓷")

# 移除 site:youtube.com
if "中文" in user_message:
    search_query = "中文 熱門 歌曲 2024"
elif "英文" in user_message:
    search_query = "英文 熱門 歌曲 2024"
elif keywords:
    search_query = f"{keywords} 官方 MV"  # 移除 site:
else:
    search_query = "熱門 歌曲 2024"

link = search_youtube_link(search_query)
return TextSendMessage(text=f"🎵 推薦音樂：{link}")

    return results
    
except Exception as e:
    print(f"YouTube 搜尋錯誤: {e}")
    return []

# 心情關鍵字對應

MOOD_KEYWORDS = {
“negative”: [“心情不好”, “難過”, “不開心”, “想哭”, “崩潰”, “低落”, “焦慮”, “沮喪”, “憂鬱”, “失落”],
“positive”: [“開心”, “快樂”, “興奮”, “愉快”],
“relaxed”: [“放鬆”, “輕鬆”, “平靜”, “舒服”],
“energetic”: [“運動”, “健身”, “跑步”, “活力”]
}

# 心情對應的音樂類型

MOOD_MUSIC_SUGGESTIONS = {
“negative”: [“療癒音樂”, “抒情歌曲”, “輕音樂”],
“positive”: [“快樂音樂”, “熱門歌曲”],
“relaxed”: [“放鬆音樂”, “自然音樂”, “冥想音樂”],
“energetic”: [“運動音樂”, “動感音樂”, “電音”]
}

def detect_mood(text):
“”“偵測使用者心情”””
for mood, keywords in MOOD_KEYWORDS.items():
if any(keyword in text for keyword in keywords):
return mood
return None

# LINE webhook 入口

@app.route(”/callback”, methods=[“POST”])
def callback():
signature = request.headers[“X-Line-Signature”]
body = request.get_data(as_text=True)

try:
    handler.handle(body, signature)
except InvalidSignatureError:
    abort(400)
return "OK"

# 文字訊息處理主體

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
user_id = event.source.user_id
user_msg = event.message.text.strip()

# 初始化使用者狀態
if user_id not in user_states:
    user_states[user_id] = {"mood": None, "waiting_for_song": False}

# 偵測心情
mood = detect_mood(user_msg)
if mood:
    user_states[user_id]["mood"] = mood
    user_states[user_id]["waiting_for_song"] = True

# 嘗試擷取歌手或歌名
keywords = extract_keywords(user_msg)

if keywords:
    # 如果有心情狀態，加上心情相關的搜尋詞
    if user_states[user_id]["mood"] in MOOD_MUSIC_SUGGESTIONS:
        mood_suggestion = MOOD_MUSIC_SUGGESTIONS[user_states[user_id]["mood"]][0]
        search_query = f"{keywords} {mood_suggestion}"
    else:
        search_query = keywords
    
    # 搜尋 YouTube
    videos = search_youtube_videos(search_query, max_results=1)
    
    if videos:
        if user_states[user_id]["mood"] == "negative":
            reply = f"聽聽這首歌，希望能讓你心情好一點 🎵\n{videos[0]['url']}"
        elif user_states[user_id]["mood"] == "positive":
            reply = f"來聽這首歌，讓心情更愉快！🎶\n{videos[0]['url']}"
        else:
            reply = f"推薦給你：{keywords} 🎵\n{videos[0]['url']}"
        
        # 重置狀態
        user_states[user_id]["waiting_for_song"] = False
    else:
        # 如果找不到，嘗試更簡單的搜尋
        simple_videos = search_youtube_videos(keywords + " 音樂", max_results=1)
        if simple_videos:
            reply = f"找到相關的音樂：\n{simple_videos[0]['url']}"
        else:
            reply = "抱歉，目前找不到相關的音樂。可以試試其他關鍵字，或是告訴我完整的歌名喔！"

elif user_states[user_id]["waiting_for_song"]:
    # 如果在等待歌曲輸入
    reply = "請告訴我你想聽誰的歌，或是哪首歌？\n例如：「我想聽周杰倫的歌」或「我想聽青花瓷」"

elif mood:
    # 如果只是表達心情
    if mood == "negative":
        reply = "我感受到你的心情不太好...想聽什麼歌嗎？音樂或許能帶來一些安慰 🎵"
    elif mood == "positive":
        reply = "你心情很好呢！想來點音樂慶祝一下嗎？🎶"
    else:
        reply = "想聽什麼類型的音樂呢？"

else:
    # 一般對話
    if "音樂" in user_msg or "歌" in user_msg:
        reply = "你可以告訴我：\n1. 想聽誰的歌（如：我想聽周杰倫）\n2. 想聽什麼歌（如：我想聽青花瓷）\n3. 你的心情（如：我心情不好）"
    else:
        reply = "嗨！我可以幫你推薦音樂喔～\n告訴我你想聽什麼，或是你現在的心情如何？"

line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# 健康檢查端點

@app.route(”/”)
def health_check():
return “LINE Bot is running!”

# 啟動應用

if **name** == “**main**”:
port = int(os.environ.get(“PORT”, 5000))
app.run(host=“0.0.0.0”, port=port)
