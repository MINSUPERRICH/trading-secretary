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

st.title("🚀 Watchlist Secretary (Bug Fix Edition)")

# --- SCANNER LOGIC ---
def run_robust_scan():
    q = Query().set_markets('america')
    q.select(
        'name', 'close', 'volume', 'relative_volume_10d_calc', 'change',
        'EMA20',               
        'EMA20|1W',            
        'EMA20|240',           
        'MACD.macd|240', 'MACD.signal|240',    
        'MACD.macd[1]|240', 'MACD.signal[1]|240', 
        'close[1]|240',     
        'close|1W',   
        'close|240', 
        'close[1]|60',      
        'close|60', 'EMA20|60'   
    )
    q.where(col('volume') > 500000)
    q.limit(4000)
    
    data = q.get_scanner_data()
    df = data[1] if isinstance(data, tuple) else data
    
    if df is None or df.empty:
        st.error("No data received from TradingView. Please try again.")
        return pd.DataFrame()
        
    # --- 🛡️ NEW SAFETY CHECK ---
    required_cols = ['close|1W', 'EMA20|1W', 'close', 'EMA20', 'close|240', 'EMA20|240', 'close|60', 'EMA20|60']
    missing = [c for c in required_cols if c not in df.columns]
    
    if missing:
        st.error(f"Missing Data Columns from TradingView: {missing}")
        return pd.DataFrame()

    # --- ENFORCE TRIPLE TREND ---
    df = df[df['close|1W'] > df['EMA20|1W']]
    df = df[df['close'] > df['EMA20']]
    df = df[df['close|240'] > df['EMA20|240']]
    
    if not df.empty:
        df['Dist From EMA (%)'] = (((df['close'] - df['EMA20']) / df['EMA20']) * 100).round(2)

        df = df.rename(columns={
            'name': 'Symbol',
            'relative_volume_10d_calc': 'RVOL (Ratio)',
            'close': 'Close ($)',
            'EMA20': 'EMA20 Daily ($)',
            'EMA20|1W': 'EMA20 Weekly ($)'
        })

        # Double Strict Logic
        def get_strict_4h(row):
            current_hist = row['MACD.macd|240'] - row['MACD.signal|240']
            prev_hist = row['MACD.macd[1]|240'] - row['MACD.signal[1]|240']
            slope_up = current_hist > prev_hist
            price_holding = row['close|240'] >= row['close[1]|240']
            return '🟢 UP' if (slope_up and price_holding) else '🔴 DOWN'

        def get_strict_1h(row):
            above_ema = row['close|60'] > row['EMA20|60']
            price_holding = row['close|60'] >= row['close[1]|60']
            return '🟢 UP' if (above_ema and price_holding) else '🔻 DIP'

        df['4H Signal'] = df.apply(get_strict_4h, axis=1)
        df['1H Trend'] = df.apply(get_strict_1h, axis=1)
        df['Change (%)'] = df.apply(lambda x: ((x['change'] / (x['Close ($)'] - x['change'])) * 100) if (x['Close ($)'] - x['change']) != 0 else 0, axis=1).round(2)
        df['Close ($)'] = df['Close ($)'].round(2)

    return df

# --- UI ---
if 'scan_data' not in st.session_state:
    st.session_state.scan_data = None

if st.button('🔥 Run Smart Sniper Scan'):
    with st.spinner('Scanning for Bounce Zone Candidates...'):
        st.session_state.scan_data = run_robust_scan()

if st.session_state.scan_data is not None and not st.session_state.scan_data.empty:
    df_display = st.session_state.scan_data.copy()
    st.divider()

    # (Filters and styling remain the same)
    def highlight_bounce_zone(val):
        return 'background-color: #FFFF99; color: black;' if val <= 1.5 else ''

    main_cols = ['Symbol', 'Close ($)', 'Dist From EMA (%)', 'Change (%)', 'RVOL (Ratio)', '4H Signal', '1H Trend']
    styled_df = df_display[main_cols].style.applymap(highlight_bounce_zone, subset=['Dist From EMA (%)'])

    st.dataframe(styled_df, use_container_width=True)
    
    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Final Report", csv, "Sniper_Fixed_Report.csv", "text/csv")
