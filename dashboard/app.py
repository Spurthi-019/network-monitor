# dashboard/app.py
# Compact one-screen dashboard with real-time buttons

import streamlit as st
import time
import sys
import os

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
))

st.set_page_config(
    page_title            = "Network Monitor",
    page_icon             = "🌐",
    layout                = "wide",
    initial_sidebar_state = "collapsed",
)

from database.db import (
    get_all_devices, get_all_metrics,
    get_metrics_summary, get_alerts,
    create_tables, insert_many_metrics,
    insert_many_alerts,
)
from monitoring.thread_monitor import monitor_all_devices
from diagnostics.analyzer import analyze_all, analyze_result
from dashboard.components.cards import (
    inject_theme, render_topbar,
    render_metric_cards, render_health_badges,
    render_alert_panel,
)
from dashboard.components.charts import (
    render_latency_timeline,
    render_packet_loss_chart,
    render_latency_per_device,
    render_health_donut,
    render_uptime_bars,
    render_device_status_table,
)
from logger_setup import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)
create_tables()
inject_theme()


def run_check(mode: str = "real"):
    """
    Run monitoring and save results.
    mode = real  → actual network check
    mode = worst → simulate terrible network
    mode = best  → simulate perfect network
    """
    devices = get_all_devices()
    if not devices:
        return
    targets = [(d["host"], d["port"]) for d in devices]
    results = monitor_all_devices(targets)

    if mode == "worst":
        for r in results:
            if r.get("reachable"):
                r["latency_ms"]          = round(
                    450 + (hash(r["host"]) % 250), 1)
                r["packet_loss_percent"] = round(
                    20 + (hash(r["host"]) % 35), 1)
                r["health"]   = "poor"
                r["message"]  = "SIMULATED: Severe degradation"
    elif mode == "best":
        for r in results:
            if r.get("reachable"):
                r["latency_ms"]          = round(
                    4 + (hash(r["host"]) % 8), 1)
                r["packet_loss_percent"] = 0.0
                r["health"]   = "excellent"
                r["message"]  = "SIMULATED: Perfect conditions"

    # Save metrics
    insert_many_metrics(results)

    # Run diagnostics using your actual function names
    alerts = analyze_all(results)

    # Save alerts — convert Alert objects to dicts
    alert_dicts = []
    for a in alerts:
        if hasattr(a, 'to_dict'):
            alert_dicts.append(a.to_dict())
        elif isinstance(a, dict):
            alert_dicts.append(a)

    if alert_dicts:
        insert_many_alerts(alert_dicts)


# ── Load fresh data ───────────────────────────────────────────
summary = get_metrics_summary()
metrics = get_all_metrics(limit=300)
alerts  = get_alerts(limit=50)
devices = get_all_devices()

# ── TOP BAR ──────────────────────────────────────────────────
# Build top bar with buttons inline on right side
col_title, col_live, col_b1, col_b2, col_b3, col_upd = \
    st.columns([3, 0.7, 0.9, 1, 0.9, 1.2])

with col_title:
    st.markdown(
        "<div style='padding-top:4px;color:#ff2d78;"
        "font-weight:700;font-size:14px;"
        "letter-spacing:2px;'>🌐 NETWORK MONITOR</div>",
        unsafe_allow_html=True)

with col_live:
    st.markdown(
        "<div style='background:rgba(255,45,120,0.15);"
        "color:#ff2d78;padding:5px 12px;"
        "border-radius:20px;font-size:10px;"
        "font-weight:700;border:1px solid #ff2d78;"
        "text-align:center;margin-top:2px;'>"
        "● LIVE</div>",
        unsafe_allow_html=True)

with col_b1:
    run_real = st.button("⚡ RUN CHECK")

with col_b2:
    run_worst = st.button("🔴 WORST CASE")

with col_b3:
    run_best = st.button("🟢 BEST CASE")

with col_upd:
    st.markdown(
        f"<div style='color:#666688;font-size:8px;"
        f"padding-top:6px;text-align:right;'>"
        f"Updated:<br>"
        f"<span style='color:#cc88ff;font-weight:700;'>"
        f"{time.strftime('%H:%M:%S')}</span></div>",
        unsafe_allow_html=True)

# Handle button clicks
if run_real:
    with st.spinner("Running real network check..."):
        run_check("real")
    st.rerun()

if run_worst:
    with st.spinner("Simulating worst conditions..."):
        run_check("worst")
    st.rerun()

if run_best:
    with st.spinner("Simulating best conditions..."):
        run_check("best")
    st.rerun()

# ── Info strip ────────────────────────────────────────────────
total     = len(devices)
runs      = sum(s.get("total_checks", 0) for s in summary)
online    = sum(1 for s in summary
                if (s.get("avg_latency_ms") or 0) > 0)
reachable = [s for s in summary
             if s.get("avg_latency_ms") is not None
             and s["avg_latency_ms"] > 0]
best_d    = min(reachable,
                key=lambda x: x["avg_latency_ms"],
                default=None)
offline_d = [s for s in summary
             if not s.get("avg_latency_ms")]
best_txt  = (f"{best_d['host']} "
             f"({best_d['avg_latency_ms']}ms)") \
            if best_d else "N/A"
worst_txt = offline_d[0]["host"] \
            if offline_d else "All online"
worst_col = "#ff2d78" if offline_d else "#22c55e"
success   = round((online/total)*100, 1) \
            if total > 0 else 0

st.markdown(f"""
<div style="background:#13131f;border:1px solid #2a1a3a;
            border-radius:8px;padding:6px 16px;
            display:flex;gap:28px;margin-bottom:6px;
            flex-wrap:wrap;align-items:center;">
    <div><div style="color:#666688;font-size:7px;
                     letter-spacing:1px;">DEVICES</div>
         <div style="color:#cc88ff;font-size:11px;
                     font-weight:700;">{total}</div></div>
    <div><div style="color:#666688;font-size:7px;
                     letter-spacing:1px;">TOTAL RUNS</div>
         <div style="color:#cc88ff;font-size:11px;
                     font-weight:700;">{runs}</div></div>
    <div><div style="color:#666688;font-size:7px;
                     letter-spacing:1px;">SUCCESS RATE</div>
         <div style="color:#cc88ff;font-size:11px;
                     font-weight:700;">{success}%</div></div>
    <div><div style="color:#666688;font-size:7px;
                     letter-spacing:1px;">BEST DEVICE</div>
         <div style="color:#22c55e;font-size:11px;
                     font-weight:700;">{best_txt}</div></div>
    <div><div style="color:#666688;font-size:7px;
                     letter-spacing:1px;">WORST DEVICE</div>
         <div style="color:{worst_col};font-size:11px;
                     font-weight:700;">{worst_txt}</div></div>
</div>
""", unsafe_allow_html=True)

# ── ROW 1: 4 metric cards ─────────────────────────────────────
render_metric_cards(summary, alerts)

# ── ROW 2: health badges ──────────────────────────────────────
render_health_badges(summary)

st.markdown(
    "<hr style='border-color:#2a1a3a;margin:6px 0;'>",
    unsafe_allow_html=True)

# ── ROW 3: Latency chart (big) + Packet loss ─────────────────
col_a, col_b = st.columns([1.4, 1])
with col_a:
    render_latency_timeline(metrics)
with col_b:
    render_packet_loss_chart(summary)

st.markdown(
    "<hr style='border-color:#2a1a3a;margin:6px 0;'>",
    unsafe_allow_html=True)

# ── ROW 4: Latency per device + Health donut + Uptime ────────
col_c, col_d, col_e = st.columns(3)
with col_c:
    render_latency_per_device(summary)
with col_d:
    render_health_donut(summary, alerts)
with col_e:
    render_uptime_bars(summary)

st.markdown(
    "<hr style='border-color:#2a1a3a;margin:6px 0;'>",
    unsafe_allow_html=True)

# ── ROW 5: Device table + Alerts ─────────────────────────────
col_f, col_g = st.columns([1.5, 1])
with col_f:
    render_device_status_table(summary)
with col_g:
    render_alert_panel(alerts)