import os
import random
import requests

# Google CSE 梗圖搜尋
def search_meme_image(query):
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_CX")
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&cx={cse_id}&searchType=image&key={api_key}"

    try:
        res = requests.get(url)
        res.raise_for_status()
        results = res.json().get("items", [])
        if results:
            return random.choice(results)["link"]
    except Exception as e:
        print("❌ 梗圖搜尋失敗：", e)

    return None

# 處理梗圖、音樂、影片等趣味請求
def handle_fun(user_message):
    if "梗圖" in user_message:
        keywords = ["療癒梗圖", "搞笑梗圖", "心情不好梗圖", "中文梗圖", "台灣迷因"]
        return search_meme_image(random.choice(keywords)) or "目前找不到梗圖 😢"

    elif "音樂" in user_message:
        return "這首歌也許能振奮你的心情：https://www.youtube.com/watch?v=ZbZSe6N_BXs"

    elif "影片" in user_message:
        return "這支短影片讓你笑一笑：https://www.youtube.com/shorts/abc123xyz"

    return "我還在學習更多有趣的內容，下次會更厲害！"

# 個人化音樂推薦
def handle_music_request(user_message):
    if "周杰倫" in user_message:
        return "這是周杰倫的經典歌曲，希望你喜歡～ https://www.youtube.com/watch?v=2jD5V8YVhJM"
    elif "別的" in user_message or "換一首" in user_message:
        return "試試這首看看，也許會讓你感覺更放鬆：https://www.youtube.com/watch?v=UfcAVejslrU"
    else:
        return "這首歌也許能讓你心情好起來～ https://www.youtube.com/watch?v=ZbZSe6N_BXs"
