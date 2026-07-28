from tools.ledger_tool import (
    get_ledger_balance, 
    get_ledger_summary, 
    get_resident_daily_detail, 
    get_overdrawn_residents
)

def execute_tool_by_intent(ai_decision: str, original_text: str):
    # 解析 AI 回傳的 intent 與 keyword
    # ... (省略解析過程)
    
    if intent == "query_ledger":
        return get_ledger_balance(keyword)
    elif intent == "query_summary":
        if "-" in keyword and len(keyword) >= 10:
            return get_ledger_summary(target_date=keyword)
        else:
            return get_ledger_summary(target_month=keyword if keyword else "2026-07")
    elif intent == "query_resident_detail":
        # 假設 keyword 包含戶別與日期，您可以透過簡單字串切割處理，或讓 AI 萃取出類似 "2A 2026-07-23"
        # 這裡示範簡易處理
        parts = keyword.split()
        res_id = parts[0] if len(parts) > 0 else "2A"
        date_str = parts[1] if len(parts) > 1 else "2026-07-23"
        return get_resident_daily_detail(res_id, date_str)
    elif intent == "query_overdrawn":
        return get_overdrawn_residents()

def ask_ai_agent(text: str):
    prompt = f"""
    你是一個社區物業管理的 AI Agent。請分析以下使用者訊息，並判斷他的意圖。
    可用的意圖選項有：
可用的意圖選項有：
    1. query_ledger (查詢特定住戶總餘額)
    2. query_summary (查詢社區整體日結或月結)
    3. query_resident_detail (查詢某住戶某一天的明細)
    4. query_overdrawn (查詢透支戶別)
    5. query_parking_resident (查詢特定住戶車位，例如 "查 2A車位")
    6. query_parking_summary (查詢車位總結算，例如 "車位總結算")
    7. query_third_car (查詢第三台車或特殊車位戶別，例如 "誰有三台車")
    8. query_tenant_parking (查詢租客車輛進駐清單，例如 "租客車位清單")
    9. unknown (無法辨識)

    請同時從訊息中提取出關鍵字（例如戶別、日期等）。
    使用者訊息："{text}"
    請以格式回傳：intent:意圖 | keyword:提取出的關鍵字
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