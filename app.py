# -*- coding: utf-8 -*-
"""
社區物業智慧管理系統
"""

import streamlit as st
import os
import pandas as pd
import plotly.express as px
import datetime
import time
import re
import random
from streamlit_gsheets import GSheetsConnection
import gspread

# ==========================================
# 0. 系統環境初始化與外觀美化
# ==========================================
st.set_page_config(page_title="社區物業智慧管理系統", layout="wide", page_icon="🏢")

st.markdown("""
<style>
:root {
    --navy:#173B5E;
    --navy-dark:#11304B;
    --blue:#2E79C7;
    --blue-soft:#EAF3FB;
    --bg:#F5F7FA;
    --card:#FFFFFF;
    --border:#DDE5EC;
    --text:#17324A;
    --muted:#718397;
    --green:#23815F;
    --green-soft:#EBF7F2;
    --amber:#A46A19;
    --amber-soft:#FFF6E8;
    --red:#A5474D;
    --red-soft:#FDEDEF;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
}
[data-testid="stHeader"] {
    background: rgba(245,247,250,.97) !important;
    border-bottom: 1px solid var(--border);
}
.block-container {
    max-width: 1480px;
    padding-top: 4.75rem;
    padding-bottom: 3rem;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,var(--navy) 0%,var(--navy-dark) 100%) !important;
}
[data-testid="stSidebar"] * { color:#F7FAFD !important; }
[data-testid="stSidebar"] hr { border-color:rgba(255,255,255,.13) !important; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding:.52rem .58rem !important;
    margin:.08rem 0 !important;
    border-radius:10px !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background:rgba(255,255,255,.08) !important;
}
[data-testid="stSidebar"] .stButton > button {
    width:100%;
    background:rgba(255,255,255,.09) !important;
    color:#fff !important;
    border:1px solid rgba(255,255,255,.16) !important;
    box-shadow:none !important;
}

h1,h2,h3,h4 { color:var(--text) !important; letter-spacing:-.015em; }
.stButton > button, .stFormSubmitButton > button {
    border-radius:9px !important;
    min-height:2.55rem;
    font-weight:650 !important;
    border:1px solid var(--border) !important;
    box-shadow:none !important;
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
    background:var(--blue) !important;
    border-color:var(--blue) !important;
    color:#fff !important;
}
div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
div[data-baseweb="textarea"] > div {
    background:#fff !important;
    border-color:var(--border) !important;
    border-radius:9px !important;
}
.stTabs [data-baseweb="tab-list"] {
    gap:.35rem;
    background:#EAF0F5 !important;
    padding:.34rem;
    border-radius:11px;
}
.stTabs [data-baseweb="tab"] {
    border-radius:8px;
    color:#526B7E !important;
    padding:.44rem .85rem;
}
.stTabs [aria-selected="true"] {
    background:#fff !important;
    color:var(--navy) !important;
    box-shadow:0 1px 5px rgba(17,48,74,.08);
}
[data-testid="stMetric"] {
    background:#fff;
    border:1px solid var(--border);
    border-radius:13px;
    padding:.9rem 1rem;
}
[data-testid="stForm"] {
    background:#fff;
    border:1px solid var(--border) !important;
    border-radius:13px !important;
    padding:1rem !important;
}
[data-testid="stDataFrame"] {
    border:1px solid var(--border);
    border-radius:11px;
    overflow:hidden;
}

/* Existing semantic boxes */
.highlight-box {
    background:var(--amber-soft); padding:14px; border-radius:10px;
    border-left:4px solid #D18A27; color:#684718;
}
.info-box-custom {
    background:var(--green-soft); padding:12px; border-radius:10px;
    border-left:4px solid #3E9A77; color:#245E49; font-weight:650; margin-bottom:10px;
}
.alert-box-custom {
    background:var(--red-soft); padding:12px; border-radius:10px;
    border-left:4px solid #B7545A; color:#7A3137; font-weight:650; margin-bottom:10px;
}

/* App shell */
.sp-brand { padding:.35rem .12rem 1rem; }
.sp-brand-name { font-size:1.22rem; font-weight:800; color:#fff !important; }
.sp-brand-sub { font-size:.66rem; letter-spacing:.17em; color:#9FC2DF !important; }
.sp-footer { font-size:.70rem; line-height:1.55; color:#9FC1DD !important; }
.sp-footer strong { color:#F3F8FC !important; }

.sp-header {
    display:flex; align-items:center; justify-content:space-between;
    background:#fff; border:1px solid var(--border); border-radius:14px;
    padding:.85rem 1rem; margin-bottom:1rem;
    box-shadow:0 2px 10px rgba(17,48,74,.035);
}
.sp-header-left { display:flex; align-items:center; gap:.75rem; }
.sp-logo {
    width:42px; height:42px; border-radius:11px; display:flex;
    align-items:center; justify-content:center; background:var(--blue-soft);
    color:var(--navy); font-weight:800;
}
.sp-title { font-size:1.04rem; font-weight:760; color:var(--text); }
.sp-subtitle { font-size:.68rem; letter-spacing:.12em; color:var(--muted); }
.sp-status {
    display:inline-flex; align-items:center; gap:.42rem;
    padding:.38rem .68rem; border-radius:999px;
    background:var(--green-soft); border:1px solid #CDE8DE;
    color:#216047; font-size:.78rem; font-weight:650;
}
.sp-dot { width:8px; height:8px; border-radius:50%; background:var(--green); }

.sp-page-head { padding:.25rem 0 .8rem; }
.sp-page-kicker { color:var(--blue); font-size:.72rem; font-weight:750; letter-spacing:.12em; }
.sp-page-title { font-size:1.62rem; font-weight:780; color:var(--text); margin:.15rem 0; }
.sp-page-desc { font-size:.9rem; color:var(--muted); }

.sp-manager-note {
    background:#F9FBFD; border:1px solid var(--border); border-radius:11px;
    padding:.78rem .95rem; color:#5B7285; font-size:.84rem; margin:.15rem 0 1rem;
}
.sp-list-head {
    display:grid; grid-template-columns:3fr 4fr 1.7fr;
    padding:.55rem .8rem; background:#EDF3F7;
    border:1px solid var(--border); border-radius:10px 10px 0 0;
    font-size:.76rem; color:#60788B; font-weight:700;
}
.sp-row-name { font-weight:700; color:var(--text); padding-top:.28rem; }
.sp-row-note { color:#6E8192; font-size:.84rem; padding-top:.30rem; }
.sp-divider { height:1px; background:#E5EBF0; margin:.35rem 0 .55rem; }
.sp-confirm {
    background:#FFF8F8; border:1px solid #F0D0D3; border-radius:10px;
    padding:.78rem .95rem; margin:.45rem 0;
}
.sp-empty {
    background:#FBFCFD; border:1px dashed #C8D6E1; border-radius:10px;
    padding:1.1rem; text-align:center; color:#7B8D9C;
}
.sp-chip {
    display:inline-block; padding:.18rem .45rem; border-radius:999px;
    background:#EDF3F8; color:#4D6477; font-size:.72rem; font-weight:650;
}

@media(max-width:900px) {
    .block-container { padding-left:1rem; padding-right:1rem; }
    .sp-header { flex-direction:column; align-items:flex-start; gap:.65rem; }
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🔌 Google Sheets 雲端連線實體大腦
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

# ============================================================
# SmartProp 統一資料來源設定
# ============================================================
# 原則：
# 1. STREAMLIT_SECRETS 只保存 Google Service Account 認證
# 2. SMARTPROP_SPREADSHEET_URL 決定正式資料庫
# 3. SMARTPROP_LEGACY_SPREADSHEET_URL 決定舊資料庫
# 4. SMARTPROP_USE_LEGACY_SHEET=true 可快速 Rollback
#
# 這樣 Web / LINE 可以共用同一份 Google Sheet，
# 但認證與資料庫位置彼此分離，日後換社區/換資料庫不用改程式碼。

DEFAULT_PRIMARY_SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1tgxjrFn5uZ0-lnGARzwsRGxNMsUfMKg2Fp7B36Y5vY4/edit"
)

DEFAULT_LEGACY_SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "18DI3Lpyk8R5pT_3K7B4oLLK_vsHYuWh2JXRP8MLyGQM/edit"
)

PRIMARY_SPREADSHEET_URL = os.getenv(
    "SMARTPROP_SPREADSHEET_URL",
    DEFAULT_PRIMARY_SPREADSHEET_URL
).strip()

LEGACY_SPREADSHEET_URL = os.getenv(
    "SMARTPROP_LEGACY_SPREADSHEET_URL",
    DEFAULT_LEGACY_SPREADSHEET_URL
).strip()

USE_LEGACY_SHEET = os.getenv(
    "SMARTPROP_USE_LEGACY_SHEET",
    "false"
).strip().lower() in {"1", "true", "yes", "on"}

if USE_LEGACY_SHEET:
    SPREADSHEET_URL = LEGACY_SPREADSHEET_URL
    DATA_SOURCE_LABEL = "舊版 Google Sheet（Rollback）"
else:
    SPREADSHEET_URL = PRIMARY_SPREADSHEET_URL
    DATA_SOURCE_LABEL = "SmartProp 共用正式資料庫"

SPREADSHEET_NAME = SPREADSHEET_URL

# 僅顯示安全資訊，不把完整 URL / ID 印到畫面

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

def _clean_text_value(value):
    """把 Google Sheet / pandas 的空值統一成空字串。"""
    if value is None or pd.isna(value):
        return ""
    text_value = str(value).strip()
    if text_value.lower() in {"nan", "none", "null", "<na>"}:
        return ""
    return text_value


def _normalize_phone(value):
    phone = _clean_text_value(value)
    if not phone:
        return ""
    phone = phone.split(".")[0]
    phone = re.sub(r"[^0-9+]", "", phone)
    if len(phone) == 9 and phone.startswith("9"):
        phone = "0" + phone
    return phone


def load_parking_ledger():
    """依 SmartProp 共用「車位登記」Schema 載入並標準化資料。"""
    required_cols = ["流水號", "車位號碼", "戶別", "車牌號碼", "車主姓名", "連絡電話", "身分標記", "車輛備註", "登記日期"]
    try:
        df = conn.read(spreadsheet=SPREADSHEET_NAME, worksheet="車位登記", ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=required_cols)

        for col in required_cols:
            if col not in df.columns:
                df[col] = "屋主" if col == "身分標記" else ""

        df["流水號"] = pd.to_numeric(df["流水號"], errors="coerce").fillna(0).astype(int)
        for col in ["車位號碼", "戶別", "車主姓名", "身分標記", "車輛備註", "登記日期"]:
            df[col] = df[col].apply(_clean_text_value)
        df["車牌號碼"] = df["車牌號碼"].apply(lambda x: format_plate_number(_clean_text_value(x)))
        df["連絡電話"] = df["連絡電話"].apply(_normalize_phone)
        df["身分標記"] = df["身分標記"].replace("", "屋主")
        return df[required_cols].copy()
    except Exception as exc:
        print("Web Parking Load Error:", type(exc).__name__, str(exc))
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

SYSTEM_SETTINGS_WORKSHEET = "系統設定"
SYSTEM_SETTINGS_COLUMNS = ["類型", "名稱", "數值", "備註"]

DEFAULT_SYSTEM_SETTINGS = [
    {"類型":"經手人","名稱":"日班-詹詹","數值":"","備註":""},
    {"類型":"經手人","名稱":"夜班-宗宗","數值":"","備註":""},
    {"類型":"經手人","名稱":"經理-00","數值":"","備註":""},
    {"類型":"常用項目","名稱":"儲值","數值":"","備註":""},
    {"類型":"常用項目","名稱":"水果錢","數值":"","備註":""},
    {"類型":"常用項目","名稱":"文具","數值":"","備註":""},
    {"類型":"常用項目","名稱":"關稅","數值":"","備註":""},
    {"類型":"常用項目","名稱":"貨到付款","數值":"","備註":""},
    {"類型":"抽籤排除","名稱":"1A","數值":"","備註":"管理中心"},
    {"類型":"車位容量","名稱":"B1汽車位","數值":"20","備註":""},
    {"類型":"車位容量","名稱":"B2汽車位","數值":"20","備註":""},
    {"類型":"車位容量","名稱":"B3汽車位","數值":"15","備註":""},
    {"類型":"車位容量","名稱":"機車位","數值":"112","備註":""},
]

def _normalize_system_settings_df(df):
    if df is None:
        df = pd.DataFrame()
    work = df.copy()
    for col in SYSTEM_SETTINGS_COLUMNS:
        if col not in work.columns:
            work[col] = ""
    for col in SYSTEM_SETTINGS_COLUMNS:
        work[col] = work[col].apply(_clean_text_value)
    work = work[SYSTEM_SETTINGS_COLUMNS]
    work = work[(work["類型"]!="") & (work["名稱"]!="")].copy()
    return work.drop_duplicates(subset=["類型","名稱"], keep="last").reset_index(drop=True)

def load_system_settings():
    try:
        df = conn.read(spreadsheet=SPREADSHEET_NAME, worksheet=SYSTEM_SETTINGS_WORKSHEET, ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(DEFAULT_SYSTEM_SETTINGS, columns=SYSTEM_SETTINGS_COLUMNS), False
        return _normalize_system_settings_df(df), True
    except Exception as exc:
        print("System Settings Load Warning:", type(exc).__name__, str(exc))
        return pd.DataFrame(DEFAULT_SYSTEM_SETTINGS, columns=SYSTEM_SETTINGS_COLUMNS), False

def _gspread_client_and_sheet():
    cfg = dict(st.secrets["connections"]["gsheets"])
    allowed = {
        "type","project_id","private_key_id","private_key","client_email","client_id",
        "auth_uri","token_uri","auth_provider_x509_cert_url","client_x509_cert_url","universe_domain",
    }
    credentials = {k:v for k,v in cfg.items() if k in allowed}
    gc = gspread.service_account_from_dict(credentials)
    return gc.open_by_url(SPREADSHEET_URL)

def save_system_settings(df_to_save):
    """
    系統設定採四欄格式：類型 / 名稱 / 數值 / 備註。
    寫入前先保留原內容，失敗時盡力還原，避免清單被清空。
    """
    df_copy = _normalize_system_settings_df(df_to_save)
    try:
        sh = _gspread_client_and_sheet()
        try:
            ws = sh.worksheet(SYSTEM_SETTINGS_WORKSHEET)
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=SYSTEM_SETTINGS_WORKSHEET, rows=200, cols=4)

        old_values = ws.get_all_values()
        matrix = [SYSTEM_SETTINGS_COLUMNS] + df_copy.astype(str).values.tolist()

        try:
            ws.clear()
            ws.update(range_name="A1", values=matrix, value_input_option="USER_ENTERED")
        except TypeError:
            ws.clear()
            ws.update("A1", matrix, value_input_option="USER_ENTERED")
        except Exception:
            try:
                ws.clear()
                if old_values:
                    try:
                        ws.update(range_name="A1", values=old_values, value_input_option="USER_ENTERED")
                    except TypeError:
                        ws.update("A1", old_values, value_input_option="USER_ENTERED")
            except Exception:
                pass
            raise

        st.session_state.system_settings_data = df_copy.copy()
        st.session_state.system_settings_cloud_ready = True
        return True
    except Exception as exc:
        st.error("系統設定儲存失敗，原資料已盡力保留。請確認 Google Sheet 連線與權限。")
        print("System Settings Save Error:", type(exc).__name__, str(exc))
        return False

def apply_system_settings_to_session():
    df = _normalize_system_settings_df(st.session_state.system_settings_data)

    handlers = df[df["類型"]=="經手人"]["名稱"].tolist()
    items = df[df["類型"]=="常用項目"]["名稱"].tolist()
    excluded = df[df["類型"]=="抽籤排除"]["名稱"].tolist()

    capacities = {"B1汽車位":20,"B2汽車位":20,"B3汽車位":15,"機車位":112}
    for _, row in df[df["類型"]=="車位容量"].iterrows():
        try:
            capacities[row["名稱"]] = int(float(row["數值"]))
        except Exception:
            pass

    st.session_state.system_settings_data = df
    st.session_state.common_handlers = handlers or ["日班-詹詹"]
    st.session_state.common_items = items or ["儲值"]
    st.session_state.lottery_excluded_res = excluded
    st.session_state.parking_capacities = capacities

def _latest_settings_for_edit():
    latest_df, ready = load_system_settings()
    if ready:
        return latest_df.copy()
    return _normalize_system_settings_df(st.session_state.get(
        "system_settings_data",
        pd.DataFrame(DEFAULT_SYSTEM_SETTINGS, columns=SYSTEM_SETTINGS_COLUMNS)
    ))

def add_setting(setting_type, name, value="", note=""):
    name = _clean_text_value(name)
    if not name:
        st.warning("名稱不可空白。")
        return False

    df = _latest_settings_for_edit()
    if ((df["類型"]==setting_type) & (df["名稱"]==name)).any():
        st.warning(f"「{name}」已存在。")
        return False

    new_row = pd.DataFrame([{
        "類型":setting_type,
        "名稱":name,
        "數值":_clean_text_value(value),
        "備註":_clean_text_value(note),
    }])
    updated = pd.concat([df, new_row], ignore_index=True)
    if save_system_settings(updated):
        apply_system_settings_to_session()
        return True
    return False

def update_setting(setting_type, original_name, new_name, value="", note=""):
    df = _latest_settings_for_edit()
    original_name = _clean_text_value(original_name)
    new_name = _clean_text_value(new_name)

    target = (df["類型"]==setting_type) & (df["名稱"]==original_name)
    if not target.any():
        st.warning(f"找不到「{original_name}」。")
        return False
    if not new_name:
        st.warning("名稱不可空白。")
        return False

    duplicate = (df["類型"]==setting_type) & (df["名稱"]==new_name) & (~target)
    if duplicate.any():
        st.warning(f"「{new_name}」已存在。")
        return False

    df.loc[target, "名稱"] = new_name
    df.loc[target, "數值"] = _clean_text_value(value)
    df.loc[target, "備註"] = _clean_text_value(note)

    if save_system_settings(df):
        apply_system_settings_to_session()
        return True
    return False

def delete_setting(setting_type, name):
    df = _latest_settings_for_edit()
    target = (df["類型"]==setting_type) & (df["名稱"]==_clean_text_value(name))
    if not target.any():
        st.warning(f"找不到「{name}」。")
        return False
    updated = df.loc[~target].reset_index(drop=True)
    if save_system_settings(updated):
        apply_system_settings_to_session()
        return True
    return False

def delete_all_settings_of_type(setting_type):
    df = _latest_settings_for_edit()
    updated = df.loc[df["類型"]!=setting_type].reset_index(drop=True)
    if save_system_settings(updated):
        apply_system_settings_to_session()
        return True
    return False

def _settings_rows(setting_type):
    df = _normalize_system_settings_df(st.session_state.system_settings_data)
    return df[df["類型"]==setting_type].reset_index(drop=True)

def render_setting_manager(
    setting_type, title, subtitle, name_label, add_label,
    note_label="備註", value_label=None, name_options=None,
    allow_add=True, allow_delete=True
):
    slug = {"經手人":"handler","常用項目":"item","抽籤排除":"exclude","車位容量":"capacity"}[setting_type]
    rows = _settings_rows(setting_type)

    h1,h2 = st.columns([5,1.5])
    with h1:
        st.subheader(title)
        st.caption(subtitle)
    with h2:
        if allow_add:
            st.button(f"＋ {add_label}", key=f"{slug}_show_add",
                      use_container_width=True,
                      on_click=lambda k=f"{slug}_adding": st.session_state.__setitem__(k, True))

    if st.session_state.get(f"{slug}_adding", False):
        with st.form(f"{slug}_add_form"):
            if name_options is not None:
                used = set(rows["名稱"].tolist())
                choices = [x for x in name_options if x not in used]
                add_name = st.selectbox(name_label, choices, key=f"{slug}_add_name") if choices else ""
                if not choices:
                    st.info("目前沒有可新增的項目。")
            else:
                add_name = st.text_input(name_label, key=f"{slug}_add_name")
            add_value = st.text_input(value_label, key=f"{slug}_add_value") if value_label else ""
            add_note = st.text_input(note_label, key=f"{slug}_add_note")

            c1,c2 = st.columns(2)
            submit = c1.form_submit_button("新增並儲存", type="primary", use_container_width=True)
            cancel = c2.form_submit_button("取消", use_container_width=True)
            if submit and add_name:
                if add_setting(setting_type, add_name, add_value, add_note):
                    st.session_state[f"{slug}_adding"] = False
                    st.success(f"已新增「{add_name}」。")
            if cancel:
                st.session_state[f"{slug}_adding"] = False

    if rows.empty:
        st.markdown('<div class="sp-empty">目前沒有資料。</div>', unsafe_allow_html=True)
        return

    st.markdown(
        '<div class="sp-list-head"><span>項目</span><span>備註</span><span>操作</span></div>',
        unsafe_allow_html=True
    )

    for idx, row in rows.iterrows():
        name = _clean_text_value(row["名稱"])
        value = _clean_text_value(row["數值"])
        note = _clean_text_value(row["備註"])
        row_key = f"{slug}_{idx}"

        c1,c2,c3,c4 = st.columns([3.1,4.1,.85,.85])
        with c1:
            st.markdown(f'<div class="sp-row-name">{name}</div>', unsafe_allow_html=True)
            if value_label and value:
                st.markdown(f'<span class="sp-chip">{value_label}：{value}</span>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="sp-row-note">{note or "—"}</div>', unsafe_allow_html=True)
        with c3:
            st.button("編輯", key=f"{row_key}_edit",
                      use_container_width=True,
                      on_click=lambda k=f"{slug}_editing", n=name: st.session_state.__setitem__(k, n))
        with c4:
            if allow_delete:
                st.button("刪除", key=f"{row_key}_delete",
                          use_container_width=True,
                          on_click=lambda k=f"{slug}_deleting", n=name: st.session_state.__setitem__(k, n))
            else:
                st.caption("固定")

        if st.session_state.get(f"{slug}_editing") == name:
            with st.form(f"{row_key}_edit_form"):
                edit_name = st.selectbox(
                    name_label, name_options,
                    index=name_options.index(name) if name_options and name in name_options else 0,
                    key=f"{row_key}_edit_name"
                ) if name_options else st.text_input(name_label, value=name, key=f"{row_key}_edit_name")

                edit_value = st.text_input(value_label, value=value, key=f"{row_key}_edit_value") if value_label else value
                edit_note = st.text_input(note_label, value=note, key=f"{row_key}_edit_note")

                e1,e2 = st.columns(2)
                save_edit = e1.form_submit_button("儲存修改", type="primary", use_container_width=True)
                cancel_edit = e2.form_submit_button("取消", use_container_width=True)
                if save_edit:
                    if update_setting(setting_type, name, edit_name, edit_value, edit_note):
                        st.session_state[f"{slug}_editing"] = None
                        st.success(f"已更新「{edit_name}」。")
                if cancel_edit:
                    st.session_state[f"{slug}_editing"] = None

        if allow_delete and st.session_state.get(f"{slug}_deleting") == name:
            st.markdown(
                f'<div class="sp-confirm">確定刪除 <b>{name}</b>？只會刪除此項目。</div>',
                unsafe_allow_html=True
            )
            d1,d2,_ = st.columns([1,1,4])
            if d1.button("確認刪除", key=f"{row_key}_confirm_delete", use_container_width=True):
                if delete_setting(setting_type, name):
                    st.session_state[f"{slug}_deleting"] = None
                    st.success(f"已刪除「{name}」。")
            if d2.button("取消", key=f"{row_key}_cancel_delete", use_container_width=True):
                st.session_state[f"{slug}_deleting"] = None

        st.markdown('<div class="sp-divider"></div>', unsafe_allow_html=True)

def refresh_all_cloud_data(show_message=True):
    """強制重新讀取 Google Sheet，避免 LINE / 網頁跨系統更新後畫面仍停留舊快取。"""
    try:
        st.session_state.ledger_data = load_cloud_ledger()
        st.session_state.parking_data = load_parking_ledger()
        st.session_state.car_space_mapping = load_binding_mapping("汽車位綁定")
        st.session_state.moto_space_mapping = load_binding_mapping("機車位綁定")
        settings_df, settings_ready = load_system_settings()
        st.session_state.system_settings_data = settings_df
        st.session_state.system_settings_cloud_ready = settings_ready
        apply_system_settings_to_session()
        if show_message:
            st.toast("☁️ 已重新同步 SmartProp 雲端資料", icon="🔄")
        return True
    except Exception as exc:
        if show_message:
            st.error(f"❌ 雲端重新同步失敗：{exc}")
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

if 'system_settings_data' not in st.session_state:
    _settings_df, _settings_ready = load_system_settings()
    st.session_state.system_settings_data = _settings_df
    st.session_state.system_settings_cloud_ready = _settings_ready
    apply_system_settings_to_session()

if 'car_space_mapping' not in st.session_state:
    st.session_state.car_space_mapping = load_binding_mapping("汽車位綁定")

if 'moto_space_mapping' not in st.session_state:
    st.session_state.moto_space_mapping = load_binding_mapping("機車位綁定")

if 'resident_initial_balances' not in st.session_state:
    st.session_state.resident_initial_balances = {res: 0 for res in st.session_state.resident_list}

if 'cash_inventory' not in st.session_state:
    st.session_state.cash_inventory = {"n1000": 0, "n500": 0, "n100": 0, "n50": 0, "n10": 0, "n1": 0}

if 'generated_line_text' not in st.session_state:
    st.session_state.generated_line_text = ""

if 'ledger_data' not in st.session_state or 'parking_data' not in st.session_state:
    with st.status("🛸 正在連線至【物業管理分析系統】雲端硬碟...", expanded=False) as status:
        st.session_state.ledger_data = load_cloud_ledger()
        st.session_state.parking_data = load_parking_ledger()
        status.update(label="✅ 雙核心數據庫無損同步成功！", state="complete")

# ============================================================
# SmartProp 導覽與同步
# ============================================================
INITIAL_CASH = 0
today_dt = datetime.date.today()

with st.sidebar:
    st.markdown(
        """
        <div class="sp-brand">
          <div class="sp-brand-name">SmartProp</div>
          <div class="sp-brand-sub">COMMUNITY OS</div>
        </div>
        """, unsafe_allow_html=True
    )

    menu = st.radio(
        "主要功能",
        ["📝 零用金收支登記與快查及對帳","🚗 車位登記及查詢","⚙️ 常駐名冊與機車抽籤管理"],
        format_func=lambda x:{
            "📝 零用金收支登記與快查及對帳":"零用金",
            "🚗 車位登記及查詢":"車位管理",
            "⚙️ 常駐名冊與機車抽籤管理":"設定與機車抽籤",
        }[x],
        key="smartprop_main_nav"
    )

    st.markdown("---")
    st.markdown("##### 系統狀態")
    if st.session_state.get("system_settings_cloud_ready", False):
        st.success("✓ Google Sheet 已連線")
    else:
        st.warning("⚠️ Google Sheet 尚未確認")

    if st.button("↻ 重新同步資料", use_container_width=True, key="refresh_cloud_data_btn"):
        refresh_all_cloud_data(show_message=True)

    st.markdown("---")
    st.markdown(
        """
        <div class="sp-footer">
          <strong>SmartProp Community OS</strong><br>
          © 2026 詹宗霖. All rights reserved.
        </div>
        """, unsafe_allow_html=True
    )

_cloud_ready = bool(st.session_state.get("system_settings_cloud_ready", False))
_status_text = "Google Sheet 已連線" if _cloud_ready else "Google Sheet 尚未確認"

st.markdown(
    f"""
    <div class="sp-header">
      <div class="sp-header-left">
        <div class="sp-logo">SP</div>
        <div>
          <div class="sp-title">社區物業智慧管理系統</div>
          <div class="sp-subtitle">SMARTPROP WEB CONSOLE</div>
        </div>
      </div>
      <div class="sp-status"><span class="sp-dot"></span>{_status_text}</div>
    </div>
    """, unsafe_allow_html=True
)

_page_info = {
    "📝 零用金收支登記與快查及對帳":("FINANCE","零用金","收支登記、住戶查詢、LINE 對帳與統計。"),
    "🚗 車位登記及查詢":("PARKING","車位管理","車位查詢、車輛登記與固定車位管理。"),
    "⚙️ 常駐名冊與機車抽籤管理":("SETTINGS","設定與機車抽籤","管理常用資料與年度機車位抽籤。"),
}
_kicker,_title,_desc = _page_info[menu]
st.markdown(
    f"""
    <div class="sp-page-head">
      <div class="sp-page-kicker">{_kicker}</div>
      <div class="sp-page-title">{_title}</div>
      <div class="sp-page-desc">{_desc}</div>
    </div>
    """, unsafe_allow_html=True
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
    st.markdown("### 零用金查詢與登記")
    
    sub_tab1, sub_tab2 = st.tabs(["收支登記與查詢", "收支統計"])
    
    with sub_tab1:
        search_keyword = st.text_input("搜尋收支紀錄", placeholder="例如：2A + 水果錢", key="main_search_bar")
        
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
            trade_type = st.radio("登記方式", ["一般收支", "住戶轉帳"], horizontal=True, key="main_trade_type")
            next_id = (
                int(pd.to_numeric(st.session_state.ledger_data["流水號"], errors="coerce").max()) + 1
                if not st.session_state.ledger_data.empty
                and "流水號" in st.session_state.ledger_data.columns
                and pd.to_numeric(st.session_state.ledger_data["流水號"], errors="coerce").notna().any()
                else 1
            )
            current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if trade_type == "一般收支":
                st.subheader("新增收支")
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

            else:
                st.subheader("住戶轉帳")
                log_date = st.date_input("轉帳日期", value=today_dt, key="trans_date")
                from_res = st.selectbox("轉出戶別", st.session_state.resident_list, index=0, key="trans_from")
                to_res = st.selectbox("轉入戶別", st.session_state.resident_list, index=1, key="trans_to")
                transfer_amount = st.number_input("轉帳金額 (元)", min_value=0, step=1, value=0, key="trans_amount")
                handler_input = st.selectbox("經手人", st.session_state.common_handlers, key="trans_handler")
                memo = st.text_input("備註說明", value="", placeholder="例如：代墊款項", key="trans_memo")
                
                if st.button("確認轉帳", type="primary", use_container_width=True, key="save_trans_btn"):
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

        with col_line:
            st.subheader("LINE 對帳通知")
            st.caption("選擇日期與戶別後，即可產生住戶對帳文字。")
            
            inspect_date = st.date_input("對帳日期", value=today_dt, key="line_inspect_date")
            target_line_res = st.selectbox("住戶戶別", st.session_state.resident_list, key="independent_line_res")
            
            if st.button("產生 LINE 對帳文字", type="primary", use_container_width=True, key="generate_line_btn"):
                st.session_state.generated_line_text = generate_line_text(
                    target_line_res, 
                    st.session_state.ledger_data, 
                    st.session_state.resident_initial_balances, 
                    check_date=inspect_date
                )
                st.toast("🎯 LINE 該戶通知訊息已成功生成！", icon="📱")
            
            st.markdown("**LINE 對帳內容**")
            if st.session_state.generated_line_text.strip():
                st.code(st.session_state.generated_line_text, language="text")
            else:
                st.info("尚未產生對帳內容。")

    with sub_tab2:
        st.markdown("### 零用金統計")
        
        df_all_ledger = st.session_state.ledger_data.copy()
        
        c_rep1, c_rep2 = st.columns(2)
        with c_rep1:
            st.markdown("#### 每日收支")
            selected_daily_date = st.date_input("日期", value=today_dt, key="report_daily_date")
            
            if not df_all_ledger.empty:
                df_all_ledger["交易日期_dt"] = pd.to_datetime(df_all_ledger["交易日期"]).dt.date
                df_daily_filtered = df_all_ledger[df_all_ledger["交易日期_dt"] == selected_daily_date]
                
                d_income = df_daily_filtered["收入金額"].sum()
                d_expense = df_daily_filtered["支出金額"].sum()
                
                st.metric("該日總收入", f"${d_income:,.0f} 元")
                st.metric("該日總支出", f"${d_expense:,.0f} 元")
                st.metric("當日淨變動", f"${d_income - d_expense:,.0f} 元")
                
                st.markdown(f"**{selected_daily_date} 收支明細**")
                if not df_daily_filtered.empty:
                    st.dataframe(df_daily_filtered[["流水號", "戶別", "項目摘要", "收入金額", "支出金額", "經手人"]], use_container_width=True, hide_index=True)
                    
                    st.markdown("##### 各戶收支金額")
                    df_daily_filtered["總金額"] = df_daily_filtered["收入金額"] + df_daily_filtered["支出金額"]
                    df_daily_agg = df_daily_filtered.groupby("戶別")["總金額"].sum().reset_index()
                    df_daily_agg = df_daily_agg[df_daily_agg["總金額"] > 0].sort_values(by="總金額", ascending=False)
                    
                    if not df_daily_agg.empty:
                        # 將日結視覺化也改為橫式圖表以保持介面一致性與美觀
                        fig_daily_bar = px.bar(
                            df_daily_agg,
                            x="總金額",
                            y="戶別",
                            orientation="h",
                            text="總金額"
                        )
                        fig_daily_bar.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=20, r=20, t=20, b=20))
                        st.plotly_chart(fig_daily_bar, use_container_width=True, key="daily_bar_chart")
                        
                        top_res = df_daily_agg.iloc[0]
                        st.info(f"當日收支金額最高戶別：{top_res['戶別']}（${top_res['總金額']:,.0f}）")
                    else:
                        st.caption("今日各戶無金額產生。")
                else:
                    st.info("該日無任何收支異動紀錄。")
            else:
                st.info("目前無零用金資料。")

        with c_rep2:
            st.markdown("#### 每月收支")
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
                
                st.markdown(f"**{selected_year} 年 {selected_month} 月交易摘要**")
                st.write(f"總共發生 **{len(df_monthly_filtered)}** 筆交易紀錄。")
                
                if not df_monthly_filtered.empty:
                    st.markdown("##### 本月收支趨勢")
                    df_monthly_filtered["交易日期_str"] = df_monthly_filtered["交易日期"].astype(str)
                    df_day_trend = df_monthly_filtered.groupby("交易日期_str")[["收入金額", "支出金額"]].sum()
                    st.line_chart(df_day_trend)
                    
                    st.markdown("##### 各戶收支排行")
                    df_monthly_filtered["總金額"] = df_monthly_filtered["收入金額"] + df_monthly_filtered["支出金額"]
                    df_m_res_agg = df_monthly_filtered.groupby("戶別")["總金額"].sum().reset_index()
                    df_m_res_agg = df_m_res_agg[df_m_res_agg["總金額"] > 0].sort_values(by="總金額", ascending=False)
                    if not df_m_res_agg.empty:
                        # 依照你的需求，將這張圖完美改成橫式，徹底解決直式擠在一起很醜的問題
                        fig_monthly_bar = px.bar(
                            df_m_res_agg,
                            x="總金額",
                            y="戶別",
                            orientation="h",
                            text="總金額"
                        )
                        fig_monthly_bar.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=20, r=20, t=20, b=20))
                        st.plotly_chart(fig_monthly_bar, use_container_width=True, key="monthly_bar_chart")
                else:
                    st.caption("該月暫無收支走勢資料。")
            else:
                st.info("目前無零用金資料。")

        st.markdown("---")
        st.markdown("#### 住戶餘額")
        
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
                
            with st.expander("查看全部住戶餘額"):
                st.dataframe(df_res_bal, use_container_width=True, hide_index=True)
        else:
            st.info("尚無足夠資料進行餘額結算。")

    st.markdown("---")
    st.subheader("現金盤點")
    
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
    c_m1.metric("帳面餘額", f"${book_balance:,.0f} 元")
    c_m2.metric("現場現金", f"${physical_total:,.0f} 元")
    
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
    st.header("車位管理")
    
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
    
    st.markdown("### 車位使用概況")
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
    st.markdown("#### 車位使用分析")

    # 1. 總車格-空位與有使用的占比 (橫式)
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
    st.plotly_chart(fig_parking_ratio, use_container_width=True, key="parking_ratio_chart")

    # 2. 車輛- 所有車跟租客車的占比 (橫式)
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
    st.plotly_chart(fig_vehicle_ratio, use_container_width=True, key="vehicle_ratio_chart")

    all_units_set = set(st.session_state.resident_list) - {"1A"}
    unregistered_car_units = sorted(list(all_units_set - units_with_registered_car))
    unregistered_moto_units = sorted(list(all_units_set - units_with_registered_moto))
    
    with st.expander("查看尚未登記車輛的住戶"):
        uc_col1, uc_col2 = st.columns(2)
        with uc_col1:
            st.markdown(f"🚗 **未登記有效汽車車牌之戶別 ({len(unregistered_car_units)} 戶)：**")
            st.info(", ".join(unregistered_car_units) if unregistered_car_units else "無")
        with uc_col2:
            st.markdown(f"🛵 **未登記有效機車車牌之戶別 ({len(unregistered_moto_units)} 戶)：**")
            st.info(", ".join(unregistered_moto_units) if unregistered_moto_units else "無")

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
        st.subheader("車位查詢")
        
        view_mode = st.radio("顯示方式", ["只看空位", "查看全部"], horizontal=True, key="park_view_mode")
        p_search = st.text_input("搜尋車位 / 戶別 / 車主 / 車牌", key="park_search_input")
        
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
            
            if view_mode == "只看空位":
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

            df_park_view = df_park_display.copy()
            for _col in df_park_view.columns:
                if df_park_view[_col].dtype == object:
                    df_park_view[_col] = df_park_view[_col].replace({"": "—", "nan": "—", "NaN": "—", "None": "—"})
            st.dataframe(df_park_view.style.apply(highlight_empty_slots, axis=1), use_container_width=True, hide_index=True)
        else:
            st.info("💡 目前車位資料庫尚無資料。")
            
    with p_col2:
        st.subheader("車位登記")
        
        p_res_code = st.selectbox("住戶戶別", st.session_state.resident_list, key="p_reg_res")
        
        existing_res_records = df_park_raw[df_park_raw["戶別"] == p_res_code] if not df_park_raw.empty and "戶別" in df_park_raw.columns else pd.DataFrame()
        current_res_count = len(existing_res_records)
        is_auto_third_car = current_res_count >= 2
        
        if is_auto_third_car:
            st.markdown(f"""
            <div class="alert-box-custom" style="padding: 8px; font-size: 13px;">
                ⚠️ <b>防呆偵測</b>：戶別 <b>{p_res_code}</b> 目前已有 {current_res_count} 筆登記，此筆將自動歸類為第三台車或彈性車位！
            </div>
            """, unsafe_allow_html=True)

        p_space_category = st.radio("車位類型", ["🚗 汽車格", "🛵 機車格"], horizontal=True, key="p_space_cat")
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

        if st.session_state.moto_space_mapping:
            st.markdown("#### 📋 目前雲端已建立的機車位綁定清單：")
            moto_map_df = pd.DataFrame(list(st.session_state.moto_space_mapping.items()), columns=["戶別", "車位編號"])
            st.dataframe(moto_map_df[moto_map_df["車位編號"] != ""], use_container_width=True, hide_index=True)

# ==========================================
# 頁籤 3：⚙️ 常駐名冊與機車抽籤管理
# ==========================================
else:
    tab_set1, tab_set2 = st.tabs(["基本設定", "年度機車位抽籤"])

    with tab_set1:
        st.markdown(
            """
            <div class="sp-manager-note">
              直接新增、編輯或刪除清單內容；完成後會同步到 Google Sheet。
              不再使用「啟用 / 停用」設定。
            </div>
            """, unsafe_allow_html=True
        )

        tab_handlers, tab_items, tab_exclude, tab_capacity = st.tabs(
            ["經手人", "常用項目", "抽籤排除", "車位容量"]
        )

        with tab_handlers:
            render_setting_manager(
                "經手人",
                "經手人",
                "零用金登記時可選擇的人員。",
                "姓名",
                "新增經手人",
                "備註",
            )

        with tab_items:
            render_setting_manager(
                "常用項目",
                "常用項目",
                "零用金登記時常用的收支項目。",
                "項目名稱",
                "新增項目",
                "備註",
            )

        with tab_exclude:
            render_setting_manager(
                "抽籤排除",
                "抽籤排除",
                "不參加機車位抽籤的戶別。",
                "戶別",
                "新增排除戶",
                "原因",
                name_options=st.session_state.resident_list,
            )

            if not _settings_rows("抽籤排除").empty:
                st.markdown("---")
                if st.session_state.get("confirm_clear_exclusions", False):
                    st.warning("確定清除全部排除戶別？")
                    q1,q2,_ = st.columns([1,1,4])
                    if q1.button("確認清除", key="clear_exclusions_yes"):
                        if delete_all_settings_of_type("抽籤排除"):
                            st.session_state.confirm_clear_exclusions = False
                            st.success("已清除全部排除戶別。")
                    if q2.button("取消", key="clear_exclusions_no"):
                        st.session_state.confirm_clear_exclusions = False
                else:
                    if st.button("清除全部排除戶", key="clear_exclusions_open"):
                        st.session_state.confirm_clear_exclusions = True

        with tab_capacity:
            render_setting_manager(
                "車位容量",
                "車位容量",
                "設定各類車位總數；這些數值會影響車位統計與抽籤。",
                "類別",
                "新增容量",
                "備註",
                value_label="數量",
                allow_add=False,
                allow_delete=False,
            )

        st.markdown("---")
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("經手人", len(_settings_rows("經手人")))
        m2.metric("常用項目", len(_settings_rows("常用項目")))
        m3.metric("排除戶", len(_settings_rows("抽籤排除")))
        m4.metric("容量設定", len(_settings_rows("車位容量")))

    with tab_set2:
        st.markdown("### 年度機車位抽籤")
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
        
        if st.button("開始抽籤", type="primary", key="run_moto_lottery_btn"):
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

# 重新整理