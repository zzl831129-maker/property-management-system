import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# 1. 連結 Google Sheets 的設定
def init_spreadsheet():
   def init_spreadsheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # 【雲端安全核心】：檢查 Streamlit 雲端保險箱裡有沒有藏鑰匙
    if "gspread_creds" in st.secrets:
        # 如果有，就將保險箱內的資料轉成字典格式，並用 from_json_keyfile_dict 讀取
        creds_dict = dict(st.secrets["gspread_creds"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        # 如果沒有（代表在自己電腦測試），就維持讀取本地的 creds.json
        creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
        
    client = gspread.authorize(creds)
    spreadsheet = client.open("住戶車籍資料庫")
    return spreadsheet.sheet1

# 初始化資料表
try:
    sheet = init_spreadsheet()
except Exception as e:
    st.error(f"連線 Google Sheet 失敗，請檢查金鑰或試算表名稱。錯誤訊息: {e}")
    st.stop()

# 網頁標題
st.title("🚗 住戶車籍資料管理系統")

# 建立側邊欄導覽選單
menu = ["查看現有資料", "新增車籍資料", "修改/刪除資料"]
choice = st.sidebar.selectbox("功能選單", menu)

# ----------------- 功能 1：查看現有資料 -----------------
if choice == "查看現有資料":
    st.subheader("📋 目前登記的車籍清單")
    
    # 讀取 Google Sheet 所有資料並轉為 Pandas DataFrame 顯示
    data = sheet.get_all_records()
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("目前資料庫中沒有任何資料。")

# ----------------- 功能 2：新增車籍資料 -----------------
elif choice == "新增車籍資料":
    st.subheader("➕ 登打新車籍資料")
    
    # 建立表單讓使用者輸入
    with st.form(key="add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            building = st.selectbox("棟別", ["A棟", "B棟", "C棟", "D棟"])
            unit_no = st.text_input("戶號 (例如: 12樓之3)")
            owner = st.text_input("屋主姓名")
        with col2:
            car_plate = st.text_input("車牌號碼")
            parking_no = st.text_input("車位號碼")
            phone = st.text_input("聯絡電話")
            
        remarks = st.text_area("備註")
        
        submit_button = st.form_submit_button(label="確認送出")
        
        if submit_button:
            if not unit_no or not car_plate:
                st.error("❌ '戶號'與'車牌號碼'為必填欄位！")
            else:
                # 將新資料打包成陣列，順序必須與 Google Sheet 欄位一致
                new_row = [building, unit_no, owner, car_plate, parking_no, phone, remarks]
                sheet.append_row(new_row)
                st.success(f"🎉 車牌 {car_plate} 資料已成功寫入 Google Sheet！")

# ----------------- 功能 3：修改/刪除資料 -----------------
elif choice == "修改/刪除資料":
    st.subheader("📝 修改現有車籍資料")
    
    data = sheet.get_all_records()
    if not data:
        st.info("目前沒有資料可供修改。")
    else:
        df = pd.DataFrame(data)
        
        # 讓使用者透過車牌號碼來搜尋要修改的資料
        all_plates = df["車牌號碼"].tolist()
        search_plate = st.selectbox("請選擇要修改的車牌號碼", all_plates)
        
        # 找出該車牌在 DataFrame 中的索引 (Index)，對應到 Google Sheet 的行數 (Row)
        target_idx = df[df["車牌號碼"] == search_plate].index[0]
        sheet_row_num = int(target_idx) + 2 # +2 是因為 Sheet 索引從 1 開始且第一行是標題
        
        # 撈出該筆資料目前的舊數值
        current_data = df.iloc[target_idx]
        
        # 顯示修改表單，並預填舊資料
        with st.form(key="update_form"):
            col1, col2 = st.columns(2)
            with col1:
                u_building = st.text_input("棟別", value=str(current_data["棟別"]))
                u_unit_no = st.text_input("戶號", value=str(current_data["戶號"]))
                u_owner = st.text_input("屋主姓名", value=str(current_data["屋主姓名"]))
            with col2:
                u_car_plate = st.text_input("車牌號碼 (不可重複)", value=str(current_data["車牌號碼"]))
                u_parking_no = st.text_input("車位號碼", value=str(current_data["車位號碼"]))
                u_phone = st.text_input("聯絡電話", value=str(current_data["聯絡電話"]))
            
            u_remarks = st.text_area("備註", value=str(current_data["備註"]))
            
            update_btn = st.form_submit_button("確認更新資料")
            
            if update_btn:
                # 重新包裝修改後的資料
                updated_row = [u_building, u_unit_no, u_owner, u_car_plate, u_parking_no, u_phone, u_remarks]
                
                # 更新指定行數的整行資料
                sheet.update(range_name=f"A{sheet_row_num}:G{sheet_row_num}", values=[updated_row])
                st.success(f"✨ 車牌 {u_car_plate} 的資料已成功更新！")
                st.info("提示：切換選單即可重整查看最新資料。")