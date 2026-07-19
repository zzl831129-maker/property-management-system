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
        model_name="models/gemini-3.5-flash", 
        tools=tools_list
    )
    
    # 建立一個 chat session
    chat = model.start_chat(enable_automatic_function_calling=True)
    
    # 發送訊息並讓模型自動處理工具呼叫
    response = chat.send_message(user_text)
    
    return response.text