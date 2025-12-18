import os
import ssl
import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse
import urllib.request

# --- 0. 環境修復與 Favicon 設置 ---
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# 配置設定
ACCESS_PASSWORD = "bedsure2025"
SHEET_ID = "1ILGAE7VSm01qsQufx8Fk2hsdt3ltUJmfhyDNa4yO8b0"
BRIEF_URL = "https://docs.google.com/document/d/1C9ipHwo2Xl5Rnjy7VjL6hQvdmJ9rjvOTFgMiOV_IGfE/edit?usp=sharing"

# Favicon 安全加載
FAVICON_FILE = "QueueFava.png"
p_icon = FAVICON_FILE if os.path.exists(FAVICON_FILE) else "📊"

st.set_page_config(
    page_title="Queue | Bedsure Portal",
    layout="wide",
    page_icon=p_icon
)

# --- 1. 全域視覺樣式 (CSS) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&family=Oswald:wght@600;700&display=swap');

[data-testid="stAppViewBlockContainer"] { padding-top: 1.5rem !important; }
html, body, [class*="css"] { font-family: 'Lato', sans-serif; }
h1, h2, h3, .client-title, [data-testid="stMetricLabel"] p {
    font-family: 'Oswald', sans-serif !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}

img { border-radius: 0px !important; }

.custom-header {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 25px;
}
.custom-header img { width: 75px; height: auto; }
.custom-header h2 { margin: 0 !important; font-size: 28px; line-height: 1.2; }

.overview-card {
    background-color: #F8F9FA;
    padding: 20px;
    border: 1px solid #EEEEEE;
    height: 100%;
}
.brief-btn {
    display: inline-block;
    background-color: #000000;
    color: #FFFFFF !important;
    padding: 8px 18px;
    text-decoration: none;
    font-family: 'Oswald';
    font-size: 13px;
    margin-top: 10px;
}

.stButton>button {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    font-family: 'Oswald' !important;
    font-weight: 700 !important;
    border-radius: 2px !important;
    width: 100% !important;
}

.insight-card {
    background-color: #FFFFFF;
    padding: 15px;
    border-left: 4px solid #1D1D1F;
    margin-bottom: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# --- 2. 數據獲取與驗證 ---
@st.cache_data(ttl=60)
def fetch_data(sid, sname):
    try:
        context = ssl._create_unverified_context()
        encoded_name = urllib.parse.quote(sname)
        url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&sheet={encoded_name}"
        with urllib.request.urlopen(url, context=context) as response:
            df = pd.read_csv(response)
            df.columns = df.columns.astype(str).str.strip()
            return df
    except Exception as e:
        st.error(f"無法讀取 [{sname}]: {e}")
        return None

def check_password():
    if st.session_state.get("password_correct", False): return True
    st.markdown("<style>.stApp { background-color: #000000 !important; }</style>", unsafe_allow_html=True)
    st.write("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([0.15, 1, 3])
    with c2:
        if os.path.exists("Queue Logo.png"): st.image("Queue Logo.png", width=140)
        st.markdown("<p style='color:#555; font-family:Oswald; font-size:11px; letter-spacing:2px; margin:20px 0 10px 0;'>SECURE PORTAL</p>", unsafe_allow_html=True)
        pwd = st.text_input("PASSWORD", type="password", label_visibility="collapsed")
        if st.button("ACCESS DASHBOARD"):
            if pwd == ACCESS_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("INVALID CODE")
    return False

# --- 3. 頁面內容 ---
if check_password():
    # 讀取數據
    df_main = fetch_data(SHEET_ID, "Bedsure_2025_Q4")
    df_analysis = fetch_data(SHEET_ID, "Comment_Analysis")

    # 側邊欄配置
    with st.sidebar:
        if os.path.exists("Queue Logo-01 transp.png"): 
            st.image("Queue Logo-01 transp.png", use_container_width=True)
        st.divider()
        st.markdown("<p style='font-family:Oswald; font-size:11px; color:#888;'>PRESENTED BY</p><p style='font-family:Oswald; font-weight:700; font-size:18px;'>QUEUE AGENCY</p>", unsafe_allow_html=True)
        
        #  刷新按鈕
        if st.button("REFRESH DATA"):
            st.cache_data.clear()
            st.rerun()
            
        st.divider()
        if st.button("LOGOUT"):
            st.session_state["password_correct"] = False
            st.rerun()

    # --- Header ---
    st.markdown(f"""
    <div class="custom-header">
    <img src="https://bedsurehome.com/cdn/shop/files/5_c54d3500-9a81-483d-b507-6ae336e6ba90.png?v=1746503863&width=1500">
    <h2>Bedsure Influencer Performance</h2>
    </div>
    """, unsafe_allow_html=True)

    # --- Project Overview 區塊 ---
    st.markdown("### 📋 PROJECT OVERVIEW")
    ov1, ov2, ov3 = st.columns([2, 1, 1])
    with ov1:
        st.markdown(f"""
        <div class="overview-card">
        <p style="font-family:Oswald; font-size:12px; color:#888; margin:0;">CAMPAIGN FOCUS</p>
        <p style="margin:5px 0;"><b>Bedsure Winter 2025: GentleSoft™ Comfort</b><br>推廣 GentleSoft™ 毯子，提升品牌在冬季居家市場的質感與互動。</p>
        <a href="{BRIEF_URL}" target="_blank" class="brief-btn">OPEN CREATOR BRIEF</a>
        </div>
        """, unsafe_allow_html=True)
    with ov2:
        st.markdown('<div class="overview-card" style="text-align:center;"><p style="font-family:Oswald; font-size:11px; color:#888; margin:0;">PLATFORM</p><p style="font-size:18px; font-weight:700; margin-top:5px;">TIKTOK & INSTAGRAM</p></div>', unsafe_allow_html=True)
    with ov3:
        st.markdown('<div class="overview-card" style="text-align:center;"><p style="font-family:Oswald; font-size:11px; color:#888; margin:0;">CORE PRODUCT</p><p style="font-size:18px; font-weight:700; margin-top:5px;">GentleSoft™</p></div>', unsafe_allow_html=True)

    # --- 數據展示區域 ---
    if df_main is not None:
        # 清洗數據
        for c in ['Views', 'Cost', 'Likes', 'Comments', 'Shares', 'Saves']:
            if c in df_main.columns:
                df_main[c] = pd.to_numeric(df_main[c].astype(str).str.replace(',', '').str.replace('$', '').str.strip(), errors='coerce').fillna(0)

        v = df_main['Views'].sum()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("TOTAL REACH", f"{v:,.0f}")
        m2.metric("TOTAL SPEND", f"${df_main['Cost'].sum():,.0f}")
        m3.metric("ENGAGEMENT", f"{(df_main[['Likes','Comments','Shares','Saves']].sum().sum()/v*100) if v>0 else 0:.2f}%")
        m4.metric("CREATORS", len(df_main['Influencer'].unique()))

        st.divider()
        tab1, tab2 = st.tabs(["PERFORMANCE DATA", "COMMENT SUMMARY"])

        with tab1:
            fig = px.bar(df_main.sort_values('Views', ascending=False), x='Influencer', y='Views', color='Platform', template="plotly_white", color_discrete_sequence=['#969696', '#424245', '#590000'])
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df_main, use_container_width=True)

        with tab2:
            if df_analysis is not None:
                if 'Keywords' in df_analysis.columns:
                    all_tags = []
                    for row in df_analysis['Keywords'].dropna():
                        all_tags.extend([t.strip().title() for t in str(row).split(',') if t.strip()])

                    if all_tags:
                        tag_counts = pd.Series(all_tags).value_counts().reset_index()
                        tag_counts.columns = ['Topic', 'Mentions']

                        c_l, c_r = st.columns([2, 1])
                        with c_l:
                            st.markdown("<p style='font-family:Oswald; font-size:12px; color:#666;'>MOST MENTIONED KEYWORDS</p>", unsafe_allow_html=True)
                            fig_tag = px.bar(tag_counts.head(10), x='Mentions', y='Topic', orientation='h', template="plotly_white", color_discrete_sequence=['#1D1D1F'])
                            st.plotly_chart(fig_tag, use_container_width=True)
                        with c_r:
                            st.markdown("<p style='font-family:Oswald; font-size:12px; color:#666;'>QUALITATIVE HIGHLIGHTS</p>", unsafe_allow_html=True)
                            for _, r in df_analysis.iterrows():
                                st.markdown(f'<div class="insight-card"><small>{r.get("Creator", "User")}</small><br><b>{r.get("Highlights", "")}</b></div>', unsafe_allow_html=True)