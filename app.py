import streamlit as st
import pandas as pd
from tradingview_screener import Query, col

st.set_page_config(page_title="Secure Watchlist Secretary", layout="wide")

# --- 🔒 SECURITY ---
MY_PASSWORD = "rich" 

with st.sidebar:
    st.header("🔐 Login")
    user_pass = st.text_input("Enter Password", type="password")
    if user_pass == MY_PASSWORD:
        st.success("Access Granted")
        st.divider()
        st.header("📂 Upload Watchlist")
        uploaded_file = st.file_uploader("Upload .csv or .xlsx", type=["csv", "xlsx"])
    else:
        st.warning("Enter password to access.")
        st.stop()

st.title("🚀 Watchlist Secretary (Triple 20 EMA)")

# --- LOAD WATCHLIST ---
watchlist_symbols = []
if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'): df_watch = pd.read_csv(uploaded_file)
        else: df_watch = pd.read_excel(uploaded_file)
        
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
    
    # We request RAW data for all timeframes at once using the pipe '|' syntax
    # 240 = 4 Hours, 1W = 1 Week
    q.select(
        'name', 'close', 'volume', 
        'EMA20',           # Daily EMA
        'close|1W', 'EMA20|1W',  # Weekly Data
        'close|240', 'EMA20|240' # 4-Hour Data
    )
    
    # Get top 3000 active stocks (by volume) to cover the market
    q.where(col('volume') > 500000)
    q.limit(3000)
    
    # Fetch Data
    df, _ = q.get_scanner_data()
    
    if df is None or df.empty:
        return pd.DataFrame()
        
    # --- FILTERING IN PYTHON (Crash-Proof) ---
    # 1. Daily Condition
    df = df[df['close'] > df['EMA20']]
    
    # 2. Weekly Condition
    df = df[df['close|1W'] > df['EMA20|1W']]
    
    # 3. 4-Hour Condition
    df = df[df['close|240'] > df['EMA20|240']]
    
    return df

if st.button('🔥 Run Triple-Confluence Scan'):
    with st.spinner('Scanning US Market...'):
        try:
            df_result = run_robust_scan()
            
            # Filter by Watchlist if uploaded
            if watchlist_symbols and not df_result.empty:
                df_result = df_result[df_result['name'].isin(watchlist_symbols)]
                msg = f"🎉 Found {len(df_result)} matches from your list!"
            else:
                msg = f"🎉 Found {len(df_result)} market-wide matches!"
            
            if not df_result.empty:
                st.success(msg)
                # Clean up columns for display
                show_cols = ['name', 'close', 'volume', 'EMA20']
                st.dataframe(df_result[show_cols], use_container_width=True)
                
                csv = df_result.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download CSV", csv, "Triple_Confluence.csv", "text/csv")
            else:
                st.warning("No stocks met the Triple EMA criteria.")
                
        except Exception as e:
            st.error(f"Error: {e}")
