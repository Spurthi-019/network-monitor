#!/usr/bin/env python
# Quick test of diagnostic rules
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from diagnostics.rules import ALL_RULES

# Test report 1: Excellent connection
report_good = {
    'host': 'google.com',
    'reachable': True,
    'latency_ms': 45.5,
    'packet_loss_percent': 0.0,
    'message': 'Device is performing perfectly'
}

print('=' * 60)
print('TEST 1: Good Connection')
print('=' * 60)
for rule in ALL_RULES:
    result = rule(report_good)
    print(f"  {result['rule']:20s} | {result['severity']:10s} | {result['detail']}")

# Test report 2: Offline device  
report_offline = {
    'host': '192.168.1.1',
    'reachable': False,
    'latency_ms': None,
    'packet_loss_percent': None,
    'message': 'Port 80 is closed'
}

print()
print('=' * 60)
print('TEST 2: Offline Device')
print('=' * 60)
for rule in ALL_RULES:
    result = rule(report_offline)
    print(f"  {result['rule']:20s} | {result['severity']:10s} | {result['detail']}")

# Test report 3: High latency and packet loss
report_degraded = {
    'host': 'slow-server.com',
    'reachable': True,
    'latency_ms': 400.0,
    'packet_loss_percent': 5.0,
    'message': 'Device is reachable but performance is degraded'
}

print()
print('=' * 60)
print('TEST 3: High Latency & Packet Loss')
print('=' * 60)
for rule in ALL_RULES:
    result = rule(report_degraded)
    severity = result['severity']
    detail = result['detail']
    score = f" (Score: {result.get('score', 'N/A')})" if 'score' in result else ""
    print(f"  {result['rule']:20s} | {severity:10s} | {detail}{score}")
