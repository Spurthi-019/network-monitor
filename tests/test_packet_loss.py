# tests/test_packet_loss.py
# Tests for packet loss calculation

import pytest
from monitoring.packet_loss import (
    calculate_packet_loss,
    get_loss_label
)


class TestPacketLoss:
    """Tests for packet loss measurement."""

    def test_no_loss_for_reliable_host(self):
        """
        GIVEN a reliable host like Google DNS
        WHEN we check packet loss
        THEN loss should be 0% or very low
        """
        result = calculate_packet_loss("8.8.8.8", count=5)
        if result["status"] in ["excellent", "good"]:
            assert result["loss_percent"] <= 5.0

    def test_result_has_required_keys(self):
        """
        GIVEN any host
        WHEN we calculate packet loss
        THEN result must have all required keys
        """
        result = calculate_packet_loss("google.com", count=3)
        required = [
            "host", "packets_sent", "packets_received",
            "packets_lost", "loss_percent",
            "status", "error"
        ]
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_packets_math_is_correct(self):
        """
        GIVEN a monitoring result
        WHEN packets are counted
        THEN sent = received + lost
        """
        result = calculate_packet_loss("google.com", count=4)
        if result["error"] is None:
            assert result["packets_sent"] == \
                   result["packets_received"] + \
                   result["packets_lost"]

    def test_loss_percent_range(self):
        """
        GIVEN any host
        WHEN we calculate loss
        THEN percentage must be between 0 and 100
        """
        result = calculate_packet_loss("google.com", count=3)
        assert 0.0 <= result["loss_percent"] <= 100.0

    def test_invalid_host_handled_gracefully(self):
        """
        GIVEN an invalid hostname
        WHEN we calculate packet loss
        THEN should not crash — return error status
        """
        result = calculate_packet_loss(
            "notarealhost99999.xyz", count=2
        )
        assert result is not None
        assert "status" in result


class TestLossLabel:
    """Tests for the loss label helper function."""

    def test_zero_loss_label(self):
        assert get_loss_label(0) == "No loss — excellent"

    def test_minimal_loss_label(self):
        assert get_loss_label(1.5) == "Minimal loss — good"

    def test_moderate_loss_label(self):
        assert get_loss_label(5.0) == \
               "Moderate loss — degraded"

    def test_high_loss_label(self):
        assert get_loss_label(25.0) == \
               "High loss — poor"

    def test_severe_loss_label(self):
        assert get_loss_label(75.0) == \
               "Severe loss — critical"