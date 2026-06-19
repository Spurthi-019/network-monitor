# tests/test_database.py
# Tests for database operations
# Uses a separate TEST database so real data is not affected

import pytest
import os
import time
import sqlite3
from database.db import (
    get_connection, create_tables,
    insert_device, get_all_devices,
    get_device_by_host, delete_device,
    insert_metric, insert_many_metrics,
    get_all_metrics, get_metrics_for_host,
    get_metrics_summary, insert_alert, get_alerts,
)

# ── Use a separate test database ──────────────────────────────
TEST_DB = "database/test_network_monitor.db"


@pytest.fixture(autouse=True)
def use_test_db(monkeypatch):
    """
    Before each test: point DB_PATH to test database.
    After each test: delete the test database.
    This keeps tests isolated from real data.
    """
    import database.db as db_module
    monkeypatch.setattr(db_module, "DB_PATH", TEST_DB)
    create_tables()
    yield
    # Cleanup after test
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


class TestDeviceOperations:
    """Tests for device CRUD operations."""

    def test_insert_and_retrieve_device(self):
        """
        GIVEN a new device
        WHEN we insert it
        THEN we should be able to retrieve it
        """
        insert_device("test.com", 80, "Test Device")
        devices = get_all_devices()
        assert len(devices) == 1
        assert devices[0]["host"] == "test.com"
        assert devices[0]["port"] == 80

    def test_duplicate_device_rejected(self):
        """
        GIVEN a device already in database
        WHEN we try to insert same host again
        THEN it should return False
        """
        insert_device("test.com", 80, "Test")
        result = insert_device("test.com", 80, "Test Again")
        assert result is False

    def test_get_device_by_host(self):
        """
        GIVEN a device in database
        WHEN we search by hostname
        THEN we should get that device back
        """
        insert_device("myhost.com", 443, "My Host")
        device = get_device_by_host("myhost.com")
        assert device is not None
        assert device["host"] == "myhost.com"
        assert device["port"] == 443

    def test_get_nonexistent_device_returns_none(self):
        """
        GIVEN an empty database
        WHEN we search for a device that doesn't exist
        THEN we should get None back
        """
        result = get_device_by_host("nothere.com")
        assert result is None

    def test_delete_device(self):
        """
        GIVEN a device in database
        WHEN we delete it
        THEN it should no longer exist
        """
        insert_device("todelete.com", 80, "Delete Me")
        deleted = delete_device("todelete.com")
        assert deleted is True
        assert get_device_by_host("todelete.com") is None

    def test_delete_nonexistent_returns_false(self):
        """
        GIVEN an empty database
        WHEN we try to delete a device that isn't there
        THEN it should return False
        """
        result = delete_device("nothere.com")
        assert result is False


class TestMetricOperations:
    """Tests for metric storage and retrieval."""

    def _make_metric(self, host="test.com",
                     latency=25.0, loss=0.0,
                     reachable=True):
        return {
            "host":                 host,
            "port":                 80,
            "latency_ms":           latency,
            "packet_loss_percent":  loss,
            "reachable":            reachable,
            "health":               "excellent",
            "message":              "Test metric",
            "timestamp":
                time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def test_insert_and_retrieve_metric(self):
        """
        GIVEN a monitoring result
        WHEN we save it
        THEN we should be able to retrieve it
        """
        insert_metric(self._make_metric())
        metrics = get_all_metrics()
        assert len(metrics) == 1
        assert metrics[0]["host"] == "test.com"
        assert metrics[0]["latency_ms"] == 25.0

    def test_insert_many_metrics(self):
        """
        GIVEN multiple monitoring results
        WHEN we save them in batch
        THEN all should be retrievable
        """
        batch = [
            self._make_metric("host1.com", 20.0),
            self._make_metric("host2.com", 30.0),
            self._make_metric("host3.com", 40.0),
        ]
        count = insert_many_metrics(batch)
        assert count == 3
        assert len(get_all_metrics()) == 3

    def test_get_metrics_for_specific_host(self):
        """
        GIVEN metrics for multiple hosts
        WHEN we filter by host
        THEN we should only get that host's metrics
        """
        insert_metric(self._make_metric("host1.com"))
        insert_metric(self._make_metric("host2.com"))
        results = get_metrics_for_host("host1.com")
        assert len(results) == 1
        assert results[0]["host"] == "host1.com"

    def test_metrics_summary_calculates_averages(self):
        """
        GIVEN multiple metrics for same host
        WHEN we get summary
        THEN avg_latency_ms should be correct average
        """
        insert_metric(self._make_metric("avg.com", 20.0))
        insert_metric(self._make_metric("avg.com", 40.0))
        summary = get_metrics_summary()
        host_summary = next(
            (s for s in summary if s["host"] == "avg.com"),
            None
        )
        assert host_summary is not None
        assert host_summary["avg_latency_ms"] == 30.0
        assert host_summary["total_checks"] == 2


class TestAlertOperations:
    """Tests for alert storage."""

    def _make_alert(self, host="test.com",
                    severity="OK"):
        return {
            "host":            host,
            "severity":        severity,
            "rule_triggered":  "TEST_RULE",
            "detail":          f"{host} test alert",
            "recommendation":  "No action needed",
            "latency_ms":      25.0,
            "packet_loss_percent": 0.0,
            "timestamp":
                time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def test_insert_and_retrieve_alert(self):
        """
        GIVEN an alert
        WHEN we save it
        THEN we should get it back
        """
        insert_alert(self._make_alert())
        alerts = get_alerts()
        assert len(alerts) == 1
        assert alerts[0]["host"] == "test.com"

    def test_filter_alerts_by_severity(self):
        """
        GIVEN alerts with different severities
        WHEN we filter by CRITICAL
        THEN we should only get CRITICAL alerts
        """
        insert_alert(self._make_alert("a.com", "OK"))
        insert_alert(self._make_alert("b.com", "CRITICAL"))
        insert_alert(self._make_alert("c.com", "WARNING"))

        critical = get_alerts(severity="CRITICAL")
        assert len(critical) == 1
        assert critical[0]["host"] == "b.com"