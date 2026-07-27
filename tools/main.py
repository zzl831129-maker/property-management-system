# main.py
from fastapi import FastAPI, Request
import uvicorn
import os
import openai # 假設您使用 OpenAI 作為 AI Agent 大腦
from tools.ledger_tool import get_ledger_balance
from tools.parking_tool import get_parking_info

app = FastAPI()

# 初始化 OpenAI (需確認環境變數有設定 OPENAI_API_KEY)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.get("/callback")
async def verify():
    print("收到 GET 核實請求")
    return {"status": "ok"}

@app.post("/callback")
async def handle_message(request: Request):
    data = await request.json()
    print(f"收到訊息: {data}")
    
    # 1. 解析 LINE 傳過來的文字訊息
    try:
        events = data.get("events", [])
        for event in events:
            if event["type"] == "message" and event["message"]["type"] == "text":
                user_message = event["message"]["text"]
                reply_token = event["replyToken"]
                
                # 2. 讓 AI Agent 辨識意圖與抓取關鍵字 (例如戶別、車位、車牌等)
                ai_response = ask_ai_agent(user_message)
                
                # 3. 根據 AI 判斷的結果去呼叫對應的 Python 工具函式
                result_text = execute_tool_by_intent(ai_response, user_message)
                
                # 4. 回傳給 LINE (此處可透過 LINE Messaging API 發送 reply_token)
                print(f"準備回傳 LINE 訊息: {result_text}")
                
    except Exception as e:
        print(f"處理 LINE 訊息發生錯誤: {e}")
        
    return {"status": "ok"}

def ask_ai_agent(text: str):
    """
    使用 LLM 判斷使用者的查詢意圖與關鍵字 (支援模糊搜尋與口語辨識)
    """
    prompt = f"""
    你是一個社區物業管理的 AI Agent。請分析以下使用者訊息，並判斷他的意圖。
    可用的意圖選項有：
    1. query_ledger (查詢零用金、帳戶餘額、花費)
    2. query_parking (查詢車位、車牌、車主、聯絡電話)
    3. unknown (無法辨識)

    請同時從訊息中提取出關鍵字（如戶別代號如 2F、車牌、姓名等）。
    使用者訊息："{text}"
    請以格式回傳：intent:意圖 | keyword:提取出的關鍵字或戶別
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        content = response.choices[0].message.content.strip()
        return content
    except Exception as e:
        print(f"AI Agent 解析失敗: {e}")
        return "intent:unknown | keyword:"

def execute_tool_by_intent(ai_decision: str, original_text: str):
    """
    根據 AI 解析出來的意圖與關鍵字，調用對應的 Python 函式
    """
    print(f"AI 決策結果: {ai_decision}")
    
    # 簡單拆解 AI 回傳的結構
    intent = "unknown"
    keyword = ""
    try:
        parts = ai_decision.split("|")
        intent = parts[0].replace("intent:", "").strip()
        keyword = parts[1].replace("keyword:", "").strip()
    except Exception:
        keyword = original_text # 若拆解失敗則將原文字帶入進行模糊比對

    if "ledger" in intent:
        # 調用零用金查詢工具
        return get_ledger_balance(keyword)
    elif "parking" in intent:
        # 調用車位查詢工具
        return get_parking_info(keyword)
    else:
        # 如果意圖不明確，嘗試進行全域關鍵字模糊比對
        return f"聽不太懂您的需求，您是想查詢「{original_text}」的零用金還是車位資訊呢？"

@app.api_route("/{path:path}", methods=["GET", "POST"])
async def catch_all(path: str, request: Request):
    print(f"收到不明請求: {request.method} /{path}")
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)