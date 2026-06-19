# socket_basics.py
# This is your very first networking program.
# It connects to Google's server and measures how long it takes.

import socket    # Python's built-in networking library
import time      # Used to measure time

def check_connection(host, port):
    """
    Try to connect to a host (IP or website name) on a specific port.
    Returns True if connection works, False if it fails.
    Also prints how long the connection took (latency).
    """

    print(f"\nTrying to connect to: {host} on port {port}")

    try:
        # Step 1: Create a socket object
        # AF_INET means we're using IPv4 addresses
        # SOCK_STREAM means we're using TCP (reliable connection)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Step 2: Set a timeout — if connection takes more than 3 seconds, give up
        sock.settimeout(3)

        # Step 3: Record the time BEFORE connecting
        start_time = time.time()

        # Step 4: Actually connect — this is where the "handshake" happens
        # connect_ex returns 0 if success, error code if failed
        result = sock.connect_ex((host, port))

        # Step 5: Record the time AFTER connecting
        end_time = time.time()

        # Step 6: Calculate latency in milliseconds
        latency = (end_time - start_time) * 1000  # multiply by 1000 to convert to ms

        # Step 7: Close the socket — always do this when done
        sock.close()

        # Step 8: Check if connection was successful
        if result == 0:
            print(f"  SUCCESS — Connected!")
            print(f"  Latency: {latency:.2f} ms")
            return True
        else:
            print(f"  FAILED — Could not connect (error code: {result})")
            return False

    except socket.timeout:
        print(f"  TIMEOUT — Connection took too long (more than 3 seconds)")
        return False

    except socket.gaierror:
        print(f"  ERROR — Could not find host '{host}'. Check the name.")
        return False

    except Exception as e:
        print(f"  UNEXPECTED ERROR: {e}")
        return False


# ── Main program ──────────────────────────────────────────────
# This block only runs when you execute this file directly
if __name__ == "__main__":

    print("=" * 50)
    print("  Network Connection Tester")
    print("=" * 50)

    # Test a few different hosts and ports
    targets = [
        ("google.com", 80),       # Google's web server
        ("github.com", 80),       # GitHub's web server
        ("8.8.8.8", 53),          # Google's DNS server
        ("192.168.1.1", 80),      # Your home router (may fail — that's ok)
        ("localhost", 8000),       # Your own computer on port 8000 (will fail for now)
    ]

    results = []

    for host, port in targets:
        success = check_connection(host, port)
        results.append((host, port, success))

    # Print a summary
    print("\n" + "=" * 50)
    print("  Summary")
    print("=" * 50)
    for host, port, success in results:
        status = "ONLINE" if success else "OFFLINE/UNREACHABLE"
        print(f"  {host}:{port}  →  {status}")
