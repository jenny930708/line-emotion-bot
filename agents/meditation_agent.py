def handle_meditation(user_message):
    if any(keyword in user_message for keyword in ["語音", "聲音", "聽冥想"]):
        return (
            "這是適合靜心的語音冥想引導音檔（約1分鐘）：\n"
            "🔊 https://www.youtube.com/watch?v=MIr3RsUWrdo\n"
            "找個安靜的地方，跟著聲音一起深呼吸吧 🌙"
        )
    
    elif any(keyword in user_message for keyword in ["呼吸", "放鬆", "冥想", "引導", "靜心"]):
        return (
            "好的，我們一起進行一段簡短的冥想練習 🌿：\n\n"
            "🧘‍♀️ **第一步：姿勢準備**\n"
            "請坐直或躺下，放鬆你的肩膀。\n\n"
            "🌬️ **第二步：呼吸節奏**\n"
            "吸氣…… 1、2、3、4\n"
            "停留…… 1、2\n"
            "吐氣…… 1、2、3、4\n\n"
            "💭 **第三步：專注當下**\n"
            "感受空氣進出你的鼻腔，每一次呼吸都帶來安定和平靜。\n\n"
            "🎵 想搭配輕音樂嗎？試試這個：\n"
            "https://www.youtube.com/watch?v=inpok4MKVLM"
        )
    
    else:
        return (
            "想來一段冥想練習嗎？\n"
            "你可以說：「我想冥想」、「給我一段語音引導」、「來個呼吸練習」等等，我會陪著你一起靜下來 💆‍♀️"
        )
