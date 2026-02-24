import streamlit as st
import pandas as pd
from tradingview_screener import Query, col

st.set_page_config(page_title="Secure Watchlist Secretary", layout="wide")

# --- 🔒 SECURITY ---
MY_PASSWORD = st.secrets.get("APP_PASSWORD", "rich")

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

st.title("🚀 Watchlist Secretary (Strict Sniper Edition)")

# --- SCANNER LOGIC ---
def run_robust_scan():
    q = Query().set_markets('america')
    q.select(
        'name', 'close', 'volume', 'relative_volume_10d_calc', 'change',
        'EMA20',               
        'MACD.macd|240', 'MACD.signal|240',    
        'MACD.macd[1]|240', 'MACD.signal[1]|240', 
        'close[1]|240',     # Added: Previous 4H Close for Strict Filter
        'close|1W', 'EMA20|1W',  
        'close|240', 'EMA20|240',
        'close[1]|60',      # Added: Previous 1H Close
        'close|60', 'EMA20|60'   
    )
    q.where(col('volume') > 500000)
    q.limit(4000)
    
    data = q.get_scanner_data()
    df = data[1] if isinstance(data, tuple) else data
    if df is None or df.empty: return pd.DataFrame()
        
    df = df[df['close|1W'] > df['EMA20|1W']]
    df = df[df['close'] > df['EMA20']]
    df = df[df['close|240'] > df['EMA20|240']]
    
    if not df.empty:
        df = df.rename(columns={
            'name': 'Symbol',
            'relative_volume_10d_calc': 'RVOL (Ratio)',
            'close': 'Close ($)',
            'EMA20': 'EMA20 (D) ($)'
        })

        # --- NEW STRICT LOGIC ---
        def get_strict_4h(row):
            # Rule 1: MACD Histogram must be growing (Slope)
            current_hist = row['MACD.macd|240'] - row['MACD.signal|240']
            prev_hist = row['MACD.macd[1]|240'] - row['MACD.signal[1]|240']
            slope_up = current_hist > prev_hist
            
            # Rule 2: Current Price must be >= Previous 4H Close (The Real-Time Filter)
            price_holding = row['close|240'] >= row['close[1]|240']
            
            return '🟢 UP' if (slope_up and price_holding) else '🔴 DOWN'

        def get_strict_1h(row):
            # Rule 1: Must be above EMA20
            above_ema = row['close|60'] > row['EMA20|60']
            # Rule 2: Price must be >= Previous 1H Close
            price_holding = row['close|60'] >= row['close[1]|60']
            
            return '🟢 UP' if (above_ema and price_holding) else '🔻 DIP'

        df['4H Signal'] = df.apply(get_strict_4h, axis=1)
        df['1H Trend'] = df.apply(get_strict_1h, axis=1)
        
        # Calculations & Rounding
        df['Change (%)'] = df.apply(lambda x: ((x['change'] / (x['Close ($)'] - x['change'])) * 100) if (x['Close ($)'] - x['change']) != 0 else 0, axis=1).round(2)
        df['Close ($)'] = df['Close ($)'].round(2)
        df['RVOL (Ratio)'] = df['RVOL (Ratio)'].round(2)

    return df

# --- UI ---
if 'scan_data' not in st.session_state:
    st.session_state.scan_data = None

if st.button('🔥 Run Strict Scan'):
    with st.spinner('Applying Strict Real-Time Filters...'):
        raw_df = run_robust_scan()
        st.session_state.scan_data = raw_df

if st.session_state.scan_data is not None and not st.session_state.scan_data.empty:
    df_display = st.session_state.scan_data.copy()
    st.divider()
    
    main_cols = ['Symbol', 'Close ($)', 'Change (%)', 'RVOL (Ratio)', '4H Signal', '1H Trend']
    st.dataframe(df_display[main_cols], use_container_width=True)
    
    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Strict Report", csv, "Sniper_Strict_Report.csv", "text/csv")
