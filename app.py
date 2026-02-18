import streamlit as st
import pandas as pd
from tradingview_screener import Query, col

st.set_page_config(page_title="Triple Confluence Scanner", layout="wide")
st.title("🚀 Triple Confluence Secretary (EMA 20)")
st.markdown("""
**Logic:**
1. Scan **Weekly** chart: Close > EMA 20
2. Scan **Daily** chart: Close > EMA 20
3. Scan **4-Hour** chart: Close > EMA 20
4. Show only stocks that pass **ALL 3** checks.
""")

def get_scan(interval_mode):
    """Runs a scan for a specific timeframe."""
    q = Query().set_markets('america')
    
    # Set the timeframe (1D, 1W, or 240 mins for 4H)
    # Note: The library uses '1d', '1w', and '240' (minutes)
    if interval_mode == '4h':
        q.get_scanner_data(time_interval='240') 
    elif interval_mode == '1w':
        q.get_scanner_data(time_interval='1W')
    else:
        q.get_scanner_data(time_interval='1d')

    # Select columns (We use EMA20 as the standard proxy for trend)
    q.select('name', 'close', 'volume', 'EMA20')
    
    # Filter: Price must be above EMA20
    q.where(
        col('close') > col('EMA20'),
        col('volume') > 500000  # Minimum volume filter
    )
    
    # We ask for a lot of results so we can find intersections later
    q.limit(1000)
    
    df, count = q.get_scanner_data()
    return df if df is not None else pd.DataFrame()

if st.button('🔥 Run Triple-Confluence Scan'):
    status = st.status("Running multi-timeframe analysis...", expanded=True)
    
    # 1. Run the 3 separate scans
    status.write("⏳ Scanning Weekly Timeframe...")
    df_weekly = get_scan('1w')
    
    status.write("⏳ Scanning Daily Timeframe...")
    df_daily = get_scan('1d')
    
    status.write("⏳ Scanning 4-Hour Timeframe...")
    df_4h = get_scan('4h')
    
    # 2. Find the Intersections (Stocks in ALL 3 lists)
    if not df_weekly.empty and not df_daily.empty and not df_4h.empty:
        # Get list of tickers from each
        tickers_weekly = set(df_weekly['name'])
        tickers_daily = set(df_daily['name'])
        tickers_4h = set(df_4h['name'])
        
        # The Magic: Find the overlapping symbols
        common_tickers = tickers_weekly.intersection(tickers_daily).intersection(tickers_4h)
        
        status.write(f"✅ Found {len(common_tickers)} stocks with Triple Confluence!")
        status.update(label="Scan Complete!", state="complete", expanded=False)
        
        if common_tickers:
            # Filter the Daily dataframe to show only the winning stocks
            final_df = df_daily[df_daily['name'].isin(common_tickers)].copy()
            
            # Show results
            st.success(f"🎉 {len(final_df)} Stocks are bullish on Weekly, Daily, AND 4-Hour charts!")
            st.dataframe(final_df[['name', 'close', 'volume', 'EMA20']], use_container_width=True)
            
            # CSV Download
            csv = final_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Triple-Confluence CSV", csv, "Triple_Confluence_Report.csv", "text/csv")
        else:
            st.warning("No stocks met all 3 conditions simultaneously.")
    else:
        status.update(label="Error", state="error")
        st.error("One of the scans returned no data. Try again during market hours.")
