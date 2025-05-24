def handle_fun(user_message):
    if "梗圖" in user_message:
        return "這張貓貓圖是不是很療癒？https://i.imgur.com/Jt6plWY.jpeg"
    elif "音樂" in user_message:
        return "這首歌也許能振奮你的心情：https://www.youtube.com/watch?v=ZbZSe6N_BXs"
    elif "影片" in user_message:
        return "這支短影片讓你笑一笑：https://www.youtube.com/shorts/abc123xyz"
    return None
def handle_music_request(user_message):
    if "周杰倫" in user_message:
        return "這是周杰倫的經典歌曲，希望你喜歡～ https://www.youtube.com/watch?v=2jD5V8YVhJM"
    elif "別的" in user_message or "換一首" in user_message:
        return "試試這首新歌看看，也許會讓你感覺更放鬆：https://www.youtube.com/watch?v=UfcAVejslrU"
    else:
        return "這首歌也許能振奮你的心情：https://www.youtube.com/watch?v=ZbZSe6N_BXs"
