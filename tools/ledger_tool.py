# 檔案路徑：tools/ledger_tool.py
import os

# 將所有會用到的外部套件匯入放在函式裡面，這是最保險的做法
def get_ledger_balance(resident_id: str):
    from services.google_sheet import get_sheet_data # 在這裡匯入，不會跟別的檔案撞車
    
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