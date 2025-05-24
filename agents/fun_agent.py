import os
import random
import requests
from bs4 import BeautifulSoup
from linebot.models import TextSendMessage, ImageSendMessage

# Yahoo 圖片搜尋（不需 API Key）
def search_meme_image(query="梗圖"):  # 預設為「梗圖」
    try:
        url = f"https://tw.images.search.yahoo.com/search/images?p={query}"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        img_tags = soup.find_all("img")
        img_urls = [img["src"] for img in img_tags if img.get("src", "").startswith("http")]
        return random.choice(img_urls) if img_urls else None
    except Exception as e:
        print("Yahoo 圖片搜尋錯誤：", e)
        return None

# 處理娛樂請求
def handle_fun(user_message):
    if "梗圖" in user_message:
        image_url = search_meme_image(user_message)  # 用使用者輸入作為關鍵字搜尋
        if image_url:
            return ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
        else:
            return TextSendMessage(text="❌ 目前找不到梗圖 😥")
    elif "音樂" in user_message:
        return TextSendMessage(text="這首歌也許能振奮你的心情：https://www.youtube.com/watch?v=ZbZSe6N_BXs")
    elif "影片" in user_message:
        return TextSendMessage(text="這支短影片讓你笑一笑：https://www.youtube.com/shorts/abc123xyz")
    else:
        return TextSendMessage(text="來點趣味放鬆一下吧～你想聽音樂、看梗圖還是影片呢？")

# 處理音樂請求
def handle_music_request(user_message):
    if "周杰倫" in user_message:
        return "這是周杰倫的經典歌曲，希望你喜歡～ https://www.youtube.com/watch?v=2jD5V8YVhJM"
    elif "別的" in user_message or "換一首" in user_message:
        return "試試這首新歌看看，也許會讓你感覺更放鬆：https://www.youtube.com/watch?v=UfcAVejslrU"
    else:
        return "這首歌也許能振奮你的心情：https://www.youtube.com/watch?v=ZbZSe6N_BXs"
