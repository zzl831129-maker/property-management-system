import os
import google.generativeai as genai

from tools.ledger_tool import (
    get_ledger_balance,
    get_ledger_summary,
    get_resident_daily_detail,
    get_overdrawn_residents,
)
from tools.parking_tool import (
    get_parking_info,
    get_parking_asset_summary,
    get_third_car_residents,
    get_tenant_parking_summary,
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

if not GEMINI_API_KEY:
    raise RuntimeError("缺少環境變數 GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

TOOLS_LIST = [
    get_ledger_balance,
    get_ledger_summary,
    get_resident_daily_detail,
    get_overdrawn_residents,
    get_parking_info,
    get_parking_asset_summary,
    get_third_car_residents,
    get_tenant_parking_summary,
]

def get_ai_response(user_text: str) -> str:
    try:
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            tools=TOOLS_LIST,
            system_instruction=(
                "你是社區物業管理查詢助理。"
                "使用者詢問零用金或車位資料時，優先使用提供的工具取得資料，"
                "不要自行猜測住戶、金額、車牌或車位資訊。"
                "回答請簡潔、清楚並使用繁體中文。"
            ),
        )
        chat = model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(user_text)
        return response.text or "查詢已完成，但 AI 沒有產生文字回覆。"
    except Exception as exc:
        message = str(exc).lower()
        if "429" in message or "quota" in message or "rate limit" in message:
            return "⚠️ AI 查詢額度目前已達限制，請稍後再試。資料本身沒有遺失，這是 AI API 的暫時限制。"
        return "⚠️ LINE Agent 暫時無法完成查詢，請稍後再試。"
