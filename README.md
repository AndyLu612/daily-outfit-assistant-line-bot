# 今日穿搭小幫手 Line Bot

這是一個「今日穿搭 / 天氣提醒」期末專案。使用者可以在 LINE 詢問天氣、穿搭、是否帶傘，Dialogflow 會判斷使用者意圖，再由 Vercel 後端查詢中央氣象署開放資料並回覆生活建議。

## 目前功能

- 今日天氣查詢
- 穿搭建議
- 帶傘提醒
- 依地區查詢天氣
- 記錄使用者預設地區與查詢紀錄到 Firebase Firestore
- 以 Dialogflow fulfillment webhook 為主要流程
- 保留 LINE webhook 作為備用直接串接方式
- 沒有 API 金鑰時，會使用內建範例天氣資料，方便開發測試

## 專案架構

```text
api/
  index.py                 Vercel 入口
weather_outfit_bot/
  app.py                   Flask 主程式與 webhook
  advice.py                穿搭、帶傘、活動建議邏輯
  config.py                環境變數設定
  firebase_store.py        Firestore 讀寫
  line_api.py              LINE 回覆訊息
  weather_api.py           中央氣象署 API 查詢
secrets/
  README.md                Firebase 金鑰放置說明
requirements.txt           Python 套件
vercel.json                Vercel 部署設定
```

## 安裝

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 啟動

```bash
flask --app weather_outfit_bot.app run --port 5000
```

本機測試：

```bash
curl "http://127.0.0.1:5000/demo?text=今天台中要帶傘嗎"
curl "http://127.0.0.1:5000/demo?text=今天穿什麼&city=台中市"
```

## 需要填入的金鑰

`.env` 內可以設定：

```text
CWA_API_KEY=
DEFAULT_CITY=台中市
GOOGLE_APPLICATION_CREDENTIALS=
```

如果走 Dialogflow 串 LINE，LINE Channel access token 與 Channel secret 通常設定在 Dialogflow 的 LINE Integration，不一定要放在 Vercel。

如果暫時沒有 Firebase 或中央氣象署 API 金鑰，系統仍可用範例資料執行。正式繳交前建議至少接上中央氣象署 API。

## Dialogflow 接法

LINE Developers 的 webhook URL 使用 Dialogflow LINE Integration 提供的網址。

Dialogflow Fulfillment webhook URL 設為：

```text
https://你的-vercel網址/dialogflow
```

每個需要後端查資料的 Intent 都要開啟：

```text
Enable webhook call for this intent
```

建議建立的 Intents：

- 今日天氣查詢
- 穿搭建議
- 帶傘提醒
- 活動建議

## 備用 LINE 直連

如果不經過 Dialogflow，也可以把 LINE Developers webhook URL 設為：

```text
https://你的-vercel網址/callback
```

這種方式才需要在 Vercel 設定：

```text
LINE_CHANNEL_ACCESS_TOKEN
LINE_CHANNEL_SECRET
```
