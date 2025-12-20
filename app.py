import os
import ssl
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
import urllib.request
import base64
import datetime

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
COMMENT_GID = "1071668085"  
TIMESTAMP_GID = "2083874747" # <--- 請務必替換為 Google Sheet 的 gid 數字
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
.custom-header { display: flex; align-items: center; gap: 15px; margin-bottom: 5px; }
.custom-header img { width: 75px; height: auto; }
.custom-header h2 { margin: 0 !important; font-size: 28px; line-height: 1.2; }
.overview-card { background-color: #F8F9FA; padding: 20px; border: 1px solid #EEEEEE; height: 100%; }
.brief-btn { display: inline-block; background-color: #000000; color: #FFFFFF !important; padding: 8px 18px; text-decoration: none; font-family: 'Oswald'; font-size: 13px; margin-top: 10px; }
.stButton>button { background-color: #FFFFFF !important; color: #000000 !important; font-family: 'Oswald' !important; font-weight: 700 !important; border-radius: 2px !important; width: 100% !important; }
.insight-card { background-color: #FFFFFF; padding: 15px; border-left: 4px solid #1D1D1F; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }

/* 呼吸燈小圓點動畫 */
@keyframes pulse {
    0% { box-shadow: 0 0 0 0px rgba(168, 109, 109, 0.7); }
    100% { box-shadow: 0 0 0 8px rgba(168, 109, 109, 0); }
}
.status-dot {
    height: 8px; width: 8px; background-color: #a86d6d; border-radius: 50%; display: inline-block;
    animation: pulse 2s infinite; margin-right: 8px;
}

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

# --- 2. 數據獲取邏輯 ---
@st.cache_data(ttl=60)
def fetch_last_sync(sid, gid):
    try:
        ts_url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}"
        ts_df = pd.read_csv(ts_url)
        return str(ts_df.iloc[0, 0])
    except:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M EST")

@st.cache_data(ttl=60)
def fetch_data(sid, sname):
    try:
        context = ssl._create_unverified_context()
        encoded_name = urllib.parse.quote(sname)
        url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&sheet={encoded_name}"
        with urllib.request.urlopen(url, context=context) as response:
            df = pd.read_csv(response)
            df.columns = df.columns.astype(str).str.strip()
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
                if 'Tier' in df.columns:
                    df['Tier'] = df['Tier'].astype(str).str.strip().str.upper()
            return df
    except Exception:
        return None

# --- 3. 核心繪圖函數 ---
def render_performance_view(df, key_suffix=""):
    if df is None or df.empty:
        st.info("NO DATA AVAILABLE")
        return
    
    # 數據計算
    total_views = df['Views'].sum()
    total_imps = df['Est_Impressions'].sum()
    total_likes = df['Likes'].sum()
    total_comments = df['Comments'].sum()
    total_shares = df['Shares'].sum()
    total_saves = df['Saves'].sum()
    total_eng = total_likes + total_comments + total_shares + total_saves
    
    df_fin = df.groupby('Influencer').agg({
        'Views': 'sum', 'Cost': 'max', 'Likes': 'sum', 
        'Comments': 'sum', 'Shares': 'sum', 'Saves': 'sum', 'Est_Impressions': 'sum'
    }).reset_index()
    
    df_fin['Total_Eng'] = df_fin['Likes'] + df_fin['Comments'] + df_fin['Shares'] + df_fin['Saves']
    df_fin['Eng_Rate'] = (df_fin['Total_Eng'] / df_fin['Views'] * 100).fillna(0)
    df_fin['CPM'] = (df_fin['Cost'] / df_fin['Views'] * 1000).fillna(0)
    
    total_cost = df_fin['Cost'].sum()
    real_cpm = (total_cost / total_views * 1000) if total_views > 0 else 0
    avg_eng_rate = (total_eng / total_views * 100) if total_views > 0 else 0
    
    # 頂部指標
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("REACH (VIEWS)", f"{total_views:,.0f}")
    m2.metric("EST. IMPRESSIONS", f"{total_imps:,.0f}")
    m3.metric("AVG. ENG. RATE", f"{avg_eng_rate:.2f}%")
    m4.metric("AVG. CPM", f"${real_cpm:.2f}")
    m5.metric("POSTS", len(df))

    highlight_style = dict(font=dict(color="white", size=12, family="Oswald"), bgcolor="#a86d6d")

    # 第一排：規模 vs 效率 (Views & CPM)
    st.write("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("<p style='font-family:Oswald; font-size:15px; color:#666;'>VIEWS BREAKDOWN BY PLATFORM</p>", unsafe_allow_html=True)
        sort_order_v = df_fin.sort_values('Views', ascending=False)['Influencer'].tolist()
        fig_v = px.bar(df, x='Influencer', y='Views', color='Platform', template="plotly_white", 
                     color_discrete_sequence=['#3d0204', '#7a0000', '#b87b7b'],
                     category_orders={"Influencer": sort_order_v}, text_auto='.2s')
        fig_v.update_traces(textposition='outside', textfont=dict(color="black", size=10))
        fig_v.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), height=400)
        st.plotly_chart(fig_v, use_container_width=True, key=f"v_{key_suffix}")

    with c2:
        st.markdown("<p style='font-family:Oswald; font-size:15px; color:#666;'>EFFICIENCY (CPM RANKING)</p>", unsafe_allow_html=True)
        fig_c = px.bar(df_fin[df_fin['Views'] > 0].sort_values('CPM', ascending=False), x='CPM', y='Influencer', orientation='h', 
                     template="plotly_white", color_discrete_sequence=['#ba7070'], text='CPM')
        fig_c.update_traces(texttemplate=' $%{text:.2f} ', textposition='inside', textfont=highlight_style['font'])
        fig_c.update_layout(height=400, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_c, use_container_width=True, key=f"c_{key_suffix}")

    # 第二排：質量分析 (ER% & Donut)
    st.write("<br>", unsafe_allow_html=True)
    c3, c4 = st.columns([3, 2])
    with c3:
        st.markdown("<p style='font-family:Oswald; font-size:15px; color:#666;'>CREATOR ENGAGEMENT RATE RANKING (%)</p>", unsafe_allow_html=True)
        fig_e = px.bar(df_fin.sort_values('Eng_Rate', ascending=True), x='Eng_Rate', y='Influencer', orientation='h', 
                     template="plotly_white", color_discrete_sequence=['#911f1f'], text='Eng_Rate')
        fig_e.update_traces(texttemplate=' %{text:.2f}% ', textposition='inside', textfont=highlight_style['font'])
        fig_e.update_layout(height=400, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_e, use_container_width=True, key=f"e_{key_suffix}")

    with c4:
        st.markdown("<p style='font-family:Oswald; font-size:15px; color:#666;'>ENGAGEMENT BEHAVIOR ANALYSIS</p>", unsafe_allow_html=True)
        pie_df = pd.DataFrame({"Metric": ["Likes", "Saves", "Comments", "Shares"], "Value": [total_likes, total_saves, total_comments, total_shares]})
        fig_p = px.pie(pie_df, names='Metric', values='Value', hole=0.6, template="plotly_white", 
                     color_discrete_sequence=['#3d0204', '#5e0b0b', '#800000', '#a52a2a'])
        fig_p.update_traces(textinfo='percent', textfont=highlight_style['font'])
        fig_p.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=350, showlegend=False)
        st.plotly_chart(fig_p, use_container_width=True, key=f"p_{key_suffix}")

    st.dataframe(df, use_container_width=True)

# --- 4. 登錄與主要流程 ---
def check_password():
    if st.session_state.get("password_correct", False): return True
    st.markdown("<style>.stApp { background-color: #000000 !important; }</style>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([0.15, 1, 3])
    with c2:
        st.write("<br><br><br>", unsafe_allow_html=True)
        if os.path.exists("Queue Logo.png"): st.image("Queue Logo.png", width=140)
        st.markdown("""
            <div style="margin-top: -10px; margin-bottom: 30px;">
                <p style="font-family: 'Oswald', sans-serif; color: #FFFFFF; font-size: 20px; letter-spacing: 4px; font-weight: 300; opacity: 0.8;">
                    CLIENT PORTAL
                </p>
            </div>
        """, unsafe_allow_html=True)
        pwd = st.text_input("PASSWORD", type="password", label_visibility="collapsed")
        if st.button("ACCESS DASHBOARD"):
            if pwd == ACCESS_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else: st.error("INVALID CODE")
    return False

if check_password():
    # 定義 GID 專用讀取函數
    def fetch_data_by_gid(sid, gid):
        try:
            context = ssl._create_unverified_context()
            url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv&gid={gid}"
            with urllib.request.urlopen(url, context=context) as response:
                df = pd.read_csv(response)
                # 強制清洗標題空格
                df.columns = [str(c).strip() for c in df.columns]
                return df
        except Exception as e:
            return None

    # 使用 GID 讀取兩個不同的分頁
    df_main = fetch_data(SHEET_ID, "Bedsure_2025_Q4") # 保留原本名稱讀取方式
    df_comments = fetch_data_by_gid(SHEET_ID, COMMENT_GID) # 強制使用 GID 讀取評論
    last_update = fetch_last_sync(SHEET_ID, TIMESTAMP_GID)
    
    # 側邊欄
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

    # 頁面標頭
    st.markdown(f'<div class="custom-header"><img src="https://bedsurehome.com/cdn/shop/files/5_c54d3500-9a81-483d-b507-6ae336e6ba90.png?v=1746503863&width=1500"><h2>Bedsure 2025 Winter Performance</h2></div>', unsafe_allow_html=True)
    
    # 自動更新狀態列
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 5px; margin-bottom: 25px;">
            <span class="status-dot"></span>
            <span style="font-family: 'Oswald'; font-size: 12px; color: #a86d6d; letter-spacing: 1px;">
                AUTO-SYNC: <span style="color: #444;">ACTIVE</span> | DATA LAST UPDATED: {last_update}
            </span>
        </div>
    """, unsafe_allow_html=True)

    # 項目概覽
    st.markdown("### PROJECT OVERVIEW")
    o1, o2, o3 = st.columns([2, 1, 1])
    with o1: st.markdown(f'<div class="overview-card"><p style="font-size:12px; color:#888; margin:0;">CAMPAIGN FOCUS</p><p><b>Bedsure Winter 2025: GentleSoft Blanket</b></p><a href="{BRIEF_URL}" target="_blank" class="brief-btn">OPEN CREATOR BRIEF</a></div>', unsafe_allow_html=True)
    with o2: st.markdown('<div class="overview-card" style="text-align:center;"><p style="font-size:11px; color:#888; margin:0;">PLATFORM</p><p style="font-size:18px; font-weight:700; margin-top:5px;">TIKTOK & INSTAGRAM</p></div>', unsafe_allow_html=True)
    with o3: st.markdown('<div class="overview-card" style="text-align:center;"><p style="font-size:11px; color:#888; margin:0;">CORE PRODUCT</p><p style="font-size:18px; font-weight:700; margin-top:5px;">GentleSoft</p></div>', unsafe_allow_html=True)

    st.write("<br>", unsafe_allow_html=True)
    
  # --- 主要分頁標籤 ---
    tp, ci, pg = st.tabs(["PERFORMANCE DATA", "COMMENT INSIGHTS", "CAMPAIGN PROGRESS"])

    with tp:
        if df_main is not None:
            stabs = st.tabs(["ALL", "NANO & MICRO", "MID-TIER & MACRO", "MEGA"])
            with stabs[0]: 
                render_performance_view(df_main, "all")
            with stabs[1]: 
                mask_nm = df_main['Tier'].astype(str).str.upper().str.contains('NANO|MICRO', na=False)
                render_performance_view(df_main[mask_nm], "nm")
            with stabs[2]: 
                mask_mm = df_main['Tier'].astype(str).str.upper().str.contains('MID|MACRO', na=False)
                render_performance_view(df_main[mask_mm], "mm")
            with stabs[3]: 
                mask_mega = df_main['Tier'].astype(str).str.upper().str.contains('MEGA', na=False)
                render_performance_view(df_main[mask_mega], "mega")

    with ci:
        st.markdown("### AUDIENCE RECEPTION ANALYSIS")
        
        if df_comments is not None and not df_comments.empty:
            df_comments.columns = [str(c).strip() for c in df_comments.columns]
            col_map = {c.lower(): c for c in df_comments.columns}
            target_col = col_map.get('sentiment')

            if target_col:
                c_top1, c_top2 = st.columns([2, 3])
                
                with c_top1:
                    st.markdown("<p style='font-family:Oswald; font-size:12px; color:#666;'>SENTIMENT DISTRIBUTION</p>", unsafe_allow_html=True)
                    fig_sent = px.pie(df_comments, names=target_col, hole=0.7,
                                     template="plotly_white",
                                     color=target_col,
                                     color_discrete_map={
                                         'Positive': '#a86d6d', 
                                         'Neutral': '#DDDDDD', 
                                         'Negative': '#1D1D1F'
                                     })
                    fig_sent.update_layout(margin=dict(t=0, b=0, l=0, r=10), height=250, showlegend=True)
                    st.plotly_chart(fig_sent, use_container_width=True, key="sent_chart_new")

                with c_top2:
                    kw_col = col_map.get('keywords')
                    if kw_col:
                        st.markdown("<p style='font-family:Oswald; font-size:12px; color:#666;'>TOP MENTIONED KEYWORDS</p>", unsafe_allow_html=True)
                        all_kw = df_comments[kw_col].astype(str).str.split(',').explode().str.strip().value_counts().reset_index()
                        all_kw.columns = ['Keyword', 'Count']
                        fig_tree = px.treemap(all_kw.head(12), path=['Keyword'], values='Count',
                                             template="plotly_white",
                                             color_discrete_sequence=['#F8F9FA'])
                        fig_tree.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250)
                        st.plotly_chart(fig_tree, use_container_width=True, key="kw_tree_new")

                st.divider()

                st.markdown("<p style='font-family:Oswald; font-size:12px; color:#666;'>TOP CREATOR HIGHLIGHTS</p>", unsafe_allow_html=True)
                card_cols = st.columns(3)
                for i, (idx, row) in enumerate(df_comments.iterrows()):
                    with card_cols[i % 3]:
                        c_name = row.get(col_map.get('creator', ''), 'Unknown')
                        c_sent_val = str(row.get(target_col, 'Neutral')).strip()
                        c_key = row.get(col_map.get('keywords', ''), '-')
                        c_high = row.get(col_map.get('highlights', ''), '-')
                        
                        s_color = "#a86d6d" if c_sent_val.capitalize() == "Positive" else "#1D1D1F" if c_sent_val.capitalize() == "Negative" else "#CCCCCC"
                        
                        st.markdown(f"""
                        <div style="background-color:#FFFFFF; padding:15px; border:1px solid #EEE; border-top:4px solid {s_color}; margin-bottom:15px; height:240px; overflow:hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                            <div style="display:flex; justify-content:space-between; align-items:start;">
                                <p style="font-family:Oswald; font-size:14px; margin:0; color:#1D1D1F; font-weight:700; text-transform:uppercase;">{c_name}</p>
                                <span style="font-size:9px; background:{s_color}; color:white; padding:2px 8px; border-radius:10px; font-family:Oswald;">{c_sent_val.upper()}</span>
                            </div>
                            <p style="font-size:10px; color:#a86d6d; margin-top:8px; font-family:Oswald; text-transform:uppercase; letter-spacing:1px;">{c_key}</p>
                            <p style="font-size:13px; line-height:1.5; color:#444; font-style:italic; margin-top:10px; font-family:'Lato';">"{c_high}"</p>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("NO DATA FOUND IN 'COMMENT SUMMARY' TAB.")

    with pg:
        st.markdown("### EXECUTION EFFICIENCY")
        cf, ct = st.columns(2)
        with cf:
            st.markdown("<p style='font-family:Oswald; font-size:12px; color:#666;'>CONVERSION FUNNEL</p>", unsafe_allow_html=True)
            fig_f = go.Figure(go.Funnel(
                y=["Screened", "Reached", "Negotiated", "Confirmed", "Dropped"], 
                x=[469, 265, 106, 16, 28], 
                marker={"color": ["#E5E5E5", "#CCCCCC", "#999999", "#1D1D1F", "#FF4B4B"]}
            ))
            fig_f.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=400)
            st.plotly_chart(fig_f, use_container_width=True, key="funnel_pg")
        
        with ct:
            st.markdown("<p style='font-family:Oswald; font-size:12px; color:#666;'>WORKLOAD BY TIER</p>", unsafe_allow_html=True)
            tdf = pd.DataFrame({
                "Tier":["Nano","Micro","Mid","Macro","Mega"],
                "S":[85,132,75,118,59],
                "R":[73,77,53,47,34],
                "C":[7,1,2,1,5]
            })
            fig_w = px.bar(tdf, x="Tier", y=["S","R","C"], barmode='group', template="plotly_white", 
                         color_discrete_sequence=["#E5E5E5", "#999999", "#1D1D1F"])
            fig_w.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=400, showlegend=False)
            st.plotly_chart(fig_w, use_container_width=True, key="workload_pg")
        
        st.markdown("<div class='insight-card'><b>Summary:</b> Queue Agency Team screened 469 creators, successfully converting 16 high-quality partnerships with efficient resource allocation.</div>", unsafe_allow_html=True)
# 水印
if os.path.exists("Queue Logo.png"):
            with open("Queue Logo.png", "rb") as f: enc = base64.b64encode(f.read()).decode()
            st.markdown(f'<img src="data:image/png;base64,{enc}" class="logo-watermark">', unsafe_allow_html=True)