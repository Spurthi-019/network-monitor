# monitoring/packet_loss.py
# Calculates how many packets are lost when communicating with a device

import subprocess
import re
import time


def calculate_packet_loss(host: str, count: int = 10) -> dict:
    """
    Send 'count' packets to host and measure how many are lost.

    How it works:
      We send 10 pings. If 3 don't come back → 30% loss.
      Windows ping already counts this for us in its output.

    Args:
        host  : Target IP or domain
        count : Number of packets to send (more = more accurate)

    Returns:
        Dictionary with loss percentage and packet counts
    """

    result = {
        "host": host,
        "packets_sent": count,
        "packets_received": 0,
        "packets_lost": 0,
        "loss_percent": 0.0,
        "status": "unknown",
        "error": None
    }

    try:
        command = ["ping", "-n", str(count), host]

        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60   # more packets = more time needed
        )

        output = process.stdout

        # Windows output contains a line like:
        # "Packets: Sent = 10, Received = 8, Lost = 2 (20% loss)"
        # We extract the numbers using regex

        sent_match     = re.search(r"Sent\s*=\s*(\d+)",     output)
        received_match = re.search(r"Received\s*=\s*(\d+)", output)
        lost_match     = re.search(r"Lost\s*=\s*(\d+)",     output)

        if sent_match and received_match and lost_match:
            sent     = int(sent_match.group(1))
            received = int(received_match.group(1))
            lost     = int(lost_match.group(1))

            result["packets_sent"]     = sent
            result["packets_received"] = received
            result["packets_lost"]     = lost
            result["loss_percent"]     = round((lost / sent) * 100, 1) if sent > 0 else 0.0

            # Classify the result
            if result["loss_percent"] == 0:
                result["status"] = "excellent"
            elif result["loss_percent"] <= 2:
                result["status"] = "good"
            elif result["loss_percent"] <= 10:
                result["status"] = "degraded"
            else:
                result["status"] = "poor"

        elif "could not find host" in output.lower():
            result["status"] = "dns_error"
            result["error"] = f"Cannot resolve hostname: {host}"

        elif "Request timed out" in output:
            result["packets_lost"]  = count
            result["loss_percent"]  = 100.0
            result["status"]        = "unreachable"
            result["error"]         = "All packets timed out — device likely offline"

        else:
            result["status"] = "error"
            result["error"]  = "Could not parse ping output"

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["error"]  = "Ping command timed out"

    except Exception as e:
        result["status"] = "error"
        result["error"]  = str(e)

    return result


def get_loss_label(loss_percent: float) -> str:
    """Convert a loss percentage to a human-readable label."""
    if loss_percent == 0:
        return "No loss — excellent"
    elif loss_percent <= 2:
        return "Minimal loss — good"
    elif loss_percent <= 10:
        return "Moderate loss — degraded"
    elif loss_percent <= 50:
        return "High loss — poor"
    else:
        return "Severe loss — critical"


# ── Test this file directly ───────────────────────────────────
if __name__ == "__main__":

    test_hosts = ["google.com", "8.8.8.8", "github.com"]

    print("=" * 60)
    print("  Packet Loss Test (sending 10 packets per host)")
    print("=" * 60)

    for host in test_hosts:
        print(f"\n  Testing: {host}")
        r = calculate_packet_loss(host, count=10)

        if r["error"]:
            print(f"  Error: {r['error']}")
        else:
            print(f"  Sent:     {r['packets_sent']}")
            print(f"  Received: {r['packets_received']}")
            print(f"  Lost:     {r['packets_lost']}")
            print(f"  Loss:     {r['loss_percent']}%  →  {get_loss_label(r['loss_percent'])}")
