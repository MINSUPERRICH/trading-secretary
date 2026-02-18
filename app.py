import streamlit as st
import pandas as pd
import tvscreener as tvs

st.set_page_config(page_title="Triple Confluence Scanner", layout="wide")
st.title("🚀 Triple Confluence Secretary (20 EMA)")
st.markdown("""
**Logic:**
1. ✅ **Weekly** Close > **20 EMA**
2. ✅ **Daily** Close > **20 EMA**
3. ✅ **4-Hour** Close > **20 EMA**
4. 🎯 Returns stocks that pass **ALL 3** tests.
*(Note: TradingView Scanner supports EMA 20, 30, 50, but not 26. We use 20 as the best standard proxy.)*
""")

def get_scan_results(interval_const):
    """Runs a specific timeframe scan for Price > EMA 20"""
    ss = tvs.StockScreener()
    ss.set_markets(tvs.Market.AMERICA)
    
    # Set the Timeframe (Daily, Weekly, or 4H)
    ss.set_interval(interval_const)
    
    # Add Filter: Close > EMA 20
    # We use EMA 20 because EMA 26 is not available in the Scanner API
    ss.add_filter(tvs.Filter(tvs.StockField.CLOSE, tvs.FilterOperator.ABOVE, tvs.StockField.EXPONENTIAL_MOVING_AVERAGE_20))
    
    # Add Filter: Volume > 500k (to filter out junk stocks)
    ss.add_filter(tvs.Filter(tvs.StockField.VOLUME, tvs.FilterOperator.ABOVE, 500000))
    
    # Get top 2000 stocks to ensure we find enough overlaps
    df = ss.get(limit=2000)
    return df

if st.button('🔥 Run Triple-Confluence Scan'):
    status = st.status("Running Triple-Pass Scan...", expanded=True)
    
    try:
        # 1. Run the 3 Separate Scans
        status.write("⏳ Scanning **Weekly** Timeframe...")
        df_weekly = get_scan_results(tvs.Interval.WEEKLY)
        
        status.write("⏳ Scanning **Daily** Timeframe...")
        df_daily = get_scan_results(tvs.Interval.DAILY)
        
        status.write("⏳ Scanning **4-Hour** Timeframe...")
        # Note: 4Hours can sometimes be tricky, we use the standard enum
        df_4h = get_scan_results(tvs.Interval.INTERVAL_4_HOURS)
        
        # 2. Find the Intersection (The Confluence)
        if not df_weekly.empty and not df_daily.empty and not df_4h.empty:
            # Extract just the symbols to find the match
            weekly_symbols = set(df_weekly['symbol'])
            daily_symbols = set(df_daily['symbol'])
            four_h_symbols = set(df_4h['symbol'])
            
            # The Magic: Find stocks that exist in ALL 3 sets
            common_symbols = weekly_symbols.intersection(daily_symbols).intersection(four_h_symbols)
            
            status.write(f"✅ Found {len(common_symbols)} Triple-Confluence matches!")
            status.update(label="Scan Complete!", state="complete", expanded=False)
            
            if common_symbols:
                # Filter one of the dataframes to show the final list
                final_df = df_daily[df_daily['symbol'].isin(common_symbols)].copy()
                
                st.success(f"🎉 {len(final_df)} Stocks are bullish on Weekly, Daily, AND 4-Hour charts!")
                
                # Show neat columns
                st.dataframe(
                    final_df[['symbol', 'name', 'close', 'change', 'volume']], 
                    use_container_width=True
                )
                
                # CSV Download
                csv = final_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Results CSV", csv, "Triple_Confluence_Report.csv", "text/csv")
            else:
                st.warning("No stocks met all 3 conditions simultaneously right now.")
        else:
            status.update(label="Error", state="error")
            st.error("One of the scans returned no data.")

    except Exception as e:
        status.update(label="Error", state="error")
        st.error(f"An error occurred: {e}")
