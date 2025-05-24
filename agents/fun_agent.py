import os
import random
import requests
from linebot.models import TextSendMessage, ImageSendMessage

# 搜尋 Google 圖片 API
def search_meme_image(query="梗圖"):  # 預設為「梗圖」
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_CX")

    if not api_key or not cse_id:
        return None

    url = f"https://www.googleapis.com/customsearch/v1?q={query}&cx={cse_id}&searchType=image&key={api_key}"

    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        items = data.get("items", [])
        if items:
            return random.choice(items)["link"]
    except Exception as e:
        print(f"[錯誤] 圖片搜尋失敗：{e}")

    return None

# 處理娛樂請求
def handle_fun(user_message):
    if "梗圖" in user_message:
        image_url = search_meme_image("梗圖")  # 預設搜尋詞
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
