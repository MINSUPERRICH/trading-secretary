import streamlit as st
import pandas as pd
from tradingview_screener import Query, col

st.set_page_config(page_title="Secure Watchlist Secretary", layout="wide")

# --- 🔒 SECURITY ---
MY_PASSWORD = "rich" 

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

st.title("🚀 Watchlist Secretary (Pre-Market Edition)")
st.markdown("""
**Strategy:**
1. ✅ **Triple Trend:** Price > 20 EMA on **Weekly**, **Daily**, and **4H**.
2. 🚀 **Momentum:** TSI Proxy (MACD) is **🟢 UP**.
3. 🌅 **Pre-Market:** See live 8:00 AM prices in the new columns.
""")

# --- LOAD WATCHLIST ---
watchlist_symbols = []
if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'): 
            df_watch = pd.read_csv(uploaded_file)
        else: 
            df_watch = pd.read_excel(uploaded_file)
        
        df_watch.columns = df_watch.columns.str.lower().str.strip()
        target_col = next((c for c in df_watch.columns if 'symbol' in c or 'ticker' in c), None)
        
        if target_col:
            watchlist_symbols = df_watch[target_col].astype(str).str.upper().str.strip().tolist()
            watchlist_symbols = [s.split(':')[-1] for s in watchlist_symbols]
            st.sidebar.success(f"✅ Loaded {len(watchlist_symbols)} symbols!")
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")

# --- THE ROBUST SCANNER ---
def run_robust_scan():
    q = Query().set_markets('america')
    
    # REQUESTING PRE-MARKET DATA ('premarket_close', 'premarket_change')
    q.select(
        'name', 'close', 'volume', 'change',
        'premarket_close', 'premarket_change',  # <--- NEW FIELDS
        'EMA20', 
        'MACD.macd', 'MACD.signal',
        'close|1W', 'EMA20|1W',
        'close|240', 'EMA20|240'
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
        
    # --- FILTER LOGIC ---
    df = df[df['close'] > df['EMA20']]
    df = df[df['close|1W'] > df['EMA20|1W']]
    df = df[df['close|240'] > df['EMA20|240']]
    
    # Clean up and add columns immediately
    if not df.empty:
        # Calculate Regular % Change
        df['Change %'] = df.apply(
            lambda x: ((x['change'] / (x['close'] - x['change'])) * 100) if (x['close'] - x['change']) != 0 else 0, axis=1
        ).round(2)

        # TSI Proxy
        df['TSI_Proxy'] = df.apply(
            lambda x: '🟢 UP' if x['MACD.macd'] > x['MACD.signal'] else '🔴 DOWN', axis=1
        )
        
        # Rounding
        df['change'] = df['change'].round(2)
        df['close'] = df['close'].round(2)
        
        # Handle Pre-Market (Fill NaN with 0 if no pre-market trade yet)
        df['premarket_close'] = df['premarket_close'].fillna(0).round(2)
        df['premarket_change'] = df['premarket_change'].fillna(0).round(2)

    return df

# --- SESSION STATE ---
if 'scan_data' not in st.session_state:
    st.session_state.scan_data = None

# --- SCAN BUTTON ---
if st.button('🔥 Run Triple-Confluence Scan'):
    with st.spinner('Scanning US Market...'):
        try:
            raw_df = run_robust_scan()
            
            if watchlist_symbols and not raw_df.empty:
                raw_df = raw_df[raw_df['name'].isin(watchlist_symbols)]
            
            st.session_state.scan_data = raw_df
            
        except Exception as e:
            st.error(f"Scan Error: {e}")

# --- DISPLAY & FILTER SECTION ---
if st.session_state.scan_data is not None and not st.session_state.scan_data.empty:
    
    df_display = st.session_state.scan_data.copy()
    
    st.divider()
    st.subheader("🎯 Filter Results")
    
    col1, col2 = st.columns(2)
    with col1:
        search_ticker = st.text_input("🔍 Find Ticker (e.g. NVDA, TSLA)")
    with col2:
        min_price = st.number_input("💰 Minimum Price ($)", min_value=0, value=0)
    
    if search_ticker:
        df_display = df_display[df_display['name'].str.contains(search_ticker.upper())]
    if min_price > 0:
        df_display = df_display[df_display['close'] >= min_price]
    
    if not df_display.empty:
        st.success(f"✅ Showing {len(df_display)} matches")
        
        # Reorder columns to show Pre-Market info
        show_cols = ['name', 'close', 'Change %', 'premarket_close', 'premarket_change', 'EMA20', 'TSI_Proxy']
        
        st.dataframe(df_display[show_cols], use_container_width=True)
        
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Report", csv, "PreMarket_Report.csv", "text/csv")
    else:
        st.warning("No stocks match filters.")

elif st.session_state.scan_data is not None:
    st.warning("No Triple Confluence stocks found.")
