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

st.title("🚀 Watchlist Secretary (TSI / MACD Logic)")
st.markdown("""
**Triple Confluence + Momentum:**
1. ✅ **Trend:** Price > 20 EMA on **Weekly**, **Daily**, and **4H**.
2. 🚀 **Momentum:** Using **MACD (12, 26)** as a proxy for **TSI**.
   *(Logic: If MACD Line > Signal Line, Momentum is 🟢 GREEN/UP)*
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
        else:
            st.sidebar.error("Could not find 'symbol' or 'ticker' column.")
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")

# --- THE ROBUST SCANNER ---
def run_robust_scan():
    q = Query().set_markets('america')
    
    # WE REQUEST TRIPLE EMA + MACD (TSI Proxy)
    q.select(
        'name', 'close', 'volume', 'change',
        'EMA20', 
        'MACD.macd', 'MACD.signal', # <--- REQUESTING MACD DATA
        'close|1W', 'EMA20|1W',
        'close|240', 'EMA20|240'
    )
    
    q.where(col('volume') > 500000)
    q.limit(4000)
    
    # --- 🛡️ SAFETY CHECK ---
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
    # 1. Daily Trend
    df = df[df['close'] > df['EMA20']]
    
    # 2. Weekly Trend
    df = df[df['close|1W'] > df['EMA20|1W']]
    
    # 3. 4-Hour Trend
    df = df[df['close|240'] > df['EMA20|240']]
    
    return df

if st.button('🔥 Run Triple-Confluence Scan'):
    with st.spinner('Scanning US Market...'):
        try:
            df_result = run_robust_scan()
            
            # Apply Watchlist Filter
            if watchlist_symbols and not df_result.empty:
                df_result = df_result[df_result['name'].isin(watchlist_symbols)]
                msg = f"🎉 Found {len(df_result)} matches from your list!"
            else:
                msg = f"🎉 Found {len(df_result)} market-wide matches!"
            
            if not df_result.empty:
                st.success(msg)
                
                # Round numbers
                df_result['MACD.macd'] = df_result['MACD.macd'].round(2)
                df_result['MACD.signal'] = df_result['MACD.signal'].round(2)
                
                # CALCULATE MOMENTUM SIGNAL (Green/Red Bar Logic)
                df_result['TSI_Proxy'] = df_result.apply(
                    lambda x: '🟢 UP' if x['MACD.macd'] > x['MACD.signal'] else '🔴 DOWN', axis=1
                )

                show_cols = ['name', 'close', 'change', 'EMA20', 'TSI_Proxy', 'MACD.macd', 'MACD.signal']
                st.dataframe(df_result[show_cols], use_container_width=True)
                
                csv = df_result.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Report", csv, "Triple_Confluence_TSI_Proxy.csv", "text/csv")
            else:
                st.warning("No stocks met the Triple EMA criteria right now.")
                
        except Exception as e:
            st.error(f"Scan Error: {e}")
