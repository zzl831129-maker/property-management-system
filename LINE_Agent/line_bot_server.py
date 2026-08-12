import os
import re
import time
import threading
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


app = Flask(__name__)

# ============================================================
# Lazy Load Router
# ============================================================

_router_get_ai_response = None
_router_import_error = None


def _get_router_handler():
    """
    延遲載入 agent.router。
    目的：讓 Flask/Gunicorn 先完成啟動與綁定 PORT，
    避免 Render 部署時因 Gemini / Google Sheet 模組初始化較慢而 timeout。
    """
    global _router_get_ai_response, _router_import_error

    if _router_get_ai_response is not None:
        return _router_get_ai_response

    if _router_import_error is not None:
        raise RuntimeError(
            f"Router 載入失敗：{_router_import_error}"
        )

    try:
        from agent.router import get_ai_response as handler
        _router_get_ai_response = handler
        print("Router lazy-loaded successfully")
        return _router_get_ai_response
    except Exception as exc:
        _router_import_error = f"{type(exc).__name__}: {exc}"
        print("Router lazy-load failed:", _router_import_error)
        raise


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
# LINE 使用者對話上下文
# ============================================================

SESSION_TTL_SECONDS = int(os.getenv("LINE_CONTEXT_TTL_SECONDS", "900"))
_session_lock = threading.Lock()
_user_sessions = {}


def _line_user_key(event):
    """取得 LINE 對話來源識別；user > group > room。"""
    source = getattr(event, "source", None)
    if source is None:
        return "unknown"

    for attr in ("user_id", "group_id", "room_id"):
        value = getattr(source, attr, None)
        if value:
            return f"{attr}:{value}"

    return "unknown"


def _get_context_resident(user_key):
    now = time.time()
    with _session_lock:
        session = _user_sessions.get(user_key)
        if not session:
            return None

        if now - session.get("updated_at", 0) > SESSION_TTL_SECONDS:
            _user_sessions.pop(user_key, None)
            return None

        return session.get("resident_id")


def _set_context_resident(user_key, resident_id):
    if not resident_id or user_key == "unknown":
        return

    with _session_lock:
        _user_sessions[user_key] = {
            "resident_id": resident_id,
            "updated_at": time.time(),
        }


def _clear_context(user_key):
    with _session_lock:
        _user_sessions.pop(user_key, None)



def _should_remember_resident_context(user_text, reply_text, explicit_resident_id):
    """
    只有真的在查某一戶時才記住上下文。
    不因一般公告、寒暄、管理型統計而更新記憶。
    """
    text = str(user_text or "")
    reply = str(reply_text or "")

    # 明確輸入戶別，且內容看起來是在查該戶
    resident_query_words = [
        "查", "查詢", "查看", "看一下", "資料", "資訊", "住戶",
        "零用金", "餘額", "交易", "明細",
        "車位", "車牌", "車輛", "停哪", "幾台",
    ]

    if explicit_resident_id and any(word in text for word in resident_query_words):
        return True

    # 反向搜尋成功查到某一戶
    if "【反向查詢結果】" in reply and "戶別｜" in reply:
        return True

    # 住戶總覽 / 單戶專項查詢成功
    if any(tag in reply for tag in [
        "｜住戶資訊總覽】",
        "｜零用金摘要】",
        "｜車位資訊",
        "｜車輛統計】",
    ]):
        return True

    return False


def _is_context_clear_command(text):
    compact = re.sub(r"\s+", "", text or "")
    return compact in {
        "清除上下文", "清除記憶", "清除记忆",
        "重新開始", "重新开始", "重來", "重来",
        "忘記剛剛", "忘记刚刚",
    }


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
# Flex：住戶資訊總覽
# ============================================================

def _build_resident_overview_flex(user_text: str, reply_text: str):
    """
    專門處理：
    查1A / 1A資料 / 查詢2A住戶

    即使該戶沒有車，也會顯示「目前無車位 / 車輛登記」，
    不會退化成只顯示零用金卡。
    """
    resident_id = _extract_resident_id(user_text)
    if not resident_id:
        return None

    if f"【{resident_id}｜住戶資訊總覽】" not in reply_text:
        return None

    # ---- 零用金 ----
    balance = _money_from_line(reply_text, "目前餘額")
    income = _money_from_line(reply_text, "累計收入")
    expense = _money_from_line(reply_text, "累計支出")
    ledger_status = "已透支" if "🔴 已透支" in reply_text else "餘額正常"

    body = [
        {
            "type": "text",
            "text": "💰 零用金",
            "weight": "bold",
            "size": "md",
        },
        _label_value("目前餘額", f"NT$ {balance}", True),
        _label_value("累計收入", f"NT$ {income}"),
        _label_value("累計支出", f"NT$ {expense}"),
        _label_value("帳務狀態", ledger_status),
        _separator(),
        {
            "type": "text",
            "text": "🅿️ 車位 / 車輛",
            "weight": "bold",
            "size": "md",
            "margin": "md",
        },
    ]

    # ---- 車位 ----
    no_parking = (
        "目前無車位登記紀錄" in reply_text
        or f"【{resident_id}｜車位查詢】" in reply_text
    )

    vehicles = _parse_parking_blocks(reply_text)

    if no_parking or not vehicles:
        body.append({
            "type": "text",
            "text": "目前無車位 / 車輛登記",
            "size": "sm",
            "wrap": True,
            "margin": "sm",
        })
    else:
        for index, vehicle in enumerate(vehicles, start=1):
            if index > 1:
                body.append({
                    "type": "separator",
                    "margin": "md",
                })

            body.extend([
                {
                    "type": "text",
                    "text": f"{vehicle['icon']} 車輛 {index}",
                    "weight": "bold",
                    "size": "sm",
                    "margin": "md" if index > 1 else "sm",
                },
                _label_value("車位", vehicle["space"], True),
                _label_value("車牌", vehicle["plate"]),
                _label_value("身分", vehicle["identity"]),
            ])

    body.extend([
        _separator(),
        _hint("資料來源：Google Sheet 即時查詢"),
    ])

    return _bubble(
        f"🏠 {resident_id}｜住戶資訊",
        body,
    )


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
            _build_resident_overview_flex(user_text, reply_text)
            or _build_ledger_flex(user_text, reply_text)
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


@app.get("/healthz")
def healthz():
    return {"status": "ok"}, 200


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
    user_key = _line_user_key(event)

    if not user_text:
        reply_text = "請輸入要查詢的內容，例如：查 8A 零用金、查 8A 車位。"
        effective_user_text = user_text
    elif _is_context_clear_command(user_text):
        _clear_context(user_key)
        reply_text = "✅ 已清除目前住戶對話上下文。"
        effective_user_text = user_text
    else:
        explicit_resident_id = _extract_resident_id(user_text)
        context_resident_id = _get_context_resident(user_key)

        # 明確輸入新戶別時，這一句查詢本身以新戶別為準；
        # 但是否真正更新記憶，要等確認這是一個住戶查詢後再決定。
        query_context_resident_id = explicit_resident_id or context_resident_id

        router_handler = _get_router_handler()
        reply_text = router_handler(
            user_text,
            context_resident_id=query_context_resident_id,
        )

        # 若本句沒戶別但使用了上下文，Flex 仍需要戶別才能正確產卡。
        effective_user_text = user_text
        if not explicit_resident_id and context_resident_id:
            effective_user_text = f"{context_resident_id} {user_text}"

        # 只有真正的住戶查詢成功後才更新上下文。
        result_resident = _extract_resident_id(reply_text)
        remembered_resident = explicit_resident_id or result_resident

        if (
            remembered_resident
            and _should_remember_resident_context(
                user_text,
                reply_text,
                explicit_resident_id,
            )
        ):
            _set_context_resident(user_key, remembered_resident)

    reply_message = _build_reply_message(effective_user_text, reply_text)

    line_bot_api.reply_message(
        ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[reply_message],
        )
    )



if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
