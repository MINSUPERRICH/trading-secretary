import streamlit as st
import pandas as pd
from tradingview_screener import Query, col

st.set_page_config(page_title="26-EMA Triple Confluence", layout="wide")
st.title("🚀 26-EMA Triple Confluence Secretary")
st.write("Filtering for stocks where **Price > 26 EMA** on Weekly, Daily, and 4H timeframes.")

def run_triple_ema_scan():
    q = Query().set_markets('america')
    
    # 1. Selecting Price and 26-EMA for 3 timeframes
    # Note: 'EMA26' is the standard field; we specify intervals in the query logic
    q.select(
        'name', 'description', 'close', 'change', 'volume',
        'EMA26',               # Daily 26 EMA
        'EMA26|240',           # 4-Hour (240 min) 26 EMA
        'EMA26|1W'             # Weekly 26 EMA
    )
    
    # 2. Apply Triple Confluence Conditions
    q.where(
        col('close') > col('EMA26'),       # Condition 1: Daily Price > 26 EMA
        col('close') > col('EMA26|240'),   # Condition 2: 4H Price > 26 EMA
        col('close') > col('EMA26|1W'),    # Condition 3: Weekly Price > 26 EMA
        col('volume') > 500000             # Basic filter: At least 500k volume
    )
    
    # 3. Order by performance
    q.order_by('change', ascending=False)
    
    df, count = q.get_scanner_data()
    return df

if st.button('🔍 Run Triple Timeframe Scan'):
    with st.spinner('Accessing TradingView Cloud Data...'):
        results = run_triple_ema_scan()
        
        if not results.empty:
            st.success(f"Found {len(results)} stocks matching the Triple 26-EMA criteria!")
            
            # Cleaning up column names for the user
            results.columns = ['Ticker', 'Name', 'Price', 'Change %', 'Vol', 'EMA 26 (1D)', 'EMA 26 (4H)', 'EMA 26 (1W)']
            st.dataframe(results, use_container_width=True)
            
            # CSV Download
            csv = results.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Results CSV", csv, "Triple_26EMA_Report.csv", "text/csv")
        else:
            st.warning("No stocks currently meet the Triple 26-EMA criteria.")

st.info("💡 This scan uses live market data. The Weekly EMA updates based on the current active week.")
