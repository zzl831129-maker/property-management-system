import re
import os
import pandas as pd
from services.google_sheet import get_sheet_data

LEDGER_SHEET_ID = os.getenv("LEDGER_SHEET_ID")


def _parking_df():
    data = get_sheet_data(LEDGER_SHEET_ID, "車位登記")
    return pd.DataFrame(data) if data else pd.DataFrame()


def _clean(value, default="—"):
    text = str(value if value is not None else "").strip()
    if not text or text.lower() in {"nan", "none"}:
        return default
    return text


def _vehicle_icon(space_no):
    text = str(space_no)
    if "機車" in text:
        return "🛵"
    if "汽車" in text or text.startswith(("B1-", "B2-", "B3-")):
        return "🚗"
    return "🅿️"


def get_parking_info(resident_id: str):
    df = _parking_df()
    if df.empty:
        return "📭 目前無車位登記資料。"

    resident_id = str(resident_id).strip().upper()
    results = df[df["戶別"].astype(str).str.strip().str.upper() == resident_id]

    if results.empty:
        return f"🔎【{resident_id}｜車位查詢】\n目前無車位登記紀錄。"

    cards = []
    for index, (_, row) in enumerate(results.iterrows(), start=1):
        space = _clean(row.get("車位號碼"))
        plate = _clean(row.get("車牌號碼"))
        owner = _clean(row.get("車主姓名"))
        phone = _format_phone(row.get("連絡電話"))
        identity = _clean(row.get("身分標記"))
        note = _clean(row.get("車輛備註"), default="")
        icon = _vehicle_icon(space)

        lines = [
            f"{icon} 車輛 {index}",
            f"車位｜{space}",
            f"車牌｜{plate}",
            f"車主｜{owner}",
            f"身分｜{identity}",
            f"電話｜{phone}",
        ]
        if note:
            lines.append(f"備註｜{note}")
        cards.append("\n".join(lines))

    return f"🏠【{resident_id}｜車位資訊｜共 {len(results)} 筆】\n━━━━━━━━━━━━\n" + "\n\n".join(cards)


def get_parking_asset_summary():
    df = _parking_df()
    if df.empty:
        return "📭 目前無車位登記資料。"

    total = len(df)
    car_mask = df["車位號碼"].astype(str).str.contains("汽車|B1-|B2-|B3-", regex=True, na=False)
    moto_mask = df["車位號碼"].astype(str).str.contains("機車", regex=False, na=False)
    car_count = int(car_mask.sum())
    moto_count = int(moto_mask.sum())
    tenant_count = int((df["身分標記"].astype(str).str.strip() == "租客").sum()) if "身分標記" in df.columns else 0

    return (
        "🅿️【社區車位總覽】\n"
        "━━━━━━━━━━━━\n"
        f"🚗 汽車登記  {car_count} 筆\n"
        f"🛵 機車登記  {moto_count} 筆\n"
        f"🔑 租客車輛  {tenant_count} 筆\n"
        f"📋 全部紀錄  {total} 筆\n"
        "━━━━━━━━━━━━"
    )


def get_third_car_residents():
    df = _parking_df()
    if df.empty:
        return "📭 目前無車位登記資料。"
    if "戶別" not in df.columns:
        return "⚠️ 找不到「戶別」欄位。"

    counts = df["戶別"].astype(str).str.strip().value_counts()
    third = counts[counts >= 3].sort_values(ascending=False)

    if third.empty:
        return "✅【第三台車清查】\n目前無住戶登記 3 台或以上車輛。"

    lines = [f"{index}. {resident} 戶｜{count} 台" for index, (resident, count) in enumerate(third.items(), start=1)]
    return f"⚠️【第三台車清查｜共 {len(third)} 戶】\n━━━━━━━━━━━━\n" + "\n".join(lines)


def get_tenant_parking_summary():
    df = _parking_df()
    if df.empty:
        return "📭 目前無車位登記資料。"
    if "身分標記" not in df.columns:
        return "⚠️ 車位登記缺少「身分標記」欄位。"

    tenants = df[df["身分標記"].astype(str).str.strip() == "租客"]
    if tenants.empty:
        return "✅【租客車輛清查】\n目前無租客車輛登記。"

    grouped = tenants.groupby("戶別").size().sort_values(ascending=False)
    lines = [f"{index}. {resident} 戶｜{count} 台" for index, (resident, count) in enumerate(grouped.items(), start=1)]
    return f"🔑【租客車輛清查｜共 {len(grouped)} 戶】\n━━━━━━━━━━━━\n" + "\n".join(lines)

def get_resident_overview_parking(resident_id: str):
    """住戶整合查詢用：回傳該戶車位資訊。"""
    return get_parking_info(resident_id)

def _normalize_plate(value):
    return re.sub(r"[^A-Za-z0-9]", "", str(value or "")).upper()


def _normalize_phone(value):
    digits = re.sub(r"\D", "", str(value or ""))
    # Google Sheet 若把台灣手機前導 0 吃掉，統一比對末 9 碼
    return digits[-9:] if len(digits) >= 9 else digits


def _format_phone(value):
    """顯示用：補回台灣手機前導 0，並格式化為 09xx-xxx-xxx。"""
    raw = str(value if value is not None else "").strip()
    raw = re.sub(r"\.0$", "", raw)
    digits = re.sub(r"\D", "", raw)

    if len(digits) == 9 and digits.startswith("9"):
        digits = "0" + digits

    if len(digits) == 10 and digits.startswith("09"):
        return f"{digits[:4]}-{digits[4:7]}-{digits[7:]}"

    return raw if raw else "—"



def _canonical_space(value):
    """將不同車位寫法統一成可精確比對格式。"""
    text = str(value or "").strip().upper()
    text = text.replace("（", "(").replace("）", ")")
    text = re.sub(r"[\s_]", "", text)

    car = re.search(r"(?:汽車位)?\(?B([123])\)?-?(\d+)$", text)
    if car:
        return f"B{car.group(1)}-{car.group(2)}"

    moto = re.search(r"(?:機車位)?(\d+(?:-\d+)?)$", text)
    if "機車" in text and moto:
        return f"機車位{moto.group(1)}"

    return text


def _format_parking_result(row):
    resident = _clean(row.get("戶別"))
    space = _clean(row.get("車位號碼"))
    plate = _clean(row.get("車牌號碼"))
    owner = _clean(row.get("車主姓名"))
    phone = _format_phone(row.get("連絡電話"))
    identity = _clean(row.get("身分標記"))
    icon = _vehicle_icon(space)

    return (
        f"{icon}【反向查詢結果】\n"
        f"戶別｜{resident}\n"
        f"車位｜{space}\n"
        f"車牌｜{plate}\n"
        f"車主｜{owner}\n"
        f"身分｜{identity}\n"
        f"電話｜{phone}"
    )


def search_parking_by_plate(plate: str):
    """輸入車牌反查戶別、車位、車主與聯絡資訊。"""
    df = _parking_df()
    if df.empty:
        return "📭 目前無車位登記資料。"

    target = _normalize_plate(plate)
    if not target:
        return "請提供有效車牌，例如：BQV9969。"

    matches = df[
        df["車牌號碼"].astype(str).apply(_normalize_plate) == target
    ]

    if matches.empty:
        return f"🔎 查無車牌「{plate}」的登記資料。"

    return "\n\n".join(_format_parking_result(row) for _, row in matches.iterrows())


def search_parking_by_space(space_keyword: str):
    """車位反查：完整車位精確匹配，不用包含搜尋。"""
    df = _parking_df()
    if df.empty:
        return "📭 目前無車位登記資料。"

    raw = str(space_keyword or "").strip()
    if not raw:
        return "請提供車位，例如：B3-33、機車位23-1。"

    target = _canonical_space(raw)
    normalized = df["車位號碼"].astype(str).apply(_canonical_space)
    matches = df[normalized == target]

    if matches.empty:
        return f"🔎 查無車位「{space_keyword}」的登記資料。"

    return "\n\n".join(_format_parking_result(row) for _, row in matches.iterrows())

def search_parking_by_phone(phone: str):
    """輸入聯絡電話反查戶別與車輛資料。"""
    df = _parking_df()
    if df.empty:
        return "📭 目前無車位登記資料。"

    target = _normalize_phone(phone)
    if len(target) < 7:
        return "請提供較完整的電話號碼。"

    matches = df[
        df["連絡電話"].astype(str).apply(_normalize_phone) == target
    ]

    if matches.empty:
        return f"🔎 查無電話「{phone}」的車位登記資料。"

    return "\n\n".join(_format_parking_result(row) for _, row in matches.iterrows())


def search_parking_registry(keyword: str):
    """萬用反向查詢：自動判斷電話、車牌、車位。"""
    text = str(keyword or "").strip()

    digits = re.sub(r"\D", "", text)
    if len(digits) >= 9:
        return search_parking_by_phone(text)

    if re.fullmatch(r"[A-Za-z]{1,4}[- ]?\d{3,4}", text):
        return search_parking_by_plate(text)

    return search_parking_by_space(text)

def search_parking_by_owner(owner_keyword: str):
    """依車主姓名/關鍵字反查車位與戶別。"""
    df = _parking_df()
    if df.empty:
        return "📭 目前無車位登記資料。"

    keyword = str(owner_keyword or "").strip()
    if not keyword:
        return "請提供車主姓名或關鍵字。"

    matches = df[
        df["車主姓名"].astype(str).str.contains(
            re.escape(keyword), case=False, na=False, regex=True
        )
    ]

    if matches.empty:
        return f"🔎 查無車主「{owner_keyword}」的車位登記資料。"

    return "\n\n".join(_format_parking_result(row) for _, row in matches.iterrows())


def get_resident_vehicle_count(resident_id: str):
    """回傳指定戶別目前登記幾台車，並列出車位類型。"""
    df = _parking_df()
    if df.empty:
        return "📭 目前無車位登記資料。"

    rid = str(resident_id or "").strip().upper()
    matches = df[
        df["戶別"].astype(str).str.strip().str.upper() == rid
    ]

    if matches.empty:
        return f"🏠【{rid}｜車輛統計】\n目前無車位 / 車輛登記。"

    spaces = [str(v).strip() for v in matches["車位號碼"].tolist()]
    car_count = sum("汽車" in x or re.search(r"B[123]", x, re.I) for x in spaces)
    moto_count = sum("機車" in x for x in spaces)

    return (
        f"🏠【{rid}｜車輛統計】\n"
        f"共登記 {len(matches)} 台\n"
        f"🚗 汽車：{car_count} 台\n"
        f"🛵 機車：{moto_count} 台"
    )


def get_parking_management_snapshot():
    """回傳管理摘要所需的確定性車位分析。"""
    df = _parking_df()
    if df.empty:
        return "📭 目前無車位登記資料。"

    residents = df["戶別"].astype(str).str.strip()
    counts = residents.value_counts()
    multi3 = counts[counts >= 3].sort_values(ascending=False)

    identity = df["身分標記"].astype(str).str.strip() if "身分標記" in df.columns else pd.Series("", index=df.index)
    tenant_df = df[identity == "租客"]
    tenant_households = tenant_df["戶別"].astype(str).str.strip().nunique() if not tenant_df.empty else 0

    spaces = df["車位號碼"].astype(str)
    car_count = int(spaces.str.contains("汽車|B1-|B2-|B3-", regex=True, na=False).sum())
    moto_count = int(spaces.str.contains("機車", regex=False, na=False).sum())

    lines = [
        "🅿️【車位管理摘要】",
        "━━━━━━━━━━━━",
        f"🚗 汽車登記｜{car_count} 筆",
        f"🛵 機車登記｜{moto_count} 筆",
        f"🔑 租客車輛｜{len(tenant_df)} 筆 / {tenant_households} 戶",
        f"⚠️ 3 台以上｜{len(multi3)} 戶",
    ]

    if not multi3.empty:
        lines.append("━━━━━━━━━━━━")
        lines.append("🚘 多車戶")
        for resident, count in multi3.head(5).items():
            lines.append(f"• {resident} 戶｜{count} 台")

    return "\n".join(lines)
