import streamlit as st
import pandas as pd
import tvscreener as tvs

st.set_page_config(page_title="Secure Watchlist Secretary", layout="wide")

# --- 🔒 SECURITY SETTINGS ---
# Change this to whatever password you want!
MY_PASSWORD = "rich" 

# --- SIDEBAR: LOGIN & UPLOAD ---
with st.sidebar:
    st.header("🔐 Login")
    user_pass = st.text_input("Enter Password", type="password")
    
    if user_pass == MY_PASSWORD:
        st.success("Access Granted")
        st.divider()
        st.header("📂 Upload Watchlist")
        # Now accepts CSV AND Excel files
        uploaded_file = st.file_uploader("Upload .csv or .xlsx", type=["csv", "xlsx"])
    else:
        st.warning("Please enter the correct password to access the tools.")
        st.stop()  # Stops the app here if password is wrong

# --- MAIN APP (Only runs if password is correct) ---
st.title("🚀 Secure Watchlist Secretary (Triple 20 EMA)")

# --- LOAD WATCHLIST LOGIC ---
watchlist_symbols = []
if uploaded_file is not None:
    try:
        # Determine if it's CSV or Excel
        if uploaded_file.name.endswith('.csv'):
            df_watch = pd.read_csv(uploaded_file)
        else:
            df_watch = pd.read_excel(uploaded_file)
            
        # Clean column names
        df_watch.columns = df_watch.columns.str.lower().str.strip()
        
        # Look for 'symbol' or 'ticker' column
        target_col = None
        for col in df_watch.columns:
            if 'symbol' in col or 'ticker' in col:
                target_col = col
                break
        
        if target_col:
            # Extract symbols
            watchlist_symbols = df_watch[target_col].astype(str).str.upper().str.strip().tolist()
            # Clean up "EXCHANGE:SYMBOL" format
            watchlist_symbols = [s.split(':')[-1] for s in watchlist_symbols]
            
            st.success(f"✅ Loaded {len(watchlist_symbols)} symbols from **{uploaded_file.name}**!")
            with st.expander("Peek at your list"):
                st.write(watchlist_symbols[:10])
        else:
            st.error("❌ Could not find a 'Symbol' or 'Ticker' column in your file.")
    except Exception as e:
        st.error(f"Error reading file: {e}")

st.markdown("---")
st.write("Ready to scan the US Market for **Triple Confluence (Price > 20 EMA)** on Weekly, Daily, and 4H charts.")

# --- SCANNER FUNCTIONS ---
def get_scan_results(interval_mode):
    """Runs a broad market scan for Price > EMA 20"""
    ss = tvs.StockScreener()
    ss.set_markets(tvs.Market.AMERICA)
    ss.set_interval(interval_mode)
    
    # Filter: Price > EMA 20 & Volume > 500k
    ss.add_filter(tvs.Filter(tvs.StockField.CLOSE, tvs.FilterOperator.ABOVE, tvs.StockField.EMA20))
    ss.add_filter(tvs.Filter(tvs.StockField.VOLUME, tvs.FilterOperator.ABOVE, 500000))
    
    return ss.get(limit=3000)

if st.button('🔥 Run Triple-Confluence Scan'):
    status = st.status("Starting Analysis...", expanded=True)
    
    try:
        # --- PHASE 1: THE TRIPLE SCAN ---
        status.write("⏳ Scanning **Weekly** Timeframe...")
        df_weekly = get_scan_results(tvs.TimeInterval.ONE_WEEK)
        
        status.write("⏳ Scanning **Daily** Timeframe...")
        df_daily = get_scan_results(tvs.TimeInterval.DAILY)
        
        status.write("⏳ Scanning **4-Hour** Timeframe...")
        try:
            df_4h = get_scan_results(tvs.TimeInterval.FOUR_HOURS)
        except:
            df_4h = get_scan_results("240")
        
        # --- PHASE 2: FIND INTERSECTION ---
        if not df_weekly.empty and not df_daily.empty and not df_4h.empty:
            weekly_set = set(df_weekly['symbol'])
            daily_set = set(df_daily['symbol'])
            four_h_set = set(df_4h['symbol'])
            
            bullish_market_symbols = weekly_set.intersection(daily_set).intersection(four_h_set)
            
            # --- PHASE 3: FILTER BY WATCHLIST ---
            final_matches = []
            
            if watchlist_symbols:
                status.write(f"🕵️ Filtering against your {len(watchlist_symbols)} uploaded symbols...")
                final_matches = list(bullish_market_symbols.intersection(set(watchlist_symbols)))
            else:
                status.write("⚠️ No file uploaded. Showing ALL market matches.")
                final_matches = list(bullish_market_symbols)
            
            status.update(label="Scan Complete!", state="complete", expanded=False)
            
            if final_matches:
                final_df = df_daily[df_daily['symbol'].isin(final_matches)].copy()
                
                st.success(f"🎉 Found {len(final_df)} matches!")
                st.dataframe(final_df[['symbol', 'name', 'close', 'change', 'volume']], use_container_width=True)
                
                csv = final_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Report", csv, "Triple_Confluence.csv", "text/csv")
            else:
                st.warning("No stocks met the criteria.")
        else:
            st.error("One of the scans returned no data.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
