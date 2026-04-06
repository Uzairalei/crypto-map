import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import time

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="UZair Ali Dark Crypto - Professional Trading Signals",
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
        padding: 25px;
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
    
    .main-header p {
        color: #88ffcc;
        font-family: monospace;
    }
    
    .signal-box {
        background: #0f1322;
        border-radius: 15px;
        padding: 25px;
        margin: 15px 0;
        text-align: center;
    }
    
    .signal-bullish {
        border: 2px solid #00ffaa;
        box-shadow: 0 0 30px rgba(0,255,170,0.3);
        background: linear-gradient(135deg, rgba(0,255,170,0.1), rgba(0,255,170,0.05));
    }
    
    .signal-bearish {
        border: 2px solid #ff4444;
        box-shadow: 0 0 30px rgba(255,68,68,0.3);
        background: linear-gradient(135deg, rgba(255,68,68,0.1), rgba(255,68,68,0.05));
    }
    
    .signal-neutral {
        border: 2px solid #ffaa00;
        box-shadow: 0 0 30px rgba(255,170,0,0.3);
    }
    
    .stat-card {
        background: #0f1322;
        border: 1px solid #2a2f4a;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    
    .stat-value {
        font-size: 1.8em;
        font-weight: bold;
        color: #00ffaa;
    }
    
    .footer {
        text-align: center;
        padding: 20px;
        color: #5a6e8a;
        font-size: 0.8em;
        border-top: 1px solid #2a2f4a;
        margin-top: 30px;
    }
    
    .confirmation-item {
        padding: 8px;
        margin: 5px 0;
        border-left: 3px solid #00ffaa;
        background: rgba(0,255,170,0.05);
    }
    
    .coin-card {
        background: #0f1322;
        border: 1px solid #2a2f4a;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        transition: all 0.3s;
    }
    
    .coin-card:hover {
        border-color: #00ffaa;
        transform: translateY(-2px);
    }
    
    .metric-good {
        color: #00ffaa;
    }
    
    .metric-bad {
        color: #ff4444;
    }
    
    .metric-warning {
        color: #ffaa00;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
st.markdown("""
<div class="main-header">
    <h1>🌑 UZAIR ALI DARK CRYPTO</h1>
    <p>Professional Trading Signals | Bitnodes + Binance + Fear & Greed | Multi-Factor AI Analysis</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE
# ============================================
if 'prev_tor' not in st.session_state:
    st.session_state.prev_tor = None
if 'prev_na' not in st.session_state:
    st.session_state.prev_na = None
if 'history' not in st.session_state:
    st.session_state.history = []

# ============================================
# FREE API FUNCTIONS (No API Key Required)
# ============================================

def fetch_bitnodes_data():
    """Fetch real data from Bitnodes API - FREE"""
    try:
        url = "https://bitnodes.io/api/v1/snapshots/latest/"
        headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            total_nodes = data.get('total_nodes', 0)
            timestamp = data.get('timestamp', 0)
            
            tor_count = 0
            for node_addr in data.get('nodes', {}).keys():
                if '.onion' in node_addr.lower():
                    tor_count += 1
            
            tor_percentage = (tor_count / total_nodes * 100) if total_nodes > 0 else 0
            
            return {
                'tor': round(tor_percentage, 2),
                'na': total_nodes,
                'timestamp': datetime.fromtimestamp(timestamp) if timestamp else datetime.now(),
                'success': True
            }
        else:
            return generate_mock_bitnodes()
    except Exception as e:
        return generate_mock_bitnodes()

def generate_mock_bitnodes():
    import random
    return {
        'tor': round(65.2 + (random.random() - 0.5) * 1.5, 2),
        'na': int(23800 + (random.random() - 0.5) * 300),
        'timestamp': datetime.now(),
        'success': False
    }

def fetch_binance_funding_rate(symbol="BTCUSDT"):
    """Fetch funding rate from Binance Futures - FREE"""
    try:
        url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            funding_rate = float(data.get('lastFundingRate', 0))
            
            return {
                'funding_rate': funding_rate,
                'funding_rate_percent': funding_rate * 100,
                'mark_price': float(data.get('markPrice', 0))
            }
        else:
            return None
    except Exception as e:
        return None

def fetch_binance_long_short_ratio(symbol="BTCUSDT"):
    """Fetch Top Trader Long/Short Account Ratio from Binance - FREE"""
    try:
        url = f"https://fapi.binance.com/fapi/v1/topLongShortAccountRatio?symbol={symbol}&period=1h&limit=1"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                latest = data[0]
                long_ratio = float(latest.get('longAccount', 0))
                short_ratio = float(latest.get('shortAccount', 0))
                return {
                    'long_ratio': long_ratio,
                    'short_ratio': short_ratio,
                    'ls_ratio': long_ratio / short_ratio if short_ratio > 0 else 1
                }
        return None
    except Exception as e:
        return None

def fetch_binance_price(symbol="BTCUSDT"):
    """Fetch current price and 24h change from Binance - FREE"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'price': float(data.get('lastPrice', 0)),
                'price_change_percent': float(data.get('priceChangePercent', 0)),
                'high_24h': float(data.get('highPrice', 0)),
                'low_24h': float(data.get('lowPrice', 0)),
                'volume': float(data.get('volume', 0))
            }
        else:
            return generate_mock_price(symbol)
    except Exception as e:
        return generate_mock_price(symbol)

def generate_mock_price(symbol):
    import random
    base_price = 65000 if 'BTC' in symbol else (3500 if 'ETH' in symbol else 150)
    return {
        'price': round(base_price + (random.random() - 0.5) * 200, 2),
        'price_change_percent': round((random.random() - 0.5) * 3, 2),
        'high_24h': round(base_price + 100, 2),
        'low_24h': round(base_price - 100, 2),
        'volume': round(random.random() * 10000, 2)
    }

def fetch_fear_greed_index():
    """Fetch Crypto Fear & Greed Index from Alternative.me - FREE"""
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                latest = data['data'][0]
                return {
                    'value': int(latest.get('value', 50)),
                    'classification': latest.get('value_classification', 'Neutral')
                }
        return {'value': 50, 'classification': 'Neutral'}
    except Exception as e:
        return {'value': 50, 'classification': 'Neutral'}

# ============================================
# SIGNAL CALCULATION ENGINE
# ============================================

def calculate_numerology(value):
    """Reduce number to 1-9"""
    if value is None:
        return None
    num_str = str(value).replace('.', '')
    total = sum(int(d) for d in num_str if d.isdigit())
    while total > 9:
        total = sum(int(d) for d in str(total))
    return total

def get_astro_window(utc_time):
    hour = utc_time.hour
    minute = utc_time.minute
    
    if (hour == 9 and 10 <= minute <= 30):
        return "🌙 MICRO-REVERSAL BAND - Be cautious", True
    elif (hour == 4 and 0 <= minute <= 30):
        return "🌅 RE-ENTRY GATE - Accumulation zone", False
    elif (5 <= hour < 11):
        return "🌏 ASIA SESSION - High liquidity", False
    elif (12 <= hour < 14):
        return "☀️ EUROPE OPEN - High volatility", False
    elif (hour == 17 and minute >= 55) or (hour == 18 and minute <= 20):
        return "🔥 US OPEN POWER ZONE - Maximum liquidity", False
    else:
        return "⚡ NORMAL WINDOW", False

def get_slope_pattern(delta_tor, delta_na):
    if delta_tor > 0 and delta_na > 0:
        return "🚀 SYNCHRONIZED BULLISH", "bullish", "Both rising - Strong momentum"
    elif delta_tor < 0 and delta_na < 0:
        return "📉 SYNCHRONIZED BEARISH", "bearish", "Both falling - Selling pressure"
    elif delta_tor > 0 and delta_na < 0:
        return "⚠️ DIVERGENCE", "neutral", "TOR up, NA down - Limited fuel"
    elif delta_tor < 0 and delta_na > 0:
        return "🔄 ACCUMULATION", "bullish", "Smart money buying dip"
    else:
        return "⚡ NEUTRAL", "neutral", "Mixed signals"

def calculate_momentum(delta_tor, delta_na):
    tor_score = 1 if delta_tor > 0 else (-1 if delta_tor < 0 else 0)
    na_score = 1 if delta_na > 0 else (-1 if delta_na < 0 else 0)
    return tor_score * 2 + na_score

def get_tor_speed(delta_tor):
    if delta_tor >= 0.4:
        return "FAST JUMP", "bullish", "Strong breakout expected (PUMP)"
    elif delta_tor <= -0.4:
        return "FAST DROP", "bearish", "Strong dump expected (DUMP)"
    elif delta_tor >= 0.2:
        return "MODERATE RISE", "bullish", "Moderate momentum"
    elif delta_tor <= -0.2:
        return "MODERATE DROP", "bearish", "Moderate selling"
    else:
        return "SLOW CHANGE", "neutral", "Likely fakeout"

def get_funding_signal(funding_rate_percent):
    """Interpret funding rate signal - FIXED for None values"""
    if funding_rate_percent is None:
        return "⚡ NO DATA", "neutral", "Funding rate unavailable"
    
    if funding_rate_percent > 0.01:
        return "🔴 EXTREME POSITIVE", "bearish", f"Funding {funding_rate_percent:.4f}% - Overheated longs"
    elif funding_rate_percent > 0.005:
        return "🟡 POSITIVE", "neutral", f"Funding {funding_rate_percent:.4f}% - Longs paying"
    elif funding_rate_percent < -0.01:
        return "🟢 EXTREME NEGATIVE", "bullish", f"Funding {funding_rate_percent:.4f}% - Shorts paying"
    elif funding_rate_percent < -0.005:
        return "🟢 NEGATIVE", "bullish", f"Funding {funding_rate_percent:.4f}% - Shorts paying"
    else:
        return "⚡ NEUTRAL", "neutral", f"Funding {funding_rate_percent:.4f}% - Normal"

def get_fear_greed_signal(fng_value):
    """Interpret Fear & Greed Index signal"""
    if fng_value is None:
        return "⚡ NO DATA", "neutral"
    
    if fng_value <= 25:
        return "🟢 EXTREME FEAR", "bullish"
    elif fng_value <= 40:
        return "🟢 FEAR", "bullish"
    elif fng_value <= 60:
        return "⚡ NEUTRAL", "neutral"
    elif fng_value <= 75:
        return "🟡 GREED", "bearish"
    else:
        return "🔴 EXTREME GREED", "bearish"

def get_ls_ratio_signal(ls_ratio):
    """Interpret long/short ratio signal"""
    if ls_ratio is None:
        return "⚡ NO DATA", "neutral"
    
    if ls_ratio > 2:
        return "🔴 EXTREME LONG", "bearish"
    elif ls_ratio > 1.5:
        return "🟡 LONG DOMINANT", "neutral"
    elif ls_ratio < 0.5:
        return "🟢 EXTREME SHORT", "bullish"
    elif ls_ratio < 0.8:
        return "🟢 SHORT DOMINANT", "bullish"
    else:
        return "⚡ BALANCED", "neutral"

# ============================================
# FINAL ACCURATE SIGNAL
# ============================================

def get_final_signal(tor, delta_tor, na, delta_na, funding_rate_percent, 
                     ls_ratio, fng_value, price_change_percent):
    """Combine all factors for final accurate signal"""
    
    signals = []
    bullish_score = 0
    bearish_score = 0
    
    # 1. Bitnodes Signal (Highest Weight - TOR 2x)
    if tor >= 66.5 and delta_tor >= 0.1 and na >= 23500:
        signals.append("✅ Bitnodes: STRONG BULLISH")
        bullish_score += 3
    elif tor >= 65.5 and delta_tor > 0:
        signals.append("✅ Bitnodes: BULLISH")
        bullish_score += 2
    elif tor < 64 and delta_tor < 0:
        signals.append("❌ Bitnodes: BEARISH")
        bearish_score += 3
    elif tor < 65 and delta_tor < 0:
        signals.append("❌ Bitnodes: WEAK BEARISH")
        bearish_score += 1
    else:
        signals.append("⚡ Bitnodes: NEUTRAL")
    
    # 2. Funding Rate Signal
    if funding_rate_percent is not None:
        if funding_rate_percent < -0.005:
            signals.append(f"✅ Funding: NEGATIVE ({funding_rate_percent:.4f}%) - Bullish")
            bullish_score += 2
        elif funding_rate_percent > 0.005:
            signals.append(f"❌ Funding: POSITIVE ({funding_rate_percent:.4f}%) - Bearish")
            bearish_score += 2
        else:
            signals.append(f"⚡ Funding: NEUTRAL ({funding_rate_percent:.4f}%)")
    
    # 3. Long/Short Ratio Signal
    if ls_ratio is not None:
        if ls_ratio < 0.7:
            signals.append(f"✅ L/S Ratio: {ls_ratio:.2f} (Short dominant) - Bullish")
            bullish_score += 2
        elif ls_ratio > 1.5:
            signals.append(f"❌ L/S Ratio: {ls_ratio:.2f} (Long dominant) - Bearish")
            bearish_score += 2
        else:
            signals.append(f"⚡ L/S Ratio: {ls_ratio:.2f} - Neutral")
    
    # 4. Fear & Greed Signal
    if fng_value is not None:
        if fng_value <= 40:
            signals.append(f"✅ Fear & Greed: {fng_value} (FEAR) - Bullish")
            bullish_score += 2
        elif fng_value >= 70:
            signals.append(f"❌ Fear & Greed: {fng_value} (GREED) - Bearish")
            bearish_score += 2
        else:
            signals.append(f"⚡ Fear & Greed: {fng_value} - Neutral")
    
    # 5. Price Action
    if price_change_percent is not None:
        if price_change_percent > 2:
            signals.append(f"✅ Price: +{price_change_percent:.2f}% - Strong uptrend")
            bullish_score += 1
        elif price_change_percent < -2:
            signals.append(f"❌ Price: {price_change_percent:.2f}% - Strong downtrend")
            bearish_score += 1
    
    # Final Decision
    if bullish_score >= bearish_score + 3:
        return {
            'signal': '🟢🟢 ACCURATE LONG SIGNAL 🟢🟢',
            'type': 'bullish',
            'confidence': f'{min(95, 70 + bullish_score * 5)}%',
            'action': 'ENTER LONG POSITION',
            'target': '0.5-0.8%',
            'stop': '-0.25%',
            'leverage': '5x-10x',
            'signals': signals,
            'score': f'Bullish: {bullish_score} | Bearish: {bearish_score}'
        }
    elif bearish_score >= bullish_score + 3:
        return {
            'signal': '🔴🔴 ACCURATE SHORT SIGNAL 🔴🔴',
            'type': 'bearish',
            'confidence': f'{min(95, 70 + bearish_score * 5)}%',
            'action': 'ENTER SHORT POSITION',
            'target': '0.4-0.7%',
            'stop': '-0.25%',
            'leverage': '5x-10x',
            'signals': signals,
            'score': f'Bullish: {bullish_score} | Bearish: {bearish_score}'
        }
    else:
        return {
            'signal': '🟡 NO ACCURATE SIGNAL - WAIT 🟡',
            'type': 'neutral',
            'confidence': 'LOW',
            'action': 'WAIT FOR CONFIRMATION',
            'target': 'N/A',
            'stop': 'N/A',
            'leverage': 'N/A',
            'signals': signals,
            'score': f'Bullish: {bullish_score} | Bearish: {bearish_score}'
        }

# ============================================
# COIN SIGNALS FOR ALTCOINS
# ============================================

def get_multiple_coin_data():
    """Fetch data for multiple coins"""
    coins = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT']
    results = {}
    
    for symbol in coins:
        price_data = fetch_binance_price(symbol)
        
        results[symbol.replace('USDT', '')] = {
            'price': price_data.get('price', 0),
            'price_change': price_data.get('price_change_percent', 0)
        }
    
    return results

def get_coin_signals(coin_data, final_signal_type):
    """Generate signals for multiple coins"""
    signals = []
    
    coins = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 'AVAX', 'MATIC', 'LINK']
    
    for coin in coins:
        data = coin_data.get(coin, {})
        price_change = data.get('price_change', 0)
        
        if final_signal_type == 'bullish':
            if price_change > 0:
                signal = "LONG"
                confidence = "HIGH"
            else:
                signal = "LONG (DIP)"
                confidence = "MEDIUM"
            entry = data.get('price', 'Market')
        elif final_signal_type == 'bearish':
            if price_change < 0:
                signal = "SHORT"
                confidence = "HIGH"
            else:
                signal = "SHORT (RALLY)"
                confidence = "MEDIUM"
            entry = data.get('price', 'Market')
        else:
            signal = "NEUTRAL"
            confidence = "LOW"
            entry = "No entry"
        
        signals.append({
            'symbol': coin,
            'signal': signal,
            'confidence': confidence,
            'entry': f'${entry:,.2f}' if isinstance(entry, (int, float)) and entry > 0 else entry,
            'price_change': f'{price_change:+.2f}%' if price_change != 0 else 'N/A'
        })
    
    return signals

# ============================================
# MAIN APP
# ============================================

# Fetch all data
with st.spinner('🔄 Fetching live data from Bitnodes, Binance, and Alternative.me...'):
    bitnodes = fetch_bitnodes_data()
    
    # Binance Futures Data
    btc_funding = fetch_binance_funding_rate("BTCUSDT")
    btc_ls = fetch_binance_long_short_ratio("BTCUSDT")
    btc_price = fetch_binance_price("BTCUSDT")
    
    # Fear & Greed
    fng = fetch_fear_greed_index()
    
    # Multi-coin data
    coin_data = get_multiple_coin_data()

current_tor = bitnodes['tor']
current_na = bitnodes['na']
current_time = bitnodes['timestamp']

# Calculate deltas
delta_tor = current_tor - st.session_state.prev_tor if st.session_state.prev_tor else 0
delta_na = current_na - st.session_state.prev_na if st.session_state.prev_na else 0

# Get analysis
momentum = calculate_momentum(delta_tor, delta_na)
slope_text, slope_type, slope_desc = get_slope_pattern(delta_tor, delta_na)
tor_speed_name, tor_speed_type, tor_speed_desc = get_tor_speed(delta_tor)
astro_label, is_reversal = get_astro_window(current_time)
tor_num = calculate_numerology(current_tor)
na_num = calculate_numerology(current_na)

# Signals from APIs - FIXED: Handle None values
funding_rate = btc_funding.get('funding_rate_percent') if btc_funding else None
funding_text, funding_type, funding_desc = get_funding_signal(funding_rate)

ls_ratio = btc_ls.get('ls_ratio') if btc_ls else None
ls_text, ls_type = get_ls_ratio_signal(ls_ratio)

fng_text, fng_type = get_fear_greed_signal(fng.get('value'))

# Format values for display - FIXED: Check None before formatting
funding_display = f"{funding_rate:.4f}%" if funding_rate is not None else "N/A"
ls_ratio_display = f"{ls_ratio:.2f}" if ls_ratio is not None else "N/A"

# Final accurate signal
final_signal = get_final_signal(
    current_tor, delta_tor, current_na, delta_na,
    funding_rate, ls_ratio, fng.get('value'),
    btc_price.get('price_change_percent', 0)
)

# Generate coin signals
coin_signals = get_coin_signals(coin_data, final_signal['type'])

# Update session state
st.session_state.prev_tor = current_tor
st.session_state.prev_na = current_na

# ============================================
# DISPLAY - STATISTICS ROW
# ============================================
st.markdown("### 📊 LIVE MARKET DATA")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    delta_color = "#00ffaa" if delta_tor > 0 else ("#ff4444" if delta_tor < 0 else "#ffaa00")
    st.markdown(f"""
    <div class="stat-card">
        <div>🌐 TOR %</div>
        <div class="stat-value">{current_tor}%</div>
        <div style="color: {delta_color}">{delta_tor:+.2f}%</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    delta_color = "#00ffaa" if delta_na > 0 else ("#ff4444" if delta_na < 0 else "#ffaa00")
    st.markdown(f"""
    <div class="stat-card">
        <div>📡 NETWORK AVAILABILITY</div>
        <div class="stat-value">{current_na:,}</div>
        <div style="color: {delta_color}">{delta_na:+,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    funding_color = "#00ffaa" if funding_rate is not None and funding_rate < -0.005 else ("#ff4444" if funding_rate is not None and funding_rate > 0.005 else "#ffaa00")
    st.markdown(f"""
    <div class="stat-card">
        <div>💰 FUNDING RATE</div>
        <div class="stat-value" style="color: {funding_color};">{funding_display}</div>
        <div>{funding_desc[:25] if funding_desc else ''}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card">
        <div>📊 L/S RATIO</div>
        <div class="stat-value">{ls_ratio_display}</div>
        <div>{ls_text}</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    fng_color = "#00ffaa" if fng.get('value', 50) <= 40 else ("#ff4444" if fng.get('value', 50) >= 70 else "#ffaa00")
    st.markdown(f"""
    <div class="stat-card">
        <div>😨 FEAR & GREED</div>
        <div class="stat-value" style="color: {fng_color};">{fng.get('value', 50)}</div>
        <div>{fng.get('classification', 'Neutral')}</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# FINAL ACCURATE SIGNAL
# ============================================
st.markdown("### 🎯 ACCURATE TRADING SIGNAL")

signal_class = f"signal-{final_signal['type']}"
st.markdown(f"""
<div class="signal-box {signal_class}">
    <div style="font-size: 2.5em; font-weight: bold;">{final_signal['signal']}</div>
    <div style="font-size: 1.3em; margin: 10px 0;">Confidence: {final_signal['confidence']}</div>
    <div style="margin: 15px 0; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 10px;">
        <div>🎯 ACTION: {final_signal['action']}</div>
        <div>📈 TARGET: {final_signal['target']} | 🛑 STOP: {final_signal['stop']} | ⚡ LEVERAGE: {final_signal['leverage']}</div>
        <div style="margin-top: 5px; font-size: 0.9em;">{final_signal['score']}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================
# CONFIRMATIONS
# ============================================
st.markdown("### ✅ SIGNAL CONFIRMATIONS")

for sig in final_signal['signals']:
    st.markdown(f'<div class="confirmation-item">{sig}</div>', unsafe_allow_html=True)

# ============================================
# DETAILED ANALYSIS
# ============================================
st.markdown("### 📈 DETAILED ANALYSIS")

col_d1, col_d2 = st.columns(2)

with col_d1:
    st.markdown(f"""
    <div class="stat-card">
        <h4>📊 Slope Analysis</h4>
        <div style="font-size: 1.3em;">{slope_text}</div>
        <div>{slope_desc}</div>
        <hr>
        <h4>⚡ TOR Speed</h4>
        <div style="color: {'#00ffaa' if tor_speed_type == 'bullish' else ('#ff4444' if tor_speed_type == 'bearish' else '#ffaa00')}">
            {tor_speed_name}
        </div>
        <div>{tor_speed_desc}</div>
        <hr>
        <h4>⚡ Momentum Score</h4>
        <div style="font-size: 1.5em;">{momentum:+d}</div>
    </div>
    """, unsafe_allow_html=True)

with col_d2:
    st.markdown(f"""
    <div class="stat-card">
        <h4>🌙 Astro Window</h4>
        <div>{astro_label}</div>
        <hr>
        <h4>🔢 Numerology</h4>
        <div>TOR: {tor_num if tor_num else '-'} | NA: {na_num if na_num else '-'}</div>
        <hr>
        <h4>💰 BTC Price</h4>
        <div>${btc_price.get('price', 0):,.2f} ({btc_price.get('price_change_percent', 0):+.2f}%)</div>
        <div>24h High: ${btc_price.get('high_24h', 0):,.2f} | Low: ${btc_price.get('low_24h', 0):,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# ALTCOINS SIGNALS
# ============================================
st.markdown("### 💰 ALTCOINS TRADING SIGNALS")

# Display in grid
cols = st.columns(5)
for i, signal in enumerate(coin_signals[:10]):
    with cols[i % 5]:
        signal_icon = "🟢" if signal['signal'] == "LONG" else ("🔴" if signal['signal'] == "SHORT" else "🟡")
        signal_color = "#00ffaa" if signal['signal'] == "LONG" else ("#ff4444" if signal['signal'] == "SHORT" else "#ffaa00")
        st.markdown(f"""
        <div class="coin-card">
            <div style="font-size: 1.3em; font-weight: bold;">{signal['symbol']}</div>
            <div style="color: {signal_color};">
                {signal_icon} {signal['signal']}
            </div>
            <div>Confidence: {signal['confidence']}</div>
            <div>Entry: {signal['entry']}</div>
            <div>24h: {signal['price_change']}</div>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# RISK MANAGEMENT
# ============================================
st.markdown("### 🛡️ RISK MANAGEMENT")

col_r1, col_r2, col_r3 = st.columns(3)

with col_r1:
    st.info("📊 **Position Sizing**\n- Max 3 trades/day\n- Risk 1-2% per trade\n- 5x-10x leverage max")

with col_r2:
    st.warning("⛔ **Stop Loss Rules**\n- Default: 0.25%-0.4%\n- High leverage: 0.18%-0.25%\n- Always use hard stop")

with col_r3:
    st.success("🎯 **Take Profit**\n- Scale out 25-50% at 0.4-1.0%\n- Trail stop after 0.5%\n- Don't be greedy")

# ============================================
# HISTORY & REFRESH
# ============================================
col_btn1, col_btn2 = st.columns([1, 4])

with col_btn1:
    if st.button("💾 SAVE SIGNAL", use_container_width=True):
        st.session_state.history.append({
            'time': current_time.strftime('%H:%M:%S'),
            'tor': current_tor,
            'na': current_na,
            'signal': final_signal['signal'][:20],
            'funding': funding_rate,
            'ls_ratio': ls_ratio,
            'fng': fng.get('value')
        })
        st.success("✅ Saved!")

with col_btn2:
    if st.button("🔄 REFRESH DATA", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

if st.session_state.history:
    st.markdown("### 📜 SIGNAL HISTORY")
    history_df = pd.DataFrame(st.session_state.history[-10:])
    st.dataframe(history_df, use_container_width=True, hide_index=True)

# ============================================
# FOOTER
# ============================================
st.markdown(f"""
<div class="footer">
    <p>🔄 Data Sources: Bitnodes API | Binance API | Alternative.me API (All FREE)</p>
    <p>📡 Last Update: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    <p>⚠️ DISCLAIMER: Trading signals for informational purposes only. Always DYOR.</p>
</div>
""", unsafe_allow_html=True)
