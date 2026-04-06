import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import time

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="UZair Ali Dark Crypto - Scalping Strategy",
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
        border-bottom: 2px solid #00ffaa;
        margin-bottom: 20px;
    }
    
    .main-header h1 {
        font-family: 'Orbitron', monospace;
        color: #00ffaa;
        font-size: 2.5em;
        text-shadow: 0 0 15px #00ffaa;
    }
    
    .signal-box {
        background: #0f1322;
        border-radius: 15px;
        padding: 25px;
        margin: 15px 0;
        text-align: center;
    }
    
    .signal-long {
        border: 2px solid #00ffaa;
        box-shadow: 0 0 30px rgba(0,255,170,0.3);
    }
    
    .signal-short {
        border: 2px solid #ff4444;
        box-shadow: 0 0 30px rgba(255,68,68,0.3);
    }
    
    .signal-neutral {
        border: 2px solid #ffaa00;
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
    
    .session-active {
        color: #00ffaa;
        font-weight: bold;
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .confirmation-item {
        padding: 10px;
        margin: 8px 0;
        border-left: 3px solid #00ffaa;
        background: rgba(0,255,170,0.05);
        border-radius: 5px;
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
    <p>Daily Scalping Strategy | 90% Discipline | Session-Based Trading</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE
# ============================================
if 'btc_direction' not in st.session_state:
    st.session_state.btc_direction = None
if 'selected_coins' not in st.session_state:
    st.session_state.selected_coins = []
if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []

# ============================================
# CHECK TRADING SESSION
# ============================================
def get_current_session():
    """Check which trading session is active (PKT Time = UTC+5)"""
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    current_time_minutes = current_hour * 60 + current_minute
    
    # Session definitions (PKT time)
    asia_start = 5 * 60      # 5:00 AM
    asia_end = 11 * 60       # 11:00 AM
    
    europe_start = 12 * 60   # 12:00 PM
    europe_end = 14 * 60     # 2:00 PM
    
    us_start = 17 * 60 + 55  # 5:55 PM
    us_end = 18 * 60 + 20    # 6:20 PM
    
    if asia_start <= current_time_minutes <= asia_end:
        return "ASIA SESSION", True, "5:00 AM - 11:00 AM PKT"
    elif europe_start <= current_time_minutes <= europe_end:
        return "EUROPE OPEN", True, "12:00 PM - 2:00 PM PKT"
    elif us_start <= current_time_minutes <= us_end:
        return "US OPEN POWER ZONE", True, "5:55 PM - 6:20 PM PKT"
    else:
        return "OFF HOURS", False, "No active session - Wait for next session"

# ============================================
# BITNODES API (Simple TOR + NA)
# ============================================
@st.cache_data(ttl=60)
def fetch_bitnodes():
    """Simple Bitnodes data fetch"""
    try:
        url = "https://bitnodes.io/api/v1/snapshots/latest/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            total_nodes = data.get('total_nodes', 0)
            
            # Count TOR nodes
            tor_count = 0
            for node_addr in data.get('nodes', {}).keys():
                if '.onion' in node_addr.lower():
                    tor_count += 1
            
            tor_percentage = (tor_count / total_nodes * 100) if total_nodes > 0 else 0
            
            return {
                'tor': round(tor_percentage, 2),
                'na': total_nodes,
                'success': True
            }
    except:
        pass
    
    # Fallback
    return {'tor': 65.2, 'na': 23800, 'success': False}

# ============================================
# SCALPING SIGNAL GENERATOR (Sirf Aapki Strategy)
# ============================================
def generate_scalp_signal(btc_direction, volume_spike, ob_imbalance, tor, na):
    """
    Generate signal based on:
    1. BTC direction (bullish/bearish)
    2. Volume spike (2x+)
    3. Orderbook imbalance (>0.15 or <-0.15)
    4. TOR % (extra filter)
    """
    
    confirmations = []
    is_bullish = False
    is_bearish = False
    
    # Check 1: BTC Direction (Primary Filter)
    if btc_direction == "bullish":
        confirmations.append("✅ BTC: BULLISH (Higher highs forming)")
        is_bullish = True
    elif btc_direction == "bearish":
        confirmations.append("❌ BTC: BEARISH (Lower lows forming)")
        is_bearish = True
    else:
        confirmations.append("⚠️ BTC: Direction not set - Select BTC direction first")
        return None, confirmations
    
    # Check 2: Volume Spike
    if volume_spike:
        confirmations.append("✅ Volume: 2x+ spike detected")
    else:
        confirmations.append("❌ Volume: No spike detected - Wait for volume confirmation")
        if is_bullish or is_bearish:
            return "WAIT", confirmations
        return None, confirmations
    
    # Check 3: Orderbook Imbalance
    if ob_imbalance > 0.15:
        confirmations.append(f"✅ Orderbook: Buy wall {ob_imbalance*100:.0f}% larger - BULLISH")
        if is_bullish:
            is_bullish = True
        else:
            confirmations.append("⚠️ OB bullish but BTC bearish - No trade")
            return "WAIT", confirmations
    elif ob_imbalance < -0.15:
        confirmations.append(f"✅ Orderbook: Sell wall {abs(ob_imbalance)*100:.0f}% larger - BEARISH")
        if is_bearish:
            is_bearish = True
        else:
            confirmations.append("⚠️ OB bearish but BTC bullish - No trade")
            return "WAIT", confirmations
    else:
        confirmations.append(f"❌ Orderbook: Imbalance {ob_imbalance:.2f} (needs >0.15 or <-0.15)")
        return "WAIT", confirmations
    
    # Check 4: TOR % Extra Filter (Optional but strong)
    if tor >= 65.5:
        confirmations.append(f"✅ TOR: {tor}% (Bullish confirmation)")
    elif tor <= 64:
        confirmations.append(f"✅ TOR: {tor}% (Bearish confirmation)")
    else:
        confirmations.append(f"⚡ TOR: {tor}% (Neutral - still tradeable)")
    
    # Final Signal Decision
    if is_bullish:
        return {
            'signal': '🟢🟢 LONG SCALP SIGNAL 🟢🟢',
            'type': 'long',
            'action': 'ENTER LONG POSITION',
            'target': '0.4% - 0.7%',
            'stop': '-0.3%',
            'leverage': '5x - 10x'
        }, confirmations
    elif is_bearish:
        return {
            'signal': '🔴🔴 SHORT SCALP SIGNAL 🔴🔴',
            'type': 'short',
            'action': 'ENTER SHORT POSITION',
            'target': '0.4% - 0.7%',
            'stop': '-0.3%',
            'leverage': '5x - 10x'
        }, confirmations
    else:
        return "WAIT", confirmations

# ============================================
# COIN SELECTION (Manual - Aap Choose Karo)
# ============================================
def get_coin_list():
    return ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 'AVAX', 'MATIC', 'LINK', 'ARB', 'OP']

# ============================================
# MAIN APP
# ============================================

# Fetch Bitnodes data
bitnodes = fetch_bitnodes()
current_tor = bitnodes['tor']
current_na = bitnodes['na']

# Check current session
session_name, is_active, session_time = get_current_session()

# ============================================
# SESSION STATUS DISPLAY
# ============================================
st.markdown("### ⏰ TRADING SESSION STATUS")

if is_active:
    st.markdown(f'<div class="stat-card"><div class="session-active">🔴 LIVE SESSION: {session_name}</div><div>{session_time}</div><div>🔥 Fast pumps/dumps expected</div></div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="stat-card"><div>⏸️ {session_name}</div><div>{session_time}</div><div>⚠️ No trade - Wait for Asia/Europe/US session</div></div>', unsafe_allow_html=True)

# ============================================
# STEP 1: BTC DIRECTION (Manual Input)
# ============================================
st.markdown("### 📊 STEP 1: BTC DIRECTION (Primary Filter)")

col1, col2 = st.columns(2)

with col1:
    if st.button("🐂 BTC BULLISH", use_container_width=True):
        st.session_state.btc_direction = "bullish"
        st.success("✅ BTC Direction: BULLISH - Only LONG setups for alts")

with col2:
    if st.button("🐻 BTC BEARISH", use_container_width=True):
        st.session_state.btc_direction = "bearish"
        st.success("✅ BTC Direction: BEARISH - Only SHORT setups for alts")

if st.session_state.btc_direction:
    st.info(f"Current BTC Direction: {'🟢 BULLISH (Long only)' if st.session_state.btc_direction == 'bullish' else '🔴 BEARISH (Short only)'}")

# ============================================
# STEP 2: COIN SELECTION
# ============================================
st.markdown("### 💰 STEP 2: SELECT COINS (Top Volume Gainers)")

coins = get_coin_list()
selected_coins = st.multiselect("Select 2-3 high-volume coins for scalping", coins, default=['SOL', 'ETH'])

if selected_coins:
    st.info(f"Selected coins: {', '.join(selected_coins)}")

# ============================================
# STEP 3: ENTRY CONFIRMATIONS
# ============================================
st.markdown("### ✅ STEP 3: ENTRY CONFIRMATIONS (All 3 required)")

col_c1, col_c2, col_c3 = st.columns(3)

with col_c1:
    volume_spike = st.checkbox("📊 Volume Spike (2x-3x average)", value=False)
    st.caption("Coin me volume spike candle")

with col_c2:
    ob_imbalance = st.slider("📚 Orderbook Imbalance", -0.5, 0.5, 0.0, 0.05)
    st.caption(">0.15 = Long | <-0.15 = Short")

with col_c3:
    st.metric("🌐 TOR % (Extra Filter)", f"{current_tor}%", 
              delta=None, delta_color="normal")
    st.caption(f"NA: {current_na:,} nodes")

# ============================================
# STEP 4: GENERATE SIGNAL
# ============================================
st.markdown("### 🎯 STEP 4: SCALPING SIGNAL")

if st.button("🔍 GENERATE SCALPING SIGNAL", use_container_width=True):
    if not st.session_state.btc_direction:
        st.error("❌ First select BTC Direction (Bullish/Bearish)")
    elif not selected_coins:
        st.error("❌ Select at least one coin")
    else:
        result, confirmations = generate_scalp_signal(
            st.session_state.btc_direction,
            volume_spike,
            ob_imbalance,
            current_tor,
            current_na
        )
        
        if result and result != "WAIT":
            signal_class = "signal-long" if result['type'] == 'long' else "signal-short"
            st.markdown(f"""
            <div class="signal-box {signal_class}">
                <div style="font-size: 2em; font-weight: bold;">{result['signal']}</div>
                <div style="font-size: 1.2em; margin: 10px 0;">🎯 ACTION: {result['action']}</div>
                <div>📈 TARGET: {result['target']} | 🛑 STOP: {result['stop']} | ⚡ LEVERAGE: {result['leverage']}</div>
                <div style="margin-top: 10px;">💰 Coins: {', '.join(selected_coins)}</div>
            </div>
            """, unsafe_allow_html=True)
        elif result == "WAIT":
            st.warning("🟡 NO SIGNAL - WAIT for all confirmations")
        else:
            st.error("❌ Missing confirmations - Check all boxes")
        
        # Show confirmations
        st.markdown("### 📋 CONFIRMATIONS CHECKLIST")
        for conf in confirmations:
            st.markdown(f'<div class="confirmation-item">{conf}</div>', unsafe_allow_html=True)

# ============================================
# BITNODES STATUS (Extra Filter)
# ============================================
st.markdown("### 🌐 BITNODES STATUS (Extra Confidence Filter)")

col_b1, col_b2 = st.columns(2)

with col_b1:
    st.markdown(f"""
    <div class="stat-card">
        <div>🌐 TOR %</div>
        <div class="stat-value">{current_tor}%</div>
        <div>{'🟢 Bullish bias' if current_tor > 65.5 else ('🔴 Bearish bias' if current_tor < 64 else '🟡 Neutral')}</div>
    </div>
    """, unsafe_allow_html=True)

with col_b2:
    st.markdown(f"""
    <div class="stat-card">
        <div>📡 Network Availability</div>
        <div class="stat-value">{current_na:,}</div>
        <div>{'🟢 Strong network' if current_na > 23500 else ('🟡 Normal' if current_na > 20000 else '🔴 Weak')}</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# QUICK REFERENCE - PUMP/DUMP SIGNAL TABLE
# ============================================
st.markdown("### 📖 QUICK REFERENCE: Pump/Dump Signal Table")

pump_dump_data = {
    "Condition": [
        "PUMP Signal",
        "DUMP Signal", 
        "Fake Pump",
        "No Clear Direction"
    ],
    "TOR %": [
        "↑65.2% → 65.6%",
        "↓66% → 65.5%",
        "64%",
        "63.5%"
    ],
    "NA Count": [
        "21k+",
        "19k",
        "<17k",
        "20k"
    ],
    "Speed": [
        "Fast ↑",
        "Fast ↓",
        "Slow",
        "Sudden ↑"
    ],
    "OB Imbalance": [
        "Buy > Sell",
        "Sell > Buy",
        "Buy > Sell",
        "Balanced"
    ],
    "Volume": [
        "Yes",
        "Yes",
        "No",
        "No"
    ],
    "Direction": [
        "🟢 PUMP",
        "🔴 DUMP",
        "⚠️ Fake (dump expected)",
        "⚡ No clear"
    ]
}

st.dataframe(pd.DataFrame(pump_dump_data), use_container_width=True, hide_index=True)

# ============================================
# RISK MANAGEMENT RULES
# ============================================
st.markdown("### 🛡️ RISK MANAGEMENT (90% Discipline)")

col_r1, col_r2, col_r3 = st.columns(3)

with col_r1:
    st.info("📊 **Position Sizing**\n\n- Max 3 trades/day\n- Risk 1-2% per trade\n- 5x-10x leverage max")

with col_r2:
    st.warning("⛔ **Stop Loss**\n\n- Default: -0.3%\n- Always use hard stop\n- Move to breakeven at +0.3%")

with col_r3:
    st.success("🎯 **Take Profit**\n\n- Target: 0.4%-0.7%\n- Scale out 50% at target\n- Don't get greedy")

# ============================================
# TRADE ENTRY FORM
# ============================================
st.markdown("### 📝 TRADE ENTRY LOG")

with st.form("trade_form"):
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        trade_coin = st.selectbox("Coin", selected_coins if selected_coins else coins)
    with col_f2:
        trade_type = st.selectbox("Type", ["LONG", "SHORT"])
    with col_f3:
        trade_leverage = st.selectbox("Leverage", [5, 10, 15, 20], index=0)
    
    submitted = st.form_submit_button("💾 LOG THIS TRADE")
    
    if submitted:
        st.session_state.trade_history.append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'coin': trade_coin,
            'type': trade_type,
            'leverage': trade_leverage,
            'session': session_name
        })
        st.success(f"✅ Trade logged: {trade_coin} {trade_type} @ {trade_leverage}x")

# Display trade history
if st.session_state.trade_history:
    st.markdown("### 📜 TODAY'S TRADES")
    history_df = pd.DataFrame(st.session_state.trade_history[-10:])
    st.dataframe(history_df, use_container_width=True, hide_index=True)

# ============================================
# RESET BUTTON
# ============================================
if st.button("🔄 RESET ALL", use_container_width=True):
    st.session_state.btc_direction = None
    st.session_state.selected_coins = []
    st.cache_data.clear()
    st.rerun()

# ============================================
# FOOTER
# ============================================
st.markdown(f"""
<div class="footer">
    <p>📡 Strategy: Daily Scalping | Sessions: Asia (5-11am) | Europe (12-2pm) | US Open (5:55-6:20pm PKT)</p>
    <p>⚠️ 90% Discipline Required | Always use Stop Loss | Max 3 trades/day</p>
</div>
""", unsafe_allow_html=True)
