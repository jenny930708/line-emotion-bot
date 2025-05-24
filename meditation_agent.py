def handle_meditation(user_message):
    if "呼吸" in user_message or "放鬆" in user_message:
        return "讓我們一起來進行呼吸練習：吸氣 1…2…3，吐氣 1…2…3…"
    return "這是你可以放鬆的冥想音樂：https://www.youtube.com/watch?v=inpok4MKVLM"