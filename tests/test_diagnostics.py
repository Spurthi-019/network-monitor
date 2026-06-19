# tests/test_diagnostics.py
# Tests for the automated diagnostic system
# Matched to actual analyzer.py output format

import pytest
from diagnostics.analyzer import (
    analyze_result,
    analyze_all,
    SEVERITY_OK,
    SEVERITY_WARNING,
    SEVERITY_CRITICAL,
)


def make_report(host="test.com", reachable=True,
                latency=25.0, loss=0.0,
                health="excellent"):
    """Helper to create a fake monitoring report."""
    return {
        "host":                 host,
        "port":                 80,
        "timestamp":            "2024-01-01 12:00:00",
        "reachable":            reachable,
        "latency_ms":           latency if reachable else None,
        "packet_loss_percent":  loss if reachable else None,
        "health":               health,
        "message":              "Test report",
    }


def get_severity(alert):
    """
    Get severity from alert dict.
    Your analyzer returns overall_severity key.
    """
    if isinstance(alert, dict):
        return alert.get("overall_severity") \
               or alert.get("severity")
    return getattr(alert, "overall_severity",
           getattr(alert, "severity", None))


def get_host(alert):
    """Get host from alert."""
    if isinstance(alert, dict):
        return alert.get("host")
    return getattr(alert, "host", None)


def get_recommendation(alert):
    """
    Get recommendation from alert.
    Your analyzer returns a recommendations LIST.
    """
    if isinstance(alert, dict):
        recs = alert.get("recommendations", [])
        if isinstance(recs, list):
            return " ".join(recs)
        return recs or alert.get("recommendation", "")
    return getattr(alert, "recommendation", "")


def get_active_issues(alert):
    """Get active issues list from alert dict."""
    if isinstance(alert, dict):
        return alert.get("active_issues", [])
    return []


class TestDiagnosticRules:
    """Tests for individual diagnostic rules."""

    def test_healthy_device_gets_ok(self):
        """
        GIVEN a device with low latency and no loss
        WHEN we analyze it
        THEN we should get an alert back (not None)
        """
        report = make_report(latency=25.0, loss=0.0)
        alert  = analyze_result(report)
        assert alert is not None

    def test_offline_device_gets_critical(self):
        """
        GIVEN an offline device
        WHEN we analyze it
        THEN overall_severity should be critical
        """
        report = make_report(
            reachable=False,
            latency=None,
            loss=None,
            health="offline"
        )
        alert = analyze_result(report)
        assert alert is not None
        assert get_severity(alert) == SEVERITY_CRITICAL

    def test_offline_device_has_active_issues(self):
        """
        GIVEN an offline device
        WHEN we analyze it
        THEN active_issues should not be empty
        """
        report = make_report(
            reachable=False,
            latency=None,
            loss=None,
            health="offline"
        )
        alert  = analyze_result(report)
        issues = get_active_issues(alert)
        assert len(issues) > 0

    def test_high_latency_triggers_warning(self):
        """
        GIVEN a device with latency above 150ms
        WHEN we analyze it
        THEN severity should be warning or critical
        """
        report = make_report(latency=200.0, loss=0.0,
                             health="degraded")
        alert  = analyze_result(report)
        assert alert is not None
        assert get_severity(alert) in [
            SEVERITY_WARNING, SEVERITY_CRITICAL
        ]

    def test_critical_latency_triggers_critical(self):
        """
        GIVEN a device with latency above 300ms
        WHEN we analyze it
        THEN severity should be warning or critical
        """
        report = make_report(latency=400.0, loss=0.0,
                             health="poor")
        alert  = analyze_result(report)
        assert alert is not None
        assert get_severity(alert) in [
            SEVERITY_WARNING, SEVERITY_CRITICAL
        ]

    def test_high_packet_loss_triggers_warning(self):
        """
        GIVEN a device with packet loss above 2%
        WHEN we analyze it
        THEN severity should be warning or critical
        """
        report = make_report(latency=30.0, loss=5.0,
                             health="degraded")
        alert  = analyze_result(report)
        assert alert is not None
        assert get_severity(alert) in [
            SEVERITY_WARNING, SEVERITY_CRITICAL
        ]

    def test_alert_has_recommendation(self):
        """
        GIVEN any monitoring report
        WHEN we analyze it
        THEN recommendations list must not be empty
        """
        report = make_report(
            reachable=False,
            health="offline"
        )
        alert = analyze_result(report)
        rec   = get_recommendation(alert)
        assert rec is not None
        assert len(rec) > 0

    def test_alert_has_host(self):
        """
        GIVEN a monitoring report with a host
        WHEN we analyze it
        THEN alert must include the same host
        """
        report = make_report(host="mydevice.local")
        alert  = analyze_result(report)
        assert get_host(alert) == "mydevice.local"

    def test_alert_has_health_score(self):
        """
        GIVEN any monitoring report
        WHEN we analyze it
        THEN alert must include health_score
        """
        report = make_report()
        alert  = analyze_result(report)
        assert isinstance(alert, dict)
        assert "health_score" in alert
        assert 0 <= alert["health_score"] <= 100

    def test_alert_has_rule_results(self):
        """
        GIVEN any monitoring report
        WHEN we analyze it
        THEN alert must include rule_results list
        """
        report = make_report()
        alert  = analyze_result(report)
        assert isinstance(alert, dict)
        assert "rule_results" in alert
        assert isinstance(alert["rule_results"], list)
        assert len(alert["rule_results"]) > 0

    def test_healthy_device_has_high_score(self):
        """
        GIVEN a healthy device
        WHEN we analyze it
        THEN health_score should be above 50
        """
        report = make_report(
            latency=20.0, loss=0.0,
            health="excellent"
        )
        alert = analyze_result(report)
        assert alert["health_score"] > 50

    def test_offline_device_has_zero_score(self):
        """
        GIVEN an offline device
        WHEN we analyze it
        THEN health_score should be 0
        """
        report = make_report(
            reachable=False,
            latency=None,
            loss=None,
            health="offline"
        )
        alert = analyze_result(report)
        assert alert["health_score"] == 0


class TestAnalyzeAll:
    """Tests for batch diagnostic analysis."""

    def test_returns_one_alert_per_report(self):
        """
        GIVEN 3 monitoring reports
        WHEN we analyze all
        THEN we should get 3 alerts back
        """
        reports = [
            make_report("host1.com"),
            make_report("host2.com"),
            make_report("host3.com"),
        ]
        alerts = analyze_all(reports)
        assert len(alerts) == 3

    def test_empty_input_returns_empty(self):
        """
        GIVEN an empty list
        WHEN we analyze all
        THEN we should get empty list back
        """
        alerts = analyze_all([])
        assert alerts == []

    def test_each_alert_has_host(self):
        """
        GIVEN multiple reports
        WHEN we analyze all
        THEN each alert should have host field
        """
        reports = [
            make_report("host1.com"),
            make_report("host2.com"),
        ]
        alerts = analyze_all(reports)
        for alert in alerts:
            assert get_host(alert) is not None

    def test_mixed_results_classified_correctly(self):
        """
        GIVEN mix of healthy and offline devices
        WHEN we analyze all
        THEN offline device should be critical
        """
        reports = [
            make_report("good.com",
                        reachable=True,
                        latency=20.0, loss=0.0),
            make_report("bad.com",
                        reachable=False,
                        health="offline"),
        ]
        alerts = analyze_all(reports)
        assert len(alerts) == 2

        severities = {
            get_host(a): get_severity(a)
            for a in alerts
        }
        assert severities["bad.com"] == SEVERITY_CRITICAL

    def test_all_alerts_have_severity(self):
        """
        GIVEN multiple reports
        WHEN we analyze all
        THEN every alert must have a severity
        """
        reports = [
            make_report("h1.com"),
            make_report("h2.com",
                        reachable=False,
                        health="offline"),
        ]
        alerts = analyze_all(reports)
        for alert in alerts:
            sev = get_severity(alert)
            assert sev in [
                SEVERITY_OK,
                SEVERITY_WARNING,
                SEVERITY_CRITICAL
            ]

    def test_all_alerts_have_recommendations(self):
        """
        GIVEN multiple reports including offline
        WHEN we analyze all
        THEN every alert should have recommendations
        """
        reports = [
            make_report("h1.com"),
            make_report("h2.com",
                        reachable=False,
                        health="offline"),
        ]
        alerts = analyze_all(reports)
        for alert in alerts:
            rec = get_recommendation(alert)
            assert rec is not None