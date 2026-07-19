import os
import google.generativeai as genai

# 進行設定
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_ai_response(user_text):
    # 將 import 放在函式內部，確保完全不會有循環引用
    from tools.ledger_tool import get_ledger_balance
    from tools.parking_tool import get_parking_info
    
    tools_list = [get_ledger_balance, get_parking_info]
    
    model = genai.GenerativeModel(
        model_name="gemini-3.5-flash",
        tools=tools_list
    )
    
    chat = model.start_chat(enable_automatic_function_calling=True)
    response = chat.send_message(user_text)
    
    return response.text