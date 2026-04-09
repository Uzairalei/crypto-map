import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="UZAIR ALI DARK CRYPTO - Elxes Real-Time Scanner",
    page_icon="🌑",
    layout="wide"
)

# ============================================
# CUSTOM CSS
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
    }
    
    .main-header {
        text-align: center;
        padding: 20px;
        border-bottom: 2px solid #00ffaa;
        margin-bottom: 20px;
    }
    
    .main-header h1 {
        font-family: 'Orbitron', monospace;
        color: #00ffaa;
        font-size: 2.5em;
        text-shadow: 0 0 15px #00ffaa;
    }
    
    .alert-card {
        background: #0f1322;
        border-radius: 10px;
        padding: 12px;
        margin: 8px 0;
        border-left: 4px solid;
        transition: 0.2s;
    }
    .alert-card:hover {
        transform: translateX(5px);
        background: #1a1f3a;
    }
    .up { border-left-color: #00ffaa; }
    .down { border-left-color: #ff4444; }
    .vol { border-left-color: #ffaa00; }
    
    .stat-card {
        background: #0f1322;
        border: 1px solid #2a2f4a;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .footer {
        text-align: center;
        padding: 20px;
        color: #5a6e8a;
        font-size: 0.8em;
        border-top: 1px solid #2a2f4a;
        margin-top: 30px;
    }
    .dataframe {
        font-size: 0.8em;
    }
    .tag {
        display: inline-block;
        background: #2a2f4a;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.7em;
        margin-right: 5px;
    }
    .tag-up { background: #00ffaa20; color: #00ffaa; }
    .tag-down { background: #ff444420; color: #ff4444; }
    .tag-vol { background: #ffaa0020; color: #ffaa00; }
</style>
""", unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
st.markdown("""
<div class="main-header">
    <h1>🌑 UZAIR ALI DARK CRYPTO</h1>
    <p>Elxes Real-Time Scanner | 1m · 3m · 5m | Delta · Volume · Wick Anomalies | Live Binance Futures</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# CONFIGURATION
# ============================================
SYMBOLS = [
    'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT',
    'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'MATICUSDT', 'LINKUSDT',
    'NEARUSDT', 'ATOMUSDT', 'LTCUSDT', 'UNIUSDT', 'ARBUSDT',
    'OPUSDT', 'APTUSDT', 'SUIUSDT', 'INJUSDT', 'TIAUSDT'
]

INTERVALS = ['1m', '3m', '5m']

# Default thresholds (can be adjusted in sidebar)
DEFAULT_THRESHOLDS = {
    '1m': {'delta': 2.0, 'volume_mult': 2.0, 'wick_ratio': 1.5},
    '3m': {'delta': 2.5, 'volume_mult': 2.0, 'wick_ratio': 1.5},
    '5m': {'delta': 3.0, 'volume_mult': 2.0, 'wick_ratio': 1.5}
}

# ============================================
# SESSION STATE
# ============================================
if 'last_data' not in st.session_state:
    st.session_state.last_data = {}
if 'large_trades' not in st.session_state:
    st.session_state.large_trades = []

# ============================================
# BINANCE API FUNCTIONS
# ============================================
def fetch_klines(symbol, interval, limit=50):
    """Fetch latest klines from Binance Futures"""
    try:
        url = "https://fapi.binance.com/fapi/v1/klines"
        params = {'symbol': symbol, 'interval': interval, 'limit': limit}
        resp = requests.get(url, params=params, timeout=5)
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
    except:
        pass
    return None

def fetch_24hr_ticker(symbol):
    try:
        url = f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return {
                'last_price': float(data['lastPrice']),
                'price_change_pct': float(data['priceChangePercent'])
            }
    except:
        pass
    return None

def fetch_recent_agg_trades(symbol, threshold_usd, limit=30):
    try:
        url = f"https://fapi.binance.com/fapi/v1/aggTrades?symbol={symbol}&limit={limit}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            trades = resp.json()
            large = []
            for t in trades:
                price = float(t['p'])
                qty = float(t['q'])
                usd = price * qty
                if usd >= threshold_usd:
                    large.append({
                        'symbol': symbol,
                        'price': price,
                        'qty': qty,
                        'usd_value': usd,
                        'time': datetime.fromtimestamp(t['T']/1000),
                        'is_buyer_maker': t['m']
                    })
            return large
    except:
        pass
    return []

# ============================================
# ANALYSIS FUNCTIONS
# ============================================
def calculate_delta(df):
    """Return (delta%, last3_avg_delta%, close_price)"""
    if df is None or len(df) < 2:
        return 0, 0, 0
    last = df.iloc[-1]
    delta = ((last['close'] - last['open']) / last['open']) * 100
    last3 = df.tail(3)
    avg_delta = ((last3['close'].iloc[-1] - last3['open'].iloc[0]) / last3['open'].iloc[0]) * 100 if len(last3) == 3 else delta
    return round(delta, 2), round(avg_delta, 2), last['close']

def calculate_volume_anomaly(df, window=30):
    """Volume multiplier vs rolling average (approx 30 min)"""
    if df is None or len(df) < 10:
        return 1.0
    window = min(window, len(df)-1)
    avg_vol = df['quote_volume'].tail(window).mean()
    curr_vol = df['quote_volume'].iloc[-1]
    mult = curr_vol / avg_vol if avg_vol > 0 else 1.0
    return round(mult, 2)

def calculate_wick_ratio(df):
    """Wick to body ratio for last candle"""
    if df is None or len(df) < 1:
        return 0
    last = df.iloc[-1]
    body = abs(last['close'] - last['open'])
    if body == 0:
        return 0
    upper_wick = last['high'] - max(last['close'], last['open'])
    lower_wick = min(last['close'], last['open']) - last['low']
    max_wick = max(upper_wick, lower_wick)
    return round(max_wick / body, 2)

def detect_anomaly_score(delta, vol_mult, wick_ratio, interval):
    """Hybrid score (0-100) based on delta, volume, wick"""
    score = 0
    # Delta contribution
    delta_th = DEFAULT_THRESHOLDS[interval]['delta']
    if abs(delta) >= delta_th:
        score += min(40, abs(delta) * 10)
    # Volume contribution
    vol_th = DEFAULT_THRESHOLDS[interval]['volume_mult']
    if vol_mult >= vol_th:
        score += min(30, vol_mult * 8)
    # Wick contribution
    wick_th = DEFAULT_THRESHOLDS[interval]['wick_ratio']
    if wick_ratio >= wick_th:
        score += min(30, wick_ratio * 12)
    return min(100, int(score))

# ============================================
# MAIN SCANNER
# ============================================
@st.cache_data(ttl=20)
def scan_all():
    results = []
    for symbol in SYMBOLS:
        ticker = fetch_24hr_ticker(symbol)
        if not ticker:
            continue
        for interval in INTERVALS:
            df = fetch_klines(symbol, interval, limit=50)
            if df is None:
                continue
            delta, avg_delta, close = calculate_delta(df)
            vol_mult = calculate_volume_anomaly(df)
            wick_ratio = calculate_wick_ratio(df)
            anomaly_score = detect_anomaly_score(delta, vol_mult, wick_ratio, interval)
            
            # Determine tags
            tags = []
            if abs(delta) >= DEFAULT_THRESHOLDS[interval]['delta']:
                tags.append(("UP" if delta > 0 else "DOWN", delta > 0))
            if vol_mult >= DEFAULT_THRESHOLDS[interval]['volume_mult']:
                tags.append(("VOL", None))
            
            results.append({
                'symbol': symbol,
                'interval': interval,
                'price': close,
                'delta': delta,
                'avg_delta': avg_delta,
                'vol_mult': vol_mult,
                'wick_ratio': wick_ratio,
                'anomaly_score': anomaly_score,
                'tags': tags,
                'timestamp': datetime.now()
            })
    # Sort by anomaly score descending
    results.sort(key=lambda x: x['anomaly_score'], reverse=True)
    return results

# ============================================
# SIDEBAR CONTROLS
# ============================================
st.sidebar.markdown("## ⚙️ Controls")
threshold_usd = st.sidebar.number_input("Large Trade Threshold (USD)", value=1000000, step=100000)
auto_refresh = st.sidebar.checkbox("Auto Refresh (20s)", value=True)
audible = st.sidebar.checkbox("Audible Alerts (|Δ%| ≥ 3)", value=False)

st.sidebar.markdown("## 📊 Thresholds (per interval)")
new_thresholds = {}
for iv in INTERVALS:
    with st.sidebar.expander(f"{iv} thresholds"):
        d = st.number_input(f"Delta % ({iv})", value=DEFAULT_THRESHOLDS[iv]['delta'], step=0.5, key=f"delta_{iv}")
        v = st.number_input(f"Volume multiplier ({iv})", value=DEFAULT_THRESHOLDS[iv]['volume_mult'], step=0.5, key=f"vol_{iv}")
        w = st.number_input(f"Wick ratio ({iv})", value=DEFAULT_THRESHOLDS[iv]['wick_ratio'], step=0.2, key=f"wick_{iv}")
        new_thresholds[iv] = {'delta': d, 'volume_mult': v, 'wick_ratio': w}
# Update thresholds globally
for iv in INTERVALS:
    DEFAULT_THRESHOLDS[iv] = new_thresholds[iv]

# ============================================
# FETCH DATA
# ============================================
with st.spinner("Scanning Binance Futures USDT pairs..."):
    scan_results = scan_all()
    large_trades = []
    if threshold_usd:
        for sym in SYMBOLS[:10]:  # limit to avoid rate limits
            large_trades.extend(fetch_recent_agg_trades(sym, threshold_usd, limit=20))
        large_trades.sort(key=lambda x: x['time'], reverse=True)
        large_trades = large_trades[:30]

# ============================================
# DISPLAY ALERTS (Top anomalies)
# ============================================
st.markdown("### 🚨 Real-Time Anomaly Alerts (Highest Score First)")

# Filter only events with anomaly_score >= 20
important = [r for r in scan_results if r['anomaly_score'] >= 20]
if not important:
    st.info("No significant anomalies in current scan. Adjust thresholds or wait for volatility.")

for event in important[:25]:
    # Determine card class
    direction = ""
    if any(t[0] == "UP" for t in event['tags']):
        card_class = "up"
        direction = "UP"
    elif any(t[0] == "DOWN" for t in event['tags']):
        card_class = "down"
        direction = "DOWN"
    else:
        card_class = "vol"
    
    # Build tag HTML
    tag_html = ""
    for tag, is_up in event['tags']:
        if tag == "VOL":
            tag_html += f'<span class="tag tag-vol">VOL</span> '
        elif tag == "UP":
            tag_html += f'<span class="tag tag-up">UP</span> '
        elif tag == "DOWN":
            tag_html += f'<span class="tag tag-down">DOWN</span> '
    
    st.markdown(f"""
    <div class="alert-card {card_class}" onclick="window.open('https://www.binance.com/en/futures/{event['symbol']}', '_blank')">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <b>{event['symbol']}</b> <span class="tag">{event['interval']}</span>
                {tag_html}
            </div>
            <div style="font-weight: bold;">Score: {event['anomaly_score']}</div>
        </div>
        <div style="margin-top: 5px; font-size: 0.9em;">
            Δ%: <b style="color:{'#00ffaa' if event['delta']>0 else '#ff4444'}">{event['delta']:+.2f}%</b> 
            | Last3 Δ: {event['avg_delta']:+.2f}%
            | Vol×: {event['vol_mult']:.1f}x
            | Wick ratio: {event['wick_ratio']:.1f}
            | Price: ${event['price']:,.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# DETAILED TABLE (All events)
# ============================================
st.markdown("### 📋 Full Scanner Table (All Pairs & Intervals)")
df_display = pd.DataFrame(scan_results)
if not df_display.empty:
    df_show = df_display[['symbol','interval','price','delta','avg_delta','vol_mult','wick_ratio','anomaly_score']].copy()
    df_show['delta'] = df_show['delta'].apply(lambda x: f"{x:+.2f}%")
    df_show['avg_delta'] = df_show['avg_delta'].apply(lambda x: f"{x:+.2f}%")
    df_show['price'] = df_show['price'].apply(lambda x: f"${x:,.2f}")
    df_show.columns = ['Symbol','Int','Price','Δ%','Last3 Δ%','Vol×','Wick Ratio','Anomaly Score']
    st.dataframe(df_show, use_container_width=True, height=400)
else:
    st.warning("No data fetched. Check network or API limits.")

# ============================================
# LARGE TRADES TABLE
# ============================================
st.markdown(f"### 💰 Large Trades ( > ${threshold_usd:,.0f} )")
if large_trades:
    trades_df = pd.DataFrame(large_trades)
    trades_df['usd_value'] = trades_df['usd_value'].apply(lambda x: f"${x:,.0f}")
    trades_df['price'] = trades_df['price'].apply(lambda x: f"${x:,.2f}")
    trades_df['side'] = trades_df['is_buyer_maker'].apply(lambda x: "SELL" if x else "BUY")
    trades_df = trades_df[['time', 'symbol', 'side', 'price', 'qty', 'usd_value']]
    trades_df.columns = ['Time', 'Symbol', 'Side', 'Price', 'Quantity', 'USD Value']
    st.dataframe(trades_df, use_container_width=True)
else:
    st.info("No large trades detected in recent scans.")

# ============================================
# AUDIBLE ALERTS (if any high delta)
# ============================================
high_delta = any(abs(r['delta']) >= 3.0 for r in scan_results)
if audible and high_delta:
    st.markdown('<audio autoplay><source src="https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3" type="audio/mpeg"></audio>', unsafe_allow_html=True)
    st.toast("🔊 High delta detected! Check alerts.", icon="⚠️")

# ============================================
# AUTO-REFRESH & FOOTER
# ============================================
if auto_refresh:
    time.sleep(20)
    st.rerun()

st.markdown(f"""
<div class="footer">
    <p>🔄 Data Source: Binance Futures API (real-time) | Last Scan: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>⚠️ Disclaimer: For informational purposes only. Not financial advice. Always DYOR.</p>
    <p>📡 Click any alert card to open symbol on Binance Futures.</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# JAVASCRIPT FOR CLICKABLE ROWS (Full table)
# ============================================
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
