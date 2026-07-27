# -*- coding: utf-8 -*-
"""
社區物業智慧管理系統 - 雲端化汽車/機車位綁定、租客標記、無破折號車牌、第三台車自動防呆與進階財務/車位報表查詢版
"""

import streamlit as st
import pandas as pd
import datetime
import time
import re
import random
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 0. 系統環境初始化與外觀美化
# ==========================================
st.set_page_config(page_title="社區物業智慧管理系統", layout="wide", page_icon="🏢")

st.markdown("""
    <style>
    .big-font { font-size:18px !important; font-weight: bold; }
    .stButton > button { border-radius: 8px !important; }
    .highlight-box { background-color: #FFF3CD; padding: 15px; border-radius: 5px; border-left: 6px solid #FFC107; color: #856404; }
    .info-box-custom { background-color: #E2F0CB; padding: 12px; border-radius: 5px; border-left: 6px solid #55A630; color: #2D6A4F; font-weight: bold; margin-bottom: 10px; }
    .alert-box-custom { background-color: #F8D7DA; padding: 12px; border-radius: 5px; border-left: 6px solid #DC3545; color: #721C24; font-weight: bold; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("🏢 社區物業智慧管理系統")
st.caption("✨ 雲端車位綁定、無破折號車牌、進階財務日/月結與未登記車位清查版")

# ==========================================
# 🔌 Google Sheets 雲端連線實體大腦
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/18DI3Lpyk8R5pT_3K7B4oLLK_vsHYuWh2JXRP8MLyGQM/edit"
SPREADSHEET_NAME = SPREADSHEET_URL  

def generate_default_units():
    units = []
    for floor in range(2, 16):
        for room in ["A", "B", "C", "D", "E", "F", "G", "H"]:
            unit = f"{floor}{room}"
            if unit != "1A":
                units.append(unit)
    return units

def load_cloud_ledger():
    required_cols = ["流水號", "交易日期", "戶別", "項目摘要", "支出金額", "收入金額", "經手人", "系統登錄時間"]
    try:
        df = conn.read(spreadsheet=SPREADSHEET_NAME, worksheet="零用金明細", ttl=0)
        if df is not None and not df.empty and "交易日期" in df.columns:
            df["交易日期"] = pd.to_datetime(df["交易日期"]).dt.date
            df["支出金額"] = pd.to_numeric(df["支出金額"]).fillna(0).astype(int)
            df["收入金額"] = pd.to_numeric(df["收入金額"]).fillna(0).astype(int)
            df["流水號"] = pd.to_numeric(df["流水號"]).fillna(0).astype(int)
            for col in ["戶別", "項目摘要", "經手人", "系統登錄時間"]:
                df[col] = df[col].astype(str).str.strip() if col in df.columns else ""
            return df[required_cols]
        return pd.DataFrame(columns=required_cols)
    except Exception as e:
        st.error(f"❌ 讀取零用金明細失敗: {e}")
        return pd.DataFrame(columns=required_cols)

def save_cloud_ledger(df_to_save):
    df_copy = df_to_save.copy()
    if not df_copy.empty:
        df_copy["交易日期"] = df_copy["交易日期"].astype(str)
        df_copy["系統登錄時間"] = df_copy["系統登錄時間"].astype(str)
    try:
        conn.update(spreadsheet=SPREADSHEET_NAME, worksheet="零用金明細", data=df_copy)
        st.toast("☁️ 零用金明細已成功同步至雲端試算表！", icon="💾")
        return True
    except Exception as e:
        if "200" in str(e) or "OK" in str(e):
            st.toast("☁️ 零用金明細已成功同步至雲端試算表！", icon="💾")
            return True
        st.error(f"❌ 寫入雲端零用金失敗: {e}")
        return False

def load_parking_ledger():
    required_cols = ["流水號", "車位號碼", "戶別", "車牌號碼", "車主姓名", "連絡電話", "身分標記", "車輛備註", "登記日期"]
    try:
        df = conn.read(spreadsheet=SPREADSHEET_NAME, worksheet="車位登記", ttl=0)
        if df is not None and not df.empty and "車位號碼" in df.columns:
            df["流水號"] = pd.to_numeric(df["流水號"]).fillna(0).astype(int)
            for col in ["車位號碼", "車牌號碼", "車主姓名", "連絡電話", "戶別", "身分標記", "車輛備註", "登記日期"]:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
                else:
                    df[col] = "屋主" if col == "身分標記" else ""
            
            if "連絡電話" in df.columns:
                df["連絡電話"] = df["連絡電話"].apply(lambda x: x.split('.')[0] if '.' in x else x)
                df["連絡電話"] = df["連絡電話"].apply(lambda x: "0" + x if len(x) == 9 and x.startswith("9") else x)
                
            df["車牌號碼"] = df["車牌號碼"].str.upper()
            return df[[c for c in required_cols if c in df.columns]]
        return pd.DataFrame(columns=required_cols)
    except Exception:
        return pd.DataFrame(columns=required_cols)

def save_parking_ledger(df_to_save):
    df_copy = df_to_save.copy()
    if not df_copy.empty:
        df_copy["登記日期"] = df_copy["登記日期"].astype(str)
        df_copy["連絡電話"] = df_copy["連絡電話"].astype(str)
        df_copy["流水號"] = pd.to_numeric(df_copy["流水號"]).astype(int)
        if "身分標記" not in df_copy.columns:
            df_copy["身分標記"] = "屋主"
        if "車輛備註" not in df_copy.columns:
            df_copy["車輛備註"] = ""
    try:
        conn.update(spreadsheet=SPREADSHEET_NAME, worksheet="車位登記", data=df_copy)
        st.toast("🚗 車位資產登記已成功同步至雲端！", icon="💾")
        return True
    except Exception as e:
        if "200" in str(e) or "OK" in str(e):
            st.toast("🚗 車位資產登記已成功同步至雲端！", icon="💾")
            return True
        st.error(f"❌ 寫入雲端車位登記分頁失敗: {e}")
        return False

def load_binding_mapping(worksheet_name):
    default_units = generate_default_units()
    try:
        df = conn.read(spreadsheet=SPREADSHEET_NAME, worksheet=worksheet_name, ttl=0)
        existing_mapping = {}
        if df is not None and not df.empty and "戶別" in df.columns:
            for _, row in df.iterrows():
                u = str(row["戶別"]).strip()
                s = str(row["车位编号"] if "车位编号" in df.columns else row.get("車位編號", "")).strip()
                if u and u != "nan":
                    s = s.replace("汽車位", "").replace("機車位", "").replace("(", "").replace(")", "").strip()
                    existing_mapping[u] = s if s and s != "nan" else ""
        
        full_mapping = {u: existing_mapping.get(u, "") for u in default_units}
        return full_mapping
    except Exception:
        return {u: "" for u in default_units}

def save_binding_mapping(worksheet_name, mapping_dict):
    try:
        df_to_save = pd.DataFrame(list(mapping_dict.items()), columns=["戶別", "車位編號"])
        conn.update(spreadsheet=SPREADSHEET_NAME, worksheet=worksheet_name, data=df_to_save)
        st.toast(f"☁️ {worksheet_name} 已成功同步至雲端！", icon="💾")
        return True
    except Exception as e:
        if "200" in str(e) or "OK" in str(e):
            st.toast(f"☁️ {worksheet_name} 已成功同步至雲端！", icon="💾")
            return True
        st.error(f"❌ 寫入 {worksheet_name} 失敗: {e}")
        return False

def format_plate_number(plate_str):
    p = str(plate_str).strip().upper().replace(" ", "").replace("-", "").replace("_", "")
    if not p or p in ["NAN", "NONE", "NULL"]:
        return ""
    return p

# ==========================================
# 1. 系統記憶體初始化
# ==========================================
if 'resident_list' not in st.session_state:
    init_res = ["1A"]
    for floor in range(2, 16):  
        for room in ["A", "B", "C", "D", "E", "F", "G", "H"]:  
            init_res.append(f"{floor}{room}")
    st.session_state.resident_list = init_res

if 'lottery_excluded_res' not in st.session_state:
    st.session_state.lottery_excluded_res = ["1A"]

if 'car_space_mapping' not in st.session_state:
    st.session_state.car_space_mapping = load_binding_mapping("汽車位綁定")

if 'moto_space_mapping' not in st.session_state:
    st.session_state.moto_space_mapping = load_binding_mapping("機車位綁定")

if 'resident_initial_balances' not in st.session_state:
    st.session_state.resident_initial_balances = {res: 0 for res in st.session_state.resident_list}

if 'cash_inventory' not in st.session_state:
    st.session_state.cash_inventory = {"n1000": 0, "n500": 0, "n100": 0, "n50": 0, "n10": 0, "n1": 0}

if 'common_items' not in st.session_state:
    st.session_state.common_items = ["儲值", "水果錢", "文具", "關稅", "貨到付款"]
if 'common_handlers' not in st.session_state:
    st.session_state.common_handlers = ["日班-詹詹", "夜班-宗宗", "經理-00"]

if 'parking_capacities' not in st.session_state:
    st.session_state.parking_capacities = {
        "B1汽車位": 20,
        "B2汽車位": 20,
        "B3汽車位": 15,
        "機車位": 112
    }

if 'generated_line_text' not in st.session_state:
    st.session_state.generated_line_text = ""

if 'ledger_data' not in st.session_state or 'parking_data' not in st.session_state:
    with st.status("🛸 正在連線至【物業管理分析系統】雲端硬碟...", expanded=False) as status:
        st.session_state.ledger_data = load_cloud_ledger()
        st.session_state.parking_data = load_parking_ledger()
        status.update(label="✅ 雙核心數據庫無損同步成功！", state="complete")

INITIAL_CASH = 0
today_dt = datetime.date.today()

menu = st.radio(
    "🛠️ 請選擇主要功能：", 
    ["📝 零用金收支登記與快查及對帳", "🚗 車位登記及查詢", "⚙️ 常駐名冊與機車抽籤管理"], 
    horizontal=True
)

def generate_line_text(target_res, ledger_df, initial_balances, check_date=None):
    init_bal = initial_balances.get(target_res, 0)
    t_dt = check_date if check_date else datetime.date.today()
    t_dt_date = pd.to_datetime(t_dt).date()
    
    header = f"【🏢 社區零用金即時對帳通知】\n戶別：{target_res}\n"
    
    if ledger_df.empty:
        return header + f"📅 異動日期：{t_dt.month}/{t_dt.day}\n💰 帳戶最新結餘：{int(init_bal):,} 元"
    
    df_temp = ledger_df.copy()
    df_temp["交易日期"] = pd.to_datetime(df_temp["交易日期"]).dt.date
    df_temp = df_temp.sort_values(by=["交易日期", "流水號"])
    
    df_before = df_temp[(df_temp["戶別"] == target_res) & (df_temp["交易日期"] < t_dt_date)]
    running_bal = init_bal
    if not df_before.empty:
        running_bal += df_before["收入金額"].sum() - df_before["支出金額"].sum()
        
    df_today = df_temp[(df_temp["戶別"] == target_res) & (df_temp["交易日期"] == t_dt_date)]
    
    if df_today.empty:
        return header + f"📅 異動日期：{t_dt.month}/{t_dt.day}\n📝 今日收支：今日暫無款項異動\n💰 當日結餘：{int(running_bal):,} 元"
        
    line_lines = [f"📅 異動日期：{t_dt.month}/{t_dt.day}\n✨ 當日動態明細："]
    
    for idx, row in df_today.iterrows():
        prev_bal = running_bal
        net_expense = int(row["支出金額"])
        net_income = int(row["收入金額"])
        summary = row['項目摘要']
        
        if net_income > 0:
            running_bal += net_income
            line_lines.append(f" ├── {prev_bal:,}元 ＋ {summary}{net_income:,}元 ＝ {running_bal:,}元")
        elif net_expense > 0:
            running_bal -= net_expense
            line_lines.append(f" ├── {prev_bal:,}元 － {summary}{net_expense:,}元 ＝ {running_bal:,}元")
            
    line_lines.append(f"====================\n💰 當日最終結餘：{running_bal:,} 元\n\n※ 這是管理中心即時對帳明細，如有疑問歡迎至櫃台洽詢。")
    return header + "\n".join(line_lines)

# ==========================================
# 頁籤 1：📝 每日零用金收支登記與快查 (含進階日/月結與透支戶別檢視)
# ==========================================
if menu == "📝 零用金收支登記與快查及對帳":
    st.markdown("### 🔍 連鎖關鍵字快查與進階財務結算看板")
    
    sub_tab1, sub_tab2 = st.tabs(["📝 一般流水帳與快查登記", "📊 進階日/月結與透支戶清查報表"])
    
    with sub_tab1:
        search_keyword = st.text_input("💡 輸入多重條件可用 + 號連結（例如：2A + 水果）(日期：西元-XX月-XX日)：", placeholder="在此輸入搜尋條件...", key="main_search_bar")
        
        df_ledger = st.session_state.ledger_data.copy()
        if not df_ledger.empty:
            df_disp = df_ledger.copy()
            df_disp["交易日期"] = df_disp["交易日期"].astype(str)
            if search_keyword.strip():
                keywords = [k.strip().lower() for k in search_keyword.split("+") if k.strip()]
                full_text = df_disp["交易日期"] + " " + df_disp["戶別"] + " " + df_disp["項目摘要"] + " " + df_disp["經手人"]
                for kw in keywords:
                    df_disp = df_disp[full_text.str.lower().str.contains(kw, na=False)]
            st.dataframe(df_disp, use_container_width=True, hide_index=True)
        else:
            st.caption("Current cloud ledger is empty.")
            
        st.markdown("---")
        
        col_input, col_line = st.columns([1, 1])
        
        with col_input:
            trade_type = st.radio("請選擇交易模式：", ["一般收支 (收入/支出)", "🔄 住戶之間互相轉帳"], horizontal=True, key="main_trade_type")
            next_id = len(st.session_state.ledger_data) + 1
            current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if trade_type == "一般收支 (收入/支出)":
                st.subheader("📥 新進收支流水帳")
                log_date = st.date_input("選擇交易日期", value=today_dt, key="ins_date")
                resident_input = st.selectbox("選擇住戶戶別", st.session_state.resident_list, key="ins_res")
                action_type = st.selectbox("收支類別", ["支出", "收入"], key="ins_type")
                
                if action_type == "支出":
                    filtered_items = [item for item in st.session_state.common_items if "儲值" not in item]
                    item_input = st.selectbox("常用項目/摘要", ["手動輸入新項目..."] + filtered_items, key="ins_item_sel")
                else:
                    item_input = st.selectbox("常用項目/摘要", ["手動輸入新項目..."] + st.session_state.common_items, key="ins_item_sel")
                    
                item_final = st.text_input("項目名稱：", placeholder="例如：水果錢", key="ins_manual_item") if item_input == "手動輸入新項目..." else item_input
                amount_input = st.number_input("金額 (元)", min_value=0, step=1, value=0, key="ins_amount")
                handler_input = st.selectbox("經手人", st.session_state.common_handlers, key="ins_handler")
                
                if st.button("💾 確定儲存並上傳至雲端", type="primary", use_container_width=True, key="save_normal_btn"):
                    if not item_final.strip() or amount_input <= 0:
                        st.error("❌ 【防呆阻擋】項目欄位不可為空，且金額必須大於 0 元！")
                    elif action_type == "支出" and "儲值" in item_final:
                        st.error("❌ 【防呆阻擋】支出模式下禁止使用任何包含「儲值」的項目！")
                    else:
                        new_row = {
                            "流水號": next_id, "交易日期": log_date, "戶別": resident_input, "項目摘要": item_final.strip(),
                            "支出金額": amount_input if action_type == "支出" else 0,
                            "收入金額": amount_input if action_type == "收入" else 0,
                            "經手人": handler_input, "系統登錄時間": current_time_str
                        }
                        with st.spinner("正在將資料同步至雲端..."):
                            updated_df = pd.concat([st.session_state.ledger_data, pd.DataFrame([new_row])], ignore_index=True)
                            if save_cloud_ledger(updated_df):
                                st.session_state.ledger_data = updated_df
                                st.success("🎉 資料成功傳入雲端！")
                                time.sleep(0.5)
                                st.rerun()
                                
            else:
                st.subheader("🔄 執行住戶之間互相轉帳")
                log_date = st.date_input("轉帳日期", value=today_dt, key="trans_date")
                from_res = st.selectbox("👤 轉出款項戶別 (扣錢)", st.session_state.resident_list, index=0, key="trans_from")
                to_res = st.selectbox("👤 接收款項戶別 (加錢)", st.session_state.resident_list, index=1, key="trans_to")
                transfer_amount = st.number_input("轉帳金額 (元)", min_value=0, step=1, value=0, key="trans_amount")
                handler_input = st.selectbox("經手人", st.session_state.common_handlers, key="trans_handler")
                memo = st.text_input("備註說明", value="", placeholder="例如：代墊款項", key="trans_memo")
                
                if st.button("🚀 確定執行住戶互轉上傳", type="primary", use_container_width=True, key="save_trans_btn"):
                    if from_res == to_res or transfer_amount <= 0:
                        st.error("❌ 【防呆阻擋】轉出與轉入戶別不可相同，且金額必須大於 0 元！")
                    else:
                        memo_str = f" ({memo.strip()})" if memo.strip() else ""
                        row_out = {
                            "流水號": next_id, "交易日期": log_date, "戶別": from_res, "項目摘要": f"轉帳給 {to_res}{memo_str}",
                            "支出金額": transfer_amount, "收入金額": 0, "經手人": handler_input, "系統登錄時間": current_time_str
                        }
                        row_in = {
                            "流水號": next_id + 1, "交易日期": log_date, "戶別": to_res, "項目摘要": f"收到 {from_res} 轉帳{memo_str}",
                            "支出金額": 0, "收入金額": transfer_amount, "經手人": handler_input, "系統登錄時間": current_time_str
                        }
                        with st.spinner("正在將雙向轉帳資料寫入雲端..."):
                            updated_df = pd.concat([st.session_state.ledger_data, pd.DataFrame([row_out, row_in])], ignore_index=True)
                            if save_cloud_ledger(updated_df):
                                st.session_state.ledger_data = updated_df
                                st.success("🎉 轉帳成功！已同步至雲端兩端名冊！")
                                time.sleep(0.5)
                                st.rerun()

        with col_line:
            st.subheader("📱 LINE 住戶通知獨立搜尋與產生器")
            st.caption("✨ 請先選擇好查詢條件與戶別，再點擊按鈕產生專屬通知！")
            
            inspect_date = st.date_input("選擇要查詢的對帳日期", value=today_dt, key="line_inspect_date")
            target_line_res = st.selectbox("🎯 挑選欲生成的戶別：", st.session_state.resident_list, key="independent_line_res")
            
            if st.button("✨ 點擊按鈕，開始產生 LINE 訊息", type="primary", use_container_width=True, key="generate_line_btn"):
                st.session_state.generated_line_text = generate_line_text(
                    target_line_res, 
                    st.session_state.ledger_data, 
                    st.session_state.resident_initial_balances, 
                    check_date=inspect_date
                )
                st.toast("🎯 LINE 該戶通知訊息已成功生成！", icon="📱")
            
            st.markdown("📋 **即時生成的 LINE 通知文字：**")
            if st.session_state.generated_line_text.strip():
                st.code(st.session_state.generated_line_text, language="text")
            else:
                st.info("💡 請先點擊上方按鈕生成對帳內容。")

    with sub_tab2:
        st.markdown("### 📊 零用金進階日結、月結與負值（透支）戶別清查")
        
        df_all_ledger = st.session_state.ledger_data.copy()
        
        c_rep1, c_rep2 = st.columns(2)
        with c_rep1:
            st.markdown("#### 📅 選擇指定「日期」進行日結算")
            selected_daily_date = st.date_input("選擇結算日期", value=today_dt, key="report_daily_date")
            
            if not df_all_ledger.empty:
                df_all_ledger["交易日期_dt"] = pd.to_datetime(df_all_ledger["交易日期"]).dt.date
                df_daily_filtered = df_all_ledger[df_all_ledger["交易日期_dt"] == selected_daily_date]
                
                d_income = df_daily_filtered["收入金額"].sum()
                d_expense = df_daily_filtered["支出金額"].sum()
                
                st.metric("該日總收入", f"${d_income:,.0f} 元")
                st.metric("該日總支出", f"${d_expense:,.0f} 元")
                st.metric("當日淨變動", f"${d_income - d_expense:,.0f} 元")
                
                st.markdown(f"**📝 當日 ({selected_daily_date}) 交易明細清單：**")
                if not df_daily_filtered.empty:
                    st.dataframe(df_daily_filtered[["流水號", "戶別", "項目摘要", "收入金額", "支出金額", "經手人"]], use_container_width=True, hide_index=True)
                else:
                    st.info("該日無任何收支異動紀錄。")
            else:
                st.info("目前無零用金資料。")

        with c_rep2:
            st.markdown("#### 🗓️ 選擇指定「月份」進行月結算")
            current_year = today_dt.year
            current_month = today_dt.month
            selected_year = st.selectbox("選擇年份", [current_year - 1, current_year, current_year + 1], index=1, key="report_year")
            selected_month = st.selectbox("選擇月份", list(range(1, 13)), index=current_month - 1, key="report_month")
            
            if not df_all_ledger.empty:
                df_all_ledger["年份"] = pd.to_datetime(df_all_ledger["交易日期"]).dt.year
                df_all_ledger["月份"] = pd.to_datetime(df_all_ledger["交易日期"]).dt.month
                df_monthly_filtered = df_all_ledger[(df_all_ledger["年份"] == selected_year) & (df_all_ledger["月份"] == selected_month)]
                
                m_income = df_monthly_filtered["收入金額"].sum()
                m_expense = df_monthly_filtered["支出金額"].sum()
                
                st.metric("該月總收入", f"${m_income:,.0f} 元")
                st.metric("該月總支出", f"${m_expense:,.0f} 元")
                st.metric("當月淨變動", f"${m_income - m_expense:,.0f} 元")
                
                st.markdown(f"**📝 當月 ({selected_year}年{selected_month}月) 交易統計摘要：**")
                st.write(f"總共發生 **{len(df_monthly_filtered)}** 筆交易紀錄。")
            else:
                st.info("目前無零用金資料。")

        st.markdown("---")
        st.markdown("#### 🚨 各戶別目前總結算與【透支（負數）住戶】自動檢視")
        
        if not df_all_ledger.empty:
            res_balances = {}
            for res in st.session_state.resident_list:
                init_b = st.session_state.resident_initial_balances.get(res, 0)
                res_df = df_all_ledger[df_all_ledger["戶別"] == res]
                tot_inc = res_df["收入金額"].sum() if not res_df.empty else 0
                tot_exp = res_df["支出金額"].sum() if not res_df.empty else 0
                res_balances[res] = init_b + tot_inc - tot_exp
                
            df_res_bal = pd.DataFrame(list(res_balances.items()), columns=["戶別", "目前結餘 (元)"])
            df_negative = df_res_bal[df_res_bal["目前結餘 (元)"] < 0]
            
            if not df_negative.empty:
                st.markdown(f"""
                <div class="alert-box-custom">
                    ⚠️ <b>【警告】系統偵測到以下 {len(df_negative)} 戶目前零用金結餘為負數（透支／欠費狀態）：</b>
                </div>
                """, unsafe_allow_html=True)
                st.dataframe(df_negative, use_container_width=True, hide_index=True)
            else:
                st.success("🟢 目前全社區所有住戶零用金結餘皆正常（無負數透支戶）。")
                
            with st.expander("👀 點擊查看全社區各戶別目前結餘總表"):
                st.dataframe(df_res_bal, use_container_width=True, hide_index=True)
        else:
            st.info("尚無足夠資料進行餘額結算。")

    st.markdown("---")
    st.subheader("🪙 現場鈔票盤點對帳看板")
    
    df_all = st.session_state.ledger_data.copy()
    total_expense = df_all["支出金額"].sum() if not df_all.empty else 0
    total_income = df_all["收入金額"].sum() if not df_all.empty else 0
    book_balance = INITIAL_CASH + total_income - total_expense
    
    col_cash1, col_cash2 = st.columns(2)
    with col_cash1:
        st.session_state.cash_inventory["n1000"] = st.number_input("1000 元張數", min_value=0, step=1, value=st.session_state.cash_inventory["n1000"], key="c_1000")
        st.session_state.cash_inventory["n500"] = st.number_input("500 元張數", min_value=0, step=1, value=st.session_state.cash_inventory["n500"], key="c_500")
        st.session_state.cash_inventory["n100"] = st.number_input("100 元張數", min_value=0, step=1, value=st.session_state.cash_inventory["n100"], key="c_100")
    with col_cash2:
        st.session_state.cash_inventory["n50"] = st.number_input("50 元硬幣個數", min_value=0, step=1, value=st.session_state.cash_inventory["n50"], key="c_50")
        st.session_state.cash_inventory["n10"] = st.number_input("10 元硬幣個數", min_value=0, step=1, value=st.session_state.cash_inventory["n10"], key="c_10")
        st.session_state.cash_inventory["n1"] = st.number_input("1 元硬幣個數", min_value=0, step=1, value=st.session_state.cash_inventory["n1"], key="c_1")
        
    physical_total = (st.session_state.cash_inventory["n1000"] * 1000 + st.session_state.cash_inventory["n500"] * 500 + st.session_state.cash_inventory["n100"] * 100 + st.session_state.cash_inventory["n50"] * 50 + st.session_state.cash_inventory["n10"] * 10 + st.session_state.cash_inventory["n1"] * 1)
    diff = physical_total - book_balance
    
    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.metric("💻 系統帳面結餘", f"${book_balance:,.0f} 元")
    c_m2.metric("🪙 現場實點現鈔", f"${physical_total:,.0f} 元")
    
    if diff == 0:
        st.success("🟢 帳目完全吻合！一塊錢都沒差！")
    elif diff < 0:
        st.error(f"🔴 帳目不符❌ 實際少錢: {diff:,.0f} 元")
    else:
        st.warning(f"🟡 帳目不符❌ 實際多錢: +{diff:,.0f} 元")

# ==========================================
# 頁籤 2：🚗 車位登記及查詢 (含未登記車位戶別清查)
# ==========================================
elif menu == "🚗 車位登記及查詢":
    st.header("🚗 社區車位資產管理系統 (支援自動綁定、租客標記與未登記車位清查)")
    
    df_park_raw = st.session_state.parking_data.copy()
    
    if "身分標記" not in df_park_raw.columns:
        df_park_raw["身分標記"] = "屋主"
    if "車輛備註" not in df_park_raw.columns:
        df_park_raw["車輛備註"] = ""

    b1_total_cap = sum(1 for s in st.session_state.car_space_mapping.values() if s.startswith("B1-"))
    b2_total_cap = sum(1 for s in st.session_state.car_space_mapping.values() if s.startswith("B2-"))
    b3_total_cap = sum(1 for s in st.session_state.car_space_mapping.values() if s.startswith("B3-"))
    total_car_cap = b1_total_cap + b2_total_cap + b3_total_cap
    
    moto_cap = len([s for s in st.session_state.moto_space_mapping.values() if s.strip() != ""])
    if moto_cap == 0:
        moto_cap = st.session_state.parking_capacities.get("機車位", 112)

    b1_used_spaces = set()
    b2_used_spaces = set()
    b3_used_spaces = set()
    moto_used_spaces = set()
    
    total_registered_cars = 0
    total_registered_motos = 0
    tenant_car_count = 0
    tenant_moto_count = 0
    tenant_units_set = set()
    
    units_with_registered_car = set()
    units_with_registered_moto = set()
    
    if not df_park_raw.empty and "車位號碼" in df_park_raw.columns and "車牌號碼" in df_park_raw.columns:
        for _, row in df_park_raw.iterrows():
            space_no = str(row["車位號碼"])
            plate = str(row["車牌號碼"]).strip().upper()
            is_tenant = str(row.get("身分標記", "屋主")) == "租客"
            res_val = str(row.get("戶別", ""))
            
            has_valid_plate = bool(
                plate and 
                plate != "NAN" and 
                plate != "NONE" and 
                plate != "" and 
                not plate.startswith("CAR-") and 
                not plate.startswith("MOTO-")
            )
            
            is_car_space = "汽車" in space_no or "B1-" in space_no or "B2-" in space_no or "B3-" in space_no
            is_moto_space = "機車" in space_no
            
            if has_valid_plate:
                if is_car_space:
                    total_registered_cars += 1
                    units_with_registered_car.add(res_val)
                    if is_tenant:
                        tenant_car_count += 1
                        tenant_units_set.add(res_val)
                elif is_moto_space:
                    total_registered_motos += 1
                    units_with_registered_moto.add(res_val)
                    if is_tenant:
                        tenant_moto_count += 1
                        tenant_units_set.add(res_val)

            if has_valid_plate:
                if "汽車位(B1)" in space_no or space_no.startswith("B1-"):
                    b1_used_spaces.add(space_no)
                elif "汽車位(B2)" in space_no or space_no.startswith("B2-"):
                    b2_used_spaces.add(space_no)
                elif "汽車位(B3)" in space_no or space_no.startswith("B3-"):
                    b3_used_spaces.add(space_no)
                elif "機車位" in space_no:
                    moto_used_spaces.add(space_no)

    b1_used = len(b1_used_spaces)
    b2_used = len(b2_used_spaces)
    b3_used = len(b3_used_spaces)
    total_car_used = len(b1_used_spaces.union(b2_used_spaces).union(b3_used_spaces))
    moto_used = len(moto_used_spaces)
    
    st.markdown("### 📊 社區車位資產與未登記車輛清查儀表板")
    dash_col1, dash_col2 = st.columns(2)
    
    with dash_col1:
        st.markdown(f"**🅿️ 汽車位總結算：實體使用 {total_car_used} / 總格數 {total_car_cap} 格 (剩餘空位：{total_car_cap - total_car_used} 格)**")
        st.progress(min(total_car_used / total_car_cap, 1.0) if total_car_cap > 0 else 0.0)
        st.caption(f"✨ 總計登記汽車數：{total_registered_cars} 台 ｜ **(租客車數: {tenant_car_count} 台)**")
        
        st.caption(f" ├── 🔹 B1 汽車區：已使用 {b1_used} / 總格數 {b1_total_cap} 格")
        st.caption(f" ├── 🔹 B2 汽車區：已使用 {b2_used} / 總格數 {b2_total_cap} 格")
        st.caption(f" └── 🔹 B3 汽車區：已使用 {b3_used} / 總格數 {b3_total_cap} 格")

    with dash_col2:
        st.markdown(f"**🛵 機車位總結算：實體使用 {moto_used} / 總格數 {moto_cap} 格 (剩餘空位：{moto_cap - moto_used} 格)**")
        st.progress(min(moto_used / moto_cap, 1.0) if moto_cap > 0 else 0.0)
        st.caption(f"✨ 總計登記機車數：{total_registered_motos} 台 ｜ **(租客機車數: {tenant_moto_count} 台)**")
        st.caption(f" └── 🛵 機車專用區：已使用 {moto_used} / 總格數 {moto_cap} 格")

    all_units_set = set(st.session_state.resident_list) - {"1A"}
    unregistered_car_units = sorted(list(all_units_set - units_with_registered_car))
    unregistered_moto_units = sorted(list(all_units_set - units_with_registered_moto))
    
    with st.expander("🔍 點擊展開：未登記「汽車」或「機車」之住戶清單"):
        uc_col1, uc_col2 = st.columns(2)
        with uc_col1:
            st.markdown(f"🚗 **未登記有效汽車車牌之戶別 ({len(unregistered_car_units)} 戶)：**")
            st.info(", ".join(unregistered_car_units) if unregistered_car_units else "無")
        with uc_col2:
            st.markdown(f"🛵 **未登記有效機車車牌之戶別 ({len(unregistered_moto_units)} 戶)：**")
            st.info(", ".join(unregistered_moto_units) if unregistered_moto_units else "無")

    # 智慧動態聯集：涵蓋手動標記以及總登記數 >= 3 的戶別
    household_counts = df_park_raw["戶別"].value_counts() if not df_park_raw.empty and "戶別" in df_park_raw.columns else pd.Series(dtype=int)
    exceeded_households = set(household_counts[household_counts >= 3].index.tolist())
    
    if not df_park_raw.empty and "車輛備註" in df_park_raw.columns:
        memo_marked = set(df_park_raw[df_park_raw["車輛備註"].str.contains("第三台車|彈性", na=False)]["戶別"].tolist())
    else:
        memo_marked = set()
        
    special_third_car_units = sorted(list(exceeded_households.union(memo_marked)))

    if special_third_car_units:
        st.markdown(f"""
        <div class="info-box-custom">
            🚗🚙 <b>【第三台車與特殊車位整合清單 (含自動防呆偵測)】</b>： 共計 <b>{len(special_third_car_units)}</b> 戶擁有第三台車或彈性車位 -> <code>{", ".join(special_third_car_units)}</code>
        </div>
        """, unsafe_allow_html=True)

    if tenant_units_set:
        st.markdown(f"""
        <div class="info-box-custom">
            👥 <b>【目前擁有租客車輛之戶別整合清單】</b>： 共計 <b>{len(tenant_units_set)}</b> 戶有租客車輛進駐 -> <code>{", ".join(sorted(list(tenant_units_set)))}</code>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    p_col1, p_col2 = st.columns([3, 2])
    
    with p_col1:
        st.subheader("🔍 車位資產檢索與空位即時判斷")
        
        view_mode = st.radio("顯示檢視模式：", ["僅顯示目前空位 (未登記車牌)", "顯示全部車位資產登記"], horizontal=True, key="park_view_mode")
        p_search = st.text_input("💡 請輸入 戶別(如:2A)、車位區域、車主姓名 或 車牌 快速檢索：", key="park_search_input")
        
        df_park_display = df_park_raw.copy()
        if not df_park_display.empty:
            def check_status(row_data):
                plate_val = str(row_data.get("車牌號碼", "")).strip().upper()
                if not plate_val or plate_val == "NAN" or plate_val == "NONE" or plate_val == "" or plate_val.startswith("CAR-") or plate_val.startswith("MOTO-"):
                    return "🟢 綁定空位 (未註冊車牌)"
                else:
                    tag = str(row_data.get("身分標記", "屋主"))
                    memo_info = str(row_data.get("車輛備註", "")).strip()
                    memo_str = f" [備註: {memo_info}]" if memo_info and memo_info != "nan" else ""
                    return f"🔴 已登記車輛 ({tag}){memo_str}"

            df_park_display["即時狀態"] = df_park_display.apply(check_status, axis=1)
            
            if view_mode == "僅顯示目前空位 (未登記車牌)":
                df_park_display = df_park_display[df_park_display["即時狀態"].str.contains("空位")]

            if p_search.strip():
                k = p_search.strip().lower()
                df_park_display = df_park_display[
                    df_park_display["車位號碼"].astype(str).str.lower().str.contains(k, na=False) | 
                    df_park_display["車主姓名"].astype(str).str.lower().str.contains(k, na=False) | 
                    df_park_display["車牌號碼"].astype(str).str.lower().str.contains(k, na=False) |
                    df_park_display["戶別"].astype(str).str.lower().str.contains(k, na=False) |
                    df_park_display["身分標記"].astype(str).str.lower().str.contains(k, na=False) |
                    df_park_display["車輛備註"].astype(str).str.lower().str.contains(k, na=False)
                ]
            
            def highlight_empty_slots(row):
                if "空位" in str(row.get("即時狀態", "")):
                    return ['background-color: #FFF3CD; color: #856404; font-weight: bold;' for _ in row]
                else:
                    return ['' for _ in row]

            st.dataframe(df_park_display.style.apply(highlight_empty_slots, axis=1), use_container_width=True, hide_index=True)
        else:
            st.info("💡 目前車位資料庫尚無資料。")
            
    with p_col2:
        st.subheader("📝 車位持有異動登記 (支援第三台車與特殊備註)")
        
        p_res_code = st.selectbox("選擇持有戶別：", st.session_state.resident_list, key="p_reg_res")
        
        # 智慧數量防呆：自動計算該戶目前已登記的車位數量
        existing_res_records = df_park_raw[df_park_raw["戶別"] == p_res_code] if not df_park_raw.empty and "戶別" in df_park_raw.columns else pd.DataFrame()
        current_res_count = len(existing_res_records)
        is_auto_third_car = current_res_count >= 2
        
        if is_auto_third_car:
            st.markdown(f"""
            <div class="alert-box-custom" style="padding: 8px; font-size: 13px;">
                ⚠️ <b>防呆偵測</b>：戶別 <b>{p_res_code}</b> 目前已有 {current_res_count} 筆登記，此筆將自動歸類為第三台車或彈性車位！
            </div>
            """, unsafe_allow_html=True)

        p_space_category = st.radio("選擇車格型態：", ["🚗 汽車格", "🛵 機車格"], horizontal=True, key="p_space_cat")
        is_car_mode = "汽車" in p_space_category
        
        default_bound = ""
        if is_car_mode:
            default_bound = st.session_state.car_space_mapping.get(p_res_code, "")
            if default_bound:
                floor_prefix = default_bound.split("-")[0] if "-" in default_bound else "B3"
                num_part = default_bound.split("-")[1] if "-" in default_bound else default_bound
                default_full_id = f"汽車位({floor_prefix}){num_part}"
            else:
                default_full_id = f"汽車位(B3)-{p_res_code}"
        else:
            default_bound = st.session_state.moto_space_mapping.get(p_res_code, "")
            if default_bound:
                default_full_id = f"機車位-{default_bound}"
            else:
                default_full_id = f"機車位-{p_res_code}"

        use_custom_space = st.checkbox("⚙️ 啟用彈性指定車位 (適用於第二台車、第三台車或停放特殊車位)", key="p_use_custom_space")
        
        if use_custom_space:
            p_id = st.text_input("請手動輸入/調整車位代號：", value=default_full_id, placeholder="例如：B3-33 或 訪客車位", key="p_custom_space_input")
        else:
            p_id = default_full_id
            st.markdown(f"""
            <div class="info-box-custom">
                🔗 <b>【雲端自動帶入車位】</b> 戶別 {p_res_code} 對應車位：<b>{p_id}</b>
            </div>
            """, unsafe_allow_html=True)

        is_tenant_checked = st.checkbox("🏷️ 勾選此車輛為【租客車輛】 (若不勾選則預設為屋主車輛)", key="p_reg_is_tenant")
        identity_tag = "租客" if is_tenant_checked else "屋主"

        raw_plate_input = st.text_input("車牌號碼 (車牌辨識免破折號)：", placeholder="ABC1234 (留白即為空位)", key="p_reg_plate")
        p_plate = format_plate_number(raw_plate_input)
        
        if raw_plate_input.strip() and p_plate != raw_plate_input.strip().upper():
            st.caption(f"✨ 【車牌自動防呆轉換】已轉為無破折號標準車牌：**{p_plate}**")

        p_name = st.text_input("車主姓名：", placeholder="例如：詹詹", key="p_reg_name").strip()
        p_phone = st.text_input("連絡電話：", placeholder="例如：0912345678", key="p_reg_phone")
        
        # 若系統判定為第三台車以上，自動在備註中預填或提示
        default_memo_text = "第三台車" if is_auto_third_car else ""
        p_vehicle_memo = st.text_input("📝 車輛備註 (選填，說明特殊狀況)：", value=default_memo_text, placeholder="例如：第三台車、租客第二台車、停放臨時格等", key="p_reg_vehicle_memo")
        
        if st.button("💾 新增車位資產登記", type="primary", use_container_width=True, key="p_reg_btn"):
            cleaned_phone = p_phone.strip().replace("-", "").replace(" ", "")
            if not p_name or not p_phone.strip():
                st.error("❌ 【防呆阻擋】車主姓名與連絡電話為必填項目，不可留白！")
            elif len(cleaned_phone) != 10 or not cleaned_phone.isdigit():
                st.error(f"❌ 【防呆阻擋】聯絡電話格式有誤！您輸入了 {len(cleaned_phone)} 碼（目前規定手機號碼必須為精確 10 碼數字，例如 0912345678）。")
            else:
                with st.spinner("正在將新車位資料寫入雲端..."):
                    next_p_id = int(df_park_raw["流水號"].max()) + 1 if not df_park_raw.empty and "流水號" in df_park_raw.columns and not df_park_raw["流水號"].isnull().all() else 1
                    
                    new_park_row = {
                        "流水號": next_p_id, 
                        "車位號碼": p_id, 
                        "戶別": p_res_code, 
                        "車牌號碼": p_plate, 
                        "車主姓名": p_name,
                        "連絡電話": str(p_phone.strip()), 
                        "身分標記": identity_tag,
                        "車輛備註": p_vehicle_memo.strip(),
                        "登記日期": datetime.date.today().strftime("%Y-%m-%d")
                    }
                    df_updated_park = pd.concat([df_park_raw, pd.DataFrame([new_park_row])], ignore_index=True)
                    if save_parking_ledger(df_updated_park):
                        st.session_state.parking_data = df_updated_park
                        st.success(f"🎉 車位 {p_id} 登記成功（身分：{identity_tag}，車牌：{p_plate if p_plate else '無'}）！")
                        time.sleep(0.5)
                        st.rerun()

    st.markdown("---")
    st.subheader("🚗 ＆ 🛵 住戶專屬車位雲端固定綁定管理後台")
    
    bind_tab1, bind_tab2 = st.tabs(["🚗 汽車位固定綁定設定", "🛵 機車位固定綁定設定"])
    
    with bind_tab1:
        with st.form("car_binding_form"):
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                bind_res = st.selectbox("選擇要綁定的住戶戶別", st.session_state.resident_list, key="bind_car_res")
                bind_floor = st.selectbox("選擇停車場層級", ["B1", "B2", "B3"], key="bind_car_floor")
            with b_col2:
                bind_space_no = st.text_input("車位編號 (例如: 104 或 33)", placeholder="104", key="bind_car_no")
                
            bind_submit = st.form_submit_button("🔗 儲存並連動更新車位登記", type="primary")
            
            if bind_submit:
                if not bind_space_no.strip():
                    st.error("❌ 【防呆阻擋】車位編號不可為空！")
                else:
                    raw_car_no = bind_space_no.strip()
                    
                    if raw_car_no.endswith("4"):
                        clean_num_str = "".join([c for c in raw_car_no if c.isdigit()])
                        if clean_num_str:
                            num_val = int(clean_num_str)
                            converted_car_no = f"{num_val - 1}-1"
                        else:
                            converted_car_no = raw_car_no
                    else:
                        converted_car_no = raw_car_no

                    combined_space = f"{bind_floor}-{converted_car_no}"
                    
                    st.session_state.car_space_mapping[bind_res] = combined_space
                    save_binding_mapping("汽車位綁定", st.session_state.car_space_mapping)
                    
                    df_p_current = st.session_state.parking_data.copy()
                    if not df_p_current.empty:
                        df_motos_only = df_p_current[df_p_current["車位號碼"].str.contains("機車", na=False)].copy()
                        df_other_cars = df_p_current[(df_p_current["車位號碼"].str.contains("汽車", na=False)) & (df_p_current["戶別"] != bind_res)].copy()
                    else:
                        df_motos_only = pd.DataFrame(columns=["流水號", "車位號碼", "戶別", "車牌號碼", "車主姓名", "連絡電話", "身分標記", "車輛備註", "登記日期"])
                        df_other_cars = pd.DataFrame(columns=["流水號", "車位號碼", "戶別", "車牌號碼", "車主姓名", "連絡電話", "身分標記", "車輛備註", "登記日期"])
                    
                    new_car_reg_row = {
                        "車位號碼": f"汽車位({bind_floor}){converted_car_no}",
                        "戶別": bind_res,
                        "車牌號碼": "",
                        "車主姓名": f"住戶-{bind_res}",
                        "連絡電話": "0900000000",
                        "身分標記": "屋主",
                        "車輛備註": "",
                        "登記日期": datetime.date.today().strftime("%Y-%m-%d")
                    }
                    
                    combined_park_df = pd.concat([df_other_cars, df_motos_only, pd.DataFrame([new_car_reg_row])], ignore_index=True)
                    combined_park_df["流水號"] = range(1, len(combined_park_df) + 1)
                    
                    if save_parking_ledger(combined_park_df):
                        st.session_state.parking_data = combined_park_df
                        st.success(f"🎉 雲端與車位登記同步成功：戶別 **{bind_res}** 成功綁定 **{combined_space}**（預設為無車牌空位）！")
                        time.sleep(1)
                        st.rerun()

        if st.session_state.car_space_mapping:
            st.markdown("#### 📋 目前雲端已建立的汽車位綁定清單：")
            car_map_df = pd.DataFrame(list(st.session_state.car_space_mapping.items()), columns=["戶別", "車位編號"])
            st.dataframe(car_map_df[car_map_df["車位編號"] != ""], use_container_width=True, hide_index=True)

    with bind_tab2:
        with st.form("moto_binding_form"):
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                bind_m_res = st.selectbox("選擇要綁定的住戶戶別", st.session_state.resident_list, key="bind_moto_res")
            with m_col2:
                bind_m_no = st.text_input("機車位編號 (例如: 4 或 33)", placeholder="4", key="bind_moto_no")
                
            bind_m_submit = st.form_submit_button("🔗 儲存並連動更新車位登記", type="primary")
            
            if bind_m_submit:
                if not bind_m_no.strip():
                    st.error("❌ 【防呆阻擋】機車位編號不可為空！")
                else:
                    raw_moto_no = bind_m_no.strip().replace("機車位", "").replace("(", "").replace(")", "").strip()
                    
                    if raw_moto_no.endswith("4"):
                        clean_m_str = "".join([c for c in raw_moto_no if c.isdigit()])
                        if clean_m_str:
                            m_val = int(clean_m_str)
                            formatted_moto = f"{m_val - 1}-1"
                        else:
                            formatted_moto = raw_moto_no
                    else:
                        formatted_moto = raw_moto_no
                    
                    st.session_state.moto_space_mapping[bind_m_res] = formatted_moto
                    save_binding_mapping("機車位綁定", st.session_state.moto_space_mapping)
                    
                    df_p_current = st.session_state.parking_data.copy()
                    if not df_p_current.empty:
                        df_cars_only = df_p_current[df_p_current["車位號碼"].str.contains("汽車", na=False)].copy()
                        df_other_motos = df_p_current[(df_p_current["車位號碼"].str.contains("機車", na=False)) & (df_p_current["戶別"] != bind_m_res)].copy()
                    else:
                        df_cars_only = pd.DataFrame(columns=["流水號", "車位號碼", "戶別", "車牌號碼", "車主姓名", "連絡電話", "身分標記", "車輛備註", "登記日期"])
                        df_other_motos = pd.DataFrame(columns=["流水號", "車位號碼", "戶別", "車牌號碼", "車主姓名", "連絡電話", "身分標記", "車輛備註", "登記日期"])
                    
                    new_moto_reg_row = {
                        "車位號碼": f"機車位-{formatted_moto}",
                        "戶別": bind_m_res,
                        "車牌號碼": "",
                        "車主姓名": f"住戶-{bind_m_res}",
                        "連絡電話": "0900000000",
                        "身分標記": "屋主",
                        "車輛備註": "",
                        "登記日期": datetime.date.today().strftime("%Y-%m-%d")
                    }
                    
                    combined_park_df = pd.concat([df_cars_only, df_other_motos, pd.DataFrame([new_moto_reg_row])], ignore_index=True)
                    combined_park_df["流水號"] = range(1, len(combined_park_df) + 1)
                    
                    if save_parking_ledger(combined_park_df):
                        st.session_state.parking_data = combined_park_df
                        st.success(f"🎉 雲端與車位登記同步成功：戶別 **{bind_m_res}** 成功綁定機車位 **{formatted_moto}**（預設為無車牌空位）！")
                        time.sleep(1)
                        st.rerun()

        if st.session_state.moto_space_mapping:
            st.markdown("#### 📋 目前雲端已建立的機車位綁定清單：")
            moto_map_df = pd.DataFrame(list(st.session_state.moto_space_mapping.items()), columns=["戶別", "車位編號"])
            st.dataframe(moto_map_df[moto_map_df["車位編號"] != ""], use_container_width=True, hide_index=True)

# ==========================================
# 頁籤 3：⚙️ 常駐名冊與機車抽籤管理
# ==========================================
else:
    st.header("⚙️ 物業後台核心常駐清單與年度機車位隨機抽籤")
    tab_set1, tab_set2 = st.tabs(["📝 基礎名冊與公設排除設定", "🏍️ 112戶年度機車位隨機抽籤與雲端同步"])
    
    with tab_set1:
        col_set1, col_set2 = st.columns(2)
        
        with col_set1:
            st.markdown("#### 📝 常用項目/摘要維護")
            new_item = st.text_input("➕ 增加常用項目：", key="backend_add_item")
            if st.button("確認增加項目", key="btn_add_item") and new_item.strip():
                if new_item.strip() not in st.session_state.common_items:
                    st.session_state.common_items.append(new_item.strip())
                    st.toast(f"已新增項目: {new_item.strip()}", icon="📝")
                    time.sleep(0.5)
                    st.rerun()
            del_item = st.selectbox("➖ 刪除常用項目：", ["請選擇要刪除的項目..."] + st.session_state.common_items, key="backend_del_item")
            if st.button("確認刪除項目", key="btn_del_item") and del_item != "請選擇要刪除的項目...":
                st.session_state.common_items.remove(del_item)
                st.toast(f"已刪除項目: {del_item}", icon="🗑️")
                time.sleep(0.5)
                st.rerun()

            st.markdown("---")
            st.markdown("#### 🏠 管理中心排除設定 (不參與機車抽籤)")
            exclude_input = st.selectbox("選擇要排除參與機車抽籤的公設/管理戶別：", st.session_state.resident_list, index=0, key="exc_res_select")
            if st.button("➕ 加入抽籤排除名單", key="add_exc_btn"):
                if exclude_input not in st.session_state.lottery_excluded_res:
                    st.session_state.lottery_excluded_res.append(exclude_input)
                    st.success(f"🎉 戶別 {exclude_input} 已成功加入抽籤排除名單！")
                    time.sleep(0.5)
                    st.rerun()
            
            st.write(f"目前排除名單: `{st.session_state.lottery_excluded_res}`")
            if st.button("🧹 清空排除名單 (恢復全部參與)", key="clear_exc_btn"):
                st.session_state.lottery_excluded_res = []
                st.success("🎉 已清空排除名單！")
                time.sleep(0.5)
                st.rerun()
                
        with col_set2:
            st.markdown("#### 👤 經手人名冊維護")
            new_handler = st.text_input("➕ 增加經手人員(職稱-人員)：", key="backend_add_handler")
            if st.button("確認增加經手人", key="btn_add_handler") and new_handler.strip():
                if new_handler.strip() not in st.session_state.common_handlers:
                    st.session_state.common_handlers.append(new_handler.strip())
                    st.toast(f"已上架新經手人: {new_handler.strip()}", icon="👤")
                    time.sleep(0.5)
                    st.rerun()
            del_handler = st.selectbox("➖ 刪除特定經手人：", ["請選擇要刪除的經手人..."] + st.session_state.common_handlers, key="backend_del_handler")
            if st.button("確認刪除經手人", key="btn_del_handler") and del_handler != "請選擇要刪除的經手人...":
                st.session_state.common_handlers.remove(del_handler)
                st.toast(f"已撤銷經手人: {del_handler}", icon="🗑️")
                time.sleep(0.5)
                st.rerun()

    with tab_set2:
        st.markdown("### 🎲 112 戶年度機車位隨機抽籤模組 (智慧保留現有車牌與身分)")
        st.markdown("""
        <div class="highlight-box">
            📌 <b>抽籤規則與隱私說明</b>：<br>
            1. 系統自動過濾排除名單（如 <b>1A 管理中心</b>），僅對純住戶進行隨機洗牌。<br>
            2. 機車位編號為純數字 <b>1 到 112 號</b>。<br>
            3. 只有當<b>尾數為 4</b> 的數字才會自動以「<b>前一個數字-1</b>」表示。<br>
            4. <b>智慧保留機制</b>：重新抽籤時，若該住戶原本已登記有車牌號碼，<b>系統將自動對應並完美保留原車牌、車主資訊與身分標記</b>！
        </div>
        """, unsafe_allow_html=True)
        
        active_participants = [res for res in st.session_state.resident_list if res not in st.session_state.lottery_excluded_res]
        max_moto_slots = st.session_state.parking_capacities["機車位"]
        
        valid_moto_spaces = []
        for i in range(1, max_moto_slots + 1):
            s_str = str(i)
            if s_str.endswith("4"):
                converted_num = f"{i-1}-1"
                valid_moto_spaces.append(f"{converted_num}")
            else:
                valid_moto_spaces.append(f"{i}")
            
        st.info(f"💡 實際參與抽籤戶數：{len(active_participants)} 戶 | 機車位總格數：{len(valid_moto_spaces)} 格")
        
        if st.button("🎲 開始執行年度機車位隨機抽籤", type="primary", key="run_moto_lottery_btn"):
            if not active_participants:
                st.error("❌ 【防呆阻擋】參與抽籤名單為空！")
            elif len(active_participants) > len(valid_moto_spaces):
                st.error(f"❌ 【名額超載阻擋】參與抽籤戶數大於機車格總數！")
            else:
                shuffled_spaces = valid_moto_spaces.copy()
                random.shuffle(shuffled_spaces)
                
                existing_moto_info = {}
                df_park_current = st.session_state.parking_data.copy()
                if not df_park_current.empty:
                    old_motos = df_park_current[df_park_current["車位號碼"].str.contains("機車", na=False)]
                    for _, row in old_motos.iterrows():
                        res = str(row["戶別"]).strip()
                        space_full = str(row["車位號碼"]).strip()
                        old_space_no = space_full.replace("機車位-", "").replace("機車位", "").strip()
                        
                        plate_val = format_plate_number(str(row["車牌號碼"]))
                        existing_moto_info[res] = {
                            "舊車位編號": old_space_no if old_space_no else "無",
                            "車牌號碼": plate_val,
                            "車主姓名": str(row["車主姓名"]).strip() if pd.notna(row["車主姓名"]) else f"住戶-{res}",
                            "連絡電話": str(row["連絡電話"]).strip() if pd.notna(row["連絡電話"]) else "0900000000",
                            "身分標記": str(row["身分標記"]).strip() if "身分標記" in row and pd.notna(row["身分標記"]) else "屋主",
                            "車輛備註": str(row["車輛備註"]).strip() if "車輛備註" in row and pd.notna(row["車輛備註"]) else ""
                        }

                lottery_results = []
                moto_mapping_updates = {}
                
                for i, res in enumerate(active_participants):
                    assigned_space = shuffled_spaces[i]
                    moto_mapping_updates[res] = assigned_space
                    
                    old_space = existing_moto_info.get(res, {}).get("舊車位編號", st.session_state.moto_space_mapping.get(res, "無"))
                    if not old_space:
                        old_space = "無"

                    if res in existing_moto_info and existing_moto_info[res]["車牌號碼"] != "":
                        saved_plate = existing_moto_info[res]["車牌號碼"]
                        saved_name = existing_moto_info[res]["車主姓名"]
                        saved_phone = existing_moto_info[res]["連絡電話"]
                        saved_tag = existing_moto_info[res]["身分標記"]
                        saved_memo = existing_moto_info[res]["車輛備註"]
                    else:
                        saved_plate = ""
                        saved_name = f"住戶-{res}"
                        saved_phone = "0900000000"
                        saved_tag = "屋主"
                        saved_memo = ""
                        
                    lottery_results.append({
                        "戶別": res,
                        "舊的車位編號": old_space,
                        "新的車位編號": assigned_space,
                        "車位號碼": f"機車位-{assigned_space}",
                        "車牌號碼": saved_plate,   
                        "車主姓名": saved_name,
                        "連絡電話": saved_phone,
                        "身分標記": saved_tag,
                        "車輛備註": saved_memo,
                        "登記日期": datetime.date.today().strftime("%Y-%m-%d")
                    })
                
                st.session_state.temp_moto_mapping_updates = moto_mapping_updates
                st.session_state.temp_lottery_df = pd.DataFrame(lottery_results)
                st.success("🎉 機車抽籤模擬完成！請於下方確認新舊車位對照無誤後，再點擊按鈕同步至雲端。")

        if 'temp_lottery_df' in st.session_state and not st.session_state.temp_lottery_df.empty:
            st.markdown("#### 📋 本次抽籤結果預覽 (新舊車位對照)：")
            
            df_preview_clean = st.session_state.temp_lottery_df[["戶別", "舊的車位編號", "新的車位編號"]].copy()
            st.dataframe(df_preview_clean, use_container_width=True, hide_index=True)
            
            if st.button("☁️ 確認無誤，一鍵更新並覆蓋雲端機車位資料庫", type="primary", key="sync_moto_to_cloud_btn"):
                if 'temp_moto_mapping_updates' in st.session_state:
                    st.session_state.moto_space_mapping.update(st.session_state.temp_moto_mapping_updates)
                    save_binding_mapping("機車位綁定", st.session_state.moto_space_mapping)

                df_park_current = st.session_state.parking_data.copy()
                
                if not df_park_current.empty:
                    df_cars_only = df_park_current[df_park_current["車位號碼"].str.contains("汽車", na=False)].copy()
                else:
                    df_cars_only = pd.DataFrame(columns=["流水號", "車位號碼", "戶別", "車牌號碼", "車主姓名", "連絡電話", "身分標記", "車輛備註", "登記日期"])
                
                new_moto_df = st.session_state.temp_lottery_df[["車位號碼", "戶別", "車牌號碼", "車主姓名", "連絡電話", "身分標記", "車輛備註", "登記日期"]].copy()
                
                combined_df = pd.concat([df_cars_only, new_moto_df], ignore_index=True)
                combined_df["流水號"] = range(1, len(combined_df) + 1)
                
                with st.spinner("正在將年度抽籤結果同步寫入雲端試算表..."):
                    if save_parking_ledger(combined_df):
                        st.session_state.parking_data = combined_df
                        st.success("🎉 恭喜！機車位抽籤結果已成功同步至雲端，且原有車主的車牌、身分與備註均已完美保留！")
                        time.sleep(1)
                        st.rerun()