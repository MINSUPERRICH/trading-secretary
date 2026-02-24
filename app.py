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

st.title("🚀 Watchlist Secretary (Double Strict Edition)")
st.markdown("""
**New Strict Logic Enabled:**
* 🚫 **Signals will flip to RED/DIP immediately** if the current price drops below the previous candle's close, even if indicators haven't crossed yet.
""")

# --- SCANNER LOGIC ---
def run_robust_scan():
    q = Query().set_markets('america')
    q.select(
        'name', 'close', 'volume', 'relative_volume_10d_calc', 'change',
        'EMA20',               
        'MACD.macd|240', 'MACD.signal|240',    
        'MACD.macd[1]|240', 'MACD.signal[1]|240', 
        'close[1]|240',     # Previous 4H Close
        'close|1W', 'EMA20|1W',  
        'close|240', 'EMA20|240',
        'close[1]|60',      # Previous 1H Close
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

        # --- DOUBLE STRICT LOGIC ---
        def get_strict_4h(row):
            # Rule 1: MACD Histogram Slope
            current_hist = row['MACD.macd|240'] - row['MACD.signal|240']
            prev_hist = row['MACD.macd[1]|240'] - row['MACD.signal[1]|240']
            slope_up = current_hist > prev_hist
            # Rule 2: Price >= Prev 4H Close
            price_holding = row['close|240'] >= row['close[1]|240']
            return '🟢 UP' if (slope_up and price_holding) else '🔴 DOWN'

        def get_strict_1h(row):
            # Rule 1: Above EMA20 (1H)
            above_ema = row['close|60'] > row['EMA20|60']
            # Rule 2: Price >= Prev 1H Close (The Filter you requested)
            price_holding = row['close|60'] >= row['close[1]|60']
            return '🟢 UP' if (above_ema and price_holding) else '🔻 DIP'

        df['4H Signal'] = df.apply(get_strict_4h, axis=1)
        df['1H Trend'] = df.apply(get_strict_1h, axis=1)
        
        # Formatting
        df['Change (%)'] = df.apply(lambda x: ((x['change'] / (x['Close ($)'] - x['change'])) * 100) if (x['Close ($)'] - x['change']) != 0 else 0, axis=1).round(2)
        df['Close ($)'] = df['Close ($)'].round(2)
        df['RVOL (Ratio)'] = df['RVOL (Ratio)'].round(2)

    return df

# --- UI ---
if 'scan_data' not in st.session_state:
    st.session_state.scan_data = None

if st.button('🔥 Run Double Strict Scan'):
    with st.spinner('Filtering for Real-Time Accuracy...'):
        raw_df = run_robust_scan()
        st.session_state.scan_state = raw_df # Save to state

if st.session_state.get('scan_state') is not None:
    df_display = st.session_state.scan_state.copy()
    st.divider()
    
    main_cols = ['Symbol', 'Close ($)', 'Change (%)', 'RVOL (Ratio)', '4H Signal', '1H Trend']
    st.dataframe(df_display[main_cols], use_container_width=True)
    
    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Final Strict Report", csv, "Sniper_DoubleStrict.csv", "text/csv")
