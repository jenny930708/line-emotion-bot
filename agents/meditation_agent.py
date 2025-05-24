def handle_meditation(user_message):
    if any(keyword in user_message for keyword in ["呼吸", "放鬆", "引導", "靜心"]):
        return (
            "讓我們一起來做個簡單的放鬆練習：\n"
            "1️⃣ 請閉上眼睛，深深吸氣…… 1、2、3……\n"
            "2️⃣ 然後慢慢吐氣…… 1、2、3……\n"
            "3️⃣ 將注意力集中在你的呼吸上，讓每一次吸吐都帶走壓力與焦躁。\n"
            "\n"
            "這首背景音樂也許能幫助你更平靜：https://www.youtube.com/watch?v=inpok4MKVLM"
        )
    else:
        return (
            "想要靜心片刻嗎？你可以說「我想冥想」、「我需要放鬆」、「給我呼吸引導」等等，我就會陪你一起靜下來 🌿"
        )
