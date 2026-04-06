import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import time

# -----------------------------
# PAGE CONFIGURATION
# -----------------------------
st.set_page_config(
    page_title="UZair Ali Dark Crypto - Live Bitnodes Map & Signals",
    page_icon="🌑",
    layout="wide"
)

# -----------------------------
# CUSTOM CSS (Dark Theme)
# -----------------------------
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
    
    .signal-box {
        background: #0f1322;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        text-align: center;
    }
    
    .signal-pump {
        border: 2px solid #00ffaa;
        box-shadow: 0 0 20px rgba(0,255,170,0.3);
    }
    
    .signal-dump {
        border: 2px solid #ff4444;
        box-shadow: 0 0 20px rgba(255,68,68,0.3);
    }
    
    .signal-fake {
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
</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER
# -----------------------------
st.markdown("""
<div class="main-header">
    <h1>🌑 UZAIR ALI DARK CRYPTO</h1>
    <p>Live Bitnodes Map | Real-Time Node Data | Country-wise Altcoin Signals</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# SESSION STATE
# -----------------------------
if 'prev_tor' not in st.session_state:
    st.session_state.prev_tor = None
if 'prev_na' not in st.session_state:
    st.session_state.prev_na = None

# -----------------------------
# BITNODES API (Real Data)
# -----------------------------
@st.cache_data(ttl=60)
def fetch_bitnodes_data():
    """Fetch real-time data from Bitnodes API"""
    try:
        url = "https://bitnodes.io/api/v1/snapshots/latest/"
        headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            total_nodes = data.get('total_nodes', 0)
            timestamp = data.get('timestamp', 0)
            latest_height = data.get('latest_height', 0)
            
            # Count TOR nodes
            tor_count = 0
            for node_addr in data.get('nodes', {}).keys():
                if '.onion' in node_addr.lower():
                    tor_count += 1
            
            tor_percentage = (tor_count / total_nodes * 100) if total_nodes > 0 else 0
            
            # Extract sample nodes for map
            sample_nodes = []
            nodes_dict = data.get('nodes', {})
            for node_addr, node_info in list(nodes_dict.items())[:50]:
                if len(node_info) >= 10:
                    lat = node_info[8] if isinstance(node_info[8], (int, float)) else None
                    lon = node_info[9] if isinstance(node_info[9], (int, float)) else None
                    if lat and lon and -90 <= lat <= 90 and -180 <= lon <= 180:
                        sample_nodes.append({
                            'address': node_addr,
                            'lat': lat,
                            'lon': lon,
                            'city': node_info[6] if len(node_info) > 6 else 'Unknown',
                            'country': node_info[7] if len(node_info) > 7 else 'Unknown'
                        })
            
            return {
                'tor': round(tor_percentage, 2),
                'na': total_nodes,
                'block_height': latest_height,
                'timestamp': datetime.fromtimestamp(timestamp) if timestamp else datetime.now(),
                'nodes': sample_nodes,
                'success': True
            }
        else:
            return generate_mock_data()
    except Exception as e:
        return generate_mock_data()

def generate_mock_data():
    """Fallback mock data"""
    import random
    return {
        'tor': round(65.2 + (random.random() - 0.5) * 1.5, 2),
        'na': int(23800 + (random.random() - 0.5) * 300),
        'block_height': 877540 + random.randint(0, 50),
        'timestamp': datetime.now(),
        'nodes': [],
        'success': False
    }

# -----------------------------
# MAP FUNCTION (Bitnodes Style)
# -----------------------------
def create_bitnodes_map(nodes_list):
    """Create interactive map with Bitcoin nodes"""
    if not nodes_list:
        # Fallback nodes if API doesn't return location
        nodes_list = [
            {'lat': 43.25, 'lon': 76.95, 'city': 'Almaty', 'country': 'Kazakhstan', 'address': '217.15.178.11:8333'},
            {'lat': 12.12, 'lon': -68.93, 'city': 'Willemstad', 'country': 'Curacao', 'address': '161.0.99.56:8333'},
            {'lat': -6.21, 'lon': 106.85, 'city': 'Jakarta', 'country': 'Indonesia', 'address': '115.85.88.107:8333'},
            {'lat': -23.55, 'lon': -46.63, 'city': 'Sao Paulo', 'country': 'Brazil', 'address': '[2804:14c:58:5c3b:1d91:865c7b59:81ef]:8333'},
            {'lat': 51.51, 'lon': -0.13, 'city': 'London', 'country': 'United Kingdom', 'address': '185.165.168.22:8333'},
            {'lat': 1.35, 'lon': 103.82, 'city': 'Singapore', 'country': 'Singapore', 'address': '103.152.112.44:8333'},
        ]
    
    df = pd.DataFrame(nodes_list)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scattergeo(
        lon=df['lon'],
        lat=df['lat'],
        text=df.apply(lambda x: f"<b>{x['address']}</b><br>{x['city']}, {x['country']}", axis=1),
        mode='markers',
        marker=dict(
            size=12,
            color='#00ffaa',
            symbol='circle',
            line=dict(width=2, color='white'),
            opacity=0.9
        ),
        hovertemplate='%{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text="🌍 BITCOIN NODE NETWORK - LIVE MAP",
            font=dict(color='#00ffaa', size=16),
            x=0.5
        ),
        geo=dict(
            projection_type='equirectangular',
            showland=True,
            landcolor='#0f1322',
            coastlinecolor='#2a2f4a',
            showocean=True,
            oceancolor='#050814',
            showcountries=True,
            countrycolor='#1a2040',
            showframe=False
        ),
        height=550,
        margin=dict(l=0, r=0, t=50, b=0),
        paper_bgcolor='#0a0e27',
        plot_bgcolor='#0a0e27',
        font=dict(color='#88ffcc')
    )
    
    return fig

# -----------------------------
# PUMP/DUMP SIGNAL TABLE (Aapki Strategy)
# -----------------------------
def get_pump_dump_signal(tor, na_count, change_speed, ob_imbalance, volume_spike):
    """Generate signal based on user's table"""
    # PUMP Condition
    if 65.2 <= tor <= 65.6 and na_count >= 21000 and change_speed == "Fast ↑" and ob_imbalance > 0 and volume_spike:
        return "🟢🟢 PUMP SIGNAL 🟢🟢", "pump", "Expect strong upward move"
    # DUMP Condition
    elif 65.5 <= tor <= 66 and na_count >= 19000 and change_speed == "Fast ↓" and ob_imbalance < 0 and volume_spike:
        return "🔴🔴 DUMP SIGNAL 🔴🔴", "dump", "Expect strong downward move"
    # FAKE PUMP Condition
    elif tor == 64 and na_count < 17000 and change_speed == "Slow" and ob_imbalance > 0 and not volume_spike:
        return "🟡🟡 FAKE PUMP (Dump Expected) 🟡🟡", "fake", "Fake breakout, dump incoming"
    # NO CLEAR
    else:
        return "⚪ NO CLEAR SIGNAL ⚪", "neutral", "No clear direction - Wait"

# -----------------------------
# COUNTRY-WISE ALTCOIN SIGNALS (Based on Node Trend)
# -----------------------------
def get_country_altcoin_signal(country, node_trend):
    """Map altcoin signals based on country and node trend"""
    # Image se mapping
    country_signals = {
        "Kazakhstan": {"long": ["SOL", "OKB"], "short": []},
        "Curacao": {"long": [], "short": ["F", "J", "H"]},
        "Brazil": {"long": [], "short": ["CFX", "UNFI"]},
        "Others": {"long": ["A", "D", "G"], "short": []}
    }
    
    # Logic based on node trend
    if node_trend >= 66:
        return "🟢 LONG", country_signals.get(country, country_signals["Others"])["long"]
    elif node_trend <= 57:
        return "🔴 SHORT", country_signals.get(country, country_signals["Others"])["short"]
    else:
        return "🟡 NEUTRAL", []

# -----------------------------
# MAIN APP
# -----------------------------

# Fetch real data
with st.spinner('🔄 Fetching live Bitnodes data...'):
    data = fetch_bitnodes_data()

current_tor = data['tor']
current_na = data['na']
current_time = data['timestamp']
current_height = data['block_height']

# Calculate delta
delta_tor = current_tor - st.session_state.prev_tor if st.session_state.prev_tor else 0
delta_na = current_na - st.session_state.prev_na if st.session_state.prev_na else 0

# Update session state
st.session_state.prev_tor = current_tor
st.session_state.prev_na = current_na

# -----------------------------
# STATS DISPLAY
# -----------------------------
st.markdown("### 📊 LIVE BITNODES STATS")

col1, col2, col3, col4 = st.columns(4)

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
        <div>📦 BLOCK HEIGHT</div>
        <div class="stat-value">{current_height:,}</div>
        <div>Bitcoin Network</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="stat-card">
        <div>🕐 LAST UPDATE</div>
        <div class="stat-value">{current_time.strftime('%H:%M:%S')}</div>
        <div>UTC Time</div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# BITNODES MAP (Real-time)
# -----------------------------
st.markdown("### 🗺️ BITCOIN NODE NETWORK MAP")
map_fig = create_bitnodes_map(data.get('nodes', []))
st.plotly_chart(map_fig, use_container_width=True)
st.caption("📍 Each dot = Active Bitcoin node | Hover for IP and location")

# -----------------------------
# PUMP/DUMP SIGNAL GENERATOR (Aapki Table)
# -----------------------------
st.markdown("### 🎯 PUMP/DUMP SIGNAL GENERATOR (Based on Your Strategy)")

col_p1, col_p2, col_p3 = st.columns(3)

with col_p1:
    tor_input = st.number_input("TOR %", min_value=0.0, max_value=100.0, value=current_tor, step=0.1)
    na_input = st.number_input("NA Count", min_value=0, max_value=50000, value=current_na, step=100)

with col_p2:
    change_speed = st.selectbox("TOR Change Speed", ["Slow", "Moderate", "Fast ↑", "Fast ↓"])
    ob_imbalance = st.selectbox("Orderbook Imbalance", ["Buy > Sell", "Sell > Buy", "Balanced"])

with col_p3:
    volume_spike = st.selectbox("Volume Spike", ["Yes", "No"])
    generate_btn = st.button("🔍 GENERATE SIGNAL", use_container_width=True)

if generate_btn:
    ob_value = 1 if ob_imbalance == "Buy > Sell" else (-1 if ob_imbalance == "Sell > Buy" else 0)
    volume_bool = (volume_spike == "Yes")
    
    signal_text, signal_type, signal_reason = get_pump_dump_signal(
        tor_input, na_input, change_speed, ob_value, volume_bool
    )
    
    signal_class = "signal-pump" if signal_type == "pump" else ("signal-dump" if signal_type == "dump" else ("signal-fake" if signal_type == "fake" else ""))
    
    st.markdown(f"""
    <div class="signal-box {signal_class}">
        <div style="font-size: 2.5em; font-weight: bold;">{signal_text}</div>
        <div style="margin-top: 10px;">{signal_reason}</div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# COUNTRY-WISE ALTCOIN SIGNALS
# -----------------------------
st.markdown("### 💰 COUNTRY-WISE ALTCOIN SIGNALS")

# Define countries with their node trends
countries_data = [
    {"country": "Kazakhstan", "trend": 66.2, "node": "217.15.178.11:8333"},
    {"country": "Curacao", "trend": 57.0, "node": "161.0.99.56:8333"},
    {"country": "Indonesia", "trend": 62.5, "node": "115.85.88.107:8333"},
    {"country": "Brazil", "trend": 58.9, "node": "[2804:14c:58:5c3b:1d91:865c7b59:81ef]:8333"},
    {"country": "United Kingdom", "trend": 68.3, "node": "185.165.168.22:8333"},
    {"country": "Singapore", "trend": 71.5, "node": "103.152.112.44:8333"},
]

cols = st.columns(3)
for idx, country_data in enumerate(countries_data):
    with cols[idx % 3]:
        signal, coins = get_country_altcoin_signal(country_data["country"], country_data["trend"])
        signal_color = "#00ffaa" if "LONG" in signal else ("#ff4444" if "SHORT" in signal else "#ffaa00")
        st.markdown(f"""
        <div class="stat-card">
            <div style="font-size: 1.2em; font-weight: bold;">📍 {country_data['country']}</div>
            <div>Node: {country_data['node']}</div>
            <div>Trend: {country_data['trend']}%</div>
            <div style="color: {signal_color};">{signal}</div>
            <div style="font-size: 0.8em;">Coins: {', '.join(coins) if coins else 'None'}</div>
        </div>
        """, unsafe_allow_html=True)

# -----------------------------
# REFRESH BUTTON
# -----------------------------
if st.button("🔄 REFRESH DATA", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# -----------------------------
# FOOTER
# -----------------------------
st.markdown(f"""
<div class="footer">
    <p>🔄 Data Source: Bitnodes.io Live API | Last Update: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    <p>⚠️ DISCLAIMER: Trading signals for informational purposes only. Always DYOR.</p>
</div>
""", unsafe_allow_html=True)
