# dashboard/components/charts.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

PINK    = "#ff2d78"
PURPLE  = "#a855f7"
MAGENTA = "#f472b6"
HOTPINK = "#ec4899"
VIOLET  = "#c084fc"
CARD    = "#13131f"
BORDER  = "#2a1a3a"
DIM     = "#888899"

COLOURS = [PINK, PURPLE, MAGENTA, HOTPINK, VIOLET,
           "#e879f9", "#fb7185"]

FILL_COLOURS = [
    "rgba(255,45,120,0.07)",
    "rgba(168,85,247,0.07)",
    "rgba(244,114,182,0.07)",
    "rgba(236,72,153,0.07)",
    "rgba(192,132,252,0.07)",
]

BASE = dict(
    paper_bgcolor = CARD,
    plot_bgcolor  = CARD,
    font          = dict(color="#ccccdd",
                         family="Courier New", size=9),
    margin        = dict(l=10, r=10, t=24, b=24),
    xaxis         = dict(gridcolor=BORDER,
                         zerolinecolor=BORDER,
                         tickfont=dict(color=DIM, size=8)),
    yaxis         = dict(gridcolor=BORDER,
                         zerolinecolor=BORDER,
                         tickfont=dict(color=DIM, size=8)),
    legend        = dict(bgcolor=CARD, bordercolor=BORDER,
                         font=dict(color="#ccccdd", size=8),
                         orientation="h", yanchor="bottom",
                         y=1.02, xanchor="right", x=1),
)


def _hdr(color: str, label: str):
    st.markdown(
        f"<div style='display:flex;align-items:center;"
        f"gap:6px;margin-bottom:2px;'>"
        f"<span style='color:{color};font-size:11px;'>"
        f"●</span>"
        f"<span style='color:#ccccdd;font-size:9px;"
        f"letter-spacing:2px;font-weight:700;'>"
        f"{label}</span></div>",
        unsafe_allow_html=True)


def render_latency_timeline(metrics: list):
    _hdr(PINK, "LATENCY OVER TIME (MS)")
    if not metrics:
        st.caption("No data — click RUN CHECK")
        return
    df = pd.DataFrame(metrics)
    df = df[df["latency_ms"].notna()].copy()
    if df.empty:
        st.caption("No latency data")
        return
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    fig = go.Figure()

    # Add RTT avg legend label
    st.markdown(
        "<div style='color:#888899;font-size:8px;"
        "margin-bottom:2px;'>"
        "— RTT avg &nbsp;&nbsp; - - RTT max</div>",
        unsafe_allow_html=True)

    for i, host in enumerate(df["host"].unique()):
        hdf   = df[df["host"] == host]
        color = COLOURS[i % len(COLOURS)]
        fill  = FILL_COLOURS[i % len(FILL_COLOURS)]
        fig.add_trace(go.Scatter(
            x=hdf["timestamp"], y=hdf["latency_ms"],
            name=host, mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=4, color=color),
            fill="tozeroy", fillcolor=fill,
        ))
        # Max line (dashed)
        fig.add_trace(go.Scatter(
            x=hdf["timestamp"], y=hdf["latency_ms"] * 1.1,
            name=f"{host} max", mode="lines",
            line=dict(color=color, width=1, dash="dash"),
            showlegend=False,
        ))
    fig.add_hline(y=150, line_dash="dash",
                  line_color="#f59e0b", line_width=1,
                  annotation_text="150ms",
                  annotation_font_color="#f59e0b",
                  annotation_font_size=8)
    fig.add_hline(y=300, line_dash="dash",
                  line_color=PINK, line_width=1,
                  annotation_text="300ms",
                  annotation_font_color=PINK,
                  annotation_font_size=8)
    layout = dict(BASE)
    layout["height"] = 220
    layout["yaxis"]  = dict(
        gridcolor=BORDER, zerolinecolor=BORDER,
        tickfont=dict(color=DIM, size=8))
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)


def render_packet_loss_chart(summary: list):
    _hdr(PURPLE, "PACKET LOSS (%)")
    if not summary:
        st.caption("No data yet")
        return
    df = pd.DataFrame(summary)
    df["avg_loss_percent"] = df["avg_loss_percent"].fillna(0)
    # Short host names for x axis
    df["short"] = df["host"].apply(
        lambda h: h[:6] if len(h) > 6 else h)
    fig = go.Figure()
    for i, row in df.iterrows():
        color = COLOURS[i % len(COLOURS)]
        fig.add_trace(go.Bar(
            x=[row["short"]], y=[row["avg_loss_percent"]],
            name=row["host"], marker_color=color,
            marker_line=dict(color=BORDER, width=0.5),
        ))
    fig.add_hline(y=2, line_dash="dot",
                  line_color="#f59e0b", line_width=1)
    layout = dict(BASE)
    layout["height"]     = 220
    layout["showlegend"] = False
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)


def render_latency_per_device(summary: list):
    _hdr(MAGENTA, "LATENCY PER DEVICE")
    rows = [{"host": s["host"],
             "latency": s["avg_latency_ms"]}
            for s in summary
            if s.get("avg_latency_ms") is not None]
    if not rows:
        st.caption("No data yet")
        return
    df = pd.DataFrame(rows).sort_values("latency")
    fig = go.Figure()
    for i, row in df.iterrows():
        color = COLOURS[i % len(COLOURS)]
        fig.add_trace(go.Bar(
            y=[row["host"]], x=[row["latency"]],
            orientation="h", name=row["host"],
            marker_color=color,
            text=f"{row['latency']}ms",
            textposition="outside",
            textfont=dict(color="#ccccdd", size=8),
        ))
    fig.add_vline(x=150, line_dash="dash",
                  line_color="#f59e0b", line_width=1)
    layout = dict(BASE)
    layout["height"]     = 220
    layout["showlegend"] = False
    layout["xaxis"]      = dict(
        gridcolor=BORDER, zerolinecolor=BORDER,
        tickfont=dict(color=DIM, size=8))
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)


def render_health_donut(summary: list, alerts: list):
    _hdr(HOTPINK, "NETWORK HEALTH")
    healthy  = sum(1 for s in summary
                   if (s.get("avg_latency_ms") or 0) > 0
                   and (s.get("avg_latency_ms") or 999) < 150)
    degraded = sum(1 for s in summary
                   if (s.get("avg_latency_ms") or 0) > 0
                   and 150 <= (s.get("avg_latency_ms") or 0) < 300)
    offline  = sum(1 for s in summary
                   if not s.get("avg_latency_ms"))
    labels, values, colors = [], [], []
    if healthy  > 0:
        labels.append("Healthy")
        values.append(healthy)
        colors.append("#22c55e")
    if degraded > 0:
        labels.append("Degraded")
        values.append(degraded)
        colors.append("#f59e0b")
    if offline  > 0:
        labels.append("Offline")
        values.append(offline)
        colors.append(PINK)
    if not values:
        st.caption("No data")
        return
    critical = sum(1 for a in alerts
                   if a.get("severity") == "CRITICAL")
    warning  = sum(1 for a in alerts
                   if a.get("severity") == "WARNING")
    score    = max(0, 100 - critical * 25 - warning * 10)
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.65,
        marker_colors=colors,
        textinfo="label+percent",
        textfont=dict(color="#ccccdd", size=9),
        marker=dict(line=dict(color=CARD, width=2)),
    ))
    fig.add_annotation(text=f"<b>{score}</b>",
                       x=0.5, y=0.56, showarrow=False,
                       font=dict(size=26, color="#ffffff",
                                 family="Courier New"))
    fig.add_annotation(text="score",
                       x=0.5, y=0.4, showarrow=False,
                       font=dict(size=9, color=DIM,
                                 family="Courier New"))
    layout = dict(BASE)
    layout["height"]     = 220
    layout["showlegend"] = True
    layout["legend"]     = dict(
        bgcolor=CARD, font=dict(color="#ccccdd", size=9),
        orientation="v", x=0.72, y=0.5)
    layout["margin"] = dict(l=0, r=0, t=20, b=10)
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)


def render_uptime_bars(summary: list):
    _hdr(VIOLET, "UPTIME PER DEVICE")
    rows = []
    for s in summary:
        on  = s.get("times_online",  0) or 0
        off = s.get("times_offline", 0) or 0
        tot = on + off
        rows.append({"host": s["host"],
                     "uptime": round((on/tot)*100, 1)
                     if tot > 0 else 0})
    if not rows:
        st.caption("No data yet")
        return
    df = pd.DataFrame(rows).sort_values("uptime")
    fig = go.Figure()
    for i, row in df.iterrows():
        color = COLOURS[i % len(COLOURS)]
        fig.add_trace(go.Bar(
            y=[row["host"]], x=[row["uptime"]],
            orientation="h", name=row["host"],
            marker_color=color,
            text=f"{row['uptime']}%",
            textposition="outside",
            textfont=dict(color="#ccccdd", size=9),
        ))
    layout = dict(BASE)
    layout["height"]     = 220
    layout["showlegend"] = False
    layout["xaxis"]      = dict(
        range=[0, 115], gridcolor=BORDER,
        zerolinecolor=BORDER, ticksuffix="%",
        tickfont=dict(color=DIM, size=8))
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)


def render_device_status_table(summary: list):
    _hdr(MAGENTA, "DEVICE STATUS TABLE")
    if not summary:
        st.caption("No devices")
        return
    rows = []
    for s in summary:
        latency = s.get("avg_latency_ms")
        loss    = s.get("avg_loss_percent")
        on      = s.get("times_online",  0) or 0
        off     = s.get("times_offline", 0) or 0
        tot     = on + off
        uptime  = round((on/tot)*100, 1) if tot > 0 else 0
        if not latency:
            h = "✗ OFFLINE"
        elif latency < 50 and (loss or 0) == 0:
            h = "✓ EXCELLENT"
        elif latency < 150 and (loss or 0) <= 2:
            h = "✓ GOOD"
        elif latency < 300 or (loss or 0) <= 10:
            h = "~ DEGRADED"
        else:
            h = "! POOR"
        rows.append({
            "Host":    s["host"],
            "Latency": f"{latency} ms" if latency else "N/A",
            "Loss":    f"{loss}%" if loss is not None else "N/A",
            "Uptime":  f"{uptime}%",
            "Health":  h,
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True,
                 hide_index=True, height=180)