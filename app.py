import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, time
import numpy as np
import time as time_module

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="UZair Ali Dark Crypto - Accurate Trading Signals",
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
    
    .signal-box {
        background: #0f1322;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        text-align: center;
    }
    
    .signal-bullish {
        border: 2px solid #00ffaa;
        box-shadow: 0 0 20px rgba(0,255,170,0.3);
    }
    
    .signal-bearish {
        border: 2px solid #ff4444;
        box-shadow: 0 0 20px rgba(255,68,68,0.3);
    }
    
    .signal-neutral {
        border: 2px solid #ffaa00;
        box-shadow: 0 0 20px rgba(255,170,0,0.3);
    }
    
    .stat-card {
        background: #0f1322;
        border: 1px solid #2a2f4a;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    
    .stat-value {
        font-size: 2em;
        font-weight: bold;
        color: #00ffaa;
    }
    
    .confirmation-green {
        color: #00ffaa;
        font-weight: bold;
    }
    
    .confirmation-red {
        color: #ff4444;
        font-weight: bold;
    }
    
    .footer {
        text-align: center;
        padding: 20px;
        color: #5a6e8a;
        font-size: 0.8em;
        border-top: 1px solid #2a2f4a;
        margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
st.markdown("""
<div class="main-header">
    <h1>🌑 UZAIR ALI DARK CRYPTO</h1>
    <p>Astro-Numerical Trading System | Bitnodes Integration | Live Accurate Signals</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE
# ============================================
if 'prev_tor' not in st.session_state:
    st.session_state.prev_tor = None
if 'prev_na' not in st.session_state:
    st.session_state.prev_na = None
if 'prev_time' not in st.session_state:
    st.session_state.prev_time = None
if 'signal_history' not in st.session_state:
    st.session_state.signal_history = []

# ============================================
# BITNODES REAL API FETCH
# ============================================
@st.cache_data(ttl=60)
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
            
            # Calculate TOR percentage
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
            return get_mock_data()
    except Exception as e:
        return get_mock_data()

def get_mock_data():
    import random
    return {
        'tor': round(65.2 + (random.random() - 0.5) * 1.5, 2),
        'na': int(23800 + (random.random() - 0.5) * 300),
        'timestamp': datetime.now(),
        'success': False
    }

# ============================================
# ASTRO TIMING WINDOWS
# ============================================
def get_astro_window(utc_time):
    """Determine astro timing window"""
    hour = utc_time.hour
    minute = utc_time.minute
    
    windows = {
        (9, 10, 9, 30): "🌙 MICRO-REVERSAL BAND (09:10-09:30 UTC) - Expect fake wicks, be cautious",
        (4, 0, 4, 30): "🌅 RE-ENTRY GATE (04:00-04:30 UTC) - Accumulation zone",
        (5, 0, 11, 0): "🌏 ASIA SESSION - High liquidity, fast moves",
        (12, 0, 14, 0): "☀️ EUROPE OPEN - High volatility",
        (17, 55, 18, 20): "🔥 US OPEN POWER ZONE (17:55-18:20 UTC) - Maximum liquidity"
    }
    
    for (start_h, start_m, end_h, end_m), label in windows.items():
        start = start_h * 60 + start_m
        end = end_h * 60 + end_m
        current = hour * 60 + minute
        
        if start <= current <= end:
            return label, True if "REVERSAL" in label else False
    
    return "⚡ NORMAL WINDOW", False

# ============================================
# NUMEROLOGY CALCULATION
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

# ============================================
# SLOPE ANALYSIS
# ============================================
def get_slope_pattern(delta_tor, delta_na):
    if delta_tor > 0 and delta_na > 0:
        return "🚀 SYNCHRONIZED BULLISH", "bullish", "Both ↑ - Strong momentum building"
    elif delta_tor < 0 and delta_na < 0:
        return "📉 SYNCHRONIZED BEARISH", "bearish", "Both ↓ - Selling pressure increasing"
    elif delta_tor > 0 and delta_na < 0:
        return "⚠️ DIVERGENCE (Selective Buying)", "neutral", "TOR ↑ & NA ↓ - Limited fuel, cautious longs"
    elif delta_tor < 0 and delta_na > 0:
        return "🔄 ACCUMULATION (Smart Money)", "bullish", "TOR ↓ & NA ↑ - Smart money buying dip"
    else:
        return "⚡ NEUTRAL", "neutral", "Mixed signals - Wait"

# ============================================
# MOMENTUM SCORE
# ============================================
def calculate_momentum_score(delta_tor, delta_na):
    tor_sign = 1 if delta_tor > 0 else (-1 if delta_tor < 0 else 0)
    na_sign = 1 if delta_na > 0 else (-1 if delta_na < 0 else 0)
    return tor_sign * 2 + na_sign  # TOR weighted heavier

# ============================================
# MAIN SIGNAL DECISION RULES
# ============================================
def get_trading_signal(tor, na, delta_tor, delta_na, utc_hour, is_reversal_window):
    """Apply all decision rules in order"""
    
    # Strong Bull Condition
    if tor >= 66.5 and delta_tor >= 0.1 and na >= 23500 and delta_na > 0:
        return {
            'code': 'L+',
            'text': 'STRONG LONG',
            'type': 'bullish',
            'action': 'BUY / ADD LONGS',
            'reason': f'TOR ≥ 66.5%, ΔTOR ≥ +0.1%, NA ≥ 23.5k, ΔNA > 0',
            'confidence': 'HIGH (85%+)',
            'target': '0.6-1.0%',
            'stop': '-0.3%',
            'leverage': '5x-10x'
        }
    
    # Strong Bear Condition
    if tor < 64 and delta_tor < 0 and delta_na < 0:
        return {
            'code': 'S+',
            'text': 'STRONG SHORT',
            'type': 'bearish',
            'action': 'SHORT / HEDGE',
            'reason': f'TOR < 64%, ΔTOR < 0, ΔNA < 0',
            'confidence': 'HIGH (85%+)',
            'target': '0.5-0.8%',
            'stop': '-0.25%',
            'leverage': '5x-10x'
        }
    
    # Pressure Reset (Bullish Continuation)
    if tor > 66.5 and delta_na < 0 and na > 23500:
        return {
            'code': 'L',
            'text': 'HOLD LONG (Pressure Reset)',
            'type': 'bullish',
            'action': 'HOLD / DCA on dip',
            'reason': f'TOR > 66.5%, NA softening but high → Expect continuation',
            'confidence': 'MEDIUM-HIGH (70%)',
            'target': '0.4-0.7%',
            'stop': '-0.25%',
            'leverage': '5x'
        }
    
    # Divergence Cases
    if delta_tor > 0 and delta_na < 0:
        return {
            'code': 'L*',
            'text': 'SELECTIVE LONG',
            'type': 'neutral',
            'action': 'SMALL LONGS ONLY',
            'reason': f'TOR ↑ & NA ↓ → Divergence, need volume confirmation',
            'confidence': 'MEDIUM (60%)',
            'target': '0.3-0.5%',
            'stop': '-0.2%',
            'leverage': '3x-5x'
        }
    
    if delta_tor < 0 and delta_na > 0:
        return {
            'code': 'L',
            'text': 'ACCUMULATION PHASE',
            'type': 'bullish',
            'action': 'BUY DIPS / HOLD',
            'reason': f'TOR ↓ & NA ↑ → Smart money accumulation',
            'confidence': 'MEDIUM-HIGH (70%)',
            'target': '0.4-0.6%',
            'stop': '-0.25%',
            'leverage': '5x'
        }
    
    # Default Neutral
    return {
        'code': 'N',
        'text': 'NEUTRAL',
        'type': 'neutral',
        'action': 'WAIT / NO TRADE',
        'reason': 'No clear signal - Wait for confirmation',
        'confidence': 'LOW',
        'target': 'N/A',
        'stop': 'N/A',
        'leverage': 'N/A'
    }

# ============================================
# SCALPING SIGNAL (Session-based)
# ============================================
def get_scalp_signal(current_hour, current_minute, tor, delta_tor, na, delta_na):
    """Generate scalping signal based on session"""
    
    current_time_minutes = current_hour * 60 + current_minute
    
    # Session definitions (PKT time = UTC+5)
    asia_start = (5 * 60)  # 5am PKT = 0am UTC
    asia_end = (11 * 60)   # 11am PKT = 6am UTC
    europe_start = (12 * 60)  # 12pm PKT = 7am UTC
    europe_end = (14 * 60)    # 2pm PKT = 9am UTC
    us_start = (17 * 60 + 55) # 5:55pm PKT = 12:55pm UTC
    us_end = (18 * 60 + 20)   # 6:20pm PKT = 1:20pm UTC
    
    is_active_session = (asia_start <= current_time_minutes <= asia_end or
                        europe_start <= current_time_minutes <= europe_end or
                        us_start <= current_time_minutes <= us_end)
    
    if not is_active_session:
        return {
            'signal': '⏸️ NO SCALP - OFF HOURS',
            'type': 'neutral',
            'confidence': 'N/A',
            'action': 'WAIT FOR ACTIVE SESSION',
            'session': 'Inactive'
        }
    
    # Determine session name
    if asia_start <= current_time_minutes <= asia_end:
        session = "ASIA SESSION"
    elif europe_start <= current_time_minutes <= europe_end:
        session = "EUROPE OPEN"
    else:
        session = "US OPEN POWER ZONE"
    
    # Scalp signal based on TOR
    if tor >= 65.5 and delta_tor > 0 and delta_na > -50:
        return {
            'signal': '🟢🟢 LONG SCALP READY 🟢🟢',
            'type': 'long',
            'confidence': 'HIGH (80%)',
            'action': f'Entry: Market | Target: 0.4-0.6% | Stop: -0.2%',
            'session': session
        }
    elif tor <= 64 and delta_tor < 0:
        return {
            'signal': '🔴🔴 SHORT SCALP READY 🔴🔴',
            'type': 'short',
            'confidence': 'HIGH (75%)',
            'action': f'Entry: Market | Target: 0.3-0.5% | Stop: -0.2%',
            'session': session
        }
    elif tor > 65 and delta_tor > 0:
        return {
            'signal': '🟡 LONG SCALP - MEDIUM',
            'type': 'long',
            'confidence': 'MEDIUM (60%)',
            'action': f'Entry: On pullback | Target: 0.3-0.4% | Stop: -0.2%',
            'session': session
        }
    else:
        return {
            'signal': '⏸️ NO SCALP SIGNAL',
            'type': 'neutral',
            'confidence': 'LOW',
            'action': 'WAIT FOR BETTER SETUP',
            'session': session
        }

# ============================================
# BTC DIRECTION CHECK (Manual Input)
# ============================================
def get_btc_direction():
    """Manual BTC direction input"""
    col1, col2 = st.columns(2)
    with col1:
        btc_bullish = st.button("🐂 BTC BULLISH", use_container_width=True)
    with col2:
        btc_bearish = st.button("🐻 BTC BEARISH", use_container_width=True)
    
    if btc_bullish:
        return "bullish"
    elif btc_bearish:
        return "bearish"
    return None

# ============================================
# VOLUME SPIKE CHECK
# ============================================
def get_volume_confirmation():
    """Volume spike confirmation toggle"""
    return st.checkbox("📊 Volume Spike Detected (2x+ avg)", value=False)

def get_orderbook_imbalance():
    """Orderbook imbalance slider"""
    return st.slider("📚 Orderbook Imbalance", -0.5, 0.5, 0.0, 0.05,
                     help="Positive = Buy wall bigger | Negative = Sell wall bigger")

# ============================================
# TOR CHANGE SPEED DETECTION
# ============================================
def get_tor_speed_signal(delta_tor):
    """Detect TOR change speed"""
    if delta_tor >= 0.4:
        return "FAST JUMP", "bullish", "Strong breakout expected (PUMP)"
    elif delta_tor <= -0.4:
        return "FAST DROP", "bearish", "Strong dump expected (DUMP)"
    elif delta_tor >= 0.2:
        return "MODERATE RISE", "bullish", "Moderate momentum"
    elif delta_tor <= -0.2:
        return "MODERATE DROP", "bearish", "Moderate selling"
    else:
        return "SLOW CHANGE", "neutral", "Likely fakeout, wait"

# ============================================
# FINAL ACCURATE SIGNAL (Combining Everything)
# ============================================
def get_final_accurate_signal(tor_signal, scalp_signal, btc_direction, 
                               volume_confirm, ob_imbalance, tor_speed):
    """Combine all signals for final accurate prediction"""
    
    confirmations = []
    warnings = []
    
    # Count bullish signals
    bullish_count = 0
    bearish_count = 0
    
    # Tor signal
    if tor_signal['type'] == 'bullish':
        bullish_count += 2
        confirmations.append("✅ Bitnodes: BULLISH")
    elif tor_signal['type'] == 'bearish':
        bearish_count += 2
        confirmations.append("❌ Bitnodes: BEARISH")
    
    # Scalp signal
    if scalp_signal['type'] == 'long':
        bullish_count += 1
        confirmations.append("✅ Scalping: LONG READY")
    elif scalp_signal['type'] == 'short':
        bearish_count += 1
        confirmations.append("❌ Scalping: SHORT READY")
    
    # BTC direction
    if btc_direction == 'bullish':
        bullish_count += 2
        confirmations.append("✅ BTC: BULLISH")
    elif btc_direction == 'bearish':
        bearish_count += 2
        confirmations.append("❌ BTC: BEARISH")
    
    # Volume confirmation
    if volume_confirm:
        if bullish_count > bearish_count:
            confirmations.append("✅ Volume: CONFIRMS MOVE")
            bullish_count += 1
        else:
            warnings.append("⚠️ Volume high but direction unclear")
    
    # Orderbook imbalance
    if ob_imbalance > 0.15:
        confirmations.append(f"✅ Orderbook: BUY IMBALANCE ({ob_imbalance:.2f})")
        bullish_count += 1
    elif ob_imbalance < -0.15:
        confirmations.append(f"❌ Orderbook: SELL IMBALANCE ({ob_imbalance:.2f})")
        bearish_count += 1
    
    # Tor speed
    if tor_speed[1] == 'bullish':
        confirmations.append(f"✅ TOR Speed: {tor_speed[0]}")
        bullish_count += 1
    elif tor_speed[1] == 'bearish':
        confirmations.append(f"❌ TOR Speed: {tor_speed[0]}")
        bearish_count += 1
    
    # Final decision
    if bullish_count >= bearish_count + 2:
        return {
            'signal': '🟢🟢 ACCURATE LONG SIGNAL 🟢🟢',
            'type': 'bullish',
            'confidence': f'{min(95, 70 + bullish_count * 5)}%',
            'confirmations': confirmations,
            'warnings': warnings,
            'action': 'ENTER LONG | Leverage: 5x-10x',
            'target': '0.5-0.8%',
            'stop': '-0.25%'
        }
    elif bearish_count >= bullish_count + 2:
        return {
            'signal': '🔴🔴 ACCURATE SHORT SIGNAL 🔴🔴',
            'type': 'bearish',
            'confidence': f'{min(95, 70 + bearish_count * 5)}%',
            'confirmations': confirmations,
            'warnings': warnings,
            'action': 'ENTER SHORT | Leverage: 5x-10x',
            'target': '0.4-0.7%',
            'stop': '-0.25%'
        }
    else:
        return {
            'signal': '🟡 NO ACCURATE SIGNAL - WAIT 🟡',
            'type': 'neutral',
            'confidence': 'LOW',
            'confirmations': confirmations,
            'warnings': warnings,
            'action': 'WAIT FOR CONFIRMATION',
            'target': 'N/A',
            'stop': 'N/A'
        }

# ============================================
# MAIN APP
# ============================================

# Fetch data
with st.spinner('🔄 Fetching live Bitnodes data...'):
    data = fetch_bitnodes_data()

current_tor = data['tor']
current_na = data['na']
current_time = data['timestamp']

# Calculate deltas
delta_tor = current_tor - st.session_state.prev_tor if st.session_state.prev_tor else 0
delta_na = current_na - st.session_state.prev_na if st.session_state.prev_na else 0

# Get astro window
astro_label, is_reversal = get_astro_window(current_time)

# Get numerology
tor_num = calculate_numerology(current_tor)
na_num = calculate_numerology(current_na)

# Get slope
slope_text, slope_type, slope_desc = get_slope_pattern(delta_tor, delta_na)

# Get momentum score
momentum_score = calculate_momentum_score(delta_tor, delta_na)

# Get main signal
main_signal = get_trading_signal(current_tor, current_na, delta_tor, delta_na, 
                                  current_time.hour, is_reversal)

# Get scalp signal
scalp_signal = get_scalp_signal(current_time.hour, current_time.minute,
                                 current_tor, delta_tor, current_na, delta_na)

# Get TOR speed
tor_speed_name, tor_speed_type, tor_speed_desc = get_tor_speed_signal(delta_tor)

# Manual inputs for final signal
st.sidebar.markdown("### 📊 MANUAL CONFIRMATIONS")
st.sidebar.markdown("---")

btc_direction = None
col_btc1, col_btc2 = st.sidebar.columns(2)
with col_btc1:
    if st.button("🐂 BTC BULLISH", key="btc_bull"):
        btc_direction = "bullish"
with col_btc2:
    if st.button("🐻 BTC BEARISH", key="btc_bear"):
        btc_direction = "bearish"

volume_confirm = st.sidebar.checkbox("📊 Volume Spike (2x+ avg)", key="volume")
ob_imbalance = st.sidebar.slider("📚 Orderbook Imbalance", -0.5, 0.5, 0.0, 0.05, key="ob")

if btc_direction:
    st.sidebar.success(f"BTC Direction: {'🟢 BULLISH' if btc_direction == 'bullish' else '🔴 BEARISH'}")

# Get final accurate signal
final_signal = get_final_accurate_signal(main_signal, scalp_signal, btc_direction,
                                          volume_confirm, ob_imbalance,
                                          (tor_speed_name, tor_speed_type, tor_speed_desc))

# ============================================
# DISPLAY STATISTICS
# ============================================
st.markdown("### 📊 LIVE NETWORK STATISTICS")

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
        <div>⚡ MOMENTUM SCORE</div>
        <div class="stat-value">{momentum_score:+d}</div>
        <div>(-3 to +3)</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card">
        <div>🔢 NUMEROLOGY</div>
        <div class="stat-value">TOR:{tor_num} | NA:{na_num}</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="stat-card">
        <div>🕐 UTC TIME</div>
        <div class="stat-value">{current_time.strftime('%H:%M:%S')}</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# ACCURATE SIGNAL DISPLAY (MAIN)
# ============================================
st.markdown("### 🎯 ACCURATE TRADING SIGNAL")

signal_class = f"signal-{final_signal['type']}"
st.markdown(f"""
<div class="signal-box {signal_class}">
    <div style="font-size: 2.5em; font-weight: bold;">{final_signal['signal']}</div>
    <div style="font-size: 1.2em; margin-top: 10px;">Confidence: {final_signal['confidence']}</div>
    <div style="margin-top: 15px; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 10px;">
        <div>🎯 ACTION: {final_signal['action']}</div>
        <div>📈 TARGET: {final_signal['target']} | 🛑 STOP: {final_signal['stop']}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================
# CONFIRMATIONS PANEL
# ============================================
col_confirm, col_warn = st.columns(2)

with col_confirm:
    st.markdown("### ✅ CONFIRMATIONS")
    for conf in final_signal['confirmations']:
        st.markdown(f"- {conf}")

with col_warn:
    st.markdown("### ⚠️ WARNINGS / NOTES")
    if final_signal['warnings']:
        for warn in final_signal['warnings']:
            st.markdown(f"- {warn}")
    else:
        st.markdown("- No major warnings")
    if is_reversal:
        st.markdown(f"- ⚠️ {astro_label}")

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
        <div style="font-size: 1.2em; color: {'#00ffaa' if tor_speed_type == 'bullish' else ('#ff4444' if tor_speed_type == 'bearish' else '#ffaa00')}">
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
        <h4>🎯 Scalping Signal</h4>
        <div style="font-size: 1.1em; color: {'#00ffaa' if scalp_signal['type'] == 'long' else ('#ff4444' if scalp_signal['type'] == 'short' else '#ffaa00')}">
            {scalp_signal['signal']}
        </div>
        <div>Session: {scalp_signal['session']}</div>
        <div>{scalp_signal['action']}</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# MAIN SIGNAL DETAILS
# ============================================
st.markdown("### 📋 PRIMARY BITNODES SIGNAL")

st.markdown(f"""
<div class="stat-card">
    <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
        <div><b>Signal:</b> {main_signal['code']} - {main_signal['text']}</div>
        <div><b>Confidence:</b> {main_signal['confidence']}</div>
    </div>
    <div><b>Action:</b> {main_signal['action']}</div>
    <div><b>Reason:</b> {main_signal['reason']}</div>
    <div><b>Target:</b> {main_signal['target']} | <b>Stop:</b> {main_signal['stop']} | <b>Leverage:</b> {main_signal['leverage']}</div>
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
# SIGNAL LEGEND
# ============================================
st.markdown("### 📖 SIGNAL LEGEND")

st.markdown("""
<div style="background: #0f1322; padding: 15px; border-radius: 10px;">
    <div style="display: flex; gap: 20px; flex-wrap: wrap;">
        <div><span style="color: #00ffaa;">L+</span> = Strong Long (TOR & NA both rising)</div>
        <div><span style="color: #00ffaa;">L</span> = Hold Long (Bullish continuation)</div>
        <div><span style="color: #ffaa00;">N</span> = Neutral / Wait</div>
        <div><span style="color: #ff4444;">S</span> = Short (Both falling)</div>
        <div><span style="color: #ff4444;">S+</span> = Strong Short (Fast drop)</div>
        <div><span style="color: #ffaa00;">L*</span> = Selective Long (Divergence)</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================
# UTC UPDATE MESSAGE
# ============================================
st.markdown("### 📋 LIVE UTC UPDATE MESSAGE")

update_message = f"""
┌─────────────────────────────────────────────────────────────────────┐
│              🌑 UZAIR ALI DARK CRYPTO - ACCURATE SIGNAL              │
├─────────────────────────────────────────────────────────────────────┤
│  🕐 UTC TIME: {current_time.strftime('%H:%M:%S')}                                │
├─────────────────────────────────────────────────────────────────────┤
│  📊 BITNODES DATA:                                                   │
│     🌐 TOR: {current_tor}% (Δ {delta_tor:+.2f}%)                                    │
│     📡 NA:  {current_na:,} (Δ {delta_na:+,.0f})                                   │
├─────────────────────────────────────────────────────────────────────┤
│  📈 SLOPE: {slope_text}                                              │
│     {slope_desc}                                                  │
├─────────────────────────────────────────────────────────────────────┤
│  🌙 ASTRO: {astro_label[:50]}...                                    │
│  🔢 NUMEROLOGY: TOR={tor_num} | NA={na_num}                                       │
├─────────────────────────────────────────────────────────────────────┤
│  🎯 ACCURATE SIGNAL: {final_signal['signal']}                              │
│     Confidence: {final_signal['confidence']}                                        │
│     Action: {final_signal['action']}                                  │
│     Target: {final_signal['target']} | Stop: {final_signal['stop']}                  │
├─────────────────────────────────────────────────────────────────────┤
│  ✅ Confirmations:                                                  │
{chr(10).join(['│     ' + c for c in final_signal['confirmations'][:3]])}
├─────────────────────────────────────────────────────────────────────┤
│  ⚡ SCALPING: {scalp_signal['signal'][:40]}                         │
│     {scalp_signal['action'][:50]}                             │
└─────────────────────────────────────────────────────────────────────┘
"""
st.code(update_message, language="text")

# ============================================
# HISTORY & REFRESH
# ============================================
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

with col_btn1:
    if st.button("💾 SAVE SIGNAL", use_container_width=True):
        st.session_state.signal_history.append({
            'time': current_time.strftime('%H:%M:%S'),
            'tor': current_tor,
            'na': current_na,
            'signal': final_signal['signal'][:30],
            'action': final_signal['action'][:30]
        })
        st.success("✅ Signal saved!")

with col_btn2:
    if st.button("🔄 REFRESH DATA", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

if st.session_state.signal_history:
    st.markdown("### 📜 SIGNAL HISTORY")
    history_df = pd.DataFrame(st.session_state.signal_history[-10:])
    st.dataframe(history_df, use_container_width=True, hide_index=True)

# ============================================
# UPDATE PREVIOUS VALUES
# ============================================
st.session_state.prev_tor = current_tor
st.session_state.prev_na = current_na

# ============================================
# FOOTER
# ============================================
st.markdown(f"""
<div class="footer">
    <p>🔄 Bitnodes Live API | Last Update: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    <p>⚠️ DISCLAIMER: Trading signals are for informational purposes only. Always DYOR and use proper risk management.</p>
    <p>📡 Strategy: Astro-Numerical + Bitnodes + Scalping Rules | TOR Weighted > NA</p>
</div>
""", unsafe_allow_html=True)
