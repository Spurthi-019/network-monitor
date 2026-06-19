# dashboard/components/cards.py
import streamlit as st
import time


def inject_theme():
    st.markdown("""
    <style>
    .stApp { background-color: #0d0d1a !important; }
    [data-testid="stSidebar"] { display: none !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    .block-container {
        padding: 0.5rem 1rem !important;
        max-width: 100% !important;
    }
    html, body, [class*="css"] {
        font-family: 'Courier New', monospace !important;
        color: #ffffff !important;
    }
    [data-testid="metric-container"] {
        background-color: #13131f !important;
        border: 1px solid #2a1a3a !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
    }
    [data-testid="stMetricLabel"] {
        color: #888899 !important;
        font-size: 9px !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 26px !important;
        font-weight: 700 !important;
        line-height: 1.1 !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 10px !important;
    }
    hr {
        border-color: #2a1a3a !important;
        margin: 6px 0 !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #ff2d78, #a855f7) !important;
        color: white !important;
        border: none !important;
        border-radius: 20px !important;
        font-family: 'Courier New', monospace !important;
        font-weight: 700 !important;
        font-size: 11px !important;
        letter-spacing: 1px !important;
        padding: 4px 16px !important;
        height: 32px !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #a855f7, #ff2d78) !important;
        transform: translateY(-1px) !important;
    }
    [data-testid="stExpander"] {
        background-color: #13131f !important;
        border: 1px solid #2a1a3a !important;
        border-radius: 8px !important;
    }
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.3rem !important;
    }
    .stDataFrame { background-color: #13131f !important; }
    </style>
    """, unsafe_allow_html=True)


def render_topbar(summary: list, devices: list):
    """Top navigation bar — exactly like screenshot."""
    total     = len(devices)
    runs      = sum(s.get("total_checks", 0) for s in summary)
    online    = sum(1 for s in summary
                    if (s.get("avg_latency_ms") or 0) > 0)
    reachable = [s for s in summary
                 if s.get("avg_latency_ms") is not None
                 and s["avg_latency_ms"] > 0]
    best      = min(reachable,
                    key=lambda x: x["avg_latency_ms"],
                    default=None)
    offline_d = [s for s in summary
                 if not s.get("avg_latency_ms")]
    best_txt  = (f"{best['host']} "
                 f"({best['avg_latency_ms']}ms)") \
                if best else "N/A"
    worst_txt = offline_d[0]["host"] \
                if offline_d else "All online"
    worst_col = "#ff2d78" if offline_d else "#22c55e"
    success   = round((online / total) * 100, 1) \
                if total > 0 else 0

    st.markdown(f"""
    <div style="background:#13131f;border:1px solid #2a1a3a;
                border-radius:10px;padding:8px 16px;
                display:flex;align-items:center;
                justify-content:space-between;
                margin-bottom:8px;">
        <div style="display:flex;align-items:center;gap:10px;">
            <span style="color:#ff2d78;font-weight:700;
                         font-size:13px;letter-spacing:2px;">
                🌐 NETWORK MONITOR</span>
        </div>
        <div style="display:flex;gap:22px;flex-wrap:wrap;
                    align-items:center;">
            <div>
                <div style="color:#666688;font-size:7px;
                            letter-spacing:1px;">DEVICES</div>
                <div style="color:#cc88ff;font-size:11px;
                            font-weight:700;">{total}</div>
            </div>
            <div>
                <div style="color:#666688;font-size:7px;
                            letter-spacing:1px;">TOTAL RUNS</div>
                <div style="color:#cc88ff;font-size:11px;
                            font-weight:700;">{runs}</div>
            </div>
            <div>
                <div style="color:#666688;font-size:7px;
                            letter-spacing:1px;">SUCCESS RATE</div>
                <div style="color:#cc88ff;font-size:11px;
                            font-weight:700;">{success}%</div>
            </div>
            <div>
                <div style="color:#666688;font-size:7px;
                            letter-spacing:1px;">BEST DEVICE</div>
                <div style="color:#22c55e;font-size:11px;
                            font-weight:700;">{best_txt}</div>
            </div>
            <div>
                <div style="color:#666688;font-size:7px;
                            letter-spacing:1px;">WORST DEVICE</div>
                <div style="color:{worst_col};font-size:11px;
                            font-weight:700;">{worst_txt}</div>
            </div>
            <div>
                <div style="color:#666688;font-size:7px;
                            letter-spacing:1px;">UPDATED</div>
                <div style="color:#cc88ff;font-size:11px;
                            font-weight:700;">
                    {time.strftime('%H:%M:%S')}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_metric_cards(summary: list, alerts: list):
    latencies = [s["avg_latency_ms"] for s in summary
                 if s.get("avg_latency_ms")]
    losses    = [s["avg_loss_percent"] for s in summary
                 if s.get("avg_loss_percent") is not None]
    avg_lat   = round(sum(latencies)/len(latencies), 2) \
                if latencies else 0.0
    avg_loss  = round(sum(losses)/len(losses), 2) \
                if losses else 0.0
    total     = len(summary)
    online    = sum(1 for s in summary
                    if (s.get("avg_latency_ms") or 0) > 0)
    offline   = total - online
    critical  = sum(1 for a in alerts
                    if a.get("severity") == "CRITICAL")
    warning   = sum(1 for a in alerts
                    if a.get("severity") == "WARNING")
    score     = max(0, 100 - critical * 25 - warning * 10)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("AVG RTT", f"{avg_lat}",
                  "milliseconds",
                  delta_color="off")
    with c2:
        st.metric("PACKET LOSS", f"{avg_loss}",
                  "percent",
                  delta_color="off")
    with c3:
        st.metric("HEALTH SCORE", f"{score}",
                  "out of 100",
                  delta_color="off")
    with c4:
        st.metric("ONLINE DEVICES", f"{online}/{total}",
                  f"{offline} offline"
                  if offline > 0 else "all online",
                  delta_color="off")


def render_health_badges(summary: list):
    latencies = [s["avg_latency_ms"] for s in summary
                 if s.get("avg_latency_ms")]
    min_lat   = round(min(latencies), 2) if latencies else 0
    max_lat   = round(max(latencies), 2) if latencies else 0
    avg_lat   = round(sum(latencies)/len(latencies), 2) \
                if latencies else 0

    if avg_lat == 0:
        ph, pc = "NO DATA", "#888899"
    elif avg_lat < 50:
        ph, pc = "EXCELLENT", "#22c55e"
    elif avg_lat < 150:
        ph, pc = "GOOD", "#22c55e"
    elif avg_lat < 300:
        ph, pc = "FAIR", "#f59e0b"
    else:
        ph, pc = "POOR", "#ff2d78"

    losses   = [s["avg_loss_percent"] for s in summary
                if s.get("avg_loss_percent") is not None]
    avg_loss = round(sum(losses)/len(losses), 2) \
               if losses else 0
    lh = "GOOD"    if avg_loss <= 2  else "POOR"
    lc = "#22c55e" if avg_loss <= 2  else "#ff2d78"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div style="background:#13131f;border:1px solid #2a1a3a;
                    border-radius:8px;padding:8px 14px;">
            <div style="color:#666688;font-size:8px;
                        letter-spacing:1px;margin-bottom:4px;">
                PING HEALTH</div>
            <span style="background:rgba(34,197,94,0.15);
                         color:{pc};padding:2px 12px;
                         border-radius:20px;font-size:10px;
                         font-weight:700;
                         border:1px solid {pc};">{ph}</span>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div style="background:#13131f;border:1px solid #2a1a3a;
                    border-radius:8px;padding:8px 14px;">
            <div style="color:#666688;font-size:8px;
                        letter-spacing:1px;">MIN RTT</div>
            <div style="color:#a855f7;font-size:18px;
                        font-weight:700;line-height:1.3;">
                {min_lat} ms</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div style="background:#13131f;border:1px solid #2a1a3a;
                    border-radius:8px;padding:8px 14px;">
            <div style="color:#666688;font-size:8px;
                        letter-spacing:1px;">MAX RTT</div>
            <div style="color:#f472b6;font-size:18px;
                        font-weight:700;line-height:1.3;">
                {max_lat} ms</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div style="background:#13131f;border:1px solid #2a1a3a;
                    border-radius:8px;padding:8px 14px;">
            <div style="color:#666688;font-size:8px;
                        letter-spacing:1px;margin-bottom:4px;">
                LOSS HEALTH</div>
            <span style="background:rgba(34,197,94,0.15);
                         color:{lc};padding:2px 12px;
                         border-radius:20px;font-size:10px;
                         font-weight:700;
                         border:1px solid {lc};">{lh}</span>
        </div>""", unsafe_allow_html=True)


def render_alert_panel(alerts: list):
    st.markdown("""
    <div style="color:#ff2d78;font-size:9px;
                letter-spacing:2px;margin-bottom:6px;
                display:flex;align-items:center;gap:6px;">
        <span>●</span><span>LATEST ALERTS</span></div>
    """, unsafe_allow_html=True)

    if not alerts:
        st.info("No alerts yet.")
        return

    for a in alerts[:6]:
        sev    = a.get("severity", "OK")
        host   = a.get("host", "unknown")
        detail = a.get("detail", "")
        ts     = a.get("timestamp", "")[-8:] \
                 if a.get("timestamp") else ""
        if sev == "CRITICAL":
            col, bg, icon = "#ff2d78", \
                            "rgba(255,45,120,0.1)", "✗"
        elif sev == "WARNING":
            col, bg, icon = "#f59e0b", \
                            "rgba(245,158,11,0.1)",  "~"
        else:
            col, bg, icon = "#22c55e", \
                            "rgba(34,197,94,0.1)",   "✓"

        st.markdown(f"""
        <div style="background:{bg};
                    border-left:3px solid {col};
                    border-radius:0 6px 6px 0;
                    padding:5px 8px;margin-bottom:4px;">
            <div style="display:flex;
                        justify-content:space-between;">
                <span style="color:{col};font-size:9px;
                             font-weight:700;">
                    {icon} {sev}</span>
                <span style="color:#444455;font-size:8px;">
                    {ts}</span>
            </div>
            <div style="color:#fff;font-size:10px;
                        font-weight:600;">{host}</div>
            <div style="color:#666688;font-size:9px;">
                {detail[:45]}</div>
        </div>""", unsafe_allow_html=True)