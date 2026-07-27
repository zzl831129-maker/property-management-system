# 檔案路徑：tools/ledger_tool.py
import os
import pandas as pd

def get_ledger_balance(resident_id: str):
    """查詢特定住戶的零用金餘額"""
    from services.google_sheet import get_sheet_data
    
    LEDGER_SHEET_ID = os.getenv("LEDGER_SHEET_ID")
    data = get_sheet_data(LEDGER_SHEET_ID, "零用金明細")
    
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
    return f"{resident_id} 戶目前的總收入為 {total_income} 元，總支出為 {total_expense} 元，目前餘額為 {balance} 元。"


def get_ledger_summary(target_date: str = None, target_month: str = None):
    """查詢整個社區的日結、月結與收支統整"""
    from services.google_sheet import get_sheet_data
    
    LEDGER_SHEET_ID = os.getenv("LEDGER_SHEET_ID")
    data = get_sheet_data(LEDGER_SHEET_ID, "零用金明細")
    if not data:
        return "目前無零用金明細資料。"
        
    df = pd.DataFrame(data)
    
    # 確保數值欄位正確
    df['收入金額'] = pd.to_numeric(df.get('收入金額', 0), errors='coerce').fillna(0)
    df['支出金額'] = pd.to_numeric(df.get('支出金額', 0), errors='coerce').fillna(0)
    
    if target_month:
        # 篩選特定月份 (例如 "2026-07")
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
        # 篩選特定日期 (例如 "2026-07-26")
        df_filtered = df[df['日期'].astype(str) == target_date]
        total_income = df_filtered['收入金額'].sum()
        total_expense = df_filtered['支出金額'].sum()
        net_change = total_income - total_expense
        
        if df_filtered.empty:
            return f"📅 當日 ({target_date}) 無任何收支異動紀錄。"
            
        return (
            f"📅 【{target_date} 日結算報告】\n"
            f"• 該日總收入：${total_income:,.0f} 元\n"
            f"• 該日總支出：${total_expense:,.0f} 元\n"
            f"• 當日淨變動：${net_change:,.0f} 元"
        )
    
    return "請指定要查詢的「月份 (例如 2026-07)」或「日期」。"