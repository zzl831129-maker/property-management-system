import os
import google.generativeai as genai
from tools.ledger_tool import get_ledger_balance
from tools.parking_tool import get_parking_info

# 進行設定
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 宣告工具清單
tools_list = [get_ledger_balance, get_parking_info]

def get_ai_response(user_text):
    model = genai.GenerativeModel(
        model_name="models/gemini-3.5-flash", # 請確認你使用的模型名稱
        tools=tools_list
    )
    
    response = model.generate_content(user_text)
    
    # 修改這裡：檢查是否有 function_call
    if response.candidates[0].content.parts[0].function_call:
        return "AI 正在呼叫工具處理您的需求，請稍候..."
    
    return response.text