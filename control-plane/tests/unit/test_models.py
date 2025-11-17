"""Tests for database models"""
import pytest
from datetime import datetime, timezone
from sqlalchemy import select


@pytest.mark.asyncio
async def test_create_device(db_session):
    """Test creating a device in database"""
    from app.models.device import Device

    device = Device(
        device_id="test-device-001",
        device_type="laptop",
        certificate_serial="abc123",
        certificate_pem="-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----",
        os="Ubuntu",
        os_version="22.04",
        status="active"
    )

    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)

    assert device.device_id == "test-device-001"
    assert device.device_type == "laptop"
    assert device.status == "active"
    assert device.enrolled_at is not None


@pytest.mark.asyncio
async def test_device_default_status(db_session):
    """Test device gets default status='active' if not specified"""
    from app.models.device import Device

    device = Device(
        device_id="test-device-002",
        device_type="server",
        certificate_serial="def456",
        certificate_pem="-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"
    )

    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)

    # Should have default status
    assert device.status == "active"


@pytest.mark.asyncio
async def test_device_enrolled_at_auto_populated(db_session):
    """Test enrolled_at is automatically set on creation"""
    from app.models.device import Device
    from datetime import timedelta

    before = datetime.now(timezone.utc)

    device = Device(
        device_id="test-device-003",
        device_type="iot",
        certificate_serial="ghi789",
        certificate_pem="-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"
    )

    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)

    # enrolled_at should be set automatically and be recent (within last 2 seconds)
    assert device.enrolled_at is not None
    time_diff = abs((datetime.now(timezone.utc) - device.enrolled_at.replace(tzinfo=timezone.utc)).total_seconds())
    assert time_diff < 2,  f"enrolled_at was set {time_diff} seconds ago, expected < 2 seconds"


@pytest.mark.asyncio
async def test_device_unique_serial(db_session):
    """Test certificate_serial must be unique"""
    from app.models.device import Device
    from sqlalchemy.exc import IntegrityError

    # Create first device
    device1 = Device(
        device_id="device-1",
        device_type="laptop",
        certificate_serial="same-serial",
        certificate_pem="-----BEGIN CERTIFICATE-----\ntest1\n-----END CERTIFICATE-----"
    )
    db_session.add(device1)
    await db_session.commit()

    # Try to create second device with same serial
    device2 = Device(
        device_id="device-2",
        device_type="laptop",
        certificate_serial="same-serial",  # Duplicate!
        certificate_pem="-----BEGIN CERTIFICATE-----\ntest2\n-----END CERTIFICATE-----"
    )
    db_session.add(device2)

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_device_can_be_queried(db_session):
    """Test devices can be queried from database"""
    from app.models.device import Device

    # Create test device
    device = Device(
        device_id="query-test-device",
        device_type="laptop",
        certificate_serial="query123",
        certificate_pem="-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"
    )
    db_session.add(device)
    await db_session.commit()

    # Query it back
    result = await db_session.execute(
        select(Device).where(Device.device_id == "query-test-device")
    )
    found_device = result.scalar_one_or_none()

    assert found_device is not None
    assert found_device.device_id == "query-test-device"
    assert found_device.device_type == "laptop"


@pytest.mark.asyncio
async def test_device_optional_fields(db_session):
    """Test device can be created without optional fields"""
    from app.models.device import Device

    # Minimal device (os, os_version, last_seen are optional)
    device = Device(
        device_id="minimal-device",
        device_type="iot",
        certificate_serial="minimal123",
        certificate_pem="-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----"
    )

    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)

    assert device.device_id == "minimal-device"
    assert device.os is None
    assert device.os_version is None
    assert device.last_seen is None
