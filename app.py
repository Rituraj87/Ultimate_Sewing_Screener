import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import datetime

# --- 1. Page Configuration & Custom CSS (3D Cards) ---
st.set_page_config(page_title="AI Hybrid Stock Screener", layout="wide", page_icon="📈")

st.markdown("""
<style>
    .card {
        background-color: #1e1e1e;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23);
        border-left: 5px solid #4CAF50;
        margin-bottom: 20px;
        transition: transform 0.3s;
    }
    .card:hover {
        transform: translateY(-5px);
    }
    .card-red {
        border-left: 5px solid #F44336;
    }
    .card-title {
        font-size: 18px;
        font-weight: bold;
        color: #ffffff;
        margin-bottom: 10px;
    }
    .stock-list {
        font-size: 14px;
        color: #cccccc;
        max-height: 100px;
        overflow-y: auto;
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        color: #fff;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. Data Fetching & Analysis Function ---
@st.cache_data(ttl=3600)  # Cache data for 1 hour to speed up
def get_stock_data(tickers):
    data_list = []
    
    # Progress bar for scanning
    progress_bar = st.progress(0)
    total_stocks = len(tickers)
    
    for i, ticker in enumerate(tickers):
        symbol = ticker + ".NS"
        try:
            # Download 1 year of data for calculations
            df = yf.download(symbol, period="1y", interval="1d", progress=False)
            
            if df.empty:
                continue
                
            # --- HYBRID STRATEGY CALCULATIONS ---
            
            # 1. Moving Averages (Golden Cross)
            df['SMA_50'] = ta.sma(df['Close'], length=50)
            df['SMA_200'] = ta.sma(df['Close'], length=200)
            
            # 2. RSI (Value/Momentum)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            # 3. Darvas Box Logic (52 Week High)
            high_52w = df['High'].max()
            current_price = df['Close'].iloc[-1]
            
            # --- LOGIC FOR SIGNAL ---
            status = "NEUTRAL"
            score = 0
            
            # Condition 1: Golden Cross / Uptrend
            if df['SMA_50'].iloc[-1] > df['SMA_200'].iloc[-1]:
                score += 1
            
            # Condition 2: Near 52 Week High (Darvas) - Within 10%
            if current_price >= (high_52w * 0.90):
                score += 1
                
            # Condition 3: RSI Momentum (Not Overbought yet)
            rsi_val = df['RSI'].iloc[-1]
            if 50 < rsi_val < 70:
                score += 1
            
            # Condition 4: Price above SMA 200 (Basic Filter)
            if current_price > df['SMA_200'].iloc[-1]:
                score += 1
            else:
                score -= 2 # Penalty for being in downtrend

            # Determine Final Status
            if score >= 3:
                status = "STRONG BUY"
            elif score <= 0:
                status = "EXIT / AVOID"
            else:
                status = "HOLD / WATCH"

            # Entry, Target, Stoploss Logic
            atr = ta.atr(df['High'], df['Low'], df['Close'], length=14).iloc[-1]
            stop_loss = current_price - (2 * atr) # 2x ATR Stoploss
            target = current_price + (4 * atr)    # 4x ATR Target (1:2 Risk Reward)
            
            # Darvas Entry (Breakout)
            darvas_entry = high_52w + (atr * 0.5)

            data_list.append({
                "Stock": ticker,
                "CMP": round(current_price, 2),
                "Status": status,
                "AI Score": score,
                "Entry (Breakout)": round(darvas_entry, 2),
                "Target": round(target, 2),
                "Stop Loss": round(stop_loss, 2),
                "RSI": round(rsi_val, 2),
                "52W High": round(high_52w, 2)
            })
            
        except Exception as e:
            continue
        
        # Update Progress
        progress_bar.progress((i + 1) / total_stocks)

    progress_bar.empty()
    return pd.DataFrame(data_list)

# --- 3. Main App Layout ---

st.title("🚀 Hybrid AI Stock Screener (Darvas + Buffett + Golden Cross)")
st.markdown("---")

# ** SAMPLE LIST ** (Replace this with full Nifty 500 list for production)
nifty_sample = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL", 
    "ITC", "KOTAKBANK", "LT", "AXISBANK", "HUL", "TATAMOTORS", "MARUTI", 
    "ULTRACEMCO", "ASIANPAINT", "SUNPHARMA", "TITAN", "M&M", "ADANIENT",
    "WIPRO", "HCLTECH", "BAJFINANCE", "NESTLEIND", "ONGC", "NTPC"
]

# Load Data
with st.spinner('Scanning Market Data... Please wait...'):
    df_results = get_stock_data(nifty_sample)

# Separate Lists
buy_stocks = df_results[df_results['Status'] == "STRONG BUY"]['Stock'].tolist()
exit_stocks = df_results[df_results['Status'] == "EXIT / AVOID"]['Stock'].tolist()

# --- 4. 3D Cards Section ---
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">🚀 STRONG BUY SIGNALS</div>
        <div class="metric-value">{len(buy_stocks)} Stocks</div>
        <div class="stock-list">
            {", ".join(buy_stocks)}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="card card-red">
        <div class="card-title">⚠️ EXIT / AVOID SIGNALS</div>
        <div class="metric-value">{len(exit_stocks)} Stocks</div>
        <div class="stock-list">
             {", ".join(exit_stocks)}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. Search & Deep Analysis ---
st.markdown("### 🔍 Deep Dive Analysis")
search_query = st.text_input("Enter Stock Name (e.g., WIPRO, RELIANCE)", "").upper()

if search_query:
    # Check if stock exists in our scanned data
    stock_info = df_results[df_results['Stock'] == search_query]
    
    if not stock_info.empty:
        s_data = stock_info.iloc[0]
        
        # Dynamic Color for Status
        status_color = "green" if "BUY" in s_data['Status'] else "red" if "EXIT" in s_data['Status'] else "orange"
        
        st.markdown(f"""
        #### Analysis for: **{search_query}**
        - **Status:** <span style="color:{status_color}; font-weight:bold; font-size:20px">{s_data['Status']}</span> (AI Score: {s_data['AI Score']}/4)
        - **Reasoning:** - RSI is {s_data['RSI']} (Momentum)
            - CMP ({s_data['CMP']}) vs 52W High ({s_data['52W High']})
        """, unsafe_allow_html=True)
        
        # Parameter Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Price", f"₹{s_data['CMP']}")
        m2.metric("Ideal Entry", f"₹{s_data['Entry (Breakout)']}")
        m3.metric("Target", f"₹{s_data['Target']}")
        m4.metric("Stop Loss", f"₹{s_data['Stop Loss']}")
        
        # Links
        tv_link = f"https://in.tradingview.com/chart/?symbol=NSE:{search_query}"
        st.markdown(f"[👉 View on TradingView]({tv_link})", unsafe_allow_html=True)
        
    else:
        st.warning("Stock not found in the current scanned list or invalid name.")

st.markdown("---")

# --- 6. The Master Table ---
st.markdown("### 📊 Nifty Scanner Results")

# Filter Options
filter_option = st.radio("Filter By:", ["All", "Strong Buy", "Exit / Avoid"], horizontal=True)

if filter_option == "Strong Buy":
    display_df = df_results[df_results['Status'] == "STRONG BUY"]
elif filter_option == "Exit / Avoid":
    display_df = df_results[df_results['Status'] == "EXIT / AVOID"]
else:
    display_df = df_results

# Styling the dataframe
st.dataframe(
    display_df.style.applymap(lambda x: 'color: green; font-weight: bold' if x == 'STRONG BUY' else ('color: red; font-weight: bold' if x == 'EXIT / AVOID' else ''), subset=['Status'])
    .format({"CMP": "₹{:.2f}", "Entry (Breakout)": "₹{:.2f}", "Target": "₹{:.2f}", "Stop Loss": "₹{:.2f}"}),
    use_container_width=True,
    height=600
)

# Sidebar info
st.sidebar.header("About Logic")
st.sidebar.info("""
**Hybrid Strategy Used:**
1. **Darvas Box:** Price near 52-Week High.
2. **Golden Cross:** SMA 50 > SMA 200.
3. **Value Check:** RSI not extremely Overbought (>70).
4. **ATR Targets:** Stops and Targets are calculated using Volatility (ATR).
""")
