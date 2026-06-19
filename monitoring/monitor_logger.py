# monitoring/monitor_logger.py
# Wraps monitoring functions with automatic logging.
# Every check result is saved to log files automatically.

import sys
import time
from pathlib import Path

# Add parent directory to path so imports work when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from logger_setup import get_logger, setup_logging
from monitoring.thread_monitor import monitor_all_devices

# Get a logger named after this module
logger = get_logger(__name__)


def log_result(report: dict):
    """
    Log a single connectivity report at the correct log level.

    Health mapping:
      excellent / good  → INFO
      degraded          → WARNING
      poor / offline    → ERROR
    """

    host    = report.get("host", "unknown")
    health  = report.get("health", "unknown")
    latency = report.get("latency_ms")
    loss    = report.get("packet_loss_percent")
    message = report.get("message", "")

    # Build a structured log line
    latency_str = f"{latency}ms" if latency is not None else "N/A"
    loss_str    = f"{loss}%"     if loss    is not None else "N/A"

    log_line = (
        f"host={host} | "
        f"latency={latency_str} | "
        f"loss={loss_str} | "
        f"health={health} | "
        f"msg={message}"
    )

    # Choose log level based on health
    if health in ("excellent", "good"):
        logger.info(log_line)

    elif health == "degraded":
        logger.warning(log_line)

    elif health in ("poor", "offline", "unknown"):
        logger.error(log_line)

    else:
        logger.debug(log_line)


def log_monitoring_round(targets: list, round_num: int = 1) -> list:
    """
    Run one full monitoring round and log every result.

    Args:
        targets   : list of (host, port) tuples
        round_num : which round number this is (for log context)

    Returns:
        list of result dictionaries
    """

    logger.info(f"=== Monitoring round {round_num} started "
                f"— checking {len(targets)} devices ===")

    start = time.time()

    # Run all checks using threads (from Phase 3)
    results = monitor_all_devices(targets)

    elapsed = round(time.time() - start, 2)

    # Log each result
    for report in results:
        log_result(report)

    # Log round summary
    total    = len(results)
    online   = sum(1 for r in results if r["reachable"])
    offline  = total - online
    problems = sum(1 for r in results
                   if r["health"] in ("degraded", "poor", "offline"))

    logger.info(
        f"=== Round {round_num} complete in {elapsed}s | "
        f"online={online}/{total} | "
        f"problems={problems} ==="
    )

    if offline > 0:
        logger.warning(
            f"{offline} device(s) OFFLINE in round {round_num}"
        )

    return results


def run_logged_monitoring(targets: list, rounds: int = 3,
                           interval: int = 10):
    """
    Run multiple monitoring rounds with full logging.

    Args:
        targets  : list of (host, port) tuples
        rounds   : number of rounds to run
        interval : seconds between rounds
    """

    logger.info("Network monitoring system STARTED")
    logger.info(f"Targets: {[h for h, p in targets]}")

    for round_num in range(1, rounds + 1):
        results = log_monitoring_round(targets, round_num)

        if round_num < rounds:
            logger.info(f"Sleeping {interval}s before next round...")
            time.sleep(interval)

    logger.info("Network monitoring system STOPPED")
    return results


# ── Test this file directly ───────────────────────────────────
if __name__ == "__main__":

    # IMPORTANT: always call setup_logging() once at the start
    setup_logging()

    logger.info("Starting Phase 4 logging test")

    targets = [
        ("google.com",  80),
        ("github.com",  80),
        ("8.8.8.8",     53),
        ("1.1.1.1",     53),
        ("192.168.1.1", 80),   # likely offline
    ]

    # Run 2 rounds, 10 seconds apart
    run_logged_monitoring(targets, rounds=2, interval=10)

    print("\n" + "=" * 60)
    print("  Check your log files:")
    print("  logs/performance.log  ← all activity")
    print("  logs/errors.log       ← only warnings and errors")
    print("=" * 60)
