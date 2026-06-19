# monitoring/connectivity.py
# Updated to use ping as primary method on Windows
# since socket connections may be blocked by firewall

import subprocess
import re
import time
try:
    from monitoring.packet_loss import calculate_packet_loss
except ImportError:
    from packet_loss import calculate_packet_loss


def check_connectivity(host: str, port: int = 80) -> dict:
    """
    Full connectivity check using Windows ping command.
    More reliable on Windows than raw sockets.
    """

    report = {
        "host":                 host,
        "port":                 port,
        "timestamp":            time.strftime("%Y-%m-%d %H:%M:%S"),
        "reachable":            False,
        "latency_ms":           None,
        "packet_loss_percent":  None,
        "health":               "unknown",
        "message":              ""
    }

    try:
        # Use Windows ping command
        command = ["ping", "-n", "4", host]
        process = subprocess.run(
            command,
            capture_output = True,
            text           = True,
            timeout        = 30
        )
        output = process.stdout

        # Check if ping succeeded
        if "Reply from" in output or "reply from" in output:
            report["reachable"] = True

            # Extract average latency
            avg_match = re.search(r"Average\s*=\s*(\d+)ms", output)
            if avg_match:
                report["latency_ms"] = float(avg_match.group(1))

            # Extract packet loss
            loss_match = re.search(r"Lost\s*=\s*(\d+)", output)
            sent_match = re.search(r"Sent\s*=\s*(\d+)", output)
            if loss_match and sent_match:
                lost = int(loss_match.group(1))
                sent = int(sent_match.group(1))
                report["packet_loss_percent"] = round(
                    (lost / sent) * 100, 1
                ) if sent > 0 else 0.0
            else:
                report["packet_loss_percent"] = 0.0

            # Determine health
            latency = report["latency_ms"] or 0
            loss    = report["packet_loss_percent"] or 0

            if latency < 50 and loss == 0:
                report["health"]  = "excellent"
                report["message"] = "Device is performing perfectly"
            elif latency < 150 and loss <= 2:
                report["health"]  = "good"
                report["message"] = "Device is healthy with minor variation"
            elif latency < 300 or loss <= 10:
                report["health"]  = "degraded"
                report["message"] = "Performance is degraded"
            else:
                report["health"]  = "poor"
                report["message"] = "Device has serious connectivity issues"

        elif "Request timed out" in output:
            report["reachable"] = False
            report["health"]    = "offline"
            report["message"]   = "Device timed out — may be offline"

        elif "could not find host" in output.lower():
            report["reachable"] = False
            report["health"]    = "offline"
            report["message"]   = f"DNS failure — cannot resolve {host}"

        else:
            report["reachable"] = False
            report["health"]    = "offline"
            report["message"]   = "Host did not respond to ping"

    except subprocess.TimeoutExpired:
        report["reachable"] = False
        report["health"]    = "offline"
        report["message"]   = "Ping command timed out"

    except Exception as e:
        report["reachable"] = False
        report["health"]    = "offline"
        report["message"]   = str(e)

    return report


def check_multiple_hosts(hosts: list) -> list:
    """Check a list of (host, port) tuples one by one."""
    reports = []
    for host, port in hosts:
        print(f"  Checking {host}:{port} ...")
        report = check_connectivity(host, port)
        reports.append(report)
    return reports


# ── Test directly ─────────────────────────────────────────────
if __name__ == "__main__":

    targets = [
        ("google.com",  80),
        ("github.com",  80),
        ("8.8.8.8",     53),
        ("1.1.1.1",     53),
        ("192.168.1.1", 80),
    ]

    print("=" * 60)
    print("  Connectivity Test — using ping")
    print("=" * 60)

    for host, port in targets:
        r = check_connectivity(host, port)
        latency = f"{r['latency_ms']} ms" if r['latency_ms'] else "N/A"
        print(f"  {host:<20} {latency:<12} "
              f"{r['health']:<12} {r['message']}")