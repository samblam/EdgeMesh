"""Tests for health reporting endpoint"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_exists(client: AsyncClient):
    """Test POST /api/v1/health endpoint exists"""
    response = await client.post(
        "/api/v1/health",
        json={
            "device_id": "test-device",
            "metrics": {"cpu_percent": 50.0}
        }
    )

    # Should not return 404
    assert response.status_code != 404


@pytest.mark.asyncio
async def test_health_report_submission(client: AsyncClient, db_session):
    """Test successful health report submission"""
    response = await client.post(
        "/api/v1/health",
        json={
            "device_id": "laptop-001",
            "status": "healthy",
            "metrics": {
                "cpu_percent": 45.5,
                "memory_percent": 62.3,
                "disk_percent": 78.1
            }
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "message" in data
    assert data["device_id"] == "laptop-001"


@pytest.mark.asyncio
async def test_health_report_creates_healthcheck_record(client: AsyncClient, db_session):
    """Test health report creates record in database"""
    from app.models.healthcheck import HealthCheck
    from sqlalchemy import select

    response = await client.post(
        "/api/v1/health",
        json={
            "device_id": "server-001",
            "status": "degraded",
            "metrics": {
                "cpu_percent": 85.0,
                "memory_percent": 90.0
            }
        }
    )

    assert response.status_code == 200

    # Verify health check was created
    result = await db_session.execute(
        select(HealthCheck).where(HealthCheck.device_id == "server-001")
    )
    health_checks = result.scalars().all()

    assert len(health_checks) > 0
    latest = health_checks[-1]
    assert latest.device_id == "server-001"
    assert latest.status == "degraded"
    assert latest.metrics["cpu_percent"] == 85.0
    assert latest.metrics["memory_percent"] == 90.0


@pytest.mark.asyncio
async def test_health_report_with_default_status(client: AsyncClient, db_session):
    """Test health report uses default status='healthy' if not provided"""
    from app.models.healthcheck import HealthCheck
    from sqlalchemy import select

    response = await client.post(
        "/api/v1/health",
        json={
            "device_id": "iot-001",
            "metrics": {"cpu_percent": 30.0}
        }
    )

    assert response.status_code == 200

    # Verify default status was used
    result = await db_session.execute(
        select(HealthCheck).where(HealthCheck.device_id == "iot-001")
    )
    health_check = result.scalar_one_or_none()

    assert health_check is not None
    assert health_check.status == "healthy"


@pytest.mark.asyncio
async def test_health_report_accepts_complex_metrics(client: AsyncClient, db_session):
    """Test health report accepts nested metrics"""
    from app.models.healthcheck import HealthCheck
    from sqlalchemy import select

    complex_metrics = {
        "cpu": {"percent": 45.5, "cores": 4},
        "memory": {"percent": 62.3, "total_gb": 16},
        "services": ["nginx", "postgres", "redis"]
    }

    response = await client.post(
        "/api/v1/health",
        json={
            "device_id": "complex-device",
            "metrics": complex_metrics
        }
    )

    assert response.status_code == 200

    # Verify complex metrics were stored
    result = await db_session.execute(
        select(HealthCheck).where(HealthCheck.device_id == "complex-device")
    )
    health_check = result.scalar_one_or_none()

    assert health_check is not None
    assert health_check.metrics["cpu"]["cores"] == 4
    assert health_check.metrics["services"] == ["nginx", "postgres", "redis"]


@pytest.mark.asyncio
async def test_health_report_validates_request_body(client: AsyncClient):
    """Test health report validates required fields"""
    # Missing metrics field
    response = await client.post(
        "/api/v1/health",
        json={
            "device_id": "test-device"
        }
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_health_report_allows_multiple_reports_same_device(client: AsyncClient, db_session):
    """Test multiple health reports from same device are all stored"""
    from app.models.healthcheck import HealthCheck
    from sqlalchemy import select

    # Submit multiple reports
    for i in range(3):
        response = await client.post(
            "/api/v1/health",
            json={
                "device_id": "multi-report-device",
                "metrics": {"iteration": i}
            }
        )
        assert response.status_code == 200

    # Verify all reports were stored
    result = await db_session.execute(
        select(HealthCheck).where(HealthCheck.device_id == "multi-report-device")
    )
    health_checks = result.scalars().all()

    assert len(health_checks) == 3
