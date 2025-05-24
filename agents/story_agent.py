import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_story_category(message):
    message = message.lower()
    if "搞笑" in message:
        return "搞笑"
    if "驚悚" in message:
        return "恐怖"
    elif "療癒" in message:
        return "療癒"
    elif "奇幻" in message:
        return "奇幻"
    elif "勵志" in message:
        return "勵志"
    elif "都好" in message or "隨便" in message:
        return "隨機"
    return None

def handle_story(user_message, user_id):
    category = extract_story_category(user_message)

    if category:
        if category == "隨機":
            prompt = "請說一個有趣的短篇故事，150字內，要有情節轉折或讓人開心。"
        else:
            prompt = f"請說一個{category}類型的短篇故事，150字內，要有趣或有轉折。"

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"⚠️ 故事生成失敗：{str(e)}"

    else:
        return "你想聽什麼類型的故事呢？例如：奇幻、療癒、搞笑、勵志… 如果都好，也可以直接說「都好」喔！"
