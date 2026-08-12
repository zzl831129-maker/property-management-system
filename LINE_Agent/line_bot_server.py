import os
import re
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from agent.router import get_ai_response

app = Flask(__name__)

LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if not LINE_ACCESS_TOKEN:
    raise RuntimeError("缺少環境變數 LINE_CHANNEL_ACCESS_TOKEN")
if not LINE_CHANNEL_SECRET:
    raise RuntimeError("缺少環境變數 LINE_CHANNEL_SECRET")

configuration = Configuration(access_token=LINE_ACCESS_TOKEN)
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


# ============================================================
# 基礎工具
# ============================================================

def _extract_resident_id(text: str):
    match = re.search(r"(?<!\d)(\d{1,3})\s*([A-Za-z])(?![A-Za-z])", text or "")
    if not match:
        return None
    return f"{match.group(1)}{match.group(2).upper()}"


def _money_from_line(text: str, label: str):
    """
    從目前 ledger_tool 的漂亮純文字結果抓金額。
    例如：
    💰 目前餘額  $3,897
    """
    pattern = rf"{re.escape(label)}\s+\$?(-?[\d,]+)"
    match = re.search(pattern, text)
    return match.group(1) if match else "—"


def _bubble(header, body_contents, footer_contents=None):
    bubble = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "paddingAll": "20px",
            "contents": [
                {
                    "type": "text",
                    "text": header,
                    "weight": "bold",
                    "size": "xl",
                    "wrap": True,
                }
            ],
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "paddingAll": "20px",
            "contents": body_contents,
        },
    }

    if footer_contents:
        bubble["footer"] = {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "paddingAll": "16px",
            "contents": footer_contents,
        }

    return bubble


def _label_value(label, value, emphasize=False):
    return {
        "type": "box",
        "layout": "horizontal",
        "contents": [
            {
                "type": "text",
                "text": label,
                "size": "sm",
                "flex": 4,
                "wrap": True,
            },
            {
                "type": "text",
                "text": value,
                "size": "lg" if emphasize else "sm",
                "weight": "bold" if emphasize else "regular",
                "align": "end",
                "flex": 6,
                "wrap": True,
            },
        ],
    }


def _separator():
    return {"type": "separator", "margin": "md"}


def _hint(text):
    return {
        "type": "text",
        "text": text,
        "size": "xs",
        "wrap": True,
        "margin": "md",
    }


# ============================================================
# Flex：零用金摘要
# ============================================================

def _build_ledger_flex(user_text: str, reply_text: str):
    resident_id = _extract_resident_id(user_text)
    if not resident_id:
        return None

    # 只把「單戶餘額摘要」轉成卡片；明細/日結/月結維持純文字
    if f"【{resident_id}｜零用金摘要】" not in reply_text:
        return None

    balance = _money_from_line(reply_text, "目前餘額")
    income = _money_from_line(reply_text, "累計收入")
    expense = _money_from_line(reply_text, "累計支出")
    status = "已透支" if "已透支" in reply_text else "餘額正常"

    body = [
        {
            "type": "text",
            "text": "目前可用餘額",
            "size": "sm",
        },
        {
            "type": "text",
            "text": f"NT$ {balance}",
            "size": "xxl",
            "weight": "bold",
            "margin": "sm",
        },
        _separator(),
        _label_value("累計收入", f"NT$ {income}"),
        _label_value("累計支出", f"NT$ {expense}"),
        _separator(),
        _label_value("帳務狀態", status, emphasize=True),
        _hint("資料來源：Google Sheet 即時查詢"),
    ]

    return _bubble(
        f"🏠 {resident_id}｜零用金",
        body,
    )


# ============================================================
# Flex：單戶車位
# ============================================================

def _parse_parking_blocks(reply_text: str):
    blocks = re.split(r"\n\s*\n", reply_text)
    vehicles = []

    for block in blocks:
        if not re.search(r"(🚗|🛵|🅿️)\s*車輛\s*\d+", block):
            continue

        def get_value(label):
            match = re.search(rf"{label}｜(.+)", block)
            return match.group(1).strip() if match else "—"

        icon_match = re.search(r"(🚗|🛵|🅿️)", block)

        vehicles.append({
            "icon": icon_match.group(1) if icon_match else "🅿️",
            "space": get_value("車位"),
            "plate": get_value("車牌"),
            "owner": get_value("車主"),
            "identity": get_value("身分"),
        })

    return vehicles


def _build_parking_flex(user_text: str, reply_text: str):
    resident_id = _extract_resident_id(user_text)
    if not resident_id:
        return None

    if f"【{resident_id}｜車位資訊" not in reply_text:
        return None

    vehicles = _parse_parking_blocks(reply_text)
    if not vehicles:
        return None

    contents = []

    for index, vehicle in enumerate(vehicles, start=1):
        if index > 1:
            contents.append(_separator())

        contents.extend([
            {
                "type": "text",
                "text": f"{vehicle['icon']} 車輛 {index}",
                "weight": "bold",
                "size": "md",
                "margin": "md" if index > 1 else "none",
            },
            _label_value("車位", vehicle["space"], emphasize=True),
            _label_value("車牌", vehicle["plate"]),
            _label_value("車主", vehicle["owner"]),
            _label_value("身分", vehicle["identity"]),
        ])

    contents.append(_hint("資料來源：Google Sheet 即時查詢"))

    return _bubble(
        f"🏠 {resident_id}｜車位資訊",
        contents,
    )


# ============================================================
# Flex：管理摘要
# ============================================================

def _build_summary_flex(reply_text: str):
    # 車位總覽
    if "【社區車位總覽】" in reply_text:
        def grab(label):
            match = re.search(rf"{label}\s+(\d+)\s*筆", reply_text)
            return match.group(1) if match else "0"

        body = [
            _label_value("🚗 汽車登記", f"{grab('汽車登記')} 筆", True),
            _label_value("🛵 機車登記", f"{grab('機車登記')} 筆", True),
            _label_value("🔑 租客車輛", f"{grab('租客車輛')} 筆"),
            _separator(),
            _label_value("📋 全部紀錄", f"{grab('全部紀錄')} 筆", True),
            _hint("社區車位資料即時統計"),
        ]
        return _bubble("🅿️ 社區車位總覽", body)

    # 零用金月結
    month_match = re.search(r"【(.+?)｜零用金月結】", reply_text)
    if month_match:
        month = month_match.group(1)
        income = _money_from_line(reply_text, "本月收入")
        expense = _money_from_line(reply_text, "本月支出")
        net = _money_from_line(reply_text, "淨變動")

        count_match = re.search(r"交易筆數\s+(\d+)\s*筆", reply_text)
        count = count_match.group(1) if count_match else "—"

        body = [
            _label_value("📥 本月收入", f"NT$ {income}"),
            _label_value("📤 本月支出", f"NT$ {expense}"),
            _separator(),
            _label_value("💰 淨變動", f"NT$ {net}", True),
            _label_value("🧾 交易筆數", f"{count} 筆"),
            _hint("資料來源：Google Sheet 即時統計"),
        ]
        return _bubble(f"📊 {month}｜零用金月結", body)

    return None


# ============================================================
# 決定 LINE 要回純文字還是 Flex
# ============================================================

def _build_reply_message(user_text: str, reply_text: str):
    """
    混合模式：
    - 單戶零用金摘要 -> Flex
    - 單戶車位 -> Flex
    - 車位總覽 / 零用金月結 -> Flex
    - 長明細、錯誤、防呆、Gemini -> Text
    """
    try:
        flex_json = (
            _build_ledger_flex(user_text, reply_text)
            or _build_parking_flex(user_text, reply_text)
            or _build_summary_flex(reply_text)
        )

        if flex_json:
            return FlexMessage(
                alt_text="SmartProp 查詢結果",
                contents=FlexContainer.from_dict(flex_json),
            )

    except Exception as exc:
        # Flex 解析失敗不影響服務，直接退回純文字
        print("Flex Message Error:", type(exc).__name__, str(exc))

    return TextMessage(text=reply_text)


# ============================================================
# Flask / LINE Webhook
# ============================================================

@app.get("/")
def health():
    return "PropertyAI LINE Agent is running", 200


@app.post("/callback")
def callback():
    signature = request.headers.get("X-Line-Signature")
    if not signature:
        abort(400)

    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK", 200


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text.strip()

    reply_text = (
        get_ai_response(user_text)
        if user_text
        else "請輸入要查詢的內容，例如：查 8A 零用金、查 8A 車位。"
    )

    reply_message = _build_reply_message(user_text, reply_text)

    line_bot_api.reply_message(
        ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[reply_message],
        )
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
