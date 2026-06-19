# api/routes/devices.py
# Handles all /devices endpoints.
# Manages the list of devices to monitor.

import sys
from pathlib import Path

# Add parent directory to path so imports work when run directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException
from api.models import DeviceAddRequest, DeviceResponse, APIResponse
from logger_setup import get_logger

logger = get_logger(__name__)

# APIRouter is like a mini-app for grouping related endpoints
router = APIRouter(prefix="/devices", tags=["Devices"])

# In-memory device store (Phase 7 will replace with database)
# This is a simple list of dicts — resets when server restarts
_devices: list = [
    {"host": "google.com",  "port": 80, "label": "Google"},
    {"host": "github.com",  "port": 80, "label": "GitHub"},
    {"host": "8.8.8.8",     "port": 53, "label": "Google DNS"},
    {"host": "1.1.1.1",     "port": 53, "label": "Cloudflare DNS"},
]


@router.get("/", response_model=list[DeviceResponse])
def get_all_devices():
    """
    GET /devices

    Returns the list of all devices being monitored.

    Example response:
    [
        {"host": "google.com", "port": 80, "label": "Google"},
        {"host": "8.8.8.8",   "port": 53, "label": "Google DNS"}
    ]
    """
    logger.info(f"GET /devices — returning {len(_devices)} devices")
    return _devices


@router.get("/{host}", response_model=DeviceResponse)
def get_device(host: str):
    """
    GET /devices/{host}

    Returns details for a single device by hostname.

    Example: GET /devices/google.com
    """
    for device in _devices:
        if device["host"] == host:
            return device

    # If not found, return HTTP 404
    raise HTTPException(
        status_code=404,
        detail=f"Device '{host}' not found in monitoring list"
    )


@router.post("/", response_model=APIResponse)
def add_device(request: DeviceAddRequest):
    """
    POST /devices

    Add a new device to the monitoring list.

    Request body:
    {
        "host": "cloudflare.com",
        "port": 80,
        "label": "Cloudflare"
    }
    """
    # Check if already exists
    for device in _devices:
        if device["host"] == request.host:
            raise HTTPException(
                status_code=409,
                detail=f"Device '{request.host}' already exists"
            )

    new_device = {
        "host":  request.host,
        "port":  request.port,
        "label": request.label or request.host,
    }
    _devices.append(new_device)

    logger.info(f"Added new device: {request.host}:{request.port}")

    return APIResponse(
        success=True,
        message=f"Device '{request.host}' added successfully",
        data=new_device
    )


@router.delete("/{host}", response_model=APIResponse)
def remove_device(host: str):
    """
    DELETE /devices/{host}

    Remove a device from the monitoring list.

    Example: DELETE /devices/google.com
    """
    global _devices
    original_count = len(_devices)
    _devices = [d for d in _devices if d["host"] != host]

    if len(_devices) == original_count:
        raise HTTPException(
            status_code=404,
            detail=f"Device '{host}' not found"
        )

    logger.info(f"Removed device: {host}")
    return APIResponse(
        success=True,
        message=f"Device '{host}' removed successfully"
    )
