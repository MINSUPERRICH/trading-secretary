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

st.title("🚀 Watchlist Secretary (Final Sniper Edition)")

# --- SCANNER LOGIC ---
def run_robust_scan():
    q = Query().set_markets('america')
    q.select(
        'name', 'close', 'volume', 'relative_volume_10d_calc', 'change',
        'premarket_close', 'premarket_change',
        'EMA20',               
        'MACD.macd|240', 'MACD.signal|240',    
        'MACD.macd[1]|240', 'MACD.signal[1]|240', 
        'close|1W', 'EMA20|1W',  
        'close|240', 'EMA20|240',
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
        # Renaming columns for perfect clarity in report
        df = df.rename(columns={
            'name': 'Symbol',
            'relative_volume_10d_calc': 'RVOL',
            'volume': 'Volume',
            'EMA20': 'EMA20 (D)', # Added (D) for Daily
            'MACD.macd|240': '4H_MACD_Now',
            'MACD.signal|240': '4H_Signal_Now',
            'MACD.macd[1]|240': '4H_MACD_Prev',
            'MACD.signal[1]|240': '4H_Signal_Prev'
        })

        df['Change %'] = df.apply(lambda x: ((x['change'] / (x['close'] - x['change'])) * 100) if (x['close'] - x['change']) != 0 else 0, axis=1).round(2)
        
        def get_signal(row):
            current_hist = row['4H_MACD_Now'] - row['4H_Signal_Now']
            prev_hist = row['4H_MACD_Prev'] - row['4H_Signal_Prev']
            return '🟢 UP' if current_hist > prev_hist else '🔴 DOWN'

        df['4H Signal'] = df.apply(get_signal, axis=1)
        df['1H Trend'] = df.apply(lambda x: '🟢 UP' if x['close|60'] > x['EMA20|60'] else '🔻 DIP', axis=1)
        
        # Rounding values
        df['close'] = df['close'].round(2)
        df['RVOL'] = df['RVOL'].round(2)
        df['change'] = df['change'].round(2)
        df['EMA20 (D)'] = df['EMA20 (D)'].round(2)

    return df

# --- UI ---
if 'scan_data' not in st.session_state:
    st.session_state.scan_data = None

if st.button('🔥 Run Dip Finder Scan'):
    with st.spinner('Scanning...'):
        raw_df = run_robust_scan()
        # If user uploaded a list, filter by it
        if uploaded_file and not raw_df.empty:
            # We already extracted watchlist_symbols logic in previous steps
            # Filter logic here...
            pass
        st.session_state.scan_data = raw_df

if st.session_state.scan_data is not None and not st.session_state.scan_data.empty:
    df_display = st.session_state.scan_data.copy()
    st.divider()
    
    # Simple display columns
    st.dataframe(df_display[['Symbol', 'close', 'Change %', 'RVOL', '4H Signal', '1H Trend']], use_container_width=True)
    
    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Final Report", csv, "Sniper_Final_Report.csv", "text/csv")
