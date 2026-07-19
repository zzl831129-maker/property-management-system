# agent/router.py
from tools.ledger_tool import get_ledger_balance
from tools.parking_tool import get_parking_info
from google import genai
from config import GEMINI_API_KEY

# 宣告工具清單
tools_list = [get_ledger_balance]

def get_ai_response(user_text):
    # 將新工具加入 tools_list
    tools_list = [get_ledger_balance, get_parking_info]
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # 關鍵：在發送請求時，必須把 tools 傳進去
    response = client.models.generate_content(
        model="models/gemini-3.5-flash",
        contents=user_text,
        config={"tools": tools_list} # 這裡賦予 AI 使用權限
    )
    return response.text