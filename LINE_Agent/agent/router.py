import re
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

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
        # 第一階段測試：
        # 只要使用者提到「零用金」，直接查詢 1A
        # 暫時繞過 Gemini，確認 Google Sheet 查詢功能是否正常
       # 從使用者訊息抓戶別，例如 1A、2B、12C
  # 從使用者訊息抓戶別，例如：1A、2B、12C
        resident_match = re.search(r"(\d+\s*[A-Za-z])", user_text)

        if resident_match:
            resident_id = resident_match.group().replace(" ", "").upper()

            if "零用金" in user_text:
                return str(get_ledger_balance(resident_id))

            if "車位" in user_text:
                return str(get_parking_info(resident_id))

        # 有查詢意圖，但沒有提供戶別
        if "零用金" in user_text:
            return "請提供戶別，例如：查詢 1A 零用金。"

        if "車位" in user_text:
            return "請提供戶別，例如：查詢 2A 車位。"

        # 其他問題才交給 Gemini
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

        chat = model.start_chat(
            enable_automatic_function_calling=True
        )

        response = chat.send_message(user_text)

        return response.text or "查詢已完成，但 AI 沒有產生文字回覆。"

    except Exception as exc:
        print(f"LINE Agent Error: {exc}")

        message = str(exc).lower()

        if "429" in message or "quota" in message or "rate limit" in message:
            return "⚠️ AI 查詢額度目前已達限制，請稍後再試。"

        return f"⚠️ LINE Agent 查詢失敗：{exc}"
