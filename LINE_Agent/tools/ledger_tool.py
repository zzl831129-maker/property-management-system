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
    for col in ["收入金額", "支出金額"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def _money(value):
    try:
        return f"${float(value):,.0f}"
    except Exception:
        return "$0"


def get_ledger_balance(resident_id: str):
    df = _ledger_df()
    if df.empty:
        return "📭 目前無零用金明細資料。"

    resident_id = str(resident_id).strip().upper()
    resident_df = df[df["戶別"].astype(str).str.strip().str.upper() == resident_id]

    if resident_df.empty:
        return f"🔎【查無住戶資料】\n戶別：{resident_id}\n目前沒有零用金收支紀錄。"

    total_income = resident_df["收入金額"].sum()
    total_expense = resident_df["支出金額"].sum()
    balance = total_income - total_expense
    status = "🟢 餘額正常" if balance >= 0 else "🔴 已透支"

    return (
        f"🏠【{resident_id}｜零用金摘要】\n"
        "━━━━━━━━━━━━\n"
        f"💰 目前餘額  {_money(balance)}\n"
        f"📥 累計收入  {_money(total_income)}\n"
        f"📤 累計支出  {_money(total_expense)}\n"
        "━━━━━━━━━━━━\n"
        f"{status}"
    )


def get_ledger_summary(target_date: str = None, target_month: str = None):
    df = _ledger_df()
    if df.empty:
        return "📭 目前無零用金明細資料。"
    if DATE_COLUMN not in df.columns:
        return f"⚠️ 零用金明細缺少「{DATE_COLUMN}」欄位。"

    date_text = pd.to_datetime(df[DATE_COLUMN], errors="coerce").dt.strftime("%Y-%m-%d")

    if target_month:
        df_filtered = df[date_text.str.startswith(str(target_month), na=False)]
        total_income = df_filtered["收入金額"].sum()
        total_expense = df_filtered["支出金額"].sum()
        net = total_income - total_expense
        return (
            f"📊【{target_month}｜零用金月結】\n"
            "━━━━━━━━━━━━\n"
            f"📥 本月收入  {_money(total_income)}\n"
            f"📤 本月支出  {_money(total_expense)}\n"
            f"💰 淨變動    {_money(net)}\n"
            f"🧾 交易筆數  {len(df_filtered)} 筆\n"
            "━━━━━━━━━━━━"
        )

    if target_date:
        df_filtered = df[date_text == str(target_date)]
        if df_filtered.empty:
            return f"📅【{target_date}｜零用金日結】\n今日無任何收支異動紀錄。"

        total_income = df_filtered["收入金額"].sum()
        total_expense = df_filtered["支出金額"].sum()
        net = total_income - total_expense

        detail_lines = []
        for _, row in df_filtered.iterrows():
            resident = str(row.get("戶別", "")).strip()
            summary = str(row.get("項目摘要", "")).strip()
            income = float(row.get("收入金額", 0) or 0)
            expense = float(row.get("支出金額", 0) or 0)
            amount_text = f"＋{_money(income)}" if income > 0 else (f"－{_money(expense)}" if expense > 0 else "$0")
            detail_lines.append(f"• {resident}｜{summary}\n  {amount_text}")

        return (
            f"📅【{target_date}｜零用金日結】\n"
            "━━━━━━━━━━━━\n"
            f"📥 今日收入  {_money(total_income)}\n"
            f"📤 今日支出  {_money(total_expense)}\n"
            f"💰 淨變動    {_money(net)}\n"
            f"🧾 交易筆數  {len(df_filtered)} 筆\n"
            "━━━━━━━━━━━━\n"
            "📋 今日明細\n"
            + "\n".join(detail_lines)
        )

    return "請指定日期或月份。"


def get_resident_daily_detail(resident_id: str, target_date: str):
    df = _ledger_df()
    if df.empty:
        return "📭 目前無零用金明細資料。"
    if DATE_COLUMN not in df.columns:
        return f"⚠️ 零用金明細缺少「{DATE_COLUMN}」欄位。"

    resident_id = str(resident_id).strip().upper()
    date_text = pd.to_datetime(df[DATE_COLUMN], errors="coerce").dt.strftime("%Y-%m-%d")
    df_filtered = df[(df["戶別"].astype(str).str.strip().str.upper() == resident_id) & (date_text == str(target_date))]

    if df_filtered.empty:
        return f"🏠【{resident_id}｜{target_date}】\n當日沒有交易明細。"

    income_total = df_filtered["收入金額"].sum()
    expense_total = df_filtered["支出金額"].sum()
    detail_lines = []

    for index, (_, row) in enumerate(df_filtered.iterrows(), start=1):
        summary = str(row.get("項目摘要", "")).strip()
        handler = str(row.get("經手人", "")).strip()
        income = float(row.get("收入金額", 0) or 0)
        expense = float(row.get("支出金額", 0) or 0)
        amount = f"📥 ＋{_money(income)}" if income > 0 else (f"📤 －{_money(expense)}" if expense > 0 else "➖ $0")
        detail_lines.append(f"{index}. {summary}\n   {amount}\n   👤 {handler or '未填寫'}")

    return (
        f"🏠【{resident_id}｜{target_date} 交易明細】\n"
        "━━━━━━━━━━━━\n"
        f"📥 當日收入  {_money(income_total)}\n"
        f"📤 當日支出  {_money(expense_total)}\n"
        f"🧾 共 {len(df_filtered)} 筆\n"
        "━━━━━━━━━━━━\n"
        + "\n\n".join(detail_lines)
    )


def get_overdrawn_residents():
    df = _ledger_df()
    if df.empty:
        return "📭 目前無零用金資料。"

    grouped = df.groupby("戶別")[["收入金額", "支出金額"]].sum()
    grouped["餘額"] = grouped["收入金額"] - grouped["支出金額"]
    overdrawn = grouped[grouped["餘額"] < 0].sort_values("餘額")

    if overdrawn.empty:
        return "✅【零用金透支清查】\n目前全社區無負數透支戶。"

    lines = [f"{index}. {resident} 戶｜🔴 {_money(row['餘額'])}" for index, (resident, row) in enumerate(overdrawn.iterrows(), start=1)]
    return f"⚠️【零用金透支清查｜共 {len(overdrawn)} 戶】\n━━━━━━━━━━━━\n" + "\n".join(lines)
