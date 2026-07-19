import os
import google.generativeai as genai
from tools.ledger_tool import get_ledger_balance
from tools.parking_tool import get_parking_info

# 進行設定
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 宣告工具清單
tools_list = [get_ledger_balance, get_parking_info]

def get_ai_response(user_text):
    # 使用模型直接進行生成，不需要建立 client
    model = genai.GenerativeModel(
        model_name="models/gemini-3.5-flash",
        tools=tools_list
    )
    
    response = model.generate_content(user_text)
    return response.text