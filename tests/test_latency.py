# tests/test_latency.py
# Tests for the latency measurement module

import pytest
from monitoring.latency import (
    measure_latency_socket,
    measure_latency_ping
)


class TestSocketLatency:
    """Tests for socket-based latency measurement."""

    def test_reachable_host_returns_latency(self):
        """
        GIVEN a known reachable host
        WHEN we measure socket latency
        THEN we should get a positive latency value
        """
        result = measure_latency_socket("google.com", 80)
        assert result["status"] == "reachable"
        assert result["latency_ms"] is not None
        assert result["latency_ms"] > 0

    def test_latency_is_reasonable(self):
        """
        GIVEN a reachable host
        WHEN we measure latency
        THEN it should be under 5000ms (5 seconds)
        """
        result = measure_latency_socket("google.com", 80)
        if result["status"] == "reachable":
            assert result["latency_ms"] < 5000

    def test_unreachable_host_returns_error(self):
        """
        GIVEN a host that doesn't exist
        WHEN we measure latency
        THEN status should NOT be reachable
        """
        result = measure_latency_socket(
            "thisdomaindoesnotexist12345.com", 80
        )
        assert result["status"] != "reachable"
        assert result["latency_ms"] is None

    def test_closed_port_returns_failure(self):
        """
        GIVEN a real host but closed port
        WHEN we measure latency
        THEN connection should fail
        """
        result = measure_latency_socket("google.com", 9999)
        assert result["status"] != "reachable"

    def test_result_has_required_keys(self):
        """
        GIVEN any host
        WHEN we measure latency
        THEN result dictionary must have all required keys
        """
        result = measure_latency_socket("google.com", 80)
        required_keys = [
            "host", "port", "method",
            "latency_ms", "status", "error"
        ]
        for key in required_keys:
            assert key in result, \
                f"Missing key: {key}"

    def test_timeout_parameter_works(self):
        """
        GIVEN a very short timeout
        WHEN connecting to a slow/unreachable host
        THEN should timeout quickly
        """
        import time
        start = time.time()
        result = measure_latency_socket(
            "192.168.99.99", 80, timeout=1
        )
        elapsed = time.time() - start
        assert elapsed < 3  # should give up within 3 seconds
        assert result["status"] in ["timeout", "error",
                                    "port_closed"]


class TestPingLatency:
    """Tests for ping-based latency measurement."""

    def test_ping_reachable_host(self):
        """
        GIVEN a known reachable host
        WHEN we ping it
        THEN we should get avg_ms value
        """
        result = measure_latency_ping("google.com", count=2)
        assert result["status"] == "reachable"
        assert result["avg_ms"] is not None
        assert result["avg_ms"] > 0

    def test_ping_returns_min_max(self):
        """
        GIVEN a reachable host
        WHEN we ping with multiple packets
        THEN min and max should both be present
        """
        result = measure_latency_ping("8.8.8.8", count=3)
        if result["status"] == "reachable":
            assert result["min_ms"] is not None
            assert result["max_ms"] is not None
            assert result["min_ms"] <= result["max_ms"]

    def test_ping_invalid_host(self):
        """
        GIVEN an invalid hostname
        WHEN we ping it
        THEN status should indicate failure
        """
        result = measure_latency_ping(
            "invalidhostname99999.xyz", count=1
        )
        assert result["status"] in [
            "dns_error", "unreachable", "timeout", "error"
        ]

    def test_ping_result_structure(self):
        """
        GIVEN any host
        WHEN we ping it
        THEN result must have all required keys
        """
        result = measure_latency_ping("google.com", count=2)
        required = [
            "host", "method", "packets_sent",
            "avg_ms", "min_ms", "max_ms",
            "status", "error"
        ]
        for key in required:
            assert key in result, f"Missing key: {key}"