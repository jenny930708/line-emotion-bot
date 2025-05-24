def handle_story(user_message, user_id):
    category = extract_story_category(user_message)
    
    if category:
        story_prompt = f"請說一個{category}類型的短篇故事，大約150字，要有趣或有轉折："
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": story_prompt}]
        )
        return response.choices[0].message.content
    else:
        return "你想聽什麼類型的故事呢？例如：奇幻、療癒、搞笑、勵志… 如果都好，也可以直接說「都好」喔！"
