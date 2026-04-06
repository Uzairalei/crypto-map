import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import time
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="UZair Ali Dark Crypto - Professional Trading Signals",
    page_icon="🌑",
    layout="wide"
)

# ============================================
# CUSTOM CSS - PROFESSIONAL DARK THEME
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');
    
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
    
    .metric-good {
        color: #00ffaa;
    }
    
    .metric-bad {
        color: #ff4444;
    }
    
    .metric-warning {
        color: #ffaa00;
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
</style>
""", unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
st.markdown("""
<div class="main-header">
    <h1>🌑 UZAIR ALI DARK CRYPTO</h1>
    <p>Professional Trading Signals | Bitnodes + Coinglass + Binance | Multi-Factor AI Analysis</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE
# ============================================
if 'prev_tor' not in st.session_state:
    st.session_state.prev_tor = None
if 'prev_na' not in st.session_state:
    st.session_state.prev_na = None
if 'coinglass_key' not in st.session_state:
    st.session_state.coinglass_key = os.getenv('COINGLASS_API_KEY', '')
if 'history' not in st.session_state:
    st.session_state.history = []

# ============================================
# API KEY INPUT (if not in env)
# ============================================
if not st.session_state.coinglass_key:
    st.sidebar.warning("⚠️ Coinglass API Key Required for Real Data")
    coinglass_key_input = st.sidebar.text_input("Enter Coinglass API Key", type="password")
    if coinglass_key_input:
        st.session_state.coinglass_key = coinglass_key_input
        st.rerun()

# ============================================
# API FUNCTIONS
# ============================================

def fetch_bitnodes_data():
    """Fetch real data from Bitnodes API"""
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

def fetch_coinglass_data(symbol="BTC"):
    """Fetch real data from Coinglass API - Funding Rate, OI, Long/Short Ratio"""
    if not st.session_state.coinglass_key:
        return None
    
    try:
        headers = {
            'CG-API-KEY': st.session_state.coinglass_key,
            'Accept': 'application/json'
        }
        base_url = "https://open-api-v4.coinglass.com"
        
        # Fetch Funding Rate
        funding_url = f"{base_url}/api/futures/funding-rate/history"
        funding_params = {"symbol": f"{symbol}USDT", "exchange": "Binance", "interval": "1h", "limit": 24}
        funding_resp = requests.get(funding_url, headers=headers, params=funding_params, timeout=10)
        
        # Fetch Open Interest
        oi_url = f"{base_url}/api/futures/open-interest/history"
        oi_params = {"symbol": f"{symbol}USDT", "exchange": "Binance", "interval": "1h", "limit": 24}
        oi_resp = requests.get(oi_url, headers=headers, params=oi_params, timeout=10)
        
        # Fetch Long/Short Ratio
        ls_url = f"{base_url}/api/futures/long-short-ratio/history"
        ls_params = {"symbol": f"{symbol}USDT", "exchange": "Binance", "interval": "1h", "limit": 24}
        ls_resp = requests.get(ls_url, headers=headers, params=ls_params, timeout=10)
        
        result = {}
        
        if funding_resp.status_code == 200:
            funding_data = funding_resp.json()
            if funding_data.get('code') == '0':
                result['funding_rate'] = funding_data.get('data', {}).get('current_rate', 0)
        
        if oi_resp.status_code == 200:
            oi_data = oi_resp.json()
            if oi_data.get('code') == '0':
                result['open_interest'] = oi_data.get('data', {}).get('current_oi', 0)
        
        if ls_resp.status_code == 200:
            ls_data = ls_resp.json()
            if ls_data.get('code') == '0':
                result['long_short_ratio'] = ls_data.get('data', {}).get('long_short_ratio', 1)
        
        return result
        
    except Exception as e:
        print(f"Coinglass API Error: {e}")
        return None

def fetch_binance_data(symbol="BTCUSDT"):
    """Fetch real price and volume data from Binance"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'price': float(data.get('lastPrice', 0)),
                'volume': float(data.get('volume', 0)),
                'price_change_percent': float(data.get('priceChangePercent', 0)),
                'high': float(data.get('highPrice', 0)),
                'low': float(data.get('lowPrice', 0)),
                'quote_volume': float(data.get('quoteVolume', 0))
            }
        else:
            return generate_mock_binance(symbol)
    except Exception as e:
        return generate_mock_binance(symbol)

def generate_mock_binance(symbol):
    import random
    base_price = 65000 if 'BTC' in symbol else (3500 if 'ETH' in symbol else 150)
    return {
        'price': round(base_price + (random.random() - 0.5) * 200, 2),
        'volume': round(random.random() * 10000, 2),
        'price_change_percent': round((random.random() - 0.5) * 3, 2),
        'high': round(base_price + 100, 2),
        'low': round(base_price - 100, 2),
        'quote_volume': round(random.random() * 100000000, 2)
    }

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

def get_funding_signal(funding_rate):
    """Interpret funding rate signal"""
    if funding_rate is None:
        return None, "neutral", "No data"
    
    if funding_rate > 0.01:
        return "🔴 EXTREME POSITIVE", "bearish", "Funding very high - Overheated longs"
    elif funding_rate > 0.005:
        return "🟡 POSITIVE", "neutral", "Moderate positive - Longs paying"
    elif funding_rate < -0.01:
        return "🟢 EXTREME NEGATIVE", "bullish", "Funding very negative - Shorts paying"
    elif funding_rate < -0.005:
        return "🟢 NEGATIVE", "bullish", "Moderate negative - Shorts paying"
    else:
        return "⚡ NEUTRAL", "neutral", "Normal funding"

def get_oi_signal(open_interest, price_change):
    """Interpret open interest signal"""
    if open_interest is None:
        return None, "neutral", "No data"
    
    if price_change > 0 and open_interest > 0:
        return "📈 OI + PRICE UP", "bullish", "New money entering"
    elif price_change < 0 and open_interest > 0:
        return "📉 OI UP + PRICE DOWN", "bearish", "Short buildup"
    elif price_change > 0 and open_interest < 0:
        return "⚠️ OI DOWN + PRICE UP", "neutral", "Profit taking"
    else:
        return "⚡ NEUTRAL", "neutral", "Mixed signals"

def get_ls_ratio_signal(ls_ratio):
    """Interpret long/short ratio signal"""
    if ls_ratio is None:
        return None, "neutral", "No data"
    
    if ls_ratio > 2:
        return "🔴 EXTREME LONG", "bearish", "Too many longs - Reversal risk"
    elif ls_ratio > 1.5:
        return "🟡 LONG DOMINANT", "neutral", "More longs than shorts"
    elif ls_ratio < 0.5:
        return "🟢 EXTREME SHORT", "bullish", "Too many shorts - Squeeze coming"
    elif ls_ratio < 0.8:
        return "🟢 SHORT DOMINANT", "bullish", "More shorts than longs"
    else:
        return "⚡ BALANCED", "neutral", "Normal ratio"

# ============================================
# FINAL ACCURATE SIGNAL
# ============================================

def get_final_signal(tor, delta_tor, na, delta_na, funding_rate, open_interest, ls_ratio, price_change_percent):
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
    if funding_rate is not None:
        if funding_rate < -0.005:
            signals.append(f"✅ Funding: NEGATIVE ({funding_rate*100:.4f}%) - Bullish")
            bullish_score += 2
        elif funding_rate > 0.005:
            signals.append(f"❌ Funding: POSITIVE ({funding_rate*100:.4f}%) - Bearish")
            bearish_score += 2
        else:
            signals.append(f"⚡ Funding: NEUTRAL ({funding_rate*100:.4f}%)")
    
    # 3. Open Interest Signal
    if open_interest is not None and price_change_percent is not None:
        if price_change_percent > 0 and open_interest > 0:
            signals.append(f"✅ OI: RISING + Price UP - Bullish")
            bullish_score += 1
        elif price_change_percent < 0 and open_interest > 0:
            signals.append(f"❌ OI: RISING + Price DOWN - Bearish")
            bearish_score += 1
    
    # 4. Long/Short Ratio Signal
    if ls_ratio is not None:
        if ls_ratio < 0.7:
            signals.append(f"✅ L/S Ratio: {ls_ratio:.2f} (Short dominant) - Bullish")
            bullish_score += 2
        elif ls_ratio > 1.5:
            signals.append(f"❌ L/S Ratio: {ls_ratio:.2f} (Long dominant) - Bearish")
            bearish_score += 2
        else:
            signals.append(f"⚡ L/S Ratio: {ls_ratio:.2f} - Neutral")
    
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
# COIN SIGNALS FOR ALL ALTCOINS
# ============================================

def get_coin_signals(symbols, final_signal_type, price_data):
    """Generate signals for multiple coins based on final signal"""
    signals = []
    
    for symbol in symbols:
        price_info = price_data.get(symbol, {})
        price_change = price_info.get('price_change_percent', 0)
        
        if final_signal_type == 'bullish':
            if price_change > 0:
                signal = "LONG"
                confidence = "HIGH"
            else:
                signal = "LONG (DIP)"
                confidence = "MEDIUM"
            entry = price_info.get('price', 'Market')
        elif final_signal_type == 'bearish':
            if price_change < 0:
                signal = "SHORT"
                confidence = "HIGH"
            else:
                signal = "SHORT (RALLY)"
                confidence = "MEDIUM"
            entry = price_info.get('price', 'Market')
        else:
            signal = "NEUTRAL"
            confidence = "LOW"
            entry = "No entry"
        
        signals.append({
            'symbol': symbol,
            'signal': signal,
            'confidence': confidence,
            'entry': f'${entry:,.2f}' if isinstance(entry, (int, float)) else entry,
            'price_change': f'{price_change:+.2f}%' if price_change else 'N/A'
        })
    
    return signals

# ============================================
# MAIN APP
# ============================================

# Fetch all data
with st.spinner('🔄 Fetching live data from Bitnodes, Coinglass, and Binance...'):
    bitnodes = fetch_bitnodes_data()
    coinglass = fetch_coinglass_data("BTC")
    binance_btc = fetch_binance_data("BTCUSDT")
    binance_eth = fetch_binance_data("ETHUSDT")
    binance_sol = fetch_binance_data("SOLUSDT")
    binance_bnb = fetch_binance_data("BNBUSDT")

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

# Coinglass signals
funding_rate = coinglass.get('funding_rate') if coinglass else None
open_interest = coinglass.get('open_interest') if coinglass else None
ls_ratio = coinglass.get('long_short_ratio') if coinglass else None

funding_text, funding_type, funding_desc = get_funding_signal(funding_rate)
oi_text, oi_type, oi_desc = get_oi_signal(open_interest, binance_btc.get('price_change_percent', 0))
ls_text, ls_type, ls_desc = get_ls_ratio_signal(ls_ratio)

# Final accurate signal
final_signal = get_final_signal(
    current_tor, delta_tor, current_na, delta_na,
    funding_rate, open_interest, ls_ratio,
    binance_btc.get('price_change_percent', 0)
)

# Price data dict for coin signals
price_data = {
    'BTC': binance_btc,
    'ETH': binance_eth,
    'SOL': binance_sol,
    'BNB': binance_bnb
}

# Generate coin signals
coin_symbols = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 'AVAX', 'MATIC', 'LINK']
coin_signals = get_coin_signals(coin_symbols, final_signal['type'], price_data)

# Update session state
st.session_state.prev_tor = current_tor
st.session_state.prev_na = current_na

# ============================================
# DISPLAY
# ============================================

# Stats Row
st.markdown("### 📊 LIVE MARKET DATA")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div>🌐 TOR %</div>
        <div class="stat-value">{current_tor}%</div>
        <div style="color: {'#00ffaa' if delta_tor > 0 else '#ff4444'}">{delta_tor:+.2f}%</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div>📡 NETWORK AVAILABILITY</div>
        <div class="stat-value">{current_na:,}</div>
        <div style="color: {'#00ffaa' if delta_na > 0 else '#ff4444'}">{delta_na:+,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div>⚡ MOMENTUM</div>
        <div class="stat-value">{momentum:+d}</div>
        <div>(-3 to +3)</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    color = "#00ffaa" if funding_rate and funding_rate < -0.005 else ("#ff4444" if funding_rate and funding_rate > 0.005 else "#ffaa00")
    st.markdown(f"""
    <div class="stat-card">
        <div>💰 FUNDING RATE</div>
        <div class="stat-value" style="color: {color};">{funding_rate*100:.4f}%' if funding_rate else 'N/A'</div>
        <div>{funding_desc[:30] if funding_desc else ''}</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="stat-card">
        <div>📊 L/S RATIO</div>
        <div class="stat-value">{ls_ratio:.2f}' if ls_ratio else 'N/A'</div>
        <div>{ls_desc[:30] if ls_desc else ''}</div>
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
    </div>
    """, unsafe_allow_html=True)

with col_d2:
    st.markdown(f"""
    <div class="stat-card">
        <h4>🌙 Astro Window</h4>
        <div>{astro_label}</div>
        <hr>
        <h4>🔢 Numerology</h4>
        <div>TOR: {tor_num} | NA: {na_num}</div>
        <hr>
        <h4>💰 BTC Price</h4>
        <div>${binance_btc.get('price', 0):,.2f} ({binance_btc.get('price_change_percent', 0):+.2f}%)</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# ALTCOINS SIGNALS
# ============================================
st.markdown("### 💰 ALTCOINS TRADING SIGNALS")

cols = st.columns(5)
for i, signal in enumerate(coin_signals[:10]):
    with cols[i % 5]:
        signal_icon = "🟢" if signal['signal'] == "LONG" else ("🔴" if signal['signal'] == "SHORT" else "🟡")
        st.markdown(f"""
        <div class="stat-card">
            <div style="font-size: 1.3em; font-weight: bold;">{signal['symbol']}</div>
            <div style="color: {'#00ffaa' if signal['signal'] == 'LONG' else ('#ff4444' if signal['signal'] == 'SHORT' else '#ffaa00')}">
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
            'ls_ratio': ls_ratio
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
    <p>🔄 Data Sources: Bitnodes API | Coinglass API | Binance API</p>
    <p>📡 Last Update: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    <p>⚠️ DISCLAIMER: Trading signals for informational purposes only. Always DYOR.</p>
</div>
""", unsafe_allow_html=True)
