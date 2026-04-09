import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import json

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="TRADENODES - Live Bitcoin Node Map",
    page_icon="🌐",
    layout="wide"
)

# ============================================
# CUSTOM CSS - BITNODES STYLE
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp {
        background-color: #0b0e1a;
    }
    
    .main-header {
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(135deg, #0a0e1a 0%, #151e2c 100%);
        border-bottom: 1px solid #2a3a4a;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        font-family: 'Inter', sans-serif;
        color: #00e5a0;
        font-size: 2.8rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        text-shadow: 0 0 8px rgba(0,229,160,0.3);
        margin: 0;
    }
    
    .main-header p {
        color: #8ba3b0;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    .stat-card {
        background: #111827;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #1f2a3a;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    
    .stat-label {
        color: #8ba3b0;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #00e5a0;
        line-height: 1.2;
    }
    
    .node-list-container {
        background: #111827;
        border-radius: 16px;
        border: 1px solid #1f2a3a;
        padding: 1rem;
        max-height: 500px;
        overflow-y: auto;
    }
    
    .node-item {
        background: #0f1722;
        border-left: 3px solid #00e5a0;
        padding: 0.8rem;
        margin-bottom: 0.8rem;
        border-radius: 8px;
        transition: all 0.2s;
    }
    
    .node-item:hover {
        transform: translateX(5px);
        background: #131c2a;
    }
    
    .node-ip {
        font-family: monospace;
        font-weight: 600;
        color: #00e5a0;
    }
    
    .node-location {
        font-size: 0.8rem;
        color: #8ba3b0;
    }
    
    .node-trend {
        font-size: 0.9rem;
        font-weight: 500;
        margin-top: 4px;
    }
    
    .signal-long {
        color: #00e5a0;
        font-weight: 600;
    }
    
    .signal-short {
        color: #ff4d4d;
        font-weight: 600;
    }
    
    .signal-neutral {
        color: #ffaa44;
        font-weight: 600;
    }
    
    .coin-pairs {
        font-size: 0.75rem;
        color: #ffaa44;
        margin-top: 4px;
    }
    
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #5a6e8a;
        font-size: 0.7rem;
        border-top: 1px solid #1f2a3a;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
st.markdown("""
<div class="main-header">
    <h1>🌐 TRADENODES</h1>
    <p>Real‑time Bitcoin Network Map | Node‑based Trading Signals</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE
# ============================================
if 'prev_tor' not in st.session_state:
    st.session_state.prev_tor = None
if 'prev_na' not in st.session_state:
    st.session_state.prev_na = None

# ============================================
# BITNODES API (REAL DATA)
# ============================================
@st.cache_data(ttl=60)
def fetch_bitnodes_data():
    """Fetch real node data from Bitnodes API"""
    try:
        url = "https://bitnodes.io/api/v1/snapshots/latest/"
        headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code == 200:
            data = r.json()
            total_nodes = data.get('total_nodes', 0)
            tor_count = sum(1 for addr in data.get('nodes', {}) if '.onion' in addr.lower())
            tor_percent = (tor_count / total_nodes * 100) if total_nodes else 0
            
            # Extract geolocated nodes for map
            node_list = []
            for addr, info in list(data.get('nodes', {}).items())[:80]:
                if len(info) >= 10:
                    lat = info[8] if isinstance(info[8], (int, float)) else None
                    lon = info[9] if isinstance(info[9], (int, float)) else None
                    if lat and lon and -90 <= lat <= 90 and -180 <= lon <= 180:
                        node_list.append({
                            'ip': addr,
                            'lat': lat,
                            'lon': lon,
                            'city': info[6] if len(info)>6 else 'Unknown',
                            'country': info[7] if len(info)>7 else 'Unknown'
                        })
            return {
                'tor': round(tor_percent, 2),
                'na': total_nodes,
                'nodes': node_list,
                'success': True,
                'timestamp': datetime.now()
            }
    except Exception as e:
        pass
    # Fallback realistic data
    import random
    return {
        'tor': round(65.2 + (random.random()-0.5)*1.5, 2),
        'na': int(23800 + (random.random()-0.5)*300),
        'nodes': [],
        'success': False,
        'timestamp': datetime.now()
    }

# ============================================
# NODE DATA WITH COIN SIGNALS (FROM YOUR IMAGE)
# ============================================
def enrich_nodes_with_signals(nodes, tor_value):
    """Add coin signals to each node based on trend"""
    # Predefined mapping for major locations (from your screenshot)
    location_signals = {
        "Almaty": {"signal": "Long", "coins": ["SOL/USDT", "OKB/USDT"], "trend_offset": +0.5},
        "Willemstad": {"signal": "Short", "coins": ["F", "J", "H"], "trend_offset": -0.2},
        "Jakarta": {"signal": "Long", "coins": ["COORDINATE"], "trend_offset": +1.0},
        "Sao Paulo": {"signal": "Short", "coins": ["CFX/USDT", "UNFI/USDT"], "trend_offset": -1.2},
        "London": {"signal": "Long", "coins": ["BTC/USDT", "ETH/USDT"], "trend_offset": +0.3},
        "Singapore": {"signal": "Long", "coins": ["BNB/USDT", "SOL/USDT"], "trend_offset": +1.2},
        "New York": {"signal": "Neutral", "coins": ["BTC/USDT"], "trend_offset": 0},
        "Frankfurt": {"signal": "Neutral", "coins": ["ETH/USDT"], "trend_offset": -0.1},
        "Tokyo": {"signal": "Neutral", "coins": ["XRP/USDT"], "trend_offset": 0.2},
    }
    
    enriched = []
    for node in nodes:
        city = node.get('city', '')
        # Find matching city
        match = None
        for key in location_signals:
            if key.lower() in city.lower():
                match = location_signals[key]
                break
        if match:
            trend = round(tor_value + match['trend_offset'], 1)
            signal = match['signal']
            coins = match['coins']
        else:
            # Default based on global TOR
            if tor_value > 65.5:
                signal = "Long"
                coins = ["BTC/USDT"]
            elif tor_value < 64.5:
                signal = "Short"
                coins = ["ETH/USDT"]
            else:
                signal = "Neutral"
                coins = ["LINK/USDT"]
            trend = round(tor_value, 1)
        
        enriched.append({
            **node,
            'trend': trend,
            'signal': signal,
            'coin_pairs': coins
        })
    return enriched

# ============================================
# CREATE PROFESSIONAL MAP
# ============================================
def create_pro_map(nodes):
    """Create a beautiful interactive map like bitnodes.io"""
    if not nodes:
        # Fallback default nodes (from your image)
        nodes = [
            {"ip": "217.15.178.11:8333", "lat": 43.25, "lon": 76.95, "city": "Almaty", "country": "Kazakhstan", "trend": 66.2, "signal": "Long", "coin_pairs": ["SOL/USDT", "OKB/USDT"]},
            {"ip": "161.0.99.56:8333", "lat": 12.12, "lon": -68.93, "city": "Willemstad", "country": "Curacao", "trend": 57.0, "signal": "Short", "coin_pairs": ["F", "J", "H"]},
            {"ip": "115.85.88.107:8333", "lat": -6.21, "lon": 106.85, "city": "Jakarta", "country": "Indonesia", "trend": 72.0, "signal": "Long", "coin_pairs": ["COORDINATE"]},
            {"ip": "[2804:14c:58:5c3b:1d91:865c:7b59:81ef]:8333", "lat": -23.55, "lon": -46.63, "city": "Sao Paulo", "country": "Brazil", "trend": 58.9, "signal": "Short", "coin_pairs": ["CFX/USDT", "UNFI/USDT"]},
            {"ip": "185.165.168.22:8333", "lat": 51.51, "lon": -0.13, "city": "London", "country": "UK", "trend": 68.3, "signal": "Long", "coin_pairs": ["BTC/USDT", "ETH/USDT"]},
            {"ip": "103.152.112.44:8333", "lat": 1.35, "lon": 103.82, "city": "Singapore", "country": "Singapore", "trend": 79.5, "signal": "Long", "coin_pairs": ["BNB/USDT", "SOL/USDT"]},
            {"ip": "45.32.18.99:8333", "lat": 40.71, "lon": -74.01, "city": "New York", "country": "USA", "trend": 64.5, "signal": "Neutral", "coin_pairs": ["BTC/USDT"]}
        ]
    
    df = pd.DataFrame(nodes)
    
    # Marker colors based on signal
    marker_colors = df['signal'].map({'Long': '#00e5a0', 'Short': '#ff4d4d', 'Neutral': '#ffaa44'}).fillna('#88aaff')
    
    # Custom hovertemplate
    hover_text = []
    for _, row in df.iterrows():
        text = f"<b>{row['ip']}</b><br>📍 {row['city']}, {row['country']}<br>📊 Trend: {row['trend']}%<br>"
        text += f"📈 Signal: <span style='color:{'#00e5a0' if row['signal']=='Long' else '#ff4d4d' if row['signal']=='Short' else '#ffaa44'}'>{row['signal']}</span><br>"
        text += f"💹 Pairs: {', '.join(row['coin_pairs'])}"
        hover_text.append(text)
    
    fig = go.Figure()
    
    # Add map background (dark)
    fig.add_trace(go.Scattergeo(
        lon=[-180, 180, 180, -180],
        lat=[-90, -90, 90, 90],
        mode='lines',
        line=dict(width=0),
        fill='toself',
        fillcolor='#0a0e1a',
        showlegend=False
    ))
    
    # Add nodes
    fig.add_trace(go.Scattergeo(
        lon=df['lon'],
        lat=df['lat'],
        text=hover_text,
        mode='markers',
        marker=dict(
            size=14,
            color=marker_colors,
            symbol='circle',
            line=dict(width=2, color='white'),
            opacity=0.9,
            sizemode='area'
        ),
        hovertemplate='%{text}<extra></extra>',
        name='Bitcoin Nodes'
    ))
    
    # Update layout for bitnodes.io style
    fig.update_layout(
        title=dict(
            text="🌍 BITCOIN NODE NETWORK",
            font=dict(color='#00e5a0', size=18, family='Inter'),
            x=0.5
        ),
        geo=dict(
            projection_type='natural earth',
            showland=True,
            landcolor='#111827',
            coastlinecolor='#2a3a4a',
            showocean=True,
            oceancolor='#0a0e1a',
            showcountries=True,
            countrycolor='#2a3a4a',
            countrywidth=1,
            showframe=False,
            lataxis=dict(range=[-60, 90]),
            lonaxis=dict(range=[-180, 180]),
            bgcolor='#0a0e1a'
        ),
        height=580,
        margin=dict(l=0, r=0, t=60, b=0),
        paper_bgcolor='#0a0e1a',
        plot_bgcolor='#0a0e1a',
        font=dict(color='#cbd5e1', family='Inter'),
        hoverlabel=dict(bgcolor='#1e293b', font_size=12, font_color='#00e5a0')
    )
    
    return fig

# ============================================
# MAIN APP LOGIC
# ============================================
data = fetch_bitnodes_data()
tor = data['tor']
na = data['na']
nodes_raw = data['nodes']
success = data['success']
timestamp = data['timestamp']

# Calculate delta
delta_tor = tor - st.session_state.prev_tor if st.session_state.prev_tor is not None else 0
delta_na = na - st.session_state.prev_na if st.session_state.prev_na is not None else 0
st.session_state.prev_tor = tor
st.session_state.prev_na = na

# Enrich nodes with coin signals
nodes = enrich_nodes_with_signals(nodes_raw, tor)

# ============================================
# STATS ROW
# ============================================
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">🌐 TOR %</div>
        <div class="stat-value">{tor}%</div>
        <div style="color: {'#00e5a0' if delta_tor>0 else '#ff4d4d'}">{delta_tor:+.2f}%</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">📡 NETWORK AVAILABILITY</div>
        <div class="stat-value">{na:,}</div>
        <div style="color: {'#00e5a0' if delta_na>0 else '#ff4d4d'}">{delta_na:+,.0f}</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">⏱️ LAST UPDATE</div>
        <div class="stat-value">{timestamp.strftime('%H:%M:%S')}</div>
        <div>UTC</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    status = "🟢 LIVE" if success else "🟡 SIMULATION"
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">DATA STATUS</div>
        <div class="stat-value" style="font-size:1.2rem;">{status}</div>
        <div>Bitnodes API</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# MAP
# ============================================
st.markdown("### 🗺️ BITCOIN NODE NETWORK MAP")
map_fig = create_pro_map(nodes)
st.plotly_chart(map_fig, use_container_width=True)
st.caption("🟢 Long signal | 🔴 Short signal | 🟡 Neutral | Hover over dots for coin details")

# ============================================
# NODE LIST WITH SIGNALS
# ============================================
st.markdown("### 📡 ACTIVE NODES & TRADING SIGNALS")

# Two columns: left for node list, right could be empty or extra info
cols = st.columns([2, 1])
with cols[0]:
    with st.container():
        for node in nodes:
            signal_class = f"signal-{node['signal'].lower()}"
            st.markdown(f"""
            <div class="node-item">
                <div class="node-ip">🔗 {node['ip']}</div>
                <div class="node-location">📍 {node['city']}, {node.get('country', 'Unknown')}</div>
                <div class="node-trend">📊 TREND: {node['trend']}%</div>
                <div class="{signal_class}">📈 Signal: {node['signal']}</div>
                <div class="coin-pairs">💹 Pairs: {', '.join(node['coin_pairs'])}</div>
            </div>
            """, unsafe_allow_html=True)

with cols[1]:
    st.markdown("""
    <div style="background:#111827; border-radius:12px; padding:1rem; border:1px solid #1f2a3a;">
        <h4 style="color:#00e5a0; margin-bottom:0.5rem;">⚡ Signal Legend</h4>
        <p><span style="color:#00e5a0;">🟢 LONG</span> = Bullish momentum</p>
        <p><span style="color:#ff4d4d;">🔴 SHORT</span> = Bearish pressure</p>
        <p><span style="color:#ffaa44;">🟡 NEUTRAL</span> = Wait for confirmation</p>
        <hr style="border-color:#1f2a3a;">
        <h4 style="color:#00e5a0;">🎯 Trading Rules</h4>
        <p>✅ Use 5x‑10x leverage<br>✅ Stop loss: -0.3%<br>✅ Target: 0.4%‑0.7%<br>✅ Max 3 trades/day</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# REFRESH BUTTON
# ============================================
if st.button("🔄 Force Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ============================================
# FOOTER
# ============================================
st.markdown(f"""
<div class="footer">
    <p>Data source: Bitnodes.io API | Last refresh: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    <p>⚠️ Trading signals are for informational purposes only. Always perform your own research.</p>
</div>
""", unsafe_allow_html=True)
