import os
import google.generativeai as genai

# 進行設定
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_ai_response(user_text):
    # 這裡將 import 移到函式內部，已成功解決循環引用問題
    from tools.ledger_tool import get_ledger_balance
    from tools.parking_tool import get_parking_info
    
    tools_list = [get_ledger_balance, get_parking_info]
    
    # 【修正重點】：模型名稱必須是 gemini-1.5-flash
    model = genai.GenerativeModel(
        model_name="gemini-3.5-flash",
        tools=tools_list
    )
    
    # 啟用自動工具呼叫功能
    chat = model.start_chat(enable_automatic_function_calling=True)
    
    # AI 會自動分析 user_text 並執行對應工具
    response = chat.send_message(user_text)
    
    return response.text