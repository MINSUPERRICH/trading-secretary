import streamlit as st
import pandas as pd
from tradingview_screener import Query, col

st.set_page_config(page_title="Secure Watchlist Secretary", layout="wide")

# --- 🔒 SECURITY ---
MY_PASSWORD = st.secrets["APP_PASSWORD"] if "APP_PASSWORD" in st.secrets else "rich"

with st.sidebar:
    st.header("🔐 Login")
    user_pass = st.text_input("Enter Password", type="password")
    if user_pass != MY_PASSWORD:
        st.warning("Enter password to access.")
        st.stop()
    
    st.success("Access Granted")
    st.divider()
    st.header("📂 Upload Watchlist")
    uploaded_file = st.file_uploader("Upload .csv or .xlsx", type=["csv", "xlsx"])

st.title("🚀 Watchlist Secretary (Dip Finder)")
st.markdown("""
**Strategy:**
1. ✅ **Triple Trend:** Price > 20 EMA on **Weekly**, **Daily**, and **4H**.
2. 🚀 **4H Signal:** Light is based on **4-Hour** MACD (Sniper Entry).
3. 📉 **1H Trend:** Shows "🔻 DIP" if 1H Price < EMA (Buying Chance).
""")

# --- THE ROBUST SCANNER ---
def run_robust_scan():
    q = Query().set_markets('america')
    
    # Requesting Triple Timeframe + 1H Data (for display only)
    q.select(
        'name', 'close', 'volume', 'change',
        'premarket_close', 'premarket_change',
        'EMA20',               # Daily
        'MACD.macd|240', 'MACD.signal|240', # 4H Signal
        'close|1W', 'EMA20|1W',  # Weekly
        'close|240', 'EMA20|240',# 4-Hour
        'close|60', 'EMA20|60'   # 1-Hour (For Dip Detection)
    )
    
    q.where(col('volume') > 500000)
    q.limit(4000)
    
    data = q.get_scanner_data()
    df = None
    if isinstance(data, tuple):
        if isinstance(data[0], pd.DataFrame): df = data[0]
        elif len(data) > 1 and isinstance(data[1], pd.DataFrame): df = data[1]
    elif isinstance(data, pd.DataFrame):
        df = data

    if df is None or df.empty:
        return pd.DataFrame()
        
    # --- TRIPLE FILTER LOGIC (We DO NOT filter by 1H) ---
    # 1. Weekly
    df = df[df['close|1W'] > df['EMA20|1W']]
    # 2. Daily
    df = df[df['close'] > df['EMA20']]
    # 3. 4-Hour
    df = df[df['close|240'] > df['EMA20|240']]
    
    if not df.empty:
        # Change %
        df['Change %'] = df.apply(
            lambda x: ((x['change'] / (x['close'] - x['change'])) * 100) if (x['close'] - x['change']) != 0 else 0, axis=1
        ).round(2)

        # 4H Momentum Signal (Your Sniper Light)
        df['4H Signal'] = df.apply(
            lambda x: '🟢 UP' if x['MACD.macd|240'] > x['MACD.signal|240'] else '🔴 DOWN', axis=1
        )

        # 1H Trend Status (The Dip Finder)
        # If Price < EMA on 1H, it marks it as a DIP
        df['1H Trend'] = df.apply(
            lambda x: '🟢 UP' if x['close|60'] > x['EMA20|60'] else '🔻 DIP', axis=1
        )
        
        # Rounding
        df['change'] = df['change'].round(2)
        df['close'] = df['close'].round(2)
        df['premarket_close'] = df['premarket_close'].fillna(0).round(2)
        df['premarket_change'] = df['premarket_change'].fillna(0).round(2)

    return df

# --- SESSION STATE ---
if 'scan_data' not in st.session_state:
    st.session_state.scan_data = None

# --- SCAN BUTTON ---
if st.button('🔥 Run Dip Finder Scan'):
    with st.spinner('Scanning W + D + 4H...'):
        try:
            raw_df = run_robust_scan()
            
            if watchlist_symbols and not raw_df.empty:
                raw_df = raw_df[raw_df['name'].isin(watchlist_symbols)]
            
            st.session_state.scan_data = raw_df
            
        except Exception as e:
            st.error(f"Scan Error: {e}")

# --- DISPLAY & FILTER ---
if st.session_state.scan_data is not None and not st.session_state.scan_data.empty:
    
    df_display = st.session_state.scan_data.copy()
    
    st.divider()
    st.subheader("🎯 Filter Results")
    
    col1, col2 = st.columns(2)
    with col1:
        search_ticker = st.text_input("🔍 Find Ticker (e.g. NVDA)")
    with col2:
        min_price = st.number_input("💰 Minimum Price ($)", min_value=0, value=0)
    
    if search_ticker:
        df_display = df_display[df_display['name'].str.contains(search_ticker.upper())]
    if min_price > 0:
        df_display = df_display[df_display['close'] >= min_price]
    
    if not df_display.empty:
        st.success(f"✅ Showing {len(df_display)} Matches")
        
        # Reordered columns for trading logic
        show_cols = ['name', 'close', 'Change %', '4H Signal', '1H Trend', 'premarket_close', 'premarket_change']
        st.dataframe(df_display[show_cols], use_container_width=True)
        
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Report", csv, "Dip_Finder_Report.csv", "text/csv")
    else:
        st.warning("No stocks match your specific filters.")

elif st.session_state.scan_data is not None:
    st.warning("No Triple Confluence stocks found.")
