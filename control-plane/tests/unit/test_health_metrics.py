"""Tests for health endpoint metrics recording"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from sqlalchemy import select
from app.models.healthcheck import HealthCheck


@pytest.mark.asyncio
async def test_health_report_records_metrics(client: AsyncClient):
    """Test that health report submission records metrics"""
    with patch('app.api.v1.health.MetricsService') as mock_metrics:
        mock_metrics.record_health_check = MagicMock()

        response = await client.post(
            "/api/v1/health",
            json={
                "device_id": "health-metrics-device",
                "status": "healthy",
                "metrics": {
                    "cpu_usage": 45.5,
                    "memory_usage": 62.3,
                    "disk_usage": 78.1
                }
            }
        )

        # Verify successful health report
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Health report received"
        assert data["device_id"] == "health-metrics-device"

        # Verify metrics were recorded
        mock_metrics.record_health_check.assert_called_once()


@pytest.mark.asyncio
async def test_health_report_creates_database_record(client: AsyncClient, db_session):
    """Test that health report creates a record in the database"""
    device_id = "health-db-device"

    response = await client.post(
        "/api/v1/health",
        json={
            "device_id": device_id,
            "status": "healthy",
            "metrics": {
                "cpu_usage": 50.0,
                "memory_usage": 60.0
            }
        }
    )

    assert response.status_code == 200

    # Verify health check was stored in database
    result = await db_session.execute(
        select(HealthCheck).where(HealthCheck.device_id == device_id)
    )
    health_check = result.scalar_one_or_none()

    assert health_check is not None
    assert health_check.device_id == device_id
    assert health_check.status == "healthy"
    assert health_check.metrics is not None


@pytest.mark.asyncio
async def test_health_report_with_minimal_metrics(client: AsyncClient):
    """Test that health report works with minimal required fields"""
    with patch('app.api.v1.health.MetricsService') as mock_metrics:
        mock_metrics.record_health_check = MagicMock()

        response = await client.post(
            "/api/v1/health",
            json={
                "device_id": "minimal-health-device",
                "status": "degraded",
                "metrics": {}  # Empty metrics object
            }
        )

        # Should still succeed with minimal data
        assert response.status_code == 200

        # Metrics should still be recorded
        mock_metrics.record_health_check.assert_called_once()


@pytest.mark.asyncio
async def test_health_report_with_comprehensive_metrics(client: AsyncClient, db_session):
    """Test that health report handles comprehensive metrics payload"""
    device_id = "comprehensive-health-device"

    comprehensive_metrics = {
        "cpu_usage": 45.5,
        "memory_usage": 62.3,
        "disk_usage": 78.1,
        "network_rx": 1024000,
        "network_tx": 512000,
        "process_count": 156,
        "open_files": 423,
        "uptime_seconds": 86400
    }

    response = await client.post(
        "/api/v1/health",
        json={
            "device_id": device_id,
            "status": "healthy",
            "metrics": comprehensive_metrics
        }
    )

    assert response.status_code == 200

    # Verify all metrics were stored
    result = await db_session.execute(
        select(HealthCheck).where(HealthCheck.device_id == device_id)
    )
    health_check = result.scalar_one_or_none()

    assert health_check is not None
    assert health_check.metrics == comprehensive_metrics


@pytest.mark.asyncio
async def test_multiple_health_reports_from_same_device(client: AsyncClient, db_session):
    """Test that multiple health reports from the same device are all stored"""
    device_id = "multi-report-device"

    # Submit first health report
    response1 = await client.post(
        "/api/v1/health",
        json={
            "device_id": device_id,
            "status": "healthy",
            "metrics": {"cpu_usage": 30.0}
        }
    )
    assert response1.status_code == 200

    # Submit second health report
    response2 = await client.post(
        "/api/v1/health",
        json={
            "device_id": device_id,
            "status": "degraded",
            "metrics": {"cpu_usage": 85.0}
        }
    )
    assert response2.status_code == 200

    # Verify both reports were stored
    result = await db_session.execute(
        select(HealthCheck).where(HealthCheck.device_id == device_id)
    )
    health_checks = result.scalars().all()

    assert len(health_checks) == 2
    # Most recent should be the degraded one
    statuses = [hc.status for hc in health_checks]
    assert "healthy" in statuses
    assert "degraded" in statuses
