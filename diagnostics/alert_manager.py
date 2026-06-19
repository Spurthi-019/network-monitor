# diagnostics/alert_manager.py
# Tracks repeated failures across monitoring rounds.
# Raises alerts when a device has consistent problems.

import sys
import time
from pathlib import Path
from collections import defaultdict

# Add parent directory to path so imports work when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from logger_setup import get_logger

logger = get_logger(__name__)

# How many consecutive failures before raising an alert
CONSECUTIVE_FAILURE_THRESHOLD = 3


class AlertManager:
    """
    Tracks the history of each device across monitoring rounds.

    Think of it like a doctor tracking a patient's vitals over time.
    One bad reading might be noise. Three bad readings in a row
    means something is definitely wrong.
    """

    def __init__(self):
        # consecutive_failures["google.com"] = 2
        # means google.com failed 2 rounds in a row
        self.consecutive_failures = defaultdict(int)

        # All alerts ever raised
        self.alert_history = []

        # Tracks if a device is currently in alert state
        self.active_alerts = {}

    def process_diagnosis(self, diagnosis: dict) -> dict | None:
        """
        Update failure tracking for one device after diagnosis.

        Returns:
            An alert dict if threshold is crossed, else None
        """

        host     = diagnosis["host"]
        severity = diagnosis["overall_severity"]

        if severity == "critical":
            # Increment failure counter for this device
            self.consecutive_failures[host] += 1
            count = self.consecutive_failures[host]

            logger.warning(
                f"Consecutive failure #{count} for {host}"
            )

            # Check if we've crossed the threshold
            if count >= CONSECUTIVE_FAILURE_THRESHOLD:
                alert = self._raise_alert(host, diagnosis, count)
                return alert

        else:
            # Device recovered — reset its counter
            if self.consecutive_failures[host] > 0:
                logger.info(
                    f"{host} recovered after "
                    f"{self.consecutive_failures[host]} failures"
                )
                self.consecutive_failures[host] = 0

                # Mark any active alert as resolved
                if host in self.active_alerts:
                    self.active_alerts[host]["resolved_at"] = (
                        time.strftime("%Y-%m-%d %H:%M:%S")
                    )
                    del self.active_alerts[host]

        return None

    def _raise_alert(self, host: str, diagnosis: dict,
                     count: int) -> dict:
        """Create and record an alert for a device."""

        alert = {
            "alert_id"         : f"{host}_{int(time.time())}",
            "host"             : host,
            "raised_at"        : time.strftime("%Y-%m-%d %H:%M:%S"),
            "consecutive_count": count,
            "severity"         : "critical",
            "issues"           : [
                i["issue_type"]
                for i in diagnosis.get("active_issues", [])
                if i.get("issue_type")
            ],
            "recommendations"  : diagnosis.get("recommendations", []),
            "resolved_at"      : None
        }

        self.alert_history.append(alert)
        self.active_alerts[host] = alert

        logger.error(
            f"ALERT RAISED | {host} | {count} consecutive "
            f"failures | issues={alert['issues']}"
        )

        return alert

    def get_active_alerts(self) -> list:
        """Return all currently active (unresolved) alerts."""
        return list(self.active_alerts.values())

    def get_alert_history(self) -> list:
        """Return all alerts ever raised."""
        return self.alert_history

    def print_status(self):
        """Print current alert manager status."""

        print("\n" + "=" * 55)
        print("  ALERT MANAGER STATUS")
        print("=" * 55)

        if self.active_alerts:
            print(f"  Active alerts: {len(self.active_alerts)}")
            for host, alert in self.active_alerts.items():
                print(f"  ✗ {host}")
                print(f"    Raised at : {alert['raised_at']}")
                print(f"    Failures  : {alert['consecutive_count']}")
                print(f"    Issues    : {alert['issues']}")
        else:
            print("  No active alerts — all devices healthy")

        if self.consecutive_failures:
            print("\n  Consecutive failure counts:")
            for host, count in self.consecutive_failures.items():
                if count > 0:
                    print(f"  {host}: {count} failure(s) in a row")

        print("=" * 55)
