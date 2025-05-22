# 情緒偵測 AI LINE 機器人 🤖💬

一個可以分析情緒並用 GPT-4 回覆訊息的聊天機器人。

## 🧠 功能

- 🎯 分析文字情緒（快樂、難過、生氣、焦慮）
- 🤖 使用 GPT-4 進行情緒對話回覆
- 🎵 根據情緒與偏好推薦 YouTube 音樂
- 📝 自動註冊、修改、查詢、刪除學生資料
- 📈 發現學生連續低落情緒，自動通報導師並附圖表

## 🚀 安裝與部署

1. 安裝依賴
```bash
pip install -r requirements.txt
```

2. 設定 `.env` 檔案
```
LINE_CHANNEL_ACCESS_TOKEN=你的 Line token
LINE_CHANNEL_SECRET=你的 Line secret
OPENAI_API_KEY=你的 OpenAI API Key
SERPAPI_KEY=你的 serpapi key
PORT=5000
```

3. 啟動伺服器
```bash
python app.py
```

4. 將 Line Webhook 指向你的 `/callback` 路徑。

## 📂 專案結構
```
├── app.py               # 主程式
├── utils.py             # 情緒分析與音樂推薦邏輯
├── students.json        # 儲存學生資料（註冊學號、姓名、導師 ID）
├── memory.json          # 儲存使用者對話上下文記憶
├── logs.txt             # 記錄使用者互動與情緒
├── requirements.txt     # 依賴套件清單
├── runtime.txt / Procfile # Render 部署用檔案
└── .env                 # 環境變數檔案
```

## 🔐 功能詳述
- 註冊格式：`註冊 F1106001 張韻蓁`
- 修改格式：`修改 F1106001 新名字`
- 刪除格式：`刪除 F1106001 張韻蓁`
- 查詢註冊：輸入 `我要查詢我的註冊內容`

## 📬 LINE 通知機制
- 當學生近 7 次互動中有 5 次以上情緒為悲傷/焦慮/憤怒時，自動通知老師。

---

🔧 歡迎根據需求自由擴充 API、報表或 LINE rich menu！
