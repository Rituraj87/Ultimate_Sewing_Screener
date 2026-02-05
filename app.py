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
            "कृपया पासवर्ड डालें", type="password", on_change=password_entered, key="password"
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
  "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS", "SBIN.NS", "INFY.NS", "LICI.NS", "ITC.NS", "HINDUNILVR.NS",
    "LT.NS", "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS", "ADANIENT.NS", "KOTAKBANK.NS", "TITAN.NS", "ONGC.NS", "TATAMOTORS.NS",
    "NTPC.NS", "AXISBANK.NS", "ADANIPORTS.NS", "POWERGRID.NS", "ULTRACEMCO.NS", "M&M.NS", "WIPRO.NS", "BAJAJFINSV.NS", "COALINDIA.NS", "JSWSTEEL.NS",
    "TATASTEEL.NS", "LTIM.NS", "HINDALCO.NS", "SBILIFE.NS", "GRASIM.NS", "TECHM.NS", "ADANIGREEN.NS", "BRITANNIA.NS", "HAL.NS", "BAJAJ-AUTO.NS",
    "ADANIPOWER.NS", "SIEMENS.NS", "DLF.NS", "INDUSINDBK.NS", "DIVISLAB.NS", "DRREDDY.NS", "EICHERMOT.NS", "JIOFIN.NS", "BEL.NS", "VARROC.NS",
    "VBL.NS", "TRENT.NS", "ZOMATO.NS", "PIDILITIND.NS", "HAVELLS.NS", "NESTLEIND.NS", "BPCL.NS", "GAIL.NS", "SHRIRAMFIN.NS", "GODREJCP.NS",
    "IOC.NS", "TATACONSUM.NS", "CIPLA.NS", "DABUR.NS", "ABB.NS", "CHOLAFIN.NS", "AMBUJACEM.NS", "PNB.NS", "INDIGO.NS", "VEDL.NS",
    "BANKBARODA.NS", "TVSMOTOR.NS", "BOSCHLTD.NS", "MOTHERSON.NS", "HEROMOTOCO.NS", "RECLTD.NS", "MANKIND.NS", "APOLLOHOSP.NS", "TORNTPOWER.NS", "ICICIPRULI.NS",
    "LODHA.NS", "CANBK.NS", "PFC.NS", "JINDALSTEL.NS", "POLYCAB.NS", "IRCTC.NS", "CUMMINSIND.NS", "COLPAL.NS", "MCDOWELL-N.NS", "PERSISTENT.NS",
    "MUTHOOTFIN.NS", "ASHOKLEY.NS", "MRF.NS", "PIIND.NS", "IDFCFIRSTB.NS", "ASTRAL.NS", "TATACOMM.NS", "PHOENIXLTD.NS", "MPHASIS.NS", "SUPREMEIND.NS",
    "TIINDIA.NS", "LALPATHLAB.NS", "AUBANK.NS", "CONCOR.NS", "ABCAPITAL.NS", "TATACHEM.NS", "FEDERALBNK.NS", "OBEROIRLTY.NS", "LTTS.NS", "ATUL.NS",
    "COROMANDEL.NS", "GMRINFRA.NS", "WHIRLPOOL.NS", "ALKEM.NS", "COFORGE.NS", "TDPOWERSYS.NS", "BHEL.NS", "SAIL.NS", "NATIONALUM.NS", "BANDHANBNK.NS",
    "GUJGASLTD.NS", "IPCALAB.NS", "LAURUSLABS.NS", "TATAELXSI.NS", "DEEPAKNTR.NS", "CROMPTON.NS", "ACC.NS", "DALBHARAT.NS", "JSL.NS", "APLAPOLLO.NS",
    "MFSL.NS", "PETRONET.NS", "ZEEL.NS", "RAMCOCEM.NS", "NAVINFLUOR.NS", "SYNGENE.NS", "TRIDENT.NS", "SOLARINDS.NS", "RVNL.NS", "IRFC.NS",
    "MAZDOCK.NS", "COCHINSHIP.NS", "FACT.NS", "SUZLON.NS", "IDEA.NS", "YESBANK.NS", "IDBI.NS", "UNIONBANK.NS", "IOB.NS", "UCOBANK.NS",
    "CENTRALBK.NS", "MAHABANK.NS", "BANKINDIA.NS", "BSE.NS", "CDSL.NS", "ANGELONE.NS", "MCX.NS", "MOTILALOFS.NS", "IEX.NS", "LUPIN.NS",
    "BIOCON.NS", "AUROPHARMA.NS", "GLENMARK.NS", "ZYDUSLIFE.NS", "GRANULES.NS", "ABFRL.NS", "BATAINDIA.NS", "RELAXO.NS", "PAGEIND.NS", "JUBLFOOD.NS",
    "DEVYANI.NS", "SAPPHIRE.NS", "KALYANKJIL.NS", "RAJESHEXPO.NS", "MANAPPURAM.NS", "M&MFIN.NS", "LICHSGFIN.NS", "POONAWALLA.NS", "SUNDARAMFIN.NS", "KPITTECH.NS",
    "CYIENT.NS", "BSOFT.NS", "SONACOMS.NS", "ZENSARTECH.NS", "OFSS.NS", "HONAUT.NS", "KEI.NS", "DIXON.NS", "AMBER.NS", "KAYNES.NS",
    "DATAPATTNS.NS", "MTARTECH.NS", "PARAS.NS", "ASTRAMICRO.NS", "CENTUM.NS", "HBLPOWER.NS", "TITAGARH.NS", "TEXRAIL.NS", "JWL.NS", "RKFORGE.NS",
    "ELECTCAST.NS", "GABRIEL.NS", "PRICOLLTD.NS", "SUBROS.NS", "LUMAXIND.NS", "MINDA CORP.NS", "UNOMINDA.NS", "ENDURANCE.NS", "CRAFTSMAN.NS", "JAMNAAUTO.NS",
    "GNA.NS", "ROLEXRINGS.NS", "SFL.NS", "TIMKEN.NS", "SCHAEFFLER.NS", "SKFINDIA.NS", "AIAENG.NS", "THERMAX.NS", "TRIVENI.NS", "PRAJIND.NS",
    "BALRAMCHIN.NS", "EIDPARRY.NS", "RENUKA.NS", "TRIVENITURB.NS", "KIRLOSENG.NS", "ELGIEQUIP.NS", "INGERRAND.NS", "KSB.NS", "POWERINDIA.NS", "HITACHI.NS",
    "VOLTAS.NS", "BLUESTARCO.NS", "KAJARIACER.NS", "CERA.NS", "SOMANYCERA.NS", "GREENPANEL.NS", "CENTURYPLY.NS", "STYLAMIND.NS", "PRINCEPIPE.NS", "FINPIPE.NS",
    "JINDALSAW.NS", "WELCORP.NS", "MAHARSEAM.NS", "RATNAMANI.NS", "APLLTD.NS", "ALEMBICLTD.NS", "ERIS.NS", "AJANTPHARM.NS", "JBITHEM.NS", "NATCOPHARM.NS",
    "PFIZER.NS", "SANOFI.NS", "ABBOTINDIA.NS", "GLAXO.NS", "ASTERDM.NS", "NARAYANA.NS", "KIMS.NS", "RAINBOW.NS", "METROPOLIS.NS", "THYROCARE.NS",
    "VIJAYA.NS", "FORTIS.NS", "MAXHEALTH.NS", "NH.NS", "HCG.NS", "POLYMED.NS", "LINDEINDIA.NS", "FLUOROCHEM.NS", "AETHER.NS", "CLEAN.NS",
    "FINEORG.NS", "VINATIORGA.NS", "ROSSARI.NS", "NOCIL.NS", "SUMICHEM.NS", "UPL.NS", "RALLIS.NS", "CHAMBLFERT.NS", "GNFC.NS", "GSFC.NS",
    "DEEPAKFERT.NS", "PARADEEP.NS", "IPL.NS", "CASTROLIND.NS", "GULFOILLUB.NS", "BLS.NS", "REDINGTON.NS", "ECLERX.NS", "FSL.NS", "TANLA.NS",
    "ROUTE.NS", "MASTEK.NS", "INTELLECT.NS", "HAPPSTMNDS.NS", "LATENTVIEW.NS", "MAPMYINDIA.NS", "RATEGAIN.NS", "NAZARA.NS", "PBFINTECH.NS", "PAYTM.NS",
    "NYKAA.NS", "DELHIVERY.NS", "HONASA.NS", "RRKABEL.NS", "CAMS.NS", "KFINTECH.NS", "PRUDENT.NS", "ANANDRATHI.NS", "SHAREINDIA.NS", "GEJTL.NS",
    "STARCEMENT.NS", "JKCEMENT.NS", "JKLAKSHMI.NS", "BIRLACORPN.NS", "HEIDELBERG.NS", "NUVOCO.NS", "ORIENTCEM.NS", "SAGCEM.NS", "KCP.NS", "INDIACEM.NS",
    "PRISMJOHN.NS", "AARTIIND.NS", "SUDARSCHEM.NS", "LAOPALA.NS", "BORORENEW.NS", "ASAHIINDIA.NS", "VIPIND.NS", "SAFARI.NS", "TTKPRESTIG.NS", "HAWKINS.NS",
    "SYMPHONY.NS", "ORIENTELEC.NS", "VGUARD.NS", "IFBIND.NS", "JOHNSONCON.NS", "PGHH.NS", "GILLETTE.NS", "EMAMILTD.NS", "MARICO.NS", "JYOTHYLAB.NS",
    "WABAG.NS", "VAIBHAVGBL.NS", "PCJEWELLER.NS", "THANGAMAYL.NS", "SENCO.NS", "GOLDIAM.NS", "RADICO.NS", "UBL.NS", "SULA.NS", "GMMPFAUDLR.NS",
    "TEJASNET.NS", "ITI.NS", "HFCL.NS", "STERLITE.NS", "INDUSTOWER.NS", "GSPL.NS", "MGL.NS", "IGL.NS", "ATGL.NS", "OIL.NS",
    "HINDPETRO.NS", "CHENNPETRO.NS", "MRPL.NS", "AEGISLOG.NS", "CONFIPET.NS", "DEEPINDS.NS", "HOEC.NS", "SELAN.NS", "JINDALDRILL.NS", "SWSOLAR.NS",
    "BOROLTD.NS", "GREAVESCOT.NS", "KIRLOSIND.NS", "PTC.NS", "SJVN.NS", "NHPC.NS", "JPPOWER.NS", "RTNPOWER.NS", "RPOWER.NS", "ADANIPOWER.NS", "JSWENERGY.NS",
    "CESC.NS", "EXIDEIND.NS", "AMARAJABAT.NS", "HBLPOWER.NS", "HUDCO.NS", "NBCC.NS", "RITES.NS", "IRCON.NS", "RAILTEL.NS", "BEML.NS", "GPPL.NS",
    "SCI.NS", "DREDGECORP.NS", "RCF.NS", "NFL.NS", "AWL.NS", "PATANJALI.NS", "MANYAVAR.NS", "RHIM.NS", "POLICYBZR.NS", "STARHEALTH.NS",
    "MEDANTA.NS", "BIKAJI.NS", "CAMPUS.NS", "METROBRAND.NS", "RUSTOMJEE.NS", "KEYSTONE.NS", "SIGNATURE.NS", "SOBHA.NS", "PRESTIGE.NS", "BRIGADE.NS",
    "GODREJPROP.NS", "SUNTECK.NS", "MAHLIFE.NS", "PURVA.NS", "ASHOKA.NS", "PNCINFRA.NS", "KNRCON.NS", "GRINFRA.NS", "HGINFRA.NS", "DILIPBUILD.NS",
    "NCC.NS", "HCC.NS", "ITDCEM.NS", "MANINFRA.NS", "JKTYRE.NS", "CEATLTD.NS", "APOLLOTYRE.NS", "BALKRISIND.NS", "TVSSRICHAK.NS", "GOCOLORS.NS",
    "VMART.NS", "SHOPERSTOP.NS", "TCNSBRANDS.NS", "ARVIND.NS", "RAYMOND.NS", "WELSPUNIND.NS", "GARFIBRES.NS", "LUXIND.NS", "DOLLAR.NS", "RUPA.NS",
    "KPRMILL.NS", "GOKEX.NS", "SWANENERGY.NS", "TRITURBINE.NS", "ELECON.NS", "AIAENGINE.NS", "TIMKEN.NS", "SCHAEFFLER.NS", "GRINDWELL.NS", "CARBORUNIV.NS",
    "MMTC.NS", "STCINDIA.NS", "GMDC.NS", "MOIL.NS", "KIOCL.NS", "HINDCOPPER.NS", "HINDZINC.NS", "GPIL.NS", "JAYNECOIND.NS", "LLOYDSME.NS",
    "IMFA.NS", "MASTEK.NS", "FSL.NS", "ECLERX.NS", "HGS.NS", "DATAMATICS.NS", "CMSINFO.NS", "SIS.NS", "QUESS.NS", "TEAMLEASE.NS",
    "BLS.NS", "JUSTDIAL.NS", "AFFLE.NS", "INDIAMART.NS", "VAIBHAVGBL.NS", "CARTRADE.NS", "EASYTRIP.NS", "YATRA.NS", "RBA.NS", "WESTLIFE.NS",
    "BARBEQUE.NS", "SPECIALITY.NS", "CHALET.NS", "LEMONHOTEL.NS", "EIHOTEL.NS", "INDHOTEL.NS", "TAJGVK.NS", "MAHSEAMLES.NS", "APOLLOPIPE.NS", "SURYA.NS"
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
