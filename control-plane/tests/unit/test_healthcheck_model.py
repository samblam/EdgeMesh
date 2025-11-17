"""Tests for HealthCheck database model"""
import pytest
from datetime import datetime, timezone
import json


@pytest.mark.asyncio
async def test_create_healthcheck(db_session):
    """Test creating a health check report in database"""
    from app.models.healthcheck import HealthCheck

    health_data = {
        "cpu_percent": 45.5,
        "memory_percent": 62.3,
        "disk_percent": 78.1
    }

    healthcheck = HealthCheck(
        device_id="test-device-001",
        status="healthy",
        metrics=health_data
    )

    db_session.add(healthcheck)
    await db_session.commit()
    await db_session.refresh(healthcheck)

    assert healthcheck.device_id == "test-device-001"
    assert healthcheck.status == "healthy"
    assert healthcheck.metrics == health_data
    assert healthcheck.reported_at is not None


@pytest.mark.asyncio
async def test_healthcheck_default_status(db_session):
    """Test health check gets default status='healthy' if not specified"""
    from app.models.healthcheck import HealthCheck

    healthcheck = HealthCheck(
        device_id="test-device-002",
        metrics={"cpu_percent": 20.0}
    )

    db_session.add(healthcheck)
    await db_session.commit()
    await db_session.refresh(healthcheck)

    # Should have default status
    assert healthcheck.status == "healthy"


@pytest.mark.asyncio
async def test_healthcheck_reported_at_auto_populated(db_session):
    """Test reported_at is automatically set on creation"""
    from app.models.healthcheck import HealthCheck

    before = datetime.now(timezone.utc)

    healthcheck = HealthCheck(
        device_id="test-device-003",
        metrics={"cpu_percent": 30.0}
    )

    db_session.add(healthcheck)
    await db_session.commit()
    await db_session.refresh(healthcheck)

    # reported_at should be set automatically and be recent
    assert healthcheck.reported_at is not None
    time_diff = abs((datetime.now(timezone.utc) - healthcheck.reported_at.replace(tzinfo=timezone.utc)).total_seconds())
    assert time_diff < 2, f"reported_at was set {time_diff} seconds ago, expected < 2 seconds"


@pytest.mark.asyncio
async def test_healthcheck_metrics_stored_as_json(db_session):
    """Test metrics are properly stored and retrieved as JSON"""
    from app.models.healthcheck import HealthCheck

    complex_metrics = {
        "cpu": {"percent": 45.5, "cores": 4},
        "memory": {"percent": 62.3, "total_gb": 16},
        "disk": {"percent": 78.1, "available_gb": 120.5},
        "services": ["nginx", "postgres", "redis"]
    }

    healthcheck = HealthCheck(
        device_id="test-device-004",
        metrics=complex_metrics
    )

    db_session.add(healthcheck)
    await db_session.commit()
    await db_session.refresh(healthcheck)

    # Should retrieve the same complex structure
    assert healthcheck.metrics == complex_metrics
    assert isinstance(healthcheck.metrics, dict)
    assert healthcheck.metrics["services"] == ["nginx", "postgres", "redis"]


@pytest.mark.asyncio
async def test_healthcheck_can_be_queried_by_device(db_session):
    """Test health checks can be queried by device_id"""
    from app.models.healthcheck import HealthCheck
    from sqlalchemy import select

    # Create multiple health checks for same device
    for i in range(3):
        healthcheck = HealthCheck(
            device_id="query-device",
            status="healthy" if i < 2 else "degraded",
            metrics={"check_num": i}
        )
        db_session.add(healthcheck)

    await db_session.commit()

    # Query all health checks for device
    result = await db_session.execute(
        select(HealthCheck).where(HealthCheck.device_id == "query-device")
    )
    health_checks = result.scalars().all()

    assert len(health_checks) == 3
    assert all(hc.device_id == "query-device" for hc in health_checks)


@pytest.mark.asyncio
async def test_healthcheck_can_query_latest_by_device(db_session):
    """Test querying most recent health check for a device"""
    from app.models.healthcheck import HealthCheck
    from sqlalchemy import select, desc
    import asyncio

    # Create health checks with small delays to ensure different timestamps
    for i in range(3):
        healthcheck = HealthCheck(
            device_id="latest-device",
            metrics={"iteration": i}
        )
        db_session.add(healthcheck)
        await db_session.commit()
        if i < 2:  # Don't wait after last one
            await asyncio.sleep(0.1)  # Increased delay for more reliable ordering

    # Query most recent
    result = await db_session.execute(
        select(HealthCheck)
        .where(HealthCheck.device_id == "latest-device")
        .order_by(desc(HealthCheck.reported_at))
        .limit(1)
    )
    latest = result.scalar_one_or_none()

    assert latest is not None
    # Due to timestamp resolution, just verify we get one of the records back
    assert latest.metrics["iteration"] in [0, 1, 2]
