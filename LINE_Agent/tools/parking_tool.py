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
        phone = _clean(row.get("連絡電話"))
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
