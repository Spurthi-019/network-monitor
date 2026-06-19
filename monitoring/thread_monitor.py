# monitoring/thread_monitor.py
# Monitors multiple devices SIMULTANEOUSLY using threads.
# Each device gets its own thread. Results are collected safely.

import threading        # Python's built-in threading library
import time
import sys
from pathlib import Path

# Add parent directory to path so imports work when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from monitoring.connectivity import check_connectivity


# ── Thread-safe result collector ─────────────────────────────
# This list stores results from all threads.
# The Lock ensures only one thread writes to it at a time.

results_list = []
results_lock = threading.Lock()   # the "only one writer at a time" guard


def monitor_single_device(host: str, port: int):
    """
    This function runs INSIDE a thread.
    Each thread calls this for its own device.

    Steps:
      1. Check connectivity for this device
      2. Acquire the lock (wait if another thread is writing)
      3. Save the result to the shared list
      4. Release the lock (let the next thread write)
    """

    print(f"  [Thread] Starting check → {host}:{port}")

    # Do the actual network check (this is the slow part)
    report = check_connectivity(host, port)

    # Safely add result to the shared list
    with results_lock:
        # 'with results_lock' automatically:
        #   - acquires the lock before the block
        #   - releases the lock after the block
        #   - even if an error occurs inside
        results_list.append(report)

    print(f"  [Thread] Finished check  → {host}:{port}  "
          f"({report['health'].upper()})")


def monitor_all_devices(targets: list) -> list:
    """
    Launch one thread per device and wait for all to finish.

    Args:
        targets: list of (host, port) tuples
                 e.g. [("google.com", 80), ("8.8.8.8", 53)]

    Returns:
        List of result dictionaries, one per device
    """

    global results_list
    results_list = []   # clear previous results before each run

    threads = []        # keep track of all thread objects

    print(f"\n  Launching {len(targets)} threads simultaneously...")
    print("  " + "-" * 50)

    start_time = time.time()

    # Step 1: Create and start one thread per device
    for host, port in targets:
        # threading.Thread(target=fn, args=(a, b)) creates a thread
        # target = the function the thread will run
        # args   = the arguments to pass to that function
        thread = threading.Thread(
            target=monitor_single_device,
            args=(host, port),
            name=f"monitor-{host}"   # give thread a readable name
        )
        threads.append(thread)
        thread.start()   # THIS is where the thread actually begins running

    # Step 2: Wait for ALL threads to finish
    # thread.join() blocks until that thread completes
    for thread in threads:
        thread.join()

    total_time = round(time.time() - start_time, 2)

    print("  " + "-" * 50)
    print(f"  All threads finished in {total_time} seconds")

    return results_list.copy()


def print_results_table(results: list):
    """Print monitoring results in a clean table format."""

    # Sort: online devices first, then by health rating
    health_order = {"excellent": 0, "good": 1, "degraded": 2,
                    "poor": 3, "offline": 4, "unknown": 5}

    sorted_results = sorted(
        results,
        key=lambda r: health_order.get(r["health"], 99)
    )

    print()
    print("=" * 70)
    print("  MONITORING REPORT")
    print("=" * 70)
    print(f"  {'Host':<22} {'Status':<8} {'Latency':<12} "
          f"{'Loss':<8} {'Health':<12} {'Message'}")
    print("  " + "-" * 68)

    for r in sorted_results:
        latency = f"{r['latency_ms']} ms" if r['latency_ms'] else "N/A"
        loss    = f"{r['packet_loss_percent']}%" \
                  if r['packet_loss_percent'] is not None else "N/A"
        status  = "UP  " if r["reachable"] else "DOWN"

        # Pick a visual indicator based on health
        indicator = {
            "excellent": "✓",
            "good":      "✓",
            "degraded":  "~",
            "poor":      "!",
            "offline":   "✗",
        }.get(r["health"], "?")

        print(f"  {indicator} {r['host']:<20} {status:<8} {latency:<12} "
              f"{loss:<8} {r['health']:<12} {r['message'][:28]}")

    print("=" * 70)


def run_continuous_monitoring(targets: list, interval: int = 30,
                              rounds: int = 3):
    """
    Run monitoring repeatedly every `interval` seconds.
    This simulates real production monitoring.

    Args:
        targets  : list of (host, port) tuples
        interval : seconds between each monitoring round
        rounds   : how many times to run (use 0 for infinite)
    """

    round_num = 0

    print("\n" + "=" * 70)
    print("  CONTINUOUS MONITORING STARTED")
    print(f"  Checking {len(targets)} devices every {interval} seconds")
    print(f"  Press Ctrl+C to stop")
    print("=" * 70)

    try:
        while True:
            round_num += 1
            print(f"\n  Round {round_num} — {time.strftime('%Y-%m-%d %H:%M:%S')}")

            results = monitor_all_devices(targets)
            print_results_table(results)

            # Stop if we've done enough rounds
            if rounds > 0 and round_num >= rounds:
                print(f"\n  Completed {rounds} rounds. Stopping.")
                break

            # Wait before next round
            print(f"\n  Next check in {interval} seconds... (Ctrl+C to stop)")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n  Monitoring stopped by user.")

    return results


# ── Test this file directly ───────────────────────────────────
if __name__ == "__main__":

    # Define devices to monitor
    targets = [
        ("google.com",  80),
        ("github.com",  80),
        ("8.8.8.8",     53),
        ("1.1.1.1",     53),   # Cloudflare DNS
        ("192.168.1.1", 80),   # home router (may be offline)
    ]

    print("=" * 70)
    print("  PHASE 3 — Multi-Device Threaded Monitor")
    print("=" * 70)

    # ── Demo 1: Single round ──────────────────────────────────
    print("\n  DEMO 1: Single monitoring round")
    results = monitor_all_devices(targets)
    print_results_table(results)

    # ── Demo 2: Continuous monitoring (3 rounds, 10s apart) ──
    print("\n  DEMO 2: Continuous monitoring")
    print("  (3 rounds, 10 seconds apart — watch threads launch together)")
    run_continuous_monitoring(targets, interval=10, rounds=3)
