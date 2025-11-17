"""Tests for HealthCheck model with specific compliance fields"""
import pytest


@pytest.mark.asyncio
async def test_healthcheck_with_compliance_fields(db_session):
    """Test HealthCheck stores individual compliance fields"""
    from app.models.healthcheck import HealthCheck

    healthcheck = HealthCheck(
        device_id="device-001",
        cpu_usage=45.5,
        memory_usage=62.3,
        disk_usage=78.1,
        os_patches_current=True,
        antivirus_enabled=True,
        disk_encrypted=True
    )

    db_session.add(healthcheck)
    await db_session.commit()
    await db_session.refresh(healthcheck)

    assert healthcheck.cpu_usage == 45.5
    assert healthcheck.memory_usage == 62.3
    assert healthcheck.disk_usage == 78.1
    assert healthcheck.os_patches_current is True
    assert healthcheck.antivirus_enabled is True
    assert healthcheck.disk_encrypted is True


@pytest.mark.asyncio
async def test_healthcheck_compliance_fields_optional(db_session):
    """Test HealthCheck compliance fields are optional"""
    from app.models.healthcheck import HealthCheck

    healthcheck = HealthCheck(
        device_id="device-002",
        status="healthy"
    )

    db_session.add(healthcheck)
    await db_session.commit()
    await db_session.refresh(healthcheck)

    # Optional fields should be None
    assert healthcheck.cpu_usage is None
    assert healthcheck.memory_usage is None
    assert healthcheck.disk_usage is None
    assert healthcheck.os_patches_current is None
    assert healthcheck.antivirus_enabled is None
    assert healthcheck.disk_encrypted is None
