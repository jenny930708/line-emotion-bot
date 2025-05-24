import requests
from bs4 import BeautifulSoup
import random

def search_meme_image_by_yahoo(keyword="梗圖"):
    try:
        url = f"https://tw.images.search.yahoo.com/search/images?p={keyword}"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        img_tags = soup.find_all("img")
        img_urls = [img["src"] for img in img_tags if img.get("src", "").startswith("http")]
        return random.choice(img_urls) if img_urls else None
    except Exception as e:
        print("❌ 錯誤：", e)
        return None

# 測試主程式
if __name__ == "__main__":
    image_url = search_meme_image_by_yahoo()
    if image_url:
        print("✅ 成功取得圖片網址：", image_url)
    else:
        print("❌ 找不到圖片")
