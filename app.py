import streamlit as st
import pandas as pd
import tvscreener as tvs

# ... (Previous password/upload code stays the same) ...

def get_scan_results(interval_string):
    """Runs a specific timeframe scan using standard TradingView strings"""
    ss = tvs.StockScreener()
    ss.set_markets(tvs.Market.AMERICA)
    
    # We pass the string directly: "1W", "1D", or "240" (for 4H)
    ss.set_interval(interval_string)
    
    # Filter: Close > EMA 20 & Volume > 500k
    ss.add_filter(tvs.Filter(tvs.StockField.CLOSE, tvs.FilterOperator.ABOVE, tvs.StockField.EMA20))
    ss.add_filter(tvs.Filter(tvs.StockField.VOLUME, tvs.FilterOperator.ABOVE, 500000))
    
    return ss.get(limit=2000)

if st.button('🔥 Run Triple-Confluence Scan'):
    status = st.status("Starting Analysis...", expanded=True)
    
    try:
        # --- PHASE 1: THE TRIPLE SCAN ---
        status.write("⏳ Scanning **Weekly** Timeframe...")
        df_weekly = get_scan_results("1W")  # Direct string for Weekly
        
        status.write("⏳ Scanning **Daily** Timeframe...")
        df_daily = get_scan_results("1D")   # Direct string for Daily
        
        status.write("⏳ Scanning **4-Hour** Timeframe...")
        df_4h = get_scan_results("240")     # Direct string for 4H (240 mins)
        
        # --- PHASE 2: INTERSECTION & WATCHLIST ---
        if not df_weekly.empty and not df_daily.empty and not df_4h.empty:
            weekly_set = set(df_weekly['symbol'])
            daily_set = set(df_daily['symbol'])
            four_h_set = set(df_4h['symbol'])
            
            bullish_market_symbols = weekly_set.intersection(daily_set).intersection(four_h_set)
            
            final_matches = []
            if watchlist_symbols:
                status.write(f"🕵️ Filtering against your {len(watchlist_symbols)} symbols...")
                final_matches = list(bullish_market_symbols.intersection(set(watchlist_symbols)))
            else:
                final_matches = list(bullish_market_symbols)
            
            status.update(label="Scan Complete!", state="complete", expanded=False)
            
            if final_matches:
                final_df = df_daily[df_daily['symbol'].isin(final_matches)].copy()
                st.success(f"🎉 Found {len(final_df)} matches!")
                st.dataframe(final_df[['symbol', 'name', 'close', 'change', 'volume']], use_container_width=True)
                
                csv = final_df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Report", csv, "Triple_Confluence.csv", "text/csv")
            else:
                st.warning("No matches found meeting the criteria today.")
        else:
            st.error("The TradingView API returned empty data for one of the timeframes.")

    except Exception as e:
        st.error(f"Scan failed: {e}")
