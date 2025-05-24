import random
import json
import os

MEMORY_FILE = "memory.json"

# 讀取使用者記憶狀態
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# 儲存使用者記憶狀態
def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 產生故事開頭
def generate_story_opening(story_type):
    if story_type == "奇幻":
        return "在一片被魔法籠罩的森林裡，一位年輕的法師正在尋找一把傳說中的寶劍……"
    elif story_type == "療癒":
        return "在一個被陽光溫柔照耀的小鎮，一位老奶奶開了一間讓人安心的貓咪咖啡廳……"
    elif story_type == "勵志":
        return "從前有個總是考試不及格的學生，某天他下定決心開始改變……"
    elif story_type == "搞笑":
        return "有一天，一隻鴨子走進了便利商店，竟然開口問：『有賣牙刷嗎？』"
    else:
        return "從前從前，有一個神祕的故事正要開始……"

# 主邏輯：處理故事請求
def handle_story(user_message, user_id):
    memory = load_memory()
    user_state = memory.get(user_id, {})

    # 初次提及故事：詢問想聽什麼類型
    if user_state.get("mode") != "story_selecting" and user_state.get("mode") != "story_telling":
        memory[user_id] = {"mode": "story_selecting"}
        save_memory(memory)
        return "你想聽什麼類型的故事呢？例如：奇幻、療癒、搞笑、勵志… 如果都好，也可以直接說「都好」喔！"

    # 使用者正在選擇類型
    elif user_state.get("mode") == "story_selecting":
        selected = user_message.strip()
        if selected == "都好":
            selected = random.choice(["奇幻", "療癒", "搞笑", "勵志"])

        story = generate_story_opening(selected)
        memory[user_id] = {
            "mode": "story_telling",
            "type": selected,
            "content": story
        }
        save_memory(memory)
        return story

    # 已經在講故事中（可擴充讓使用者回應時繼續接故事）
    elif user_state.get("mode") == "story_telling":
        return "這個故事還沒寫完呢，不如你也說說看接下來發生了什麼？或者你想換一個故事類型嗎？"

    return "我不太確定你想聽什麼故事，再說一次好嗎？"
