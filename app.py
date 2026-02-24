# --- AUTO-RENAME MACD & DAILY COLUMNS ---
        # 1. Rename exact matches to include "MACD" and standardize Daily to "D"
        rename_dict = {
            # 4-Hour Timeframe
            "4H_Signal_Now": "4H_MACD_Signal_Now",
            "4H_Signal_Prev": "4H_MACD_Signal_Prev",
            "4H Signal": "4H_MACD_Trend",
            
            # Daily Timeframe (Catches various export names and forces "D_")
            "1D_Signal_Now": "D_MACD_Signal_Now",
            "1D_Signal_Prev": "D_MACD_Signal_Prev",
            "1D Signal": "D_MACD_Trend",
            "Signal_Now": "D_MACD_Signal_Now",   # If it exports without a timeframe, it defaults to D
            "Signal_Prev": "D_MACD_Signal_Prev", 
            "MACD_Now": "D_MACD_Now",
            "MACD_Prev": "D_MACD_Prev"
        }
        working_df = working_df.rename(columns=rename_dict)
        
        # 2. Catch-all: If any column says "Daily", shrink it to just "D"
        working_df.columns = working_df.columns.str.replace("Daily", "D", regex=False)
        
        st.session_state["master_df"] = working_df
        # ----------------------------------------
