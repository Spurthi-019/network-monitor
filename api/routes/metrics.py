# api/routes/metrics.py
# Handles /metrics and /monitor endpoints.
# Triggers actual network monitoring and returns results.

import sys
import time
from pathlib import Path

# Add parent directory to path so imports work when run directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException
from api.models import (
    MonitorRequest, MetricResponse,
    NetworkReportResponse, AlertResponse
)
from monitoring.thread_monitor import monitor_all_devices
from diagnostics.analyzer import analyze_all
from diagnostics.rules import SEVERITY_OK, SEVERITY_WARNING, SEVERITY_CRITICAL
from api.routes.devices import _devices
from logger_setup import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Metrics"])

# Store last monitoring results in memory
_last_results: list = []
_last_report:  dict = {}


def generate_network_report(diagnoses: list) -> dict:
    """
    Convert diagnostic results into a NetworkReportResponse.
    
    Summarizes:
    - Overall status (OK / WARNING / CRITICAL)
    - Health score (0-100)
    - Device counts by health status
    - All alerts
    """
    
    severity_rank = {SEVERITY_OK: 0, SEVERITY_WARNING: 1, SEVERITY_CRITICAL: 2}
    
    worst_severity = SEVERITY_OK
    for diag in diagnoses:
        curr_severity = diag.get("overall_severity", SEVERITY_OK)
        if severity_rank.get(curr_severity, 0) > severity_rank.get(worst_severity, 0):
            worst_severity = curr_severity
    
    # Count device statuses
    healthy = sum(1 for d in diagnoses if d["overall_severity"] == SEVERITY_OK)
    warning = sum(1 for d in diagnoses if d["overall_severity"] == SEVERITY_WARNING)
    critical = sum(1 for d in diagnoses if d["overall_severity"] == SEVERITY_CRITICAL)
    
    # Get hosts by severity
    critical_hosts = [d["host"] for d in diagnoses if d["overall_severity"] == SEVERITY_CRITICAL]
    warning_hosts = [d["host"] for d in diagnoses if d["overall_severity"] == SEVERITY_WARNING]
    
    # Average health score across all devices
    scores = [d.get("health_score", 0) for d in diagnoses if d.get("health_score") is not None]
    avg_health_score = int(sum(scores) / len(scores)) if scores else 0
    
    # Build alert list from active issues
    alerts = []
    for diag in diagnoses:
        for issue in diag.get("active_issues", []):
            alert = AlertResponse(
                host=diag["host"],
                severity=issue["severity"],
                rule_triggered=issue["rule"],
                detail=issue["detail"],
                recommendation=issue.get("recommendation", ""),
                timestamp=diag["timestamp"],
                latency_ms=diag["raw_report"].get("latency_ms"),
                packet_loss_percent=diag["raw_report"].get("packet_loss_percent")
            )
            alerts.append(alert)
    
    # Map severity to status string
    status_map = {
        SEVERITY_OK: "OK",
        SEVERITY_WARNING: "WARNING",
        SEVERITY_CRITICAL: "CRITICAL"
    }
    
    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "overall_status": status_map.get(worst_severity, "UNKNOWN"),
        "health_score": avg_health_score,
        "total_devices": len(diagnoses),
        "healthy_count": healthy,
        "warning_count": warning,
        "critical_count": critical,
        "critical_hosts": critical_hosts,
        "warning_hosts": warning_hosts,
        "alerts": alerts
    }


@router.get("/metrics", response_model=list[MetricResponse])
def get_last_metrics():
    """
    GET /metrics

    Returns the results from the most recent monitoring run.
    Returns empty list if no monitoring has been done yet.

    Tip: Call POST /monitor first to populate this.
    """
    if not _last_results:
        return []

    logger.info(f"GET /metrics — returning {len(_last_results)} results")
    return _last_results


@router.get("/status")
def get_network_status():
    """
    GET /status

    Returns the overall network health status.
    Quick summary — no full report details.

    Example response:
    {
        "overall_status": "WARNING",
        "health_score": 75,
        "total_devices": 5,
        "online": 4,
        "offline": 1
    }
    """
    if not _last_report:
        return {
            "overall_status": "UNKNOWN",
            "health_score":   None,
            "message": "No monitoring data yet. Call POST /monitor first."
        }

    return {
        "overall_status": _last_report.get("overall_status"),
        "health_score":   _last_report.get("health_score"),
        "total_devices":  _last_report.get("total_devices"),
        "online":         _last_report.get("healthy_count", 0)
                          + _last_report.get("warning_count", 0),
        "offline":        _last_report.get("critical_count", 0),
        "timestamp":      _last_report.get("timestamp"),
    }


@router.post("/monitor", response_model=NetworkReportResponse)
def run_monitoring(request: MonitorRequest = None):
    """
    POST /monitor

    Trigger a full monitoring run RIGHT NOW.

    Option A — monitor specific hosts (send request body):
    {
        "hosts": ["google.com", "8.8.8.8"],
        "ports": [80, 53]
    }

    Option B — monitor all saved devices (empty body):
    POST /monitor  with no body

    Returns a full network diagnostic report.
    """
    global _last_results, _last_report

    # Build target list
    if request and request.hosts:
        # Use hosts from request body
        ports = request.ports or []
        targets = []
        for i, host in enumerate(request.hosts):
            port = ports[i] if i < len(ports) else 80
            targets.append((host, port))
    else:
        # Fall back to saved device list
        targets = [(d["host"], d["port"]) for d in _devices]

    if not targets:
        raise HTTPException(
            status_code=400,
            detail="No targets to monitor. Add devices first."
        )

    logger.info(f"POST /monitor — starting run for {len(targets)} targets")

    # Run monitoring (Phase 3)
    raw_results = monitor_all_devices(targets)

    # Run diagnostics (Phase 5)
    diagnoses = analyze_all(raw_results)
    network_report = generate_network_report(diagnoses)

    # Store for GET /metrics and GET /status
    _last_results = raw_results
    _last_report  = network_report

    logger.info(
        f"POST /monitor — complete. "
        f"Status={network_report['overall_status']} "
        f"Score={network_report['health_score']}"
    )

    return network_report
