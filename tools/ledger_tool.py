import os
import google.generativeai as genai
from tools.ledger_tool import get_ledger_balance
from tools.parking_tool import get_parking_info

# 進行設定
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 宣告工具清單
tools_list = [get_ledger_balance, get_parking_info]

def get_ai_response(user_text):
    # 務必使用 1.5-flash，因為它對工具呼叫的支援度最好
    model = genai.GenerativeModel(
        model_name="gemini-3.5-flash",
        tools=tools_list
    )
    
    # 啟用自動工具呼叫功能
    chat = model.start_chat(enable_automatic_function_calling=True)
    
    # AI 會自動分析 user_text，如果需要，會自動呼叫 ledger_tool 或 parking_tool
    response = chat.send_message(user_text)
    
    # 直接回傳結果
    return response.text