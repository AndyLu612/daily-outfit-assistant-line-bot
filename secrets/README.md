# Firebase 金鑰放這裡

請把 Firebase 下載的服務帳戶金鑰 JSON 放在這個資料夾，例如：

```text
secrets/firebase-service-account.json
```

然後在專案根目錄建立 `.env`，加入：

```text
GOOGLE_APPLICATION_CREDENTIALS=/Users/andylu/Documents/Codex/2026-06-10/daily-outfit-assistant-line-bot/secrets/firebase-service-account.json
```

注意：不要把 JSON 金鑰傳到 GitHub 或公開平台。
