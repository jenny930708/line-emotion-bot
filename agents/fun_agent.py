import os
import random
import requests
from linebot.models import TextSendMessage, ImageSendMessage
from bs4 import BeautifulSoup

# 用 Yahoo 搜尋「梗圖」，擷取圖片網址
def search_meme_image_by_yahoo(query="梗圖"):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        url = f"https://tw.images.search.yahoo.com/search/images?p={query}"
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # 抓取所有圖片連結
        img_tags = soup.select("img")
        img_urls = [img["src"] for img in img_tags if img.get("src") and img["src"].startswith("http")]

        if img_urls:
            return random.choice(img_urls)
    except Exception as e:
        print(f"[Yahoo 搜圖錯誤] {e}")
    
    return None

# 處理娛樂請求
def handle_fun(user_message):
    if "梗圖" in user_message:
        image_url = search_meme_image_by_yahoo()
        if image_url:
            return ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
        else:
            return TextSendMessage(text="❌ 目前找不到梗圖 😥")

    elif "音樂" in user_message:
        return TextSendMessage(text="這首歌也許能振奮你的心情：https://www.youtube.com/watch?v=ZbZSe6N_BXs")

    elif "影片" in user_message:
        return TextSendMessage(text="這支短影片讓你笑一笑：https://www.youtube.com/shorts/abc123xyz")

    return TextSendMessage(text="想看點有趣的嗎？你可以說「梗圖」、「影片」或「音樂」喔！")

# 處理音樂請求
def handle_music_request(user_message):
    music_suggestions = {
        "水晶": "https://www.youtube.com/watch?v=lFcSrYw-ARY",  # 水晶音樂
        "輕音樂": "https://www.youtube.com/watch?v=2OEL4P1Rz04",
        "放鬆": "https://www.youtube.com/watch?v=2OEL4P1Rz04",
        "冥想": "https://www.youtube.com/watch?v=MIr3RsUWrdo",
        "自然": "https://www.youtube.com/watch?v=OdIJ2x3nxzQ",
        "雨聲": "https://www.youtube.com/watch?v=eZp4zAm5qvY",
        "周杰倫": "https://www.youtube.com/watch?v=2jD5V8YVhJM",
        "鋼琴": "https://www.youtube.com/watch?v=5qap5aO4i9A",
        "清晨": "https://www.youtube.com/watch?v=J8CklYbmeM0"
    }

    for keyword, url in music_suggestions.items():
        if keyword in user_message:
            return f"這首音樂適合你現在的狀態 🎵：{url}"

    # 預設回覆
    return "這首歌也許能振奮你的心情：https://www.youtube.com/watch?v=ZbZSe6N_BXs"
