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

# 音樂需求處理：包含關鍵字對應與隨機播放
def handle_music_request(user_message):
    music_suggestions = {
        "周杰倫": "https://www.youtube.com/watch?v=2jD5V8YVhJM",
        "林俊傑": "https://www.youtube.com/watch?v=Q9CSj5L8RNI",
        "白噪音": "https://www.youtube.com/watch?v=q76bMs-NwRk",
        "水晶": "https://www.youtube.com/watch?v=C2N1wSkCjZ8",
        "輕音樂": "https://www.youtube.com/watch?v=lFcSrYw-ARY",
        "放鬆": "https://www.youtube.com/watch?v=1ZYbU82GVz4",
        "鋼琴": "https://www.youtube.com/watch?v=4Tr0otuiQuU",
    }

    for keyword, url in music_suggestions.items():
        if keyword in user_message:
            return f"🎵 這是我為你挑選的 {keyword} 音樂，希望你會喜歡：{url}"

    fallback_music = [
        "https://www.youtube.com/watch?v=ZbZSe6N_BXs",
        "https://www.youtube.com/watch?v=UfcAVejslrU",
        "https://www.youtube.com/watch?v=5qap5aO4i9A"
    ]
    return f"🎵 這首音樂也許能陪伴你現在的心情：{random.choice(fallback_music)}"

# 梗圖、音樂、影片回覆
def handle_fun(user_message):
    if "梗圖" in user_message:
        # 抽取主題關鍵字，例如「動物」、「狗」、「貓」、「搞笑」
        theme_keywords = ["動物", "狗", "貓", "熊", "老虎", "貓咪", "狗狗", "鯊魚", "食物", "人類", "日常", "漫畫", "梗"]
        matched_theme = next((word for word in theme_keywords if word in user_message), None)
        search_query = f"{matched_theme}梗圖" if matched_theme else "梗圖"

        image_url = search_meme_image_by_yahoo(search_query)
        if image_url:
            return ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
        else:
            return TextSendMessage(text=f"❌ 沒找到與「{search_query}」相關的梗圖 😥")

    elif "音樂" in user_message:
        return TextSendMessage(text=handle_music_request(user_message))

    elif "影片" in user_message:
        return TextSendMessage(text="這支短影片讓你笑一笑：https://www.youtube.com/shorts/abc123xyz")

    return TextSendMessage(text="你想看看什麼樣的梗圖呢？可以說「貓的梗圖」、「美食梗圖」之類的哦！")
