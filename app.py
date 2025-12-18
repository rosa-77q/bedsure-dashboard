import os
import ssl
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

FAVICON_FILE = "QueueFava.png"
p_icon = FAVICON_FILE if os.path.exists(FAVICON_FILE) else "📊"

st.set_page_config(page_title="Queue | Bedsure Portal", layout="wide", page_icon=p_icon)

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
.custom-header { display: flex; align-items: center; gap: 15px; margin-bottom: 25px; }
.custom-header img { width: 75px; height: auto; }
.custom-header h2 { margin: 0 !important; font-size: 28px; line-height: 1.2; }
.overview-card { background-color: #F8F9FA; padding: 20px; border: 1px solid #EEEEEE; height: 100%; }
.brief-btn { display: inline-block; background-color: #000000; color: #FFFFFF !important; padding: 8px 18px; text-decoration: none; font-family: 'Oswald'; font-size: 13px; margin-top: 10px; }
.stButton>button { background-color: #FFFFFF !important; color: #000000 !important; font-family: 'Oswald' !important; font-weight: 700 !important; border-radius: 2px !important; width: 100% !important; }
.insight-card { background-color: #FFFFFF; padding: 15px; border-left: 4px solid #1D1D1F; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# --- 2. 數據獲取與處理邏輯 ---
@st.cache_data(ttl=60)
def fetch_data(sid, sname):
    try:
        context = ssl._create_unverified_context()
        encoded_name = urllib.parse.quote(sname)
        url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&sheet={encoded_name}"
        with urllib.request.urlopen(url, context=context) as response:
            df = pd.read_csv(response)
            df.columns = df.columns.astype(str).str.strip()
            for c in ['Views', 'Cost', 'Likes', 'Comments', 'Shares', 'Saves']:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '').str.replace('$', '').str.replace(' ', ''), errors='coerce').fillna(0)
            
            # 🚀 擬定 Est. Impressions 估算公式
            def calc_imps(row):
                v = row.get('Views', 0)
                plat = str(row.get('Platform', '')).upper()
                if 'TIKTOK' in plat: return v * 1.12
                if 'INS' in plat or 'INSTAGRAM' in plat: return v * 1.15
                return v * 1.10
            
            df['Est_Impressions'] = df.apply(calc_imps, axis=1)
            return df
    except Exception as e:
        st.error(f"數據讀取失敗 [{sname}]: {e}")
        return None

def render_performance_view(df):
    if df is None or df.empty:
        st.info("目前此分類下暫無數據")
        return
    
    # 🚀 跨平台合併與 Package Deal 處理
    df_grouped = df.groupby('Influencer').agg({
        'Views': 'sum',
        'Est_Impressions': 'sum',
        'Cost': 'max', 
        'Likes': 'sum',
        'Comments': 'sum',
        'Shares': 'sum',
        'Saves': 'sum'
    }).reset_index()

    total_views = df_grouped['Views'].sum()
    total_imps = df_grouped['Est_Impressions'].sum()
    total_cost = df_grouped['Cost'].sum()
    avg_cpm = (total_cost / total_views * 1000) if total_views > 0 else 0
    total_eng = df_grouped[['Likes','Comments','Shares','Saves']].sum().sum()
    
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("EST. IMPRESSIONS", f"{total_imps:,.0f}")
    m2.metric("REACH (VIEWS)", f"{total_views:,.0f}")
    m3.metric("AVG. CPM", f"${avg_cpm:.2f}")
    m4.metric("ENGAGEMENT", f"{(total_eng/total_views*100) if total_views>0 else 0:.2f}%")
    m5.metric("POSTS", len(df))

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<p style='font-family:Oswald; font-size:12px; color:#666;'>VIEWS BY INFLUENCER</p>", unsafe_allow_html=True)
        fig_v = px.bar(df_grouped.sort_values('Views', ascending=False), x='Influencer', y='Views', 
                     template="plotly_white", color_discrete_sequence=['#1D1D1F'])
        st.plotly_chart(fig_v, use_container_width=True)
    with c2:
        st.markdown("<p style='font-family:Oswald; font-size:12px; color:#666;'>CPM RANKING (LOWER IS BETTER)</p>", unsafe_allow_html=True)
        df_grouped['CPM'] = (df_grouped['Cost'] / df_grouped['Views']) * 1000
        df_cpm = df_grouped[df_grouped['Views'] > 0].sort_values('CPM', ascending=True)
        fig_c = px.bar(df_cpm, x='CPM', y='Influencer', orientation='h',
                     template="plotly_white", color_discrete_sequence=['#86868B'])
        st.plotly_chart(fig_c, use_container_width=True)
    st.dataframe(df, use_container_width=True)

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
            else: st.error("INVALID CODE")
    return False

# --- 3. 主頁面邏輯 ---
if check_password():
    df_main = fetch_data(SHEET_ID, "Bedsure_2025_Q4")
    df_analysis = fetch_data(SHEET_ID, "Comment_Analysis")

    with st.sidebar:
        if os.path.exists("Queue Logo-01 transp.png"): 
            st.image("Queue Logo-01 transp.png", use_container_width=True)
        st.divider()
        st.markdown("<p style='font-family:Oswald; font-size:11px; color:#888;'>PRESENTED BY</p><p style='font-family:Oswald; font-weight:700; font-size:18px;'>QUEUE AGENCY</p>", unsafe_allow_html=True)
        if st.button("REFRESH DATA"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        if st.button("LOGOUT"):
            st.session_state["password_correct"] = False
            st.rerun()

    st.markdown(f'<div class="custom-header"><img src="https://bedsurehome.com/cdn/shop/files/5_c54d3500-9a81-483d-b507-6ae336e6ba90.png?v=1746503863&width=1500"><h2>Bedsure 2025 Winter Influencer Performance</h2></div>', unsafe_allow_html=True)

    st.markdown("### 📋 PROJECT OVERVIEW")
    ov1, ov2, ov3 = st.columns([2, 1, 1])
    with ov1:
        st.markdown(f'<div class="overview-card"><p style="font-size:12px; color:#888; margin:0;">CAMPAIGN FOCUS</p><p><b>Bedsure Winter 2025: GentleSoft™ Blanket</b><br>提升品牌在冬季居家市場的爆光與互動。</p><a href="{BRIEF_URL}" target="_blank" class="brief-btn">OPEN CREATOR BRIEF</a></div>', unsafe_allow_html=True)
    with ov2: st.markdown('<div class="overview-card" style="text-align:center;"><p style="font-size:11px; color:#888; margin:0;">PLATFORM</p><p style="font-size:18px; font-weight:700; margin-top:5px;">TIKTOK & INSTAGRAM</p></div>', unsafe_allow_html=True)
    with ov3: st.markdown('<div class="overview-card" style="text-align:center;"><p style="font-size:11px; color:#888; margin:0;">CORE PRODUCT</p><p style="font-size:18px; font-weight:700; margin-top:5px;">GentleSoft™ Blanket</p></div>', unsafe_allow_html=True)

    st.write("<br>", unsafe_allow_html=True)
    tab_perf, tab_comm, tab_prog = st.tabs(["PERFORMANCE DATA", "COMMENT SUMMARY", "CAMPAIGN PROGRESS"])

    with tab_perf:
        if df_main is not None:
            s_tabs = st.tabs(["ALL", "NANO & MICRO (小)", "MID-TIER (中)", "MACRO & MEGA (大)"])
            with s_tabs[0]: render_performance_view(df_main)
            with s_tabs[1]: render_performance_view(df_main[df_main['Tier'].str.upper().isin(['NANO', 'MICRO'])])
            with s_tabs[2]: render_performance_view(df_main[df_main['Tier'].str.upper() == 'MID-TIER'])
            with s_tabs[3]: render_performance_view(df_main[df_main['Tier'].str.upper().isin(['MACRO', 'MEGA'])])

    with tab_comm:
        if df_analysis is not None:
            c_l, c_r = st.columns([2, 1])
            with c_l:
                if 'Keywords' in df_analysis.columns:
                    all_tags = []
                    for row in df_analysis['Keywords'].dropna():
                        all_tags.extend([t.strip().title() for t in str(row).split(',') if t.strip()])
                    if all_tags:
                        tag_counts = pd.Series(all_tags).value_counts().reset_index().head(10)
                        tag_counts.columns = ['Topic', 'Mentions']
                        st.markdown("<p style='font-family:Oswald; font-size:12px; color:#666;'>MOST MENTIONED KEYWORDS</p>", unsafe_allow_html=True)
                        st.plotly_chart(px.bar(tag_counts, x='Mentions', y='Topic', orientation='h', template="plotly_white", color_discrete_sequence=['#1D1D1F']), use_container_width=True)
            with c_r:
                st.markdown("<p style='font-family:Oswald; font-size:12px; color:#666;'>QUALITATIVE HIGHLIGHTS</p>", unsafe_allow_html=True)
                for _, r in df_analysis.iterrows():
                    st.markdown(f'<div class="insight-card"><small>{r.get("Creator", "User")}</small><br><b>{r.get("Highlights", "")}</b></div>', unsafe_allow_html=True)

    with tab_prog:
        st.markdown("### EXECUTION EFFICIENCY")
        c_f, c_t = st.columns([1, 1])
        with c_f:
            st.markdown("<p style='font-family:Oswald; font-size:12px; color:#666;'>CONVERSION FUNNEL</p>", unsafe_allow_html=True)
            fig_funnel = go.Figure(go.Funnel(
                y = ["Screened", "Reached Out", "Negotiated", "Confirmed", "Dropped"],
                x = [469, 265, 106, 16, 28],
                textinfo = "value+percent initial",
                marker = {"color": ["#E5E5E5", "#CCCCCC", "#999999", "#1D1D1F", "#FF4B4B"]}
            ))
            fig_funnel.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_funnel, use_container_width=True)
        with c_t:
            st.markdown("<p style='font-family:Oswald; font-size:12px; color:#666;'>WORKLOAD BY TIER</p>", unsafe_allow_html=True)
            tier_df = pd.DataFrame({
                "Tier": ["Nano", "Micro", "Midtier", "Macro", "Mega"],
                "Screened": [85, 132, 75, 118, 59],
                "Reached": [73, 77, 53, 47, 34],
                "Confirmed": [7, 1, 2, 1, 5]
            })
            fig_tier = px.bar(tier_df, x="Tier", y=["Screened", "Reached", "Confirmed"], 
                             barmode='group', template="plotly_white", color_discrete_sequence=["#E5E5E5", "#999999", "#1D1D1F"])
            st.plotly_chart(fig_tier, use_container_width=True)
        st.markdown("<div class='insight-card'><b>Campaign Summary:</b> Queue Agency 團隊共篩選 469 位博主，轉化出 16 位高品質合作者。</div>", unsafe_allow_html=True)