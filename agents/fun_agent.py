from linebot.models import TextSendMessage, ImageSendMessage
import random

# ✅ 放上你自己上傳到 Imgur、GitHub、或圖片 CDN 的圖檔連結
MEME_IMAGES = [
    "https://i.imgur.com/Lbm90xz.png",  # 再晚我就要生氣了（你上傳圖）
    "https://i.imgur.com/Ym4TPrd.png",  # 我明明這麼可愛（你上傳圖）
    "https://i.imgur.com/S1yXD8u.png",  # 社畜都一樣（你上傳圖）
]

def handle_fun(user_message):
    if "梗圖" in user_message:
        image_url = random.choice(MEME_IMAGES)
        return ImageSendMessage(
            original_content_url=image_url,
            preview_image_url=image_url
        )
    elif "音樂" in user_message:
        return TextSendMessage(text="這首歌也許能振奮你的心情：https://www.youtube.com/watch?v=ZbZSe6N_BXs")
    elif "影片" in user_message:
        return TextSendMessage(text="這支短影片讓你笑一笑：https://www.youtube.com/shorts/abc123xyz")
    return None

def handle_music_request(user_message):
    if "周杰倫" in user_message:
        return TextSendMessage(text="這是周杰倫的經典歌曲，希望你喜歡～ https://www.youtube.com/watch?v=2jD5V8YVhJM")
    elif "別的" in user_message or "換一首" in user_message:
        return TextSendMessage(text="試試這首新歌看看，也許會讓你感覺更放鬆：https://www.youtube.com/watch?v=UfcAVejslrU")
    else:
        return TextSendMessage(text="這首歌也許能振奮你的心情：https://www.youtube.com/watch?v=ZbZSe6N_BXs")
