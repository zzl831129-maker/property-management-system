import os
import pandas as pd
from services.google_sheet import get_sheet_data

LEDGER_SHEET_ID = os.getenv("LEDGER_SHEET_ID")
DATE_COLUMN = "交易日期"

def _ledger_df():
    data = get_sheet_data(LEDGER_SHEET_ID, "零用金明細")
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    for c in ["收入金額", "支出金額"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df

def get_ledger_balance(resident_id: str):
    df = _ledger_df()
    if df.empty:
        return "目前無零用金明細資料。"
    resident_df = df[df["戶別"].astype(str) == str(resident_id)]
    if resident_df.empty:
        return f"抱歉，找不到戶別為 {resident_id} 的住戶資料。"
    total_income = resident_df["收入金額"].sum()
    total_expense = resident_df["支出金額"].sum()
    balance = total_income - total_expense
    return f"{resident_id} 戶目前的總收入為 {total_income:,.0f} 元，總支出為 {total_expense:,.0f} 元，目前餘額為 {balance:,.0f} 元。"

def get_ledger_summary(target_date: str = None, target_month: str = None):
    df = _ledger_df()
    if df.empty:
        return "目前無零用金明細資料。"
    if DATE_COLUMN not in df.columns:
        return f"零用金明細缺少「{DATE_COLUMN}」欄位。"

    date_text = pd.to_datetime(df[DATE_COLUMN], errors="coerce").dt.strftime("%Y-%m-%d")

    if target_month:
        df_filtered = df[date_text.str.startswith(str(target_month), na=False)]
        total_income = df_filtered["收入金額"].sum()
        total_expense = df_filtered["支出金額"].sum()
        return (
            f"📊 【{target_month} 月結算報告】\n"
            f"• 該月總收入：${total_income:,.0f} 元\n"
            f"• 該月總支出：${total_expense:,.0f} 元\n"
            f"• 當月淨變動：${total_income-total_expense:,.0f} 元\n"
            f"• 總共發生 {len(df_filtered)} 筆交易紀錄。"
        )

    if target_date:
        df_filtered = df[date_text == str(target_date)]
        if df_filtered.empty:
            return f"📅 當日 ({target_date}) 無任何收支異動紀錄。"
        total_income = df_filtered["收入金額"].sum()
        total_expense = df_filtered["支出金額"].sum()
        details = "\n".join(
            f"- 戶別: {r.get('戶別')} | 摘要: {r.get('項目摘要')} | 收入: {r.get('收入金額')} | 支出: {r.get('支出金額')}"
            for _, r in df_filtered.iterrows()
        )
        return (
            f"📅 【{target_date} 日結算與明細】\n"
            f"• 該日總收入：${total_income:,.0f} 元\n"
            f"• 該日總支出：${total_expense:,.0f} 元\n"
            f"• 當日淨變動：${total_income-total_expense:,.0f} 元\n\n"
            f"詳細交易清單：\n{details}"
        )
    return "請指定日期或月份。"

def get_resident_daily_detail(resident_id: str, target_date: str):
    df = _ledger_df()
    if df.empty:
        return "目前無零用金明細資料。"
    if DATE_COLUMN not in df.columns:
        return f"零用金明細缺少「{DATE_COLUMN}」欄位。"
    date_text = pd.to_datetime(df[DATE_COLUMN], errors="coerce").dt.strftime("%Y-%m-%d")
    df_filtered = df[
        (df["戶別"].astype(str) == str(resident_id)) &
        (date_text == str(target_date))
    ]
    if df_filtered.empty:
        return f"📅 {target_date} 當天，{resident_id} 戶無任何交易明細紀錄。"
    details = "\n".join(
        f"- 摘要: {r.get('項目摘要')} | 收入: {r.get('收入金額')} | 支出: {r.get('支出金額')} | 經手人: {r.get('經手人', '')}"
        for _, r in df_filtered.iterrows()
    )
    return f"🏠 【{resident_id} 戶 - {target_date} 交易明細】\n{details}"

def get_overdrawn_residents():
    df = _ledger_df()
    if df.empty:
        return "目前無資料。"
    grouped = df.groupby("戶別")[["收入金額", "支出金額"]].sum()
    grouped["餘額"] = grouped["收入金額"] - grouped["支出金額"]
    overdrawn = grouped[grouped["餘額"] < 0]
    if overdrawn.empty:
        return "✅ 目前全社區所有住戶零用金皆正常（無負數透支戶）。"
    result = "⚠️ 【目前透支（負值）戶別清單】\n"
    for resident, row in overdrawn.iterrows():
        result += f"• {resident} 戶：餘額 ${row['餘額']:,.0f} 元\n"
    return result
