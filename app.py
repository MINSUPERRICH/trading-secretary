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

st.title("🚀 Watchlist Secretary (Dip Finder + Sorting)")
st.markdown("""
**Strategy:**
1. ✅ **Triple Trend:** Price > 20 EMA on **Weekly**, **Daily**, and **4H**.
2. 🚀 **4H Signal:** Light is based on **4-Hour** MACD (Sniper Entry).
3. 📉 **1H Trend:** Shows "🔻 DIP" if 1H Price < EMA (Buying Chance).
""")

# --- 1. INITIALIZE WATCHLIST ---
watchlist_symbols = [] 

# --- 2. LOAD WATCHLIST ---
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

# --- 3. THE ROBUST SCANNER ---
def run_robust_scan():
    q = Query().set_markets('america')
    
    q.select(
        'name', 'close', 'volume', 'change',
        'premarket_close', 'premarket_change',
        'EMA20',               
        'MACD.macd|240', 'MACD.signal|240', 
        'close|1W', 'EMA20|1W',
        'close|240', 'EMA20|240',
        'close|60', 'EMA20|60'
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
    df = df[df['close|1W'] > df['EMA20|1W']]
    df = df[df['close'] > df['EMA20']]
    df = df[df['close|240'] > df['EMA20|240']]
    
    if not df.empty:
        df['Change %'] = df.apply(
            lambda x: ((x['change'] / (x['close'] - x['change'])) * 100) if (x['close'] - x['change']) != 0 else 0, axis=1
        ).round(2)

        df['4H Signal'] = df.apply(
            lambda x: '🟢 UP' if x['MACD.macd|240'] > x['MACD.signal|240'] else '🔴 DOWN', axis=1
        )

        df['1H Trend'] = df.apply(
            lambda x: '🟢 UP' if x['close|60'] > x['EMA20|60'] else '🔻 DIP', axis=1
        )
        
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
    st.subheader("🎯 Filter & Sort")
    
    # --- FILTERS + SORTING ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_ticker = st.text_input("🔍 Find Ticker (e.g. NVDA)")
    with col2:
        min_price = st.number_input("💰 Minimum Price ($)", min_value=0, value=0)
    with col3:
        # NEW: Sorting Dropdown
        sort_option = st.selectbox(
            "🔃 Sort Results By:", 
            ["Default", "Change % (High to Low)", "Pre-Market % (High to Low)", "Price (High to Low)"]
        )
    
    # 1. Apply Filters
    if search_ticker:
        df_display = df_display[df_display['name'].str.contains(search_ticker.upper())]
    if min_price > 0:
        df_display = df_display[df_display['close'] >= min_price]
        
    # 2. Apply Sorting (This fixes the Download Order!)
    if sort_option == "Change % (High to Low)":
        df_display = df_display.sort_values(by="Change %", ascending=False)
    elif sort_option == "Pre-Market % (High to Low)":
        df_display = df_display.sort_values(by="premarket_change", ascending=False)
    elif sort_option == "Price (High to Low)":
        df_display = df_display.sort_values(by="close", ascending=False)
    
    if not df_display.empty:
        st.success(f"✅ Showing {len(df_display)} Matches")
        
        show_cols = ['name', 'close', 'Change %', '4H Signal', '1H Trend', 'premarket_close', 'premarket_change']
        st.dataframe(df_display[show_cols], use_container_width=True)
        
        # Download button now uses the SORTED df_display
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Report (Sorted)", csv, "Sorted_Report.csv", "text/csv")
    else:
        st.warning("No stocks match your specific filters.")

elif st.session_state.scan_data is not None:
    st.warning("No Triple Confluence stocks found.")
