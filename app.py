import os
import ssl
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import urllib.request
import base64

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

# --- 1. 全域視覺樣式 (CSS) - 原始設計完全不動 ---
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

/* 右下角圖片水印 */
.logo-watermark {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 80px;
    opacity: 0.15;
    z-index: 9999;
    pointer-events: none;
}
</style>
""", unsafe_allow_html=True)

# --- 2. 數據獲取與核心邏輯 ---
@st.cache_data(ttl=60)
def fetch_data(sid, sname):
    try:
        context = ssl._create_unverified_context()
        encoded_name = urllib.parse.quote(sname)
        url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&sheet={encoded_name}"
        with urllib.request.urlopen(url, context=context) as response:
            df = pd.read_csv(response)
            df.columns = df.columns.astype(str).str.strip()
            
            # 只有在處理 performance 數據時才進行轉換
            if "Bedsure" in sname:
                for c in ['Views', 'Cost', 'Likes', 'Comments', 'Shares', 'Saves']:
                    if c in df.columns:
                        df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '').str.replace('$', '').str.replace(' ', ''), errors='coerce').fillna(0)
                
                def calc_imps(row):
                    v = row.get('Views', 0)
                    plat = str(row.get('Platform', '')).upper()
                    if 'TIKTOK' in plat: return v * 1.12
                    if 'INS' in plat or 'INSTAGRAM' in plat: return v * 1.15
                    return v * 1.10
                df['Est_Impressions'] = df.apply(calc_imps, axis=1)
                # 預處理 Tier 確保過濾成功
                if 'Tier' in df.columns:
                    df['Tier'] = df['Tier'].astype(str).str.strip().str.upper()
            return df
    except Exception:
        return None

def render_performance_view(df, key_suffix=""):
    if df is None or df.empty:
        st.info("NO DATA AVAILABLE")
        return
    
    # --- 1. 數據計算 ---
    total_views = df['Views'].sum()
    total_imps = df['Est_Impressions'].sum()
    total_likes = df['Likes'].sum()
    total_comments = df['Comments'].sum()
    total_shares = df['Shares'].sum()
    total_saves = df['Saves'].sum()
    total_eng = total_likes + total_comments + total_shares + total_saves
    
    df['Influencer'] = df['Influencer'].astype(str).str.strip()
    df_fin = df.groupby('Influencer').agg({
        'Views': 'sum', 'Cost': 'max', 'Likes': 'sum', 
        'Comments': 'sum', 'Shares': 'sum', 'Saves': 'sum', 'Est_Impressions': 'sum'
    }).reset_index()
    
    df_fin['Total_Eng'] = df_fin['Likes'] + df_fin['Comments'] + df_fin['Shares'] + df_fin['Saves']
    df_fin['Eng_Rate'] = (df_fin['Total_Eng'] / df_fin['Views'] * 100).fillna(0)
    df_fin['CPM'] = (df_fin['Cost'] / df_fin['Views']) * 1000
    
    total_cost = df_fin['Cost'].sum()
    real_cpm = (total_cost / total_views * 1000) if total_views > 0 else 0
    avg_eng_rate = (total_eng / total_views * 100) if total_views > 0 else 0
    
    # --- 2. 頂部數據指標 ---
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("REACH (VIEWS)", f"{total_views:,.0f}")
    m2.metric("EST. IMPRESSIONS", f"{total_imps:,.0f}")
    m3.metric("AVG. ENG. RATE", f"{avg_eng_rate:.2f}%")
    m4.metric("AVG. CPM", f"${real_cpm:.2f}")
    m5.metric("POSTS", len(df))

    highlight_color = "#a86d6d"
    label_style = dict(
        font=dict(color="white", size=12, family="Oswald"),
        bgcolor=highlight_color,
        bordercolor=highlight_color,
        borderwidth=2
    )

    st.write("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([3, 2])
    
    with c1:
        st.markdown("<p style='font-family:Oswald; font-size:15px; color:#666;'>VIEWS BREAKDOWN BY PLATFORM</p>", unsafe_allow_html=True)
        sort_order_v = df_fin.sort_values('Views', ascending=False)['Influencer'].tolist()
        fig_v = px.bar(df, x='Influencer', y='Views', color='Platform', template="plotly_white", 
                     color_discrete_sequence=['#3d0204', '#7a0000', '#b87b7b'],
                     category_orders={"Influencer": sort_order_v},
                     text_auto='.2s') # 自動顯示簡寫數值
        fig_v.update_traces(textposition='outside', textfont=dict(color="black", size=10)) # 柱狀圖上方數字
        fig_v.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), height=400)
        st.plotly_chart(fig_v, use_container_width=True, key=f"v_{key_suffix}")

    with c2:
        st.markdown("<p style='font-family:Oswald; font-size:15px; color:#666;'>EFFICIENCY (CPM RANKING)</p>", unsafe_allow_html=True)
        df_cpm_rank = df_fin[df_fin['Views'] > 0].sort_values('CPM', ascending=False)
        fig_c = px.bar(df_cpm_rank, x='CPM', y='Influencer', orientation='h', 
                     template="plotly_white", color_discrete_sequence=['#ba7070'],
                     text='CPM')
        fig_c.update_traces(texttemplate='$%{text:.2f}', textposition='auto', 
                          textfont=label_style['font'], cliponaxis=False)
        # 💡 在這裡手動加上標籤背景 (Highlight)
        fig_c.update_traces(insidetextanchor='end', textfont_color="white")
        fig_c.update_layout(height=400, xaxis_title="CPM (USD)", yaxis_title="")
        st.plotly_chart(fig_c, use_container_width=True, key=f"c_{key_suffix}")

    st.write("<br>", unsafe_allow_html=True)
    c3, c4 = st.columns([3, 2])
    
    with c3:
        st.markdown("<p style='font-family:Oswald; font-size:15px; color:#666;'>CREATOR ENGAGEMENT RATE RANKING (%)</p>", unsafe_allow_html=True)
        df_eng_rank = df_fin.sort_values('Eng_Rate', ascending=True)
        fig_e = px.bar(df_eng_rank, x='Eng_Rate', y='Influencer', orientation='h', 
                     template="plotly_white", color_discrete_sequence=['#911f1f'],
                     text='Eng_Rate')
        fig_e.update_traces(texttemplate='%{text:.2f}%', textposition='auto',
                          textfont=label_style['font'])
        fig_e.update_layout(height=400, xaxis_title="Eng. Rate (%)", yaxis_title="")
        st.plotly_chart(fig_e, use_container_width=True, key=f"e_{key_suffix}")

    with c4:
        st.markdown("<p style='font-family:Oswald; font-size:15px; color:#666;'>ENGAGEMENT BEHAVIOR ANALYSIS</p>", unsafe_allow_html=True)
        pie_df = pd.DataFrame({"Metric": ["Likes", "Saves", "Comments", "Shares"],
                              "Value": [total_likes, total_saves, total_comments, total_shares]})
        fig_p = px.pie(pie_df, names='Metric', values='Value', hole=0.6, template="plotly_white", 
                     color_discrete_sequence=['#3d0204', '#5e0b0b', '#800000', '#a52a2a'])
        fig_p.update_traces(textinfo='percent', textfont=label_style['font']) # 餅圖百分比高亮
        fig_p.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=350)
        st.plotly_chart(fig_p, use_container_width=True, key=f"p_{key_suffix}")

    st.dataframe(df, use_container_width=True)

# --- 3. 登錄與側邊欄邏輯 (完全保留原始結構) ---
def check_password():
    if st.session_state.get("password_correct", False): return True
    st.markdown("<style>.stApp { background-color: #000000 !important; }</style>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([0.15, 1, 3])
    with c2:
        st.write("<br><br><br>", unsafe_allow_html=True)
        if os.path.exists("Queue Logo.png"): st.image("Queue Logo.png", width=140)
        pwd = st.text_input("PASSWORD", type="password", label_visibility="collapsed")
        if st.button("ACCESS DASHBOARD"):
            if pwd == ACCESS_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else: st.error("INVALID CODE")
    return False

if check_password():
    df_main = fetch_data(SHEET_ID, "Bedsure_2025_Q4")
    df_comments = fetch_data(SHEET_ID, "Comment Summary") # 讀取正確的 tab
    
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

    st.markdown(f'<div class="custom-header"><img src="https://bedsurehome.com/cdn/shop/files/5_c54d3500-9a81-483d-b507-6ae336e6ba90.png?v=1746503863&width=1500"><h2>Bedsure 2025 Winter Performance</h2></div>', unsafe_allow_html=True)

    st.markdown("### PROJECT OVERVIEW")
    o1, o2, o3 = st.columns([2, 1, 1])
    with o1: st.markdown(f'<div class="overview-card"><p style="font-size:12px; color:#888; margin:0;">CAMPAIGN FOCUS</p><p><b>Bedsure Winter 2025: GentleSoft Blanket</b></p><a href="{BRIEF_URL}" target="_blank" class="brief-btn">OPEN CREATOR BRIEF</a></div>', unsafe_allow_html=True)
    with o2: st.markdown('<div class="overview-card" style="text-align:center;"><p style="font-size:11px; color:#888; margin:0;">PLATFORM</p><p style="font-size:18px; font-weight:700; margin-top:5px;">TIKTOK & INSTAGRAM</p></div>', unsafe_allow_html=True)
    with o3: st.markdown('<div class="overview-card" style="text-align:center;"><p style="font-size:11px; color:#888; margin:0;">CORE PRODUCT</p><p style="font-size:18px; font-weight:700; margin-top:5px;">GentleSoft</p></div>', unsafe_allow_html=True)

    st.write("<br>", unsafe_allow_html=True)
    # PERFORMANCE DATA 放在第一，並加入 COMMENT INSIGHTS
    tp, ci, pg = st.tabs(["PERFORMANCE DATA", "COMMENT INSIGHTS", "CAMPAIGN PROGRESS"])

    with tp:
        if df_main is not None:
            # 這是你的四個 Tab
            stabs = st.tabs(["ALL", "NANO & MICRO", "MID-TIER & MACRO", "MEGA"])
            
            with stabs[0]: 
                render_performance_view(df_main, "all")
            
            with stabs[1]: 
                # 只要內容包含 "NANO" 或 "MICRO" (不論大小寫) 都能抓到
                mask_nm = df_main['Tier'].astype(str).str.upper().str.contains('NANO|MICRO', na=False)
                render_performance_view(df_main[mask_nm], "nm")
            
            with stabs[2]: 
                # 只要內容包含 "MID" 或 "MACRO" (相容 MID-TIER, MIDTIER 等)
                mask_mm = df_main['Tier'].astype(str).str.upper().str.contains('MID|MACRO', na=False)
                render_performance_view(df_main[mask_mm], "mm")
            
            with stabs[3]: 
                # 只要內容包含 "MEGA"
                mask_mega = df_main['Tier'].astype(str).str.upper().str.contains('MEGA', na=False)
                render_performance_view(df_main[mask_mega], "mega")

    with ci:
        st.markdown("### AUDIENCE RECEPTION")
        if df_comments is not None:
            for idx, row in df_comments.iterrows():
                # 使用 .get 解決 KeyError
                sentiment = str(row.get('Sentiment', 'Neutral'))
                st.markdown(f"""
                <div class="insight-card">
                    <p style="font-family:Oswald; font-size:16px; margin-bottom:5px; color:#1D1D1F;">{row.get('Creator', 'Unknown')}</p>
                    <p style="font-size:13px; color:#666; margin-bottom:2px;">
                        <b>Keywords:</b> {row.get('Keywords', '-')} &nbsp;&nbsp;|&nbsp;&nbsp; 
                        <b>Sentiment:</b> {sentiment}
                    </p>
                    <p style="font-size:14px; margin-top:8px; line-height:1.4;">{row.get('Highlights', '-')}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("NO DATA IN 'Comment Summary'")

    with pg:
        st.markdown("### EXECUTION EFFICIENCY")
        cf, ct = st.columns(2)
        with cf:
            st.markdown("<p style='font-family:Oswald; font-size:12px; color:#666;'>CONVERSION FUNNEL</p>", unsafe_allow_html=True)
            fig_f = go.Figure(go.Funnel(y=["Screened", "Reached", "Negotiated", "Confirmed", "Dropped"], x=[469, 265, 106, 16, 28], marker={"color": ["#E5E5E5", "#CCCCCC", "#999999", "#1D1D1F", "#FF4B4B"]}))
            st.plotly_chart(fig_f, use_container_width=True, key="f_pg")
        with ct:
            st.markdown("<p style='font-family:Oswald; font-size:12px; color:#666;'>WORKLOAD BY TIER</p>", unsafe_allow_html=True)
            tdf = pd.DataFrame({"Tier":["Nano","Micro","Mid","Macro","Mega"],"S":[85,132,75,118,59],"R":[73,77,53,47,34],"C":[7,1,2,1,5]})
            st.plotly_chart(px.bar(tdf, x="Tier", y=["S","R","C"], barmode='group', template="plotly_white", color_discrete_sequence=["#E5E5E5", "#999999", "#1D1D1F"]), use_container_width=True, key="w_pg")
        st.markdown("<div class='insight-card'><b>Summary:</b> Queue Agency Team screened 469 creators, converting 16 high-quality partnerships.</div>", unsafe_allow_html=True)

    # 渲染圖片水印
    if os.path.exists("Queue Logo.png"):
        with open("Queue Logo.png", "rb") as f:
            enc = base64.b64encode(f.read()).decode()
        st.markdown(f'<img src="data:image/png;base64,{enc}" class="logo-watermark">', unsafe_allow_html=True)