import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(page_title="UZAIR ALI DARK CRYPTO - Real-Time Scanner", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%); }
    .main-header { text-align: center; padding: 20px; border-bottom: 2px solid #00ffaa; margin-bottom: 20px; }
    .main-header h1 { font-family: monospace; color: #00ffaa; text-shadow: 0 0 10px #00ffaa; }
    .alert-card { background: #0f1322; border-radius: 10px; padding: 12px; margin: 8px 0; border-left: 4px solid; cursor: pointer; }
    .up { border-left-color: #00ffaa; }
    .down { border-left-color: #ff4444; }
    .vol { border-left-color: #ffaa00; }
    .tag { display: inline-block; background: #2a2f4a; padding: 2px 8px; border-radius: 12px; font-size: 0.7em; margin-right: 5px; }
    .tag-up { background: #00ffaa20; color: #00ffaa; }
    .tag-down { background: #ff444420; color: #ff4444; }
    .tag-vol { background: #ffaa0020; color: #ffaa00; }
    .footer { text-align: center; padding: 20px; color: #5a6e8a; font-size: 0.8em; border-top: 1px solid #2a2f4a; margin-top: 30px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🌑 UZAIR ALI DARK CRYPTO</h1><p>Real-Time Scanner | 1m · 3m · 5m | Delta · Volume · Wick | Live Binance Futures</p></div>', unsafe_allow_html=True)

# ============================================
# SYMBOLS & INTERVALS
# ============================================
SYMBOLS = [
    'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT',
    'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'MATICUSDT', 'LINKUSDT',
    'NEARUSDT', 'ATOMUSDT', 'LTCUSDT', 'UNIUSDT', 'ARBUSDT',
    'OPUSDT', 'APTUSDT', 'SUIUSDT'
]
INTERVALS = ['1m', '3m', '5m']

# Default thresholds (user can adjust)
THRESHOLDS = {
    '1m': {'delta': 2.0, 'vol_mult': 2.0, 'wick_ratio': 1.5},
    '3m': {'delta': 2.5, 'vol_mult': 2.0, 'wick_ratio': 1.5},
    '5m': {'delta': 3.0, 'vol_mult': 2.0, 'wick_ratio': 1.5}
}

# ============================================
# API FUNCTIONS with error handling
# ============================================
def fetch_klines(symbol, interval, limit=30):
    """Fetch klines, return DataFrame or None"""
    try:
        url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df[['open','high','low','close','quote_volume']] = df[['open','high','low','close','quote_volume']].astype(float)
            return df
        else:
            return None
    except Exception as e:
        return None

def fetch_price(symbol):
    try:
        url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return float(resp.json()['price'])
    except:
        pass
    return None

# ============================================
# ANALYSIS FUNCTIONS
# ============================================
def analyze_candle(df, interval):
    if df is None or len(df) < 3:
        return None
    last = df.iloc[-1]
    prev = df.iloc[-2]
    # Delta % (open vs close)
    delta = ((last['close'] - last['open']) / last['open']) * 100
    # Last 3 avg delta
    last3 = df.tail(3)
    avg_delta = ((last3['close'].iloc[-1] - last3['open'].iloc[0]) / last3['open'].iloc[0]) * 100
    # Volume anomaly (vs rolling ~30min avg)
    window = min(30, len(df)-1)
    avg_vol = df['quote_volume'].tail(window).mean()
    curr_vol = last['quote_volume']
    vol_mult = curr_vol / avg_vol if avg_vol > 0 else 1.0
    # Wick ratio (max wick / body)
    body = abs(last['close'] - last['open'])
    if body == 0:
        wick_ratio = 0
    else:
        upper_wick = last['high'] - max(last['close'], last['open'])
        lower_wick = min(last['close'], last['open']) - last['low']
        wick_ratio = max(upper_wick, lower_wick) / body
    # Anomaly score (0-100)
    score = 0
    if abs(delta) >= THRESHOLDS[interval]['delta']:
        score += min(40, abs(delta) * 8)
    if vol_mult >= THRESHOLDS[interval]['vol_mult']:
        score += min(30, vol_mult * 6)
    if wick_ratio >= THRESHOLDS[interval]['wick_ratio']:
        score += min(30, wick_ratio * 10)
    score = min(100, int(score))
    # Tags
    tags = []
    if abs(delta) >= THRESHOLDS[interval]['delta']:
        tags.append(("UP" if delta > 0 else "DOWN", delta > 0))
    if vol_mult >= THRESHOLDS[interval]['vol_mult']:
        tags.append(("VOL", None))
    return {
        'symbol': None,  # will fill later
        'interval': interval,
        'price': last['close'],
        'delta': round(delta, 2),
        'avg_delta': round(avg_delta, 2),
        'vol_mult': round(vol_mult, 2),
        'wick_ratio': round(wick_ratio, 2),
        'anomaly_score': score,
        'tags': tags
    }

# ============================================
# SCAN ALL
# ============================================
def scan_all():
    results = []
    for sym in SYMBOLS:
        price = fetch_price(sym)
        if price is None:
            continue
        for iv in INTERVALS:
            df = fetch_klines(sym, iv, limit=40)
            if df is None:
                continue
            analysis = analyze_candle(df, iv)
            if analysis:
                analysis['symbol'] = sym
                analysis['price'] = price
                results.append(analysis)
        # small delay to avoid rate limit
        time.sleep(0.1)
    # sort by anomaly score desc
    results.sort(key=lambda x: x['anomaly_score'], reverse=True)
    return results

# ============================================
# SIDEBAR
# ============================================
st.sidebar.markdown("## ⚙️ Thresholds")
for iv in INTERVALS:
    with st.sidebar.expander(f"{iv} thresholds"):
        d = st.number_input(f"Delta % ({iv})", value=THRESHOLDS[iv]['delta'], step=0.5, key=f"d_{iv}")
        v = st.number_input(f"Volume multiplier ({iv})", value=THRESHOLDS[iv]['vol_mult'], step=0.5, key=f"v_{iv}")
        w = st.number_input(f"Wick ratio ({iv})", value=THRESHOLDS[iv]['wick_ratio'], step=0.2, key=f"w_{iv}")
        THRESHOLDS[iv] = {'delta': d, 'vol_mult': v, 'wick_ratio': w}

auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=True)
audible = st.sidebar.checkbox("🔊 Audible alerts (|Δ%|≥3)", value=False)
st.sidebar.markdown("---")
st.sidebar.info("💡 Click any alert row to open Binance Futures chart.")

# ============================================
# MAIN SCAN
# ============================================
with st.spinner("Scanning Binance Futures (real-time)..."):
    data = scan_all()

if not data:
    st.error("❌ No data received. Binance API might be rate-limited. Please wait and refresh.")
    st.stop()

# ============================================
# DISPLAY ALERTS
# ============================================
st.markdown(f"### 🚨 Real-Time Anomalies (Last scan: {datetime.now().strftime('%H:%M:%S')})")
important = [d for d in data if d['anomaly_score'] >= 20]
if not important:
    st.info("No anomalies above threshold. Adjust thresholds or wait for volatility.")
else:
    for event in important[:30]:
        card_class = "up" if any(t[0]=="UP" for t in event['tags']) else ("down" if any(t[0]=="DOWN" for t in event['tags']) else "vol")
        tag_html = ""
        for tag, _ in event['tags']:
            tag_html += f'<span class="tag tag-{tag.lower()}">{tag}</span> '
        st.markdown(f"""
        <div class="alert-card {card_class}" onclick="window.open('https://www.binance.com/en/futures/{event['symbol']}', '_blank')">
            <div style="display: flex; justify-content: space-between;">
                <div><b>{event['symbol']}</b> <span class="tag">{event['interval']}</span> {tag_html}</div>
                <div>Score: {event['anomaly_score']}</div>
            </div>
            <div>Δ%: <b style="color:{'#0f0' if event['delta']>0 else '#f44'}">{event['delta']:+.2f}%</b> | Last3 Δ: {event['avg_delta']:+.2f}% | Vol×: {event['vol_mult']:.1f}x | Wick: {event['wick_ratio']:.1f} | Price: ${event['price']:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# FULL TABLE
# ============================================
st.markdown("### 📋 Full Scanner Output")
df_full = pd.DataFrame(data)
if not df_full.empty:
    df_show = df_full[['symbol','interval','price','delta','avg_delta','vol_mult','wick_ratio','anomaly_score']].copy()
    df_show['delta'] = df_show['delta'].apply(lambda x: f"{x:+.2f}%")
    df_show['avg_delta'] = df_show['avg_delta'].apply(lambda x: f"{x:+.2f}%")
    df_show['price'] = df_show['price'].apply(lambda x: f"${x:,.2f}")
    df_show.columns = ['Symbol','Int','Price','Δ%','Last3 Δ%','Vol×','Wick','Score']
    st.dataframe(df_show, use_container_width=True, height=500)
else:
    st.warning("No data to display. Check API connectivity.")

# ============================================
# AUDIBLE ALERTS
# ============================================
high_delta = any(abs(d['delta']) >= 3.0 for d in data)
if audible and high_delta:
    st.markdown('<audio autoplay><source src="https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3" type="audio/mpeg"></audio>', unsafe_allow_html=True)

# ============================================
# AUTO REFRESH
# ============================================
if auto_refresh:
    time.sleep(30)
    st.rerun()

# ============================================
# FOOTER
# ============================================
st.markdown(f"""
<div class="footer">
    <p>🔄 Binance Futures API (real-time) | Last scan: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>⚠️ Not financial advice. Always DYOR. Click any row to open chart.</p>
</div>
""", unsafe_allow_html=True)

# Clickable rows in dataframe
st.markdown("""
<script>
document.querySelectorAll('.dataframe tbody tr').forEach(row => {
    row.style.cursor = 'pointer';
    row.addEventListener('click', () => {
        let symbol = row.cells[0].innerText;
        window.open('https://www.binance.com/en/futures/' + symbol, '_blank');
    });
});
</script>
""", unsafe_allow_html=True)
