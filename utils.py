# utils.py
import random

def detect_emotion(text):
    keywords = {
        "開心": ["開心", "快樂", "興奮", "開朗", "爽"],
        "難過": ["難過", "悲傷", "沮喪", "失落", "心情不好"],
        "生氣": ["生氣", "憤怒", "火大", "爆炸", "煩"],
        "焦慮": ["緊張", "焦慮", "擔心", "不安", "壓力"]
    }
    for emotion, words in keywords.items():
        if any(word in text for word in words):
            return emotion
    return "中性"

def suggest_music(emotion, user_text):
    links = {
        "開心": [
            "https://www.youtube.com/watch?v=ZbZSe6N_BXs",  # Happy
            "https://www.youtube.com/watch?v=d-diB65scQU"   # Walking on Sunshine
        ],
        "難過": [
            "https://www.youtube.com/watch?v=RgKAFK5djSk",  # See You Again
            "https://www.youtube.com/watch?v=uelHwf8o7_U"   # Love the Way You Lie
        ],
        "生氣": [
            "https://www.youtube.com/watch?v=9WbCfHutDSE",  # Calm down music
            "https://www.youtube.com/watch?v=ffxKSjUwKdU"   # Chill piano
        ],
        "焦慮": [
            "https://www.youtube.com/watch?v=2OEL4P1Rz04",  # Lo-fi relax
            "https://www.youtube.com/watch?v=5qap5aO4i9A"   # Lo-fi beats
        ],
        "中性": [
            "https://www.youtube.com/watch?v=5qap5aO4i9A",  # Lo-fi neutral
            "https://www.youtube.com/watch?v=fEvM-OUbaKs"   # Relaxing music
        ]
    }

    lang = "中文" if any(c in user_text for c in "你好我是中文音樂") else "英文"
    if "周杰倫" in user_text:
        return "https://www.youtube.com/results?search_query=周杰倫+歌曲"
    elif "英文" in user_text:
        return "https://www.youtube.com/results?search_query=english+pop+music"
    elif "中文" in user_text:
        return "https://www.youtube.com/results?search_query=中文流行音樂"

    return random.choice(links.get(emotion, links["中性"]))
