# diagnostics/rules.py
# Defines all diagnostic rules.
# A rule takes a monitoring result and returns a diagnosis.
# Adding a new rule = adding a new function. Clean and simple.

# ── Severity levels ──────────────────────────────────────────
# These are the possible outcomes of any diagnosis
SEVERITY_OK       = "ok"        # everything is fine
SEVERITY_WARNING  = "warning"   # something needs attention
SEVERITY_CRITICAL = "critical"  # action required immediately

# ── Thresholds ───────────────────────────────────────────────
# Change these values to tune sensitivity
LATENCY_WARNING_MS  = 150   # above this = warning
LATENCY_CRITICAL_MS = 300   # above this = critical

LOSS_WARNING_PCT    = 2.0   # above this = warning
LOSS_CRITICAL_PCT   = 10.0  # above this = critical


def diagnose_latency(report: dict) -> dict:
    """
    Rule: check if latency is too high.

    Args:
        report: a connectivity result dictionary from Phase 2/3

    Returns:
        A diagnosis dictionary with severity and recommendation
    """

    diagnosis = {
        "rule"           : "latency_check",
        "severity"       : SEVERITY_OK,
        "issue_type"     : None,
        "detail"         : "",
        "recommendation" : ""
    }

    latency = report.get("latency_ms")

    # If device is offline, latency check is not applicable
    if latency is None:
        diagnosis["severity"]   = SEVERITY_OK
        diagnosis["detail"]     = "No latency data — device unreachable"
        return diagnosis

    if latency > LATENCY_CRITICAL_MS:
        diagnosis["severity"]        = SEVERITY_CRITICAL
        diagnosis["issue_type"]      = "high_latency"
        diagnosis["detail"]          = (
            f"Latency {latency}ms exceeds critical threshold "
            f"({LATENCY_CRITICAL_MS}ms)"
        )
        diagnosis["recommendation"]  = (
            "Investigate network path — check for congestion, "
            "routing issues, or overloaded device"
        )

    elif latency > LATENCY_WARNING_MS:
        diagnosis["severity"]        = SEVERITY_WARNING
        diagnosis["issue_type"]      = "elevated_latency"
        diagnosis["detail"]          = (
            f"Latency {latency}ms exceeds warning threshold "
            f"({LATENCY_WARNING_MS}ms)"
        )
        diagnosis["recommendation"]  = (
            "Monitor closely — may indicate network congestion "
            "or increased load"
        )

    else:
        diagnosis["detail"] = f"Latency {latency}ms is within normal range"

    return diagnosis


def diagnose_packet_loss(report: dict) -> dict:
    """
    Rule: check if packet loss is too high.
    """

    diagnosis = {
        "rule"           : "packet_loss_check",
        "severity"       : SEVERITY_OK,
        "issue_type"     : None,
        "detail"         : "",
        "recommendation" : ""
    }

    loss = report.get("packet_loss_percent")

    if loss is None:
        diagnosis["detail"] = "No packet loss data available"
        return diagnosis

    if loss > LOSS_CRITICAL_PCT:
        diagnosis["severity"]        = SEVERITY_CRITICAL
        diagnosis["issue_type"]      = "severe_packet_loss"
        diagnosis["detail"]          = (
            f"Packet loss {loss}% exceeds critical threshold "
            f"({LOSS_CRITICAL_PCT}%)"
        )
        diagnosis["recommendation"]  = (
            "Connection is severely degraded — check physical "
            "cables, Wi-Fi signal, or ISP issues"
        )

    elif loss > LOSS_WARNING_PCT:
        diagnosis["severity"]        = SEVERITY_WARNING
        diagnosis["issue_type"]      = "packet_loss_detected"
        diagnosis["detail"]          = (
            f"Packet loss {loss}% exceeds warning threshold "
            f"({LOSS_WARNING_PCT}%)"
        )
        diagnosis["recommendation"]  = (
            "Some packets are being dropped — monitor for "
            "worsening trend"
        )

    else:
        diagnosis["detail"] = f"Packet loss {loss}% is acceptable"

    return diagnosis


def diagnose_connectivity(report: dict) -> dict:
    """
    Rule: check if device is reachable at all.
    """

    diagnosis = {
        "rule"           : "connectivity_check",
        "severity"       : SEVERITY_OK,
        "issue_type"     : None,
        "detail"         : "",
        "recommendation" : ""
    }

    reachable = report.get("reachable", False)
    host      = report.get("host", "unknown")
    message   = report.get("message", "")

    if not reachable:
        diagnosis["severity"]       = SEVERITY_CRITICAL
        diagnosis["issue_type"]     = "device_unreachable"
        diagnosis["detail"]         = (
            f"Device '{host}' is not reachable. Reason: {message}"
        )
        diagnosis["recommendation"] = (
            "Verify the device is powered on, check network "
            "cables, firewall rules, and DNS resolution"
        )
    else:
        diagnosis["detail"] = f"Device '{host}' is reachable"

    return diagnosis


def diagnose_health_score(report: dict) -> dict:
    """
    Rule: overall health score based on combined metrics.
    Gives a single number 0-100 summarising device health.

    Scoring:
      Start at 100
      Deduct points for latency, loss, and offline status
    """

    diagnosis = {
        "rule"        : "health_score",
        "severity"    : SEVERITY_OK,
        "issue_type"  : None,
        "score"       : 100,
        "detail"      : "",
        "recommendation": ""
    }

    score   = 100
    reasons = []

    # Deduct for being offline
    if not report.get("reachable", False):
        score = 0
        reasons.append("device offline (-100)")

    else:
        # Deduct for latency
        latency = report.get("latency_ms") or 0
        if latency > LATENCY_CRITICAL_MS:
            score -= 40
            reasons.append(f"critical latency (-40)")
        elif latency > LATENCY_WARNING_MS:
            score -= 20
            reasons.append(f"elevated latency (-20)")

        # Deduct for packet loss
        loss = report.get("packet_loss_percent") or 0
        if loss > LOSS_CRITICAL_PCT:
            score -= 40
            reasons.append(f"critical packet loss (-40)")
        elif loss > LOSS_WARNING_PCT:
            score -= 20
            reasons.append(f"packet loss detected (-20)")

    score = max(0, score)   # never go below 0
    diagnosis["score"] = score

    if score == 100:
        diagnosis["severity"] = SEVERITY_OK
        diagnosis["detail"]   = "Perfect health score"
    elif score >= 60:
        diagnosis["severity"] = SEVERITY_WARNING
        diagnosis["detail"]   = f"Score {score}/100 — {', '.join(reasons)}"
    else:
        diagnosis["severity"]        = SEVERITY_CRITICAL
        diagnosis["issue_type"]      = "poor_health"
        diagnosis["detail"]          = f"Score {score}/100 — {', '.join(reasons)}"
        diagnosis["recommendation"]  = "Immediate investigation required"

    return diagnosis


# Registry: all rules in one list — easy to add new ones
ALL_RULES = [
    diagnose_connectivity,
    diagnose_latency,
    diagnose_packet_loss,
    diagnose_health_score,
]
