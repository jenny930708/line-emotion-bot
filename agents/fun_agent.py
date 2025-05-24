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
    music_map = {
        "周杰倫": "https://www.youtube.com/watch?v=2jD5V8YVhJM",
        "林俊傑": "https://www.youtube.com/watch?v=F62HMs1N6Vc",
        "白噪音": "https://www.youtube.com/watch?v=eZp4zAm5qvY",
        "水晶": "https://www.youtube.com/watch?v=lFcSrYw-ARY",
        "輕音樂": "https://www.youtube.com/watch?v=2OEL4P1Rz04",
        "放鬆": "https://www.youtube.com/watch?v=MIr3RsUWrdo",
        "鋼琴": "https://www.youtube.com/watch?v=5qap5aO4i9A",
        "自然": "https://www.youtube.com/watch?v=OdIJ2x3nxzQ",
        "雨聲": "https://www.youtube.com/watch?v=q76bMs-NwRk"
    }

    for keyword, url in music_map.items():
        if keyword in user_message:
            return f"🎶 這是你想聽的「{keyword}」音樂：{url}"

    # 如果沒有明確需求，就隨機選一首
    random_url = random.choice(list(music_map.values()))
    return f"🎵 這首歌也許能陪伴你現在的心情：{random_url}"

# 梗圖、音樂、影片回覆
def handle_fun(user_message):
    if "梗圖" in user_message:
        image_url = search_meme_image_by_yahoo()
        if image_url:
            return ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
        else:
            return TextSendMessage(text="❌ 目前找不到梗圖 😥")
    
    elif "音樂" in user_message:
        return TextSendMessage(text=handle_music_request(user_message))

    elif "影片" in user_message:
        return TextSendMessage(text="這支短影片讓你笑一笑：https://www.youtube.com/shorts/abc123xyz")

    return TextSendMessage(text="想放鬆一下嗎？你可以說「梗圖」、「影片」或「音樂」來跟我互動喔！")
