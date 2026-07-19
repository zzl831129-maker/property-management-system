# -*- coding: utf-8 -*-
"""
SmartProp v31.0 - 物業管理旗艦防呆完全體 (雙向即時通知與對帳回歸版)
"""

import streamlit as st
import pandas as pd
import datetime
import time
import re
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 0. 系統環境初始化與外觀美化
# ==========================================
st.set_page_config(page_title="社區物業管理系統", layout="wide", page_icon="🏢")

st.markdown("""
    <style>
    .big-font { font-size:18px !important; font-weight: bold; }
    .stButton > button { border-radius: 8px !important; }
    .highlight-box { background-color: #FFF3CD; padding: 15px; border-radius: 5px; border-left: 6px solid #FFC107; }
    </style>
""", unsafe_allow_html=True)

st.title("🏢 社區物業管理系統")
st.caption("✨7/2詹詹模擬版")

# ==========================================
# 🔌 Google Sheets 雲端連線實體大腦
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/18DI3Lpyk8R5pT_3K7B4oLLK_vsHYuWh2JXRP8MLyGQM/edit"
SPREADSHEET_NAME = SPREADSHEET_URL  # 修正變數未定義對齊 Bug

def load_cloud_ledger():
    """讀取第一張分頁：零用金明細 (精準對齊您的 8 大原始欄位)"""
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
    except Exception:
        return pd.DataFrame(columns=required_cols)

def save_cloud_ledger(df_to_save):
    """安全寫入零用金明細"""
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
    """讀取第二張分頁：車位登記 (7欄)"""
    required_cols = ["流水號", "車位號碼", "戶別", "車牌號碼", "車主姓名", "連絡電話", "登記日期"]
    try:
        df = conn.read(spreadsheet=SPREADSHEET_NAME, worksheet="車位登記", ttl=0)
        if df is not None and not df.empty and "車位號碼" in df.columns:
            df["流水號"] = pd.to_numeric(df["流水號"]).fillna(0).astype(int)
            for col in ["車位號碼", "車牌號碼", "車主姓名", "連絡電話", "戶別", "登記日期"]:
                df[col] = df[col].astype(str).str.strip() if col in df.columns else ""
            
            if "連絡電話" in df.columns:
                df["連絡電話"] = df["連絡電話"].apply(lambda x: x.split('.')[0] if '.' in x else x)
                df["連絡電話"] = df["連絡電話"].apply(lambda x: "0" + x if len(x) == 9 and x.startswith("9") else x)
                
            df["車牌號碼"] = df["車牌號碼"].str.upper()
            return df[required_cols]
        return pd.DataFrame(columns=required_cols)
    except Exception:
        return pd.DataFrame(columns=required_cols)

def save_parking_ledger(df_to_save):
    """安全寫入第二張分頁：車位登記"""
    df_copy = df_to_save.copy()
    if not df_copy.empty:
        df_copy["登記日期"] = df_copy["登記日期"].astype(str)
        df_copy["連絡電話"] = df_copy["連絡電話"].astype(str)
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

# ==========================================
# 1. 系統記憶體初始化
# ==========================================
if 'resident_list' not in st.session_state:
    init_res = ["1A"]
    for floor in range(2, 16):  
        for room in ["A", "B", "C", "D", "E", "F", "G", "H"]:  
            init_res.append(f"{floor}{room}")
    st.session_state.resident_list = init_res

if 'resident_initial_balances' not in st.session_state:
    st.session_state.resident_initial_balances = {res: 0 for res in st.session_state.resident_list}

if 'cash_inventory' not in st.session_state:
    st.session_state.cash_inventory = {"n1000": 0, "n500": 0, "n100": 0, "n50": 0, "n10": 0, "n1": 0}

if 'common_items' not in st.session_state:
    st.session_state.common_items = ["儲值", "水果錢", "文具", "代墊物業費", "大門電路維修"]
if 'common_handlers' not in st.session_state:
    st.session_state.common_handlers = ["詹詹", "宗宗", "管理員A", "00"]

# 🚀 執行雲端數據庫同步 (增加防重複加載機制，消除雲端延遲導致的舊資料刷新問題)
if 'ledger_data' not in st.session_state or 'parking_data' not in st.session_state:
    with st.status("🛸 正在連線至【物業管理分析系統】雲端硬碟...", expanded=False) as status:
        st.session_state.ledger_data = load_cloud_ledger()
        st.session_state.parking_data = load_parking_ledger()
        status.update(label="✅ 雙核心數據庫無損同步成功！", state="complete")

INITIAL_CASH = 0
today_dt = datetime.date.today()

# 功能分頁導覽
menu = st.radio(
    "🛠️ 請選擇主要功能模組：", 
    ["📝 零用金收支登記與快查及對帳看板", "🚗 車位登記及查詢", "⚙️ 常駐名冊管理"], 
    horizontal=True
)

# 🌟 精準格式化工具：優化為簡短乾淨的「當日明細 + 最新結餘」通知格式
def generate_line_text(target_res, ledger_df, initial_balances):
    init_bal = initial_balances.get(target_res, 0)
    
    # 1. 精準計算該戶別累積到目前最新的總餘額
    current_bal = init_bal
    if not ledger_df.empty:
        df_res_all = ledger_df[ledger_df["戶別"] == target_res]
        current_bal += df_res_all["收入金額"].sum() - df_res_all["支出金額"].sum()
        
    header = f"【🏢 社區零用金即時對帳通知】\n戶別：{target_res}\n"
    t_dt = datetime.date.today()
    
    if ledger_df.empty:
        return header + f"📅 異動日期：{t_dt.month}/{t_dt.day}\n💰 帳戶最新結餘：{int(current_bal):,} 元"
    
    # 2. 僅篩選該戶別「今天（當日）」發生的收支明細
    df_today = ledger_df[(ledger_df["戶別"] == target_res) & (ledger_df["交易日期"] == t_dt)].copy()
    
    if df_today.empty:
        return header + f"📅 異動日期：{t_dt.month}/{t_dt.day}\n📝 今日收支：今日暫無款項異動\n💰 帳戶最新結餘：{int(current_bal):,} 元"
        
    line_lines = [f"📅 異動日期：{t_dt.month}/{t_dt.day}\n✨ 當日明細："]
    for idx, row in df_today.iterrows():
        net_expense = int(row["支出金額"])
        net_income = int(row["收入金額"])
        
        if net_expense > 0:
            line_lines.append(f" ├── {row['項目摘要']}：-{net_expense:,}元")
        elif net_income > 0:
            line_lines.append(f" ├── {row['項目摘要']}：+{net_income:,}元")
            
    line_lines.append(f"====================\n💰 帳戶最新結餘：{current_bal:,} 元\n\n※ 這是管理室即時對帳明細，如有疑問歡迎至管理室洽詢。")
    return header + "\n".join(line_lines)

# ==========================================
# 頁籤 1：📝 每日零用金收支登記與快查
# ==========================================
if menu == "📝 零用金收支登記與快查及對帳看板":
    st.markdown("### 🔍 萬能連鎖關鍵字快查看板")
    search_keyword = st.text_input("💡 輸入多重條件可用 + 號連結（例如：2A + 水果）：", placeholder="在此輸入搜尋條件...", key="main_search_bar")
    
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
        st.caption("目前雲端尚無零用金明細資料。")
        
    st.markdown("---")
    
    trade_type = st.radio("請選擇交易模式：", ["一般收支 (收入/支出)", "🔄 住戶之間互相轉帳"], horizontal=True, key="main_trade_type")
    
    col_input, col_line = st.columns([3, 2])
    
    with col_input:
        next_id = len(st.session_state.ledger_data) + 1
        current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if trade_type == "一般收支 (收入/支出)":
            st.subheader("📥 新增收支流水帳")
            c1, c2 = st.columns(2)
            with c1:
                log_date = st.date_input("選擇交易日期", value=today_dt, key="ins_date")
                resident_input = st.selectbox("選擇住戶戶別", st.session_state.resident_list, key="ins_res")
                action_type = st.selectbox("收支類別", ["支出", "收入"], key="ins_type")
            with c2:
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
                            # 🔥 核心優化：直接寫入本機狀態記憶體，消除更新延遲感
                            st.session_state.ledger_data = updated_df
                            st.session_state["line_res_selector"] = resident_input
                            st.session_state["last_trade_type"] = "normal"
                            st.success("🎉 資料成功傳入雲端！")
                            time.sleep(0.5)
                            st.rerun()
                            
        else:
            st.subheader("🔄 執行住戶之間互相轉帳")
            c1, c2 = st.columns(2)
            with c1:
                log_date = st.date_input("轉帳日期", value=today_dt, key="trans_date")
                from_res = st.selectbox("👤 轉出款項戶別 (扣錢)", st.session_state.resident_list, index=0, key="trans_from")
                to_res = st.selectbox("👤 接收款項戶別 (加錢)", st.session_state.resident_list, index=1, key="trans_to")
            with c2:
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
                            # 🔥 核心優化：直接寫入本機狀態記憶體，消除更新延遲感
                            st.session_state.ledger_data = updated_df
                            st.session_state["line_res_selector"] = from_res
                            st.session_state["last_active_from"] = from_res
                            st.session_state["last_active_to"] = to_res
                            st.session_state["last_trade_type"] = "transfer"
                            st.success("🎉 轉帳成功！已同步至雲端兩端名冊！")
                            time.sleep(0.5)
                            st.rerun()

    with col_line:
        st.markdown("### 📱 LINE 住戶通知文字快速生成器")
        
        # 如果是剛做完「住戶互轉」，右邊分開兩個獨立分頁方便複製
        if st.session_state.get("last_trade_type") == "transfer":
            f_res = st.session_state.get("last_active_from", from_res)
            t_res = st.session_state.get("last_active_to", to_res)
            st.markdown("<b style='color:#007BFF;'>🔄 偵測到剛完成互轉交易！請各別複製：</b>", unsafe_allow_html=True)
            
            tab_out, tab_in = st.tabs([f"📤 轉出戶 ({f_res}) 扣款明細", f"📥 轉入戶 ({t_res}) 入帳明細"])
            with tab_out:
                msg_out = generate_line_text(f_res, st.session_state.ledger_data, st.session_state.resident_initial_balances)
                st.text_area(f"📋 複製【轉出戶 {f_res}】通知：", value=msg_out, height=140, key="line_tab_out_box")
            with tab_in:
                msg_in = generate_line_text(t_res, st.session_state.ledger_data, st.session_state.resident_initial_balances)
                st.text_area(f"📋 複製【轉入戶 {t_res}】通知：", value=msg_in, height=140, key="line_tab_in_box")
            st.markdown("---")
            st.caption("💡 *下方仍保留手動切換選單：*")
        
        # 智慧型定位下拉選單索引
        if "line_res_selector" in st.session_state and st.session_state.line_res_selector in st.session_state.resident_list:
            default_line_idx = st.session_state.resident_list.index(st.session_state.line_res_selector)
        elif trade_type == "一般收支 (收入/支出)":
            default_line_idx = st.session_state.resident_list.index(resident_input)
        else:
            default_line_idx = st.session_state.resident_list.index(from_res)
            
        target_line_res = st.selectbox("選取手動查詢戶別的流水號明細：", st.session_state.resident_list, index=default_line_idx, key="line_res_selector")
        
        final_text = generate_line_text(target_line_res, st.session_state.ledger_data, st.session_state.resident_initial_balances)
        st.text_area("📋 複製自選戶別通知文字：", value=final_text, height=200, key="line_text_output")

    # ==========================================
    # 🪙 實地鈔票盤點對帳功能 (主頁最下方)
    # ==========================================
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
        st.error(f"🔴 帳目不符❌ 實地少錢: {diff:,.0f} 元")
    else:
        st.warning(f"🟡 帳目不符❌ 實地多錢: +{diff:,.0f} 元")

# ==========================================
# 頁籤 2：🚗 車位登記及查詢 (完全保留)
# ==========================================
elif menu == "🚗 車位登記及查詢":
    st.header("🚗 社區車位資產管理系統")
    p_col1, p_col2 = st.columns([3, 2])
    
    df_park_raw = st.session_state.parking_data.copy()
    
    with p_col1:
        st.subheader("🔍 車位資產看板")
        p_search = st.text_input("💡 請輸入 戶別(如:1A)、車位區域、車主姓名 或 車牌 快速檢索：", key="park_search_input")
        
        df_park_display = df_park_raw.copy()
        if not df_park_display.empty:
            if p_search.strip():
                k = p_search.strip().lower()
                df_park_display = df_park_display[
                    df_park_display["車位號碼"].astype(str).str.lower().str.contains(k, na=False) | 
                    df_park_display["車主姓名"].astype(str).str.lower().str.contains(k, na=False) | 
                    df_park_display["車牌號碼"].astype(str).str.lower().str.contains(k, na=False) |
                    df_park_display["戶別"].astype(str).str.lower().str.contains(k, na=False)
                ]
            st.dataframe(df_park_display, use_container_width=True, hide_index=True)
        else:
            st.info("💡 目前車位資料庫尚無資料。")
            
    with p_col2:
        st.subheader("📝 車位持有異動登記")
        c_zone, c_num = st.columns(2)
        with c_zone:
            p_area_type = st.selectbox("車位型態：", ["汽車位(B1)", "汽車位(B2)", "汽車位(B3)", "機車位"], key="p_reg_type")
        with c_num:
            p_area_num = st.text_input("車位/車格編號：", placeholder="例如：105", key="p_reg_num")
        
        p_id = f"{p_area_type}-{p_area_num}" if p_area_num.strip() else ""
        p_res_code = st.selectbox("持有戶別：", st.session_state.resident_list, key="p_reg_res")
        p_plate = st.text_input("車牌號碼：", placeholder="ABC-1234", key="p_reg_plate").strip().upper()
        p_name = st.text_input("車主姓名：", placeholder="例如：詹詹", key="p_reg_name").strip()
        p_phone = st.text_input("連絡電話：", placeholder="例如：0912345678", key="p_reg_phone")
        
        is_car = "汽車位" in p_area_type
        
        if p_res_code and not df_park_raw.empty:
            existing_cars = df_park_raw[(df_park_raw["戶別"] == p_res_code) & (df_park_raw["車位號碼"].str.contains("汽車", na=False)) & (df_park_raw["車位號碼"] != p_id)]
            existing_motos = df_park_raw[(df_park_raw["戶別"] == p_res_code) & (df_park_raw["車位號碼"].str.contains("機車", na=False)) & (df_park_raw["車位號碼"] != p_id)]
            
            if is_car:
                st.info(f"📋 戶別 **{p_res_code}** 目前已登記汽車：**{len(existing_cars)}** 台。")
                if len(existing_cars) >= 2:
                    st.markdown(f"""
                    <div class="highlight-box">
                        ⚠️ 🟡 <b>【汽車超額示警】</b> 戶別 <b>{p_res_code}</b> 已登記滿 2 台汽車！<br>
                        依社區規範，此筆（第 {len(existing_cars)+1} 台）需加強合約備查與合規稽查！
                    </div><br>
                    """, unsafe_allow_html=True)
            else:
                st.info(f"🏍️ 戶別 **{p_res_code}** 目前已登記機車：**{len(existing_motos)}** 台 (機車數量無上限)。")

        if st.button("💾 儲存/變更車位資產登記", type="primary", use_container_width=True, key="p_reg_btn"):
            phone_digits = re.sub(r"\D", "", p_phone.strip())
            clean_plate = p_plate.strip().upper().replace(" ", "")
            
            is_duplicate_plate = False
            dup_space_id = ""
            dup_owner_name = ""
            
            if not df_park_raw.empty:
                df_other_spaces = df_park_raw[df_park_raw["車位號碼"] != p_id]
                if clean_plate in df_other_spaces["車牌號碼"].values:
                    is_duplicate_plate = True
                    dup_row = df_other_spaces[df_other_spaces["車牌號碼"] == clean_plate].iloc[0]
                    dup_space_id = dup_row["車位號碼"]
                    dup_owner_name = dup_row["車主姓名"]
            
            if not p_area_num.strip() or not p_plate or not p_name or not p_phone.strip():
                st.error("❌ 【防呆阻擋】所有欄位皆為必填項目，不可留白！")
            elif not re.match(r"^[A-Z0-9\-]+$", clean_plate):
                st.error("❌ 【車牌防呆阻擋】車牌號碼只能包含英文字母、數字與減號（-），請勿輸入中文字或其他符號！")
            elif len(clean_plate.replace("-", "")) < 4 or len(clean_plate.replace("-", "")) > 8:
                st.error("❌ 【車牌防呆阻擋】車牌的純英文字母與數字總長度不符（應為 4~8 碼），請檢查是否打錯！")
            elif is_duplicate_plate:
                st.error(f"❌ 【車牌重複阻擋】此車牌 <b>{clean_plate}</b> 已經登記在車位 <b>{dup_space_id}</b> 內（登記人：{dup_owner_name}）！同一台車不能同時重複登記在不同車位中！", unsafe_allow_html=True)
            elif len(phone_digits) < 9 or len(phone_digits) > 10:
                st.error(f"❌ 【電話防呆阻擋】您輸入的電話包含 {len(phone_digits)} 碼數字！不應出現 11 碼或低於 9 碼，請確認是否打錯！")
            else:
                with st.spinner("正在更新雲端【車位登記】分頁..."):
                    df_clean = df_park_raw[df_park_raw["車位號碼"] != p_id] if not df_park_raw.empty else pd.DataFrame()
                    
                    next_p_id = len(df_clean) + 1
                    new_park_row = {
                        "流水號": next_p_id, "車位號碼": p_id, "戶別": p_res_code, 
                        "車牌號碼": clean_plate, "車主姓名": p_name,
                        "連絡電話": str(p_phone.strip()), "登記日期": datetime.date.today().strftime("%Y-%m-%d")
                    }
                    df_updated_park = pd.concat([df_clean, pd.DataFrame([new_park_row])], ignore_index=True)
                    if save_parking_ledger(df_updated_park):
                        st.session_state.parking_data = df_updated_park
                        st.success(f"🎉 車位 {p_id} 變更與唯一性校驗成功！")
                        time.sleep(0.5)
                        st.rerun()

# ==========================================
# 頁籤 3：⚙️ 常駐名冊管理 (完全保留)
# ==========================================
else:
    st.header("⚙️ 物業後台核心常駐清單設定")
    col_set1, col_set2, col_set3 = st.columns(3)
    
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
            
    with col_set2:
        st.markdown("#### 👤 經手人名冊維護")
        new_handler = st.text_input("➕ 增加經手人人員：", key="backend_add_handler")
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
            
    with col_set3:
        st.markdown("#### 🏠 住戶群外加註冊")
        new_res = st.text_input("➕ 註冊外加戶別代碼：", placeholder="例如：1A", key="backend_add_res")
        new_res_bal = st.number_input("該戶初始餘額：", value=0, step=1, key="backend_add_res_bal")
        if st.button("確認註冊此戶別", key="btn_add_res") and new_res.strip():
            if new_res.strip() not in st.session_state.resident_list:
                st.session_state.resident_list.append(new_res.strip())
                st.session_state.resident_initial_balances[new_res.strip()] = new_res_bal
                st.success(f"🎉 成功建立 {new_res.strip()} 戶！")
                time.sleep(0.5)
                st.rerun()