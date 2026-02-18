import streamlit as st
import pandas as pd
import tvscreener as tvs

st.set_page_config(page_title="Triple Confluence Scanner", layout="wide")
st.title("🚀 Triple Confluence Secretary (26 EMA)")
st.markdown("Scanning for stocks above the **26 EMA** on **Weekly**, **Daily**, and **4-Hour** charts.")

def run_scan():
    # 1. Initialize the Screener
    ss = tvs.StockScreener()
    ss.set_markets(tvs.Market.AMERICA)
    
    # 2. Define the 26-EMA for different timeframes
    # Note: 240 = 4 Hours, 1W = 1 Week
    ema26_daily = tvs.StockField.EXPONENTIAL_MOVING_AVERAGE_26
    ema26_4h = tvs.StockField.EXPONENTIAL_MOVING_AVERAGE_26.with_interval("240")
    ema26_weekly = tvs.StockField.EXPONENTIAL_MOVING_AVERAGE_26.with_interval("1W")
    
    # 3. Add the filters (Close Price > EMA)
    # Daily
    ss.add_filter(tvs.Filter(tvs.StockField.CLOSE, tvs.FilterOperator.ABOVE, ema26_daily))
    # 4-Hour
    ss.add_filter(tvs.Filter(tvs.StockField.CLOSE, tvs.FilterOperator.ABOVE, ema26_4h))
    # Weekly
    ss.add_filter(tvs.Filter(tvs.StockField.CLOSE, tvs.FilterOperator.ABOVE, ema26_weekly))
    
    # 4. Volume Filter (> 500k)
    ss.add_filter(tvs.Filter(tvs.StockField.VOLUME, tvs.FilterOperator.ABOVE, 500000))

    # 5. Execute Scan (Get Top 100)
    df = ss.get(limit=100)
    return df

if st.button('🔥 Run Triple-Confluence Scan'):
    with st.spinner('Scanning US Market for Triple 26-EMA setups...'):
        try:
            df = run_scan()
            
            if not df.empty:
                # Clean up the columns for display
                display_df = df[['symbol', 'name', 'close', 'change', 'volume']].copy()
                
                st.success(f"✅ Found {len(display_df)} stocks meeting ALL criteria!")
                st.dataframe(display_df, use_container_width=True)
                
                # CSV Download
                csv = display_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Results", csv, "Triple_26EMA_Report.csv", "text/csv")
            else:
                st.warning("No stocks found. The market might be choppy!")
                
        except Exception as e:
            st.error(f"Scan failed: {e}")
