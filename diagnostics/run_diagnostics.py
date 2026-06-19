# diagnostics/run_diagnostics.py
# Entry point to test the full diagnostic pipeline.

import sys
import time
from pathlib import Path

# Add parent directory to path so imports work when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from logger_setup import setup_logging, get_logger
from monitoring.thread_monitor import monitor_all_devices
from diagnostics.analyzer import analyze_all, print_diagnosis_report
from diagnostics.alert_manager import AlertManager

logger = get_logger(__name__)


def run_full_diagnostic(targets: list, rounds: int = 3,
                         interval_sec: int = 10):
    """
    Run full monitoring + diagnostics for multiple rounds.
    Simulates what a real production system does continuously.
    """

    alert_manager = AlertManager()

    for round_num in range(1, rounds + 1):
        print(f"\n{'='*55}")
        print(f"  ROUND {round_num} of {rounds}")
        print(f"{'='*55}")

        # Step 1: Monitor all devices (Phase 3)
        logger.info(f"Round {round_num} — starting monitoring")
        reports = monitor_all_devices(targets)

        # Step 2: Diagnose every result (Phase 5)
        diagnoses = analyze_all(reports)

        # Step 3: Print diagnosis report
        print_diagnosis_report(diagnoses)

        # Step 4: Check for repeated failures
        for diagnosis in diagnoses:
            alert = alert_manager.process_diagnosis(diagnosis)
            if alert:
                print(f"\n  ⚠  ALERT: {alert['host']} has failed "
                      f"{alert['consecutive_count']} times in a row!")
                print(f"     Issues: {alert['issues']}")

        # Step 5: Show alert manager status
        alert_manager.print_status()

        if round_num < rounds:
            print(f"\n  Waiting {interval_sec}s before round "
                  f"{round_num + 1}...")
            time.sleep(interval_sec)

    logger.info("Diagnostic session complete")


# ── Run it ────────────────────────────────────────────────────
if __name__ == "__main__":

    setup_logging()

    targets = [
        ("google.com",  80),
        ("github.com",  80),
        ("8.8.8.8",     53),
        ("1.1.1.1",     53),
        ("192.168.1.1", 80),   # likely offline — will trigger alerts
    ]

    run_full_diagnostic(targets, rounds=3, interval_sec=10)
