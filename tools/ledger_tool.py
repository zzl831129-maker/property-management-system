# tools/ledger_tool.py
from services.google_sheet import get_sheet_data
from config import LEDGER_SHEET_ID

def get_ledger_balance(resident_id: str):
    # 1. 抓取所有資料
    data = get_sheet_data(LEDGER_SHEET_ID, "零用金明細")
    
    total_income = 0
    total_expense = 0
    found = False
    
    # 2. 遍歷資料進行累加運算
    for row in data:
        # 比對戶別 (注意：你的表格欄位名稱是 '戶別')
        if str(row.get('戶別', '')) == str(resident_id):
            found = True
            # 將字串轉為數字進行加總 (若欄位為空則預設為 0)
            income = float(row.get('收入金額', 0) or 0)
            expense = float(row.get('支出金額', 0) or 0)
            
            total_income += income
            total_expense += expense
            
    if not found:
        return f"抱歉，找不到戶別為 {resident_id} 的住戶資料。"
    
    # 3. 計算餘額
    balance = total_income - total_expense
    return f"{resident_id} 戶目前的總收入為 {total_income} 元，總支出為 {total_expense} 元，目前餘額為 {balance} 元。"