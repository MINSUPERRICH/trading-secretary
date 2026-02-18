import streamlit as st
from tradingview_screener import Query, Column

st.title("🚀 Triple Confluence Secretary")

# This scans 918+ symbols in about 3 seconds
def get_data():
    q = Query().set_markets('america')
    q.select('name', 'change', 'volume', 'relative_volume_10d_calc')
    # Add your technical conditions here
    # e.g., 'RSI' > 50, etc.
    df = q.get_scanner_data()
    return df

if st.button('Run Deep Scan'):
    with st.spinner('Scanning 918 symbols...'):
        data = get_data()
        st.write(f"Found {len(data)} matches!")
        st.dataframe(data)