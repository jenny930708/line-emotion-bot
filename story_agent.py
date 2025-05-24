def handle_story(user_message, user_id):
    if "故事" in user_message or "說故事" in user_message:
        return "從前從前，有一隻不會飛的小鳥……你想牠接下來遇到什麼事呢？"
    return None