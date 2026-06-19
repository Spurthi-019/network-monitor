# api/models.py
# Pydantic models — define what data looks like coming IN and going OUT.
# FastAPI uses these to auto-validate requests and auto-generate docs.

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Request models (data the CLIENT sends TO your API) ────────

class DeviceAddRequest(BaseModel):
    """
    Shape of the JSON body when adding a new device to monitor.

    Example request body:
    {
        "host": "google.com",
        "port": 80,
        "label": "Google DNS"
    }
    """
    host:  str         = Field(..., example="google.com",
                               description="IP address or hostname")
    port:  int         = Field(80,  example=80,
                               description="Port number to check")
    label: Optional[str] = Field(None, example="Google",
                               description="Friendly name for the device")


class MonitorRequest(BaseModel):
    hosts: Optional[List[str]] = Field(None, example=["google.com", "8.8.8.8"])
    ports: Optional[List[int]] = Field(None, example=[80, 53])


# ── Response models (data your API sends BACK to the client) ──

class DeviceResponse(BaseModel):
    """One device in the device list."""
    host:   str
    port:   int
    label:  Optional[str] = None


class MetricResponse(BaseModel):
    """A single monitoring metric result."""
    host:                str
    timestamp:           str
    reachable:           bool
    latency_ms:          Optional[float] = None
    packet_loss_percent: Optional[float] = None
    health:              str
    message:             str


class AlertResponse(BaseModel):
    """A single diagnostic alert."""
    host:            str
    severity:        str
    rule_triggered:  str
    detail:          str
    recommendation:  str
    timestamp:       str
    latency_ms:          Optional[float] = None
    packet_loss_percent: Optional[float] = None


class NetworkReportResponse(BaseModel):
    """Full network health report returned by POST /monitor."""
    timestamp:      str
    overall_status: str
    health_score:   int
    total_devices:  int
    healthy_count:  int
    warning_count:  int
    critical_count: int
    critical_hosts: List[str]
    warning_hosts:  List[str]
    alerts:         List[AlertResponse]


class APIResponse(BaseModel):
    """Generic wrapper for simple success/error messages."""
    success: bool
    message: str
    data:    Optional[dict] = None
