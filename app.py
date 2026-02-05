import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# --- 1. CONFIGURATION & PASSWORD SYSTEM ---
st.set_page_config(page_title="Secure Hybrid AI Screener", layout="wide", page_icon="🔐")

# पासवर्ड चेक करने का फंक्शन
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "rituraj123":  # यहाँ अपना पासवर्ड बदलें
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # पासवर्ड को मेमोरी से हटा दें
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # अगर अभी तक पासवर्ड नहीं डाला गया
        st.text_input(
            "कृपया पासवर्ड डालें (Default: rituraj123):", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # गलत पासवर्ड
        st.text_input(
            "गलत पासवर्ड! फिर से कोशिश करें:", type="password", on_change=password_entered, key="password"
        )
        return False
    else:
        # सही पासवर्ड
        return True

if not check_password():
    st.stop()  # अगर पासवर्ड गलत है तो ऐप यहीं रुक जाएगा

# --- 2. CUSTOM CSS ---
st.markdown("""
<style>
    .card { background-color: #1e1e1e; border-radius: 15px; padding: 20px; border-left: 5px solid #4CAF50; margin-bottom: 20px; }
    .card-red { border-left: 5px solid #F44336; }
    .card-title { font-size: 18px; font-weight: bold; color: #fff; }
    .metric-value { font-size: 32px; font-weight: bold; color: #fff; }
</style>
""", unsafe_allow_html=True)

# --- 3. DATA FUNCTION (UPDATED) ---
@st.cache_data(ttl=3600)
def get_stock_data(tickers):
    data_list = []
    progress_bar = st.progress(0)
    total_stocks = len(tickers)
    
    for i, ticker in enumerate(tickers):
        symbol = ticker + ".NS"
        try:
            df = yf.download(symbol, period="1y", interval="1d", progress=False)
            
            # --- FIX: अगर डेटा खाली है तो स्किप करें ---
            if df.empty or len(df) < 200:
                continue
                
            # Calculations
            df['SMA_50'] = ta.sma(df['Close'], length=50)
            df['SMA_200'] = ta.sma(df['Close'], length=200)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            high_52w = float(df['High'].max())
            current_price = float(df['Close'].iloc[-1])
            
            # Logic
            score = 0
            # 1. Golden Cross
            if df['SMA_50'].iloc[-1] > df['SMA_200'].iloc[-1]: score += 1
            # 2. Darvas (Near High)
            if current_price >= (high_52w * 0.90): score += 1
            # 3. RSI
            if 50 < df['RSI'].iloc[-1] < 70: score += 1
            # 4. Above 200 SMA
            if current_price > df['SMA_200'].iloc[-1]: score += 1
            else: score -= 2

            status = "NEUTRAL"
            if score >= 3: status = "STRONG BUY"
            elif score <= 0: status = "EXIT / AVOID"
            else: status = "HOLD / WATCH"

            atr = ta.atr(df['High'], df['Low'], df['Close'], length=14).iloc[-1]
            
            data_list.append({
                "Stock": ticker,
                "CMP": round(current_price, 2),
                "Status": status,
                "AI Score": score,
                "Entry": round(high_52w + (atr * 0.5), 2),
                "Target": round(current_price + (4 * atr), 2),
                "Stop Loss": round(current_price - (2 * atr), 2),
                "RSI": round(df['RSI'].iloc[-1], 2),
                "52W High": round(high_52w, 2)
            })
            
        except Exception:
            continue
        
        progress_bar.progress((i + 1) / total_stocks)

    progress_bar.empty()
    
    # --- FIX: अगर लिस्ट खाली है तो खाली DataFrame लौटाएं ---
    if not data_list:
        return pd.DataFrame(columns=["Stock", "CMP", "Status", "AI Score", "Entry", "Target", "Stop Loss", "RSI", "52W High"])
        
    return pd.DataFrame(data_list)

# --- 4. MAIN APP LOGIC ---
st.title("🚀 Hybrid AI Stock Screener (Protected)")
st.markdown("---")

# Sample List
nifty_sample = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL", 
    "ITC", "KOTAKBANK", "LT", "AXISBANK", "HUL", "TATAMOTORS", "MARUTI", "WIPRO"
]

with st.spinner('Scanning Market Data...'):
    df_results = get_stock_data(nifty_sample)

# --- FIX: अगर डेटा नहीं मिला तो एरर न दें ---
if df_results.empty:
    st.warning("⚠️ कोई डेटा नहीं मिला। शायद इंटरनेट धीमा है या मार्केट बंद है। कृपया पेज रिफ्रेश करें।")
    st.stop()

# बाकी कोड वैसे ही काम करेगा क्योंकि अब df_results खाली नहीं है
buy_stocks = df_results[df_results['Status'] == "STRONG BUY"]['Stock'].tolist()
exit_stocks = df_results[df_results['Status'] == "EXIT / AVOID"]['Stock'].tolist()

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""<div class="card"><div class="card-title">🚀 STRONG BUY</div><div class="metric-value">{len(buy_stocks)}</div><div>{", ".join(buy_stocks)}</div></div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="card card-red"><div class="card-title">⚠️ EXIT NOW</div><div class="metric-value">{len(exit_stocks)}</div><div>{", ".join(exit_stocks)}</div></div>""", unsafe_allow_html=True)

st.markdown("### 📊 Scanner Results")
st.dataframe(df_results.style.applymap(lambda x: 'color: green' if x == 'STRONG BUY' else ('color: red' if x == 'EXIT / AVOID' else ''), subset=['Status']), use_container_width=True)
