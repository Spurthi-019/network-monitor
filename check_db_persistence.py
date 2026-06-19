#!/usr/bin/env python
# Verify database persistence

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from database.db import get_all_devices, get_metrics_summary

print("\n" + "=" * 70)
print("DATABASE PERSISTENCE CHECK")
print("=" * 70)

devices = get_all_devices()
print(f"\nDevices in database: {len(devices)}")
for d in devices:
    print(f"  → {d['host']}:{d['port']} ({d['label']})")

print("\nMetrics summary:")
summary = get_metrics_summary()
if summary:
    for s in summary:
        print(f"  → {s['host']}: {s['total_checks']} checks, avg={s['avg_latency_ms']}ms")
else:
    print("  (No metrics yet)")

print("\n" + "=" * 70)
