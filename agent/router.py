# 檔案路徑：agent/router.py
import os
import google.generativeai as genai

# 在這裡設定 API Key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_ai_response(user_text):
    # 在這裡匯入工具，避免循環引用
    from tools.ledger_tool import get_ledger_balance
    from tools.parking_tool import get_parking_info
    
    tools_list = [get_ledger_balance, get_parking_info]
    
    # 務必使用 1.5-flash
    model = genai.GenerativeModel(
        model_name="gemini-3.5-flash",
        tools=tools_list
    )
    
    chat = model.start_chat(enable_automatic_function_calling=True)
    response = chat.send_message(user_text)
    
    return response.text