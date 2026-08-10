import os
import pandas as pd
from services.google_sheet import get_sheet_data

LEDGER_SHEET_ID = os.getenv("LEDGER_SHEET_ID")

def _parking_df():
    data = get_sheet_data(LEDGER_SHEET_ID, "車位登記")
    return pd.DataFrame(data) if data else pd.DataFrame()

def get_parking_info(resident_id: str):
    df = _parking_df()
    if df.empty:
        return "目前無車位登記資料。"
    results = df[df["戶別"].astype(str) == str(resident_id)]
    if results.empty:
        return f"{resident_id} 戶目前無車位登記紀錄。"
    summary = "\n".join(
        f"• 車位: {r.get('車位號碼')} | 車牌: {r.get('車牌號碼')} | 車主: {r.get('車主姓名')} | 電話: {r.get('連絡電話')}"
        for _, r in results.iterrows()
    )
    return f"🚗 【{resident_id} 戶車位資訊】\n{summary}"

def get_parking_asset_summary():
    df = _parking_df()
    if df.empty:
        return "目前無車位登記資料。"
    return f"🅿️ 【社區車位資產總結算】\n• 總登記車輛紀錄數：{len(df)} 筆\n• 汽車位與機車位使用狀況已同步連線。"

def get_third_car_residents():
    df = _parking_df()
    if df.empty:
        return "目前無資料。"
    if "戶別" not in df.columns:
        return "找不到戶別欄位。"
    counts = df["戶別"].astype(str).value_counts()
    third = counts[counts >= 3]
    if third.empty:
        return "✅ 目前無任何住戶擁有 3 台或以上的車輛。"
    result = "⚠️ 【擁擠車位 / 第三台車戶別清單】\n"
    for resident, count in third.items():
        result += f"• {resident} 戶：共登記 {count} 台車/車位\n"
    return result

def get_tenant_parking_summary():
    df = _parking_df()
    if df.empty:
        return "目前無資料。"
    if "身分標記" not in df.columns:
        return "車位登記缺少「身分標記」欄位。"
    tenants = df[df["身分標記"].astype(str).str.strip() == "租客"]
    if tenants.empty:
        return "✅ 目前無租客車輛登記。"
    grouped = tenants.groupby("戶別").size().sort_values(ascending=False)
    result = "🅿️ 【目前擁有租客車輛之戶別清單】\n"
    for resident, count in grouped.items():
        result += f"• {resident} 戶：{count} 台\n"
    return result
