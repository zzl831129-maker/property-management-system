# PropertyAI LINE Agent Fixed - 比對版

這份資料夾是比較用版本，不會修改你目前的 GitHub / Render。

## 建議架構
- line_bot_server.py：LINE Webhook 入口（Flask + LINE SDK v3）
- agent/router.py：Gemini Agent + Tool Calling
- tools/ledger_tool.py：零用金查詢工具
- tools/parking_tool.py：車位查詢工具
- services/google_sheet.py：Google Sheets 連線層

## 主要修正
1. 移除不存在的 config.py 依賴。
2. LINE Token / Secret 改讀 Render Environment Variables。
3. 移除把 Secret 印到 Logs 的除錯程式。
4. Flask 改支援 Render 的 PORT。
5. 新增 / health route。
6. 註冊現有 8 個 Tools。
7. Gemini 模型名稱改由 GEMINI_MODEL 控制。
8. Gemini 429 / quota 時回傳可理解訊息。
9. 零用金日期欄位統一為「交易日期」。
10. 租客車位改即時讀取「身分標記」。
11. Google Credentials / Sheet ID 加防呆。
12. 使用 LINE Agent 專用 requirements.txt 與 Dockerfile。

## Render 第二個 Service 環境變數
- LINE_CHANNEL_ACCESS_TOKEN
- LINE_CHANNEL_SECRET
- GEMINI_API_KEY
- GEMINI_MODEL（可選）
- GOOGLE_APPLICATION_CREDENTIALS_JSON
- LEDGER_SHEET_ID

不要把上述值 commit 到 GitHub。

## 暫不納入
- 原 main.py（FastAPI 版本）：保留為歷史版本
- 原 tools/main.py：保留為歷史草稿
- Streamlit app.py：屬於另一個 Render Web Service
