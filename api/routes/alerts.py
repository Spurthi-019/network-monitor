# api/routes/alerts.py (UPDATED — now uses database)

import sys
from pathlib import Path

# Add parent directory to path so imports work when run directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, Query
from database.db import get_alerts
from logger_setup import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=list)
def get_alerts_endpoint(
    severity: str = Query(
        None,
        description="Filter by severity: OK, WARNING, CRITICAL"
    ),
    limit: int = Query(50, description="Max rows to return")
):
    """
    GET /alerts
    GET /alerts?severity=CRITICAL
    GET /alerts?severity=WARNING

    Returns diagnostic alerts from the database.
    Optionally filter by severity level.
    """
    alerts = get_alerts(severity=severity, limit=limit)
    logger.info(f"GET /alerts — {len(alerts)} alerts returned")
    return alerts
