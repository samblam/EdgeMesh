"""
Unit tests for /metrics endpoint
"""
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestMetricsEndpoint:
    """Test suite for /metrics endpoint"""

    def test_metrics_endpoint_exists(self):
        """Test that /metrics endpoint exists"""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_endpoint_returns_prometheus_format(self):
        """Test that /metrics endpoint returns Prometheus format"""
        response = client.get("/metrics")

        # Verify content type
        assert "text/plain" in response.headers.get("content-type", "")

        # Verify response contains metrics
        content = response.text
        assert len(content) > 0

    def test_metrics_endpoint_contains_device_metrics(self):
        """Test that /metrics endpoint contains device metrics"""
        response = client.get("/metrics")
        content = response.text

        # Check for device metrics
        assert "edgemesh_devices_total" in content
        assert "edgemesh_device_enrollments_total" in content

    def test_metrics_endpoint_contains_authorization_metrics(self):
        """Test that /metrics endpoint contains authorization metrics"""
        response = client.get("/metrics")
        content = response.text

        # Check for authorization metrics
        assert "edgemesh_authorization_decisions_total" in content
        assert "edgemesh_authorization_latency_seconds" in content

    def test_metrics_endpoint_contains_connection_metrics(self):
        """Test that /metrics endpoint contains connection metrics"""
        response = client.get("/metrics")
        content = response.text

        # Check for connection metrics
        assert "edgemesh_connections_active" in content
        assert "edgemesh_connections_total" in content

    def test_metrics_endpoint_contains_health_metrics(self):
        """Test that /metrics endpoint contains health metrics"""
        response = client.get("/metrics")
        content = response.text

        # Check for health metrics
        assert "edgemesh_health_checks_total" in content
        assert "edgemesh_unhealthy_devices" in content

    def test_metrics_format_has_help_text(self):
        """Test that metrics have HELP text"""
        response = client.get("/metrics")
        content = response.text

        # Prometheus format includes HELP lines
        assert "# HELP" in content
        assert "# TYPE" in content

    def test_metrics_endpoint_no_authentication_required(self):
        """Test that /metrics endpoint doesn't require authentication"""
        # Metrics should be accessible without auth for Prometheus scraping
        response = client.get("/metrics")
        assert response.status_code == 200
