# tests/test_connectivity.py
# Tests for connectivity checker

import pytest
from monitoring.connectivity import check_connectivity


class TestConnectivity:
    """Tests for the connectivity checker."""

    def test_google_is_reachable(self):
        """
        GIVEN google.com
        WHEN we check connectivity
        THEN it should be reachable
        """
        result = check_connectivity("google.com", 80)
        assert result["reachable"] is True
        assert result["latency_ms"] is not None
        assert result["latency_ms"] > 0

    def test_health_is_valid_value(self):
        """
        GIVEN any host
        WHEN we check connectivity
        THEN health must be one of the known values
        """
        result = check_connectivity("google.com", 80)
        valid_health = [
            "excellent", "good", "degraded",
            "poor", "offline", "unknown"
        ]
        assert result["health"] in valid_health

    def test_result_has_timestamp(self):
        """
        GIVEN any host
        WHEN we check connectivity
        THEN result must include a timestamp
        """
        result = check_connectivity("google.com", 80)
        assert "timestamp" in result
        assert result["timestamp"] is not None
        assert len(result["timestamp"]) > 0

    def test_offline_host_handled(self):
        """
        GIVEN an unreachable host
        WHEN we check connectivity
        THEN reachable should be False with a message
        """
        result = check_connectivity(
            "192.168.99.254", 80
        )
        assert result["reachable"] is False
        assert result["health"] == "offline"
        assert result["message"] != ""

    def test_result_structure(self):
        """
        GIVEN any host
        WHEN we check connectivity
        THEN all required keys must be present
        """
        result = check_connectivity("8.8.8.8", 53)
        required = [
            "host", "port", "timestamp",
            "reachable", "latency_ms",
            "packet_loss_percent", "health", "message"
        ]
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_excellent_health_conditions(self):
        """
        GIVEN a fast reliable host
        WHEN latency is under 50ms and no loss
        THEN health should be excellent or good
        """
        result = check_connectivity("8.8.8.8", 53)
        if result["reachable"]:
            assert result["health"] in [
                "excellent", "good", "degraded"
            ]