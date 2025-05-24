# agents/fun_agent.py
import os
import random
import requests
from bs4 import BeautifulSoup
from linebot.models import TextSendMessage, ImageSendMessage

# Yahoo 梗圖搜尋
def search_meme_image_by_yahoo(query="梗圖"):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f"https://tw.images.search.yahoo.com/search/images?p={query}"
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        img_tags = soup.select("img")
        img_urls = [img["src"] for img in img_tags if img.get("src") and img["src"].startswith("http")]
        if img_urls:
            return random.choice(img_urls)
    except Exception as e:
        print(f"[Yahoo 搜圖錯誤] {e}")
    return None

# 音樂需求處理：改為回傳 YouTube 搜尋連結

def handle_music_request(user_message):
    if "音樂" in user_message or "歌" in user_message:
        keywords = ["周杰倫", "林俊傑", "白噪音", "水晶音樂", "輕音樂", "放鬆", "鋼琴", "冥想", "療癒", "純音樂"]
        query = next((kw for kw in keywords if kw in user_message), None)
        if not query:
            return TextSendMessage(text="請告訴我你想聽什麼音樂，例如：周杰倫、白噪音、水晶音樂等。")

        youtube_search_link = f"https://www.youtube.com/results?search_query={query}+音樂"
        return TextSendMessage(text=f"🎵 這是我幫你找的 {query} 音樂搜尋結果：\n{youtube_search_link}")

    return TextSendMessage(text="你可以說「我想聽周杰倫的歌」、「來點放鬆音樂」等等喔～")

# 處理娛樂需求（梗圖、影片）
def handle_fun(user_message):
    if "梗圖" in user_message:
        theme_keywords = ["動物", "狗", "貓", "熊", "老虎", "貓咪", "狗狗", "鯊魚", "食物", "人類", "日常", "漫畫", "梗"]
        matched_theme = next((word for word in theme_keywords if word in user_message), None)
        search_query = f"{matched_theme}梗圖" if matched_theme else "梗圖"

        image_url = search_meme_image_by_yahoo(search_query)
        if image_url:
            return ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
        else:
            return TextSendMessage(text=f"❌ 沒找到與「{search_query}」相關的梗圖 😥")

    elif "影片" in user_message:
        return TextSendMessage(text="這支短影片讓你笑一笑：https://www.youtube.com/shorts/abc123xyz")

    elif "音樂" in user_message:
        return handle_music_request(user_message)

    return TextSendMessage(text="想放鬆一下嗎？你可以說：播放音樂、搞笑影片、梗圖等等喔！")
