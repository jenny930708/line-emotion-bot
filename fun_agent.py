def handle_fun(user_message):
    if "梗圖" in user_message:
        return "這張貓貓圖是不是很療癒？https://i.imgur.com/Jt6plWY.jpeg"
    elif "音樂" in user_message:
        return "這首歌也許能振奮你的心情：https://www.youtube.com/watch?v=ZbZSe6N_BXs"
    elif "影片" in user_message:
        return "這支短影片讓你笑一笑：https://www.youtube.com/shorts/abc123xyz"
    return None