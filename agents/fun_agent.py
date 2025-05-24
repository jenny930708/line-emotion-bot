import requests
import random
import os

# 從環境變數取得金鑰與搜尋引擎 ID（建議用 .env 管理）
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyCtZLO51BXdvP9tsC5feXfqnpNs0EnIT9g")
GOOGLE_CX = os.getenv("GOOGLE_CSE_CX", "5727922bc758a4ec7")

def search_meme_image(query):
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": query + " site:imgur.com OR site:pinimg.com OR site:redd.it OR site:twimg.com",  # 限定常見梗圖來源
        "searchType": "image",
        "num": 10,
        "safe": "high",
    }
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        items = response.json().get("items", [])
        if not items:
            return None
        return random.choice(items)["link"]
    except Exception as e:
        print(f"[ERROR] 搜尋圖片失敗：{e}")
        return None

def handle_fun(user_message):
    if "梗圖" in user_message:
        keywords = ["台灣 梗圖", "台灣 爆笑 圖", "迷因", "笑死", "上班好累"]
        image_url = search_meme_image(random.choice(keywords))
        if image_url:
            return {
                "type": "image",
                "originalContentUrl": image_url,
                "previewImageUrl": image_url
            }
        else:
            return {
                "type": "text",
                "text": "目前找不到相關的梗圖 😢"
            }
    elif "音樂" in user_message:
        return {
            "type": "text",
            "text": "這首歌也許能振奮你的心情：https://www.youtube.com/watch?v=ZbZSe6N_BXs"
        }
    elif "影片" in user_message:
        return {
            "type": "text",
            "text": "這支短影片讓你笑一笑：https://www.youtube.com/shorts/abc123xyz"
        }
    return None

def handle_music_request(user_message):
    if "周杰倫" in user_message:
        return "這是周杰倫的經典歌曲，希望你喜歡～ https://www.youtube.com/watch?v=2jD5V8YVhJM"
    elif "別的" in user_message or "換一首" in user_message:
        return "試試這首新歌看看，也許會讓你感覺更放鬆：https://www.youtube.com/watch?v=UfcAVejslrU"
    else:
        return "這首歌也許能振奮你的心情：https://www.youtube.com/watch?v=ZbZSe6N_BXs"
