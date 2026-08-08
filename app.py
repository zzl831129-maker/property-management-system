# -*- coding: utf-8 -*-
"""
社區物業智慧管理系統
"""

import streamlit as st
import pandas as pd
import plotly.express as px
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
st.caption("✨7/29")

# ==========================================
# 🔌 Google Sheets 雲端連線實體大腦 (已修正 SPREADSHEET_NAME)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)
# 修正重點：改為直接帶入 Google 試算表在雲端硬碟中的檔案名稱，解決 Public 寫入報錯問題
SPREADSHEET_NAME = "物業管理分析系統"  

def generate_default_units():
    units = []
    for floor in range(2, 16):
        for room in ["A", "B", "C", "D", "E", "F", "G", "H"]:
            unit = f"{floor}{room}"
            if unit != "2A":
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
    st.markdown("### 🔍 關鍵字快查與財務結算")
    
    sub_tab1, sub_tab2 = st.tabs(["📝 一般流水帳與快查登記", "📊 日/月結與透支戶清查報表"])
    
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
                    
                    st.markdown("##### 📊 【日結視覺化】今日各戶收支金額佔比分析")
                    df_daily_filtered["總金額"] = df_daily_filtered["收入金額"] + df_daily_filtered["支出金額"]
                    df_daily_agg = df_daily_filtered.groupby("戶別")["總金額"].sum().reset_index()
                    df_daily_agg = df_daily_agg[df_daily_agg["總金額"] > 0].sort_values(by="總金額", ascending=False)
                    
                    if not df_daily_agg.empty:
                        fig_daily_bar = px.bar(
                            df_daily_agg,
                            x="總金額",
                            y="戶別",
                            orientation="h",
                            text="總金額"
                        )
                        fig_daily_bar.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=20, r=20, t=20, b=20))
                        st.plotly_chart(fig_daily_bar, use_container_width=True)
                        
                        top_res = df_daily_agg.iloc[0]
                        st.info(f"💡 **今日收支最頻繁／金額佔比最高戶別**：【{top_res['戶別']}】 (總計 ${top_res['總金額']:,.0f} 元)")
                    else:
                        st.caption("今日各戶無金額產生。")
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
                
                if not df_monthly_filtered.empty:
                    st.markdown("##### 📈 【月結視覺化】本月每日收支走勢與佔比圖")
                    df_monthly_filtered["交易日期_str"] = df_monthly_filtered["交易日期"].astype(str)
                    df_day_trend = df_monthly_filtered.groupby("交易日期_str")[["收入金額", "支出金額"]].sum()
                    st.line_chart(df_day_trend)
                    
                    st.markdown("##### 🏢 【月結視覺化】本月各戶總收支佔比排行")
                    df_monthly_filtered["總金額"] = df_monthly_filtered["收入金額"] + df_monthly_filtered["支出金額"]
                    df_m_res_agg = df_monthly_filtered.groupby("戶別")["總金額"].sum().reset_index()
                    df_m_res_agg = df_m_res_agg[df_m_res_agg["總金額"] > 0].sort_values(by="總金額", ascending=False)
                    if not df_m_res_agg.empty:
                        fig_monthly_bar = px.bar(
                            df_m_res_agg,
                            x="總金額",
                            y="戶別",
                            orientation="h",
                            text="總金額"
                        )
                        fig_monthly_bar.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=20, r=20, t=20, b=20))
                        st.plotly_chart(fig_monthly_bar, use_container_width=True)
                else:
                    st.caption("該月暫無收支走勢資料。")
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
# 頁籤 2：🚗 車位登記及查詢
# ==========================================
elif menu == "🚗 車位登記及查詢":
    st.header("🚗 社區車位資產管理系統")
    
    df_park_raw = st.session_state.parking_data.copy()
    
    if "身分標記" not in df_park_raw.columns:
        df_park_raw["身分標記"] = "屋主"
    if "車輛備註" not in df_park_raw.columns:
        df_park_raw["車輛備註"] = ""

    b1_total_cap = sum(1 for s in st.session_state.car_space_mapping.values() if s.startswith("B1-"))
    b2_total_cap = sum(1 for s in st.session_state.car_space_mapping.values() if s.startswith("B2-"))
    b3_total_cap = sum(1 for s in st.session_state.car_space_mapping.values() if s.startswith("B3-"))
    total_car_cap = b1_total_cap + b2_total_cap + b3_total_cap
    if total_car_cap == 0:
        total_car_cap = 55  # 預設值防呆
    
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

    total_car_used = len(b1_used_spaces.union(b2_used_spaces).union(b3_used_spaces))
    moto_used = len(moto_used_spaces)
    
    st.markdown("### 📊 社區車位資產與未登記車輛清查")
    dash_col1, dash_col2 = st.columns(2)
    
    with dash_col1:
        st.markdown(f"**🅿️ 汽車位總結算：實體使用 {total_car_used} / 總格數 {total_car_cap} 格 (剩餘空位：{total_car_cap - total_car_used} 格)**")
        st.progress(min(total_car_used / total_car_cap, 1.0) if total_car_cap > 0 else 0.0)
        st.caption(f"✨ 總計登記汽車數：{total_registered_cars} 台 ｜ **(租客車數: {tenant_car_count} 台)**")

    with dash_col2:
        st.markdown(f"**🛵 機車位總結算：實體使用 {moto_used} / 總格數 {moto_cap} 格 (剩餘空位：{moto_cap - moto_used} 格)**")
        st.progress(min(moto_used / moto_cap, 1.0) if moto_cap > 0 else 0.0)
        st.caption(f"✨ 總計登記機車數：{total_registered_motos} 台 ｜ **(租客機車數: {tenant_moto_count} 台)**")

    st.markdown("---")
    st.markdown("#### 📈 【車位圖像化分析】車位與車輛佔比狀況 (橫式長條圖)")

    parking_ratio_data = pd.DataFrame({
        "車位類別": ["汽車位", "機車位"],
        "總車格": [total_car_cap, moto_cap],
        "使用中": [total_car_used, moto_used],
        "空位": [max(0, total_car_cap - total_car_used), max(0, moto_cap - moto_used)]
    })
    
    fig_parking_ratio = px.bar(
        parking_ratio_data,
        x=["使用中", "空位"],
        y="車位類別",
        orientation="h",
        title="總車格 - 空位與有使用的占比",
        labels={"value": "車格數量", "variable": "車位狀態", "車位類別": ""},
        text_auto=True
    )
    fig_parking_ratio.update_layout(barmode="stack", yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_parking_ratio, use_container_width=True)

    vehicle_ratio_data = pd.DataFrame({
        "車輛類型": ["汽車", "機車"],
        "所有車 (自用/住戶)": [
            max(0, total_registered_cars - tenant_car_count), 
            max(0, total_registered_motos - tenant_moto_count)
        ],
        "租客車": [tenant_car_count, tenant_moto_count]
    })

    fig_vehicle_ratio = px.bar(
        vehicle_ratio_data,
        x=["所有車 (自用/住戶)", "租客車"],
        y="車輛類型",
        orientation="h",
        title="車輛- 所有車跟租客車的占比",
        labels={"value": "車輛數量", "variable": "車輛身分", "車輛類型": ""},
        text_auto=True
    )
    fig_vehicle_ratio.update_layout(barmode="stack", yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_vehicle_ratio, use_container_width=True)

# ==========================================
# 頁籤 3：⚙️ 常駐名冊與機車抽籤管理
# ==========================================
elif menu == "⚙️ 常駐名冊與機車抽籤管理":
    st.header("⚙️ 常駐戶別名冊與機車位抽籤管理")
    st.info("💡 在此可進行常駐戶別設定、管理服務帳號常態清單，或執行機車位抽籤流程。")
    
    st.subheader("📋 目前系統常駐住戶總覽")
    st.write(f"目前共計有 **{len(st.session_state.resident_list)}** 個住戶戶別。")
    st.write(", ".join(st.session_state.resident_list))
