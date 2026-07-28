# 檔案路徑：tools/ledger_tool.py
import os
import pandas as pd
from services.google_sheet import get_sheet_data

LEDGER_SHEET_ID = os.getenv("LEDGER_SHEET_ID")

def get_ledger_balance(resident_id: str):
    """查詢特定住戶的零用金總餘額"""
    data = get_sheet_data(LEDGER_SHEET_ID, "零用金明細")
    if not data:
        return "目前無零用金明細資料。"
        
    total_income = 0
    total_expense = 0
    found = False
    
    for row in data:
        if str(row.get('戶別', '')) == str(resident_id):
            found = True
            income = float(row.get('收入金額', 0) or 0)
            expense = float(row.get('支出金額', 0) or 0)
            total_income += income
            total_expense += expense
            
    if not found:
        return f"抱歉，找不到戶別為 {resident_id} 的住戶資料。"
    
    balance = total_income - total_expense
    return f"{resident_id} 戶目前的總收入為 {total_income:,.0f} 元，總支出為 {total_expense:,.0f} 元，目前餘額為 {balance:,.0f} 元。"


def get_ledger_summary(target_date: str = None, target_month: str = None):
    """查詢社區整體日結或月結"""
    data = get_sheet_data(LEDGER_SHEET_ID, "零用金明細")
    if not data:
        return "目前無零用金明細資料。"
        
    df = pd.DataFrame(data)
    df['收入金額'] = pd.to_numeric(df.get('收入金額', 0), errors='coerce').fillna(0)
    df['支出金額'] = pd.to_numeric(df.get('支出金額', 0), errors='coerce').fillna(0)
    
    if target_month:
        df_filtered = df[df['日期'].astype(str).str.startswith(target_month)]
        total_income = df_filtered['收入金額'].sum()
        total_expense = df_filtered['支出金額'].sum()
        net_change = total_income - total_expense
        count = len(df_filtered)
        
        return (
            f"📊 【{target_month} 月結算報告】\n"
            f"• 該月總收入：${total_income:,.0f} 元\n"
            f"• 該月總支出：${total_expense:,.0f} 元\n"
            f"• 當月淨變動：${net_change:,.0f} 元\n"
            f"• 總共發生 {count} 筆交易紀錄。"
        )
    elif target_date:
        df_filtered = df[df['日期'].astype(str) == target_date]
        total_income = df_filtered['收入金額'].sum()
        total_expense = df_filtered['支出金額'].sum()
        net_change = total_income - total_expense
        
        if df_filtered.empty:
            return f"📅 當日 ({target_date}) 無任何收支異動紀錄。"
            
        details = "\n".join([
            f"- 戶別: {r.get('戶別')} | 摘要: {r.get('項目摘要')} | 收入: {r.get('收入金額')} | 支出: {r.get('支出金額')}"
            for _, r in df_filtered.iterrows()
        ])
        
        return (
            f"📅 【{target_date} 日結算與明細】\n"
            f"• 該日總收入：${total_income:,.0f} 元\n"
            f"• 該日總支出：${total_expense:,.0f} 元\n"
            f"• 當月/當日淨變動：${net_change:,.0f} 元\n\n"
            f"詳細交易清單：\n{details}"
        )
    return "請指定日期或月份。"


def get_resident_daily_detail(resident_id: str, target_date: str):
    """查詢某住戶某一天的明細"""
    data = get_sheet_data(LEDGER_SHEET_ID, "零用金明細")
    if not data:
        return "目前無零用金明細資料。"
        
    df = pd.DataFrame(data)
    # 篩選特定戶別與特定日期
    df_filtered = df[(df['戶別'].astype(str) == str(resident_id)) & (df['日期'].astype(str) == target_date)]
    
    if df_filtered.empty:
        return f"📅 {target_date} 當天，{resident_id} 戶無任何交易明細紀錄。"
        
    details = "\n".join([
        f"- 摘要: {r.get('項目摘要')} | 收入: {r.get('收入金額')} | 支出: {r.get('支出金額')} | 經手人: {r.get('經手人', '')}"
        for _, r in df_filtered.iterrows()
    ])
    
    return f"🏠 【{resident_id} 戶 - {target_date} 交易明細】\n{details}"


def get_overdrawn_residents():
    """自動清查目前餘額為負值的戶別（透支戶）"""
    data = get_sheet_data(LEDGER_SHEET_ID, "零用金明細")
    if not data:
        return "目前無資料。"
        
    df = pd.DataFrame(data)
    df['收入金額'] = pd.to_numeric(df.get('收入金額', 0), errors='coerce').fillna(0)
    df['支出金額'] = pd.to_numeric(df.get('支出金額', 0), errors='coerce').fillna(0)
    
    # 依戶別加總計算餘額
    grouped = df.groupby('戶別')[['收入金額', '支出金額']].sum()
    grouped['餘額'] = grouped['收入金額'] - grouped['支出金額']
    
    # 篩選餘額小於 0 的戶別
    overdrawn = grouped[grouped['餘額'] < 0]
    
    if overdrawn.empty:
        return "✅ 目前全社區所有住戶零用金皆正常（無負數透支戶）。"
        
    result_str = "⚠️ 【目前透支（負值）戶別清單】\n"
    for resident, row in overdrawn.iterrows():
        result_str += f"• {resident} 戶：餘額 ${row['餘額']:,.0f} 元\n"
        
    return result_str