# monitoring/latency.py
# Measures how long it takes to reach a device (latency)
# Uses two methods: socket-based and Windows ping command

import socket
import time
import subprocess
import re


def measure_latency_socket(host: str, port: int = 80, timeout: int = 3) -> dict:
    """
    Measure latency by opening a TCP socket connection.

    How it works:
      1. Record time before connecting
      2. Connect to the host
      3. Record time after connecting
      4. Difference = latency

    Args:
        host    : IP address or domain name (e.g. "google.com")
        port    : Port number to connect to (default 80)
        timeout : Give up after this many seconds

    Returns:
        A dictionary with latency result and status
    """

    result = {
        "host": host,
        "port": port,
        "method": "socket",
        "latency_ms": None,
        "status": "unknown",
        "error": None
    }

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        start = time.time()
        connection_result = sock.connect_ex((host, port))
        end = time.time()

        sock.close()

        if connection_result == 0:
            latency = round((end - start) * 1000, 2)  # convert to ms
            result["latency_ms"] = latency
            result["status"] = "reachable"
        else:
            result["status"] = "port_closed"
            result["error"] = f"Port {port} is closed or filtered"

    except socket.timeout:
        result["status"] = "timeout"
        result["error"] = "Connection timed out"

    except socket.gaierror:
        result["status"] = "dns_error"
        result["error"] = f"Cannot resolve hostname: {host}"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def measure_latency_ping(host: str, count: int = 4) -> dict:
    """
    Measure latency using the Windows ping command.

    How it works:
      Windows has a built-in 'ping' command.
      We run it from Python using subprocess,
      capture the output, and extract the average time.

    Args:
        host  : IP address or domain name
        count : How many ping packets to send (default 4)

    Returns:
        A dictionary with average, min, max latency
    """

    result = {
        "host": host,
        "method": "ping",
        "packets_sent": count,
        "avg_ms": None,
        "min_ms": None,
        "max_ms": None,
        "status": "unknown",
        "error": None,
        "raw_output": ""
    }

    try:
        # Run: ping -n 4 google.com
        # -n = number of packets (Windows flag)
        command = ["ping", "-n", str(count), host]

        # subprocess.run executes the command and captures output
        process = subprocess.run(
            command,
            capture_output=True,   # capture what ping prints
            text=True,             # return output as string (not bytes)
            timeout=30             # give up after 30 seconds
        )

        output = process.stdout
        result["raw_output"] = output

        # Check if ping succeeded — Windows prints "Reply from" on success
        if "Reply from" in output or "reply from" in output:
            result["status"] = "reachable"

            # Extract average time using regex
            # Windows output looks like: "Minimum = 10ms, Maximum = 20ms, Average = 15ms"
            avg_match = re.search(r"Average\s*=\s*(\d+)ms", output)
            min_match = re.search(r"Minimum\s*=\s*(\d+)ms", output)
            max_match = re.search(r"Maximum\s*=\s*(\d+)ms", output)

            if avg_match:
                result["avg_ms"] = int(avg_match.group(1))
            if min_match:
                result["min_ms"] = int(min_match.group(1))
            if max_match:
                result["max_ms"] = int(max_match.group(1))

        elif "Request timed out" in output:
            result["status"] = "timeout"
            result["error"] = "All ping packets timed out"

        elif "could not find host" in output.lower():
            result["status"] = "dns_error"
            result["error"] = f"Cannot find host: {host}"

        else:
            result["status"] = "unreachable"
            result["error"] = "Host did not respond to ping"

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["error"] = "Ping command itself timed out"

    except FileNotFoundError:
        result["status"] = "error"
        result["error"] = "ping command not found on this system"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


# ── Test this file directly ───────────────────────────────────
if __name__ == "__main__":

    test_hosts = ["google.com", "github.com", "8.8.8.8"]

    print("=" * 55)
    print("  METHOD 1: Socket-based latency")
    print("=" * 55)

    for host in test_hosts:
        r = measure_latency_socket(host)
        if r["status"] == "reachable":
            print(f"  {host:20s} → {r['latency_ms']} ms  ✓")
        else:
            print(f"  {host:20s} → {r['status']} — {r['error']}")

    print()
    print("=" * 55)
    print("  METHOD 2: Ping-based latency")
    print("=" * 55)

    for host in test_hosts:
        r = measure_latency_ping(host)
        if r["status"] == "reachable":
            print(f"  {host:20s} → avg: {r['avg_ms']} ms  "
                  f"min: {r['min_ms']} ms  max: {r['max_ms']} ms  ✓")
        else:
            print(f"  {host:20s} → {r['status']} — {r['error']}")
