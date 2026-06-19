# tests/test_api.py
# Tests for FastAPI REST endpoints
# Uses httpx to make real HTTP requests to running API

import pytest
from fastapi.testclient import TestClient
from api.main import app

# TestClient simulates HTTP requests without
# needing the server to actually be running
client = TestClient(app)


class TestRootEndpoint:
    """Tests for GET /"""

    def test_root_returns_200(self):
        """
        GIVEN the API is running
        WHEN we call GET /
        THEN we should get 200 OK
        """
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_status_online(self):
        """
        GIVEN the API is running
        WHEN we call GET /
        THEN response should say status online
        """
        response = client.get("/")
        data = response.json()
        assert data["status"] == "online"

    def test_root_mentions_docs(self):
        """
        GIVEN the API is running
        WHEN we call GET /
        THEN response should mention docs URL
        """
        response = client.get("/")
        data = response.json()
        assert "docs" in data


class TestDevicesEndpoint:
    """Tests for /devices endpoints."""

    def test_get_devices_returns_list(self):
        """
        GIVEN the API is running
        WHEN we call GET /devices
        THEN response should be a list
        """
        response = client.get("/devices/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_add_device_success(self):
        """
        GIVEN a new device
        WHEN we POST to /devices
        THEN device should be added successfully
        """
        response = client.post("/devices/", json={
            "host":  "testdevice99.com",
            "port":  80,
            "label": "Test Device"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_add_duplicate_device_returns_409(self):
        """
        GIVEN a device already in the list
        WHEN we try to add it again
        THEN we should get 409 Conflict
        """
        client.post("/devices/", json={
            "host": "duplicate99.com",
            "port": 80
        })
        response = client.post("/devices/", json={
            "host": "duplicate99.com",
            "port": 80
        })
        assert response.status_code == 409

    def test_get_nonexistent_device_returns_404(self):
        """
        GIVEN a device that doesn't exist
        WHEN we GET /devices/{host}
        THEN we should get 404 Not Found
        """
        response = client.get(
            "/devices/doesnotexist99999.com"
        )
        assert response.status_code == 404

    def test_delete_device(self):
        """
        GIVEN a device in the list
        WHEN we DELETE /devices/{host}
        THEN device should be removed
        """
        client.post("/devices/", json={
            "host": "todelete99.com",
            "port": 80
        })
        response = client.delete(
            "/devices/todelete99.com"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestStatusEndpoint:
    """Tests for GET /status"""

    def test_status_returns_200(self):
        """
        GIVEN the API is running
        WHEN we call GET /status
        THEN we should get 200 OK
        """
        response = client.get("/status")
        assert response.status_code == 200

    def test_status_has_required_fields(self):
        """
        GIVEN monitoring has been run
        WHEN we call GET /status
        THEN response should have status field
        """
        response = client.get("/status")
        data = response.json()
        assert "overall_status" in data \
               or "status" in data \
               or "message" in data


class TestMetricsEndpoint:
    """Tests for GET /metrics"""

    def test_metrics_returns_200(self):
        """
        GIVEN the API is running
        WHEN we call GET /metrics
        THEN we should get 200 OK
        """
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_returns_list(self):
        """
        GIVEN the API is running
        WHEN we call GET /metrics
        THEN response should be a list
        """
        response = client.get("/metrics")
        assert isinstance(response.json(), list)