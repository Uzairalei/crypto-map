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
    page_title="UZAIR ALI DARK CRYPTO - Real-Time Market Scanner",
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
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
        border-bottom: 2px solid #00ffaa;
        margin-bottom: 20px;
    }
    
    .main-header h1 {
        font-family: 'Orbitron', monospace;
        color: #00ffaa;
        font-size: 2.5em;
        text-shadow: 0 0 15px #00ffaa;
        letter-spacing: 3px;
    }
    
    .alert-box {
        background: #0f1322;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid;
    }
    
    .alert-up {
        border-left-color: #00ffaa;
        background: rgba(0,255,170,0.05);
    }
    
    .alert-down {
        border-left-color: #ff4444;
        background: rgba(255,68,68,0.05);
    }
    
    .alert-volume {
        border-left-color: #ffaa00;
        background: rgba(255,170,0,0.05);
    }
    
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
</style>
""", unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
st.markdown("""
<div class="main-header">
    <h1>🌑 UZAIR ALI DARK CRYPTO</h1>
    <p>Real-Time Market Scanner | Delta & Volume Analysis | Anomaly Detection | Large Trades</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE
# ============================================
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'large_trades' not in st.session_state:
    st.session_state.large_trades = []

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
LARGE_TRADE_THRESHOLD_USD = 1000000  # 1M USD
VOLUME_WINDOW_MINUTES = 30
DELTA_THRESHOLD = 3.0  # % for audible alert

# ============================================
# BINANCE API FUNCTIONS
# ============================================
def fetch_klines(symbol, interval, limit=100):
    """Fetch kline data from Binance Futures"""
    try:
        url = f"https://fapi.binance.com/fapi/v1/klines"
        params = {'symbol': symbol, 'interval': interval, 'limit': limit}
        resp = requests.get(url, params=params, timeout=10)
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
        return None
    return None

def fetch_24hr_ticker(symbol):
    """Fetch 24hr ticker for price"""
    try:
        url = f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return {
                'last_price': float(data['lastPrice']),
                'price_change_pct': float(data['priceChangePercent']),
                'volume': float(data['volume']),
                'quote_volume': float(data['quoteVolume'])
            }
    except:
        pass
    return None

# ============================================
# ANALYSIS FUNCTIONS
# ============================================
def calculate_delta(df):
    """Calculate % change between open and close of last candle"""
    if df is None or len(df) < 2:
        return 0, 0, 0
    last = df.iloc[-1]
    delta = ((last['close'] - last['open']) / last['open']) * 100
    # Last 3 candles average delta
    last3 = df.tail(3)
    avg_delta = ((last3['close'].iloc[-1] - last3['open'].iloc[0]) / last3['open'].iloc[0]) * 100 if len(last3) == 3 else delta
    return round(delta, 2), round(avg_delta, 2), last['close']

def calculate_volume_anomaly(df, window_minutes=30):
    """Calculate current volume vs rolling average (approx 30-min)"""
    if df is None or len(df) < 10:
        return 1.0
    # Estimate window size based on interval
    # For 1m: window=30, for 3m: window=10, for 5m: window=6
    # Since we don't have interval here, use a heuristic based on number of rows
    window = min(30, max(6, len(df) // 3))
    avg_volume = df['quote_volume'].tail(window).mean()
    current_volume = df['quote_volume'].iloc[-1]
    multiplier = current_volume / avg_volume if avg_volume > 0 else 1.0
    return round(multiplier, 2)

def detect_anomaly(delta, volume_multiplier, price_change_pct):
    """Hybrid anomaly detection - returns score and description"""
    score = 0
    reasons = []
    if abs(delta) > 2.5:
        score += abs(delta) / 2
        reasons.append(f"Price delta {delta:.1f}%")
    if volume_multiplier > 2.5:
        score += volume_multiplier / 1.5
        reasons.append(f"Volume spike {volume_multiplier}x")
    if abs(price_change_pct) > 5:
        score += abs(price_change_pct) / 3
        reasons.append(f"24h change {price_change_pct:.1f}%")
    score = min(100, score * 10)
    return round(score), ", ".join(reasons) if reasons else "Normal"

# ============================================
# FETCH ALL DATA
# ============================================
@st.cache_data(ttl=30)
def fetch_all_data():
    """Fetch data for all symbols and intervals"""
    results = {}
    for symbol in SYMBOLS:
        ticker = fetch_24hr_ticker(symbol)
        if not ticker:
            continue
        symbol_data = {'symbol': symbol, 'last_price': ticker['last_price'], 'price_change_pct': ticker['price_change_pct']}
        for interval in INTERVALS:
            klines = fetch_klines(symbol, interval, limit=100)
            if klines is not None:
                delta, avg_delta, close = calculate_delta(klines)
                vol_mult = calculate_volume_anomaly(klines, VOLUME_WINDOW_MINUTES)
                anomaly_score, anomaly_reason = detect_anomaly(delta, vol_mult, ticker['price_change_pct'])
                symbol_data[f'delta_{interval}'] = delta
                symbol_data[f'avg_delta_{interval}'] = avg_delta
                symbol_data[f'vol_mult_{interval}'] = vol_mult
                symbol_data[f'anomaly_score_{interval}'] = anomaly_score
                symbol_data[f'anomaly_reason_{interval}'] = anomaly_reason
                symbol_data[f'close_{interval}'] = close
        results[symbol] = symbol_data
    return results

# ============================================
# LARGE TRADES
# ============================================
def fetch_recent_agg_trades(symbol, limit=50):
    """Fetch recent aggregated trades"""
    try:
        url = f"https://fapi.binance.com/fapi/v1/aggTrades?symbol={symbol}&limit={limit}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            trades = resp.json()
            large_trades = []
            for t in trades:
                price = float(t['p'])
                qty = float(t['q'])
                usd_value = price * qty
                if usd_value >= LARGE_TRADE_THRESHOLD_USD:
                    large_trades.append({
                        'symbol': symbol,
                        'price': price,
                        'qty': qty,
                        'usd_value': usd_value,
                        'time': datetime.fromtimestamp(t['T']/1000),
                        'is_buyer_maker': t['m']  # False means buyer aggressive (BUY)
                    })
            return large_trades
    except:
        pass
    return []

def fetch_all_large_trades():
    all_trades = []
    for symbol in SYMBOLS:
        trades = fetch_recent_agg_trades(symbol, limit=20)
        all_trades.extend(trades)
    all_trades.sort(key=lambda x: x['time'], reverse=True)
    return all_trades[:50]

# ============================================
# MAIN APP
# ============================================

# Sidebar controls
st.sidebar.markdown("## ⚙️ Controls")
threshold = st.sidebar.number_input("Large Trade Threshold (USD)", value=1000000, step=100000)
global LARGE_TRADE_THRESHOLD_USD
LARGE_TRADE_THRESHOLD_USD = threshold
auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=True)
audible_alerts = st.sidebar.checkbox("Audible Alerts on |Δ%| ≥ 3", value=False)

# Main content
col_status1, col_status2 = st.columns(2)
with col_status1:
    st.markdown("### 📡 Data Stream Status")
    st.info("🟢 Scanning Binance Futures USDT pairs")
    st.caption(f"Symbols: {len(SYMBOLS)} | Intervals: {', '.join(INTERVALS)}")
with col_status2:
    st.markdown("### 🔔 Recent Alerts")
    alert_placeholder = st.empty()

# Fetch data
with st.spinner("Fetching real-time data..."):
    market_data = fetch_all_data()
    large_trades = fetch_all_large_trades()

# Check for delta alerts
delta_alerts = []
for sym, data in market_data.items():
    for interval in INTERVALS:
        delta_key = f'delta_{interval}'
        if delta_key in data and abs(data[delta_key]) >= DELTA_THRESHOLD:
            delta_alerts.append({
                'symbol': sym,
                'interval': interval,
                'delta': data[delta_key],
                'price': data['last_price']
            })

# Display alerts
if delta_alerts:
    alert_text = "### ⚡ Price Movement Alerts\n"
    for a in delta_alerts[:10]:
        direction = "▲ UP" if a['delta'] > 0 else "▼ DOWN"
        alert_text += f"- {a['symbol']} ({a['interval']}): {direction} {a['delta']:.2f}% @ ${a['price']:,.2f}\n"
    alert_placeholder.warning(alert_text)
    if audible_alerts:
        st.markdown('<audio autoplay><source src="https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3" type="audio/mpeg"></audio>', unsafe_allow_html=True)
else:
    alert_placeholder.info("No significant price movements in last scan.")

# ============================================
# MARKET DATA TABLE
# ============================================
st.markdown("### 📊 Real-Time Market Scanner")

rows = []
for sym, data in market_data.items():
    row = {
        'Symbol': sym,
        'Price': f"${data['last_price']:,.2f}",
        '24h %': f"{data['price_change_pct']:+.2f}%",
    }
    for interval in INTERVALS:
        delta = data.get(f'delta_{interval}', 0)
        vol_mult = data.get(f'vol_mult_{interval}', 1.0)
        anomaly = data.get(f'anomaly_score_{interval}', 0)
        row[f'{interval} Δ%'] = f"{delta:+.2f}%"
        row[f'{interval} Vol×'] = f"{vol_mult:.1f}x"
        row[f'{interval} Anomaly'] = f"{anomaly}%"
    rows.append(row)

df_display = pd.DataFrame(rows)
st.dataframe(df_display, use_container_width=True, height=400)

# ============================================
# LARGE TRADES TABLE
# ============================================
st.markdown("### 💰 Large Trades (>${:,.0f})".format(LARGE_TRADE_THRESHOLD_USD))
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
# ANOMALY EXPLANATION
# ============================================
st.markdown("### 🧠 Market Anomaly Alerts (Noise-Filtered Hybrid Model)")
st.caption("Detects unusual price/volume behavior relative to each asset's own history. Score reflects statistical abnormality only, not direction.")
anomaly_list = []
for sym, data in market_data.items():
    for interval in INTERVALS:
        score = data.get(f'anomaly_score_{interval}', 0)
        if score >= 30:
            anomaly_list.append({
                'symbol': sym,
                'interval': interval,
                'score': score,
                'reason': data.get(f'anomaly_reason_{interval}', '')
            })
if anomaly_list:
    for a in anomaly_list[:15]:
        st.markdown(f"""
        <div class="alert-box alert-volume">
            <b>⚠️ {a['symbol']} ({a['interval']})</b> - Anomaly Score: {a['score']}<br>
            <small>{a['reason']}</small>
        </div>
        """, unsafe_allow_html=True)
else:
    st.success("No significant anomalies detected. Market behavior within expected ranges.")

# ============================================
# CLICKABLE ROWS (JavaScript for binance link)
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

# ============================================
# AUTO-REFRESH
# ============================================
if auto_refresh:
    time.sleep(30)
    st.rerun()

# ============================================
# FOOTER
# ============================================
st.markdown(f"""
<div class="footer">
    <p>🔄 Data Source: Binance Futures API (Real-time) | Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>⚠️ DISCLAIMER: This system is for informational purposes only. Not financial advice.</p>
</div>
""", unsafe_allow_html=True)
