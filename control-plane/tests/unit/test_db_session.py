"""Tests for database session management"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.models.device import Device


@pytest.mark.asyncio
async def test_session_commits_changes(db_session: AsyncSession):
    """Test that database session commits changes successfully"""
    device_id = "test-commit-device"

    # Add a device
    device = Device(
        device_id=device_id,
        device_type="laptop",
        certificate_serial="test-serial-commit",
        certificate_pem="test-cert"
    )
    db_session.add(device)
    await db_session.commit()

    # Verify it was committed
    await db_session.refresh(device)
    assert device.device_id == device_id
    assert device.status == "active"  # Default status


@pytest.mark.asyncio
async def test_session_rollback_on_error(db_session: AsyncSession):
    """Test that session can be rolled back on error"""
    device_id = "test-rollback-device"

    # Add initial device
    device1 = Device(
        device_id=device_id,
        device_type="laptop",
        certificate_serial="test-serial-1",
        certificate_pem="test-cert"
    )
    db_session.add(device1)
    await db_session.commit()

    # Try to add duplicate (will cause IntegrityError)
    device2 = Device(
        device_id=device_id,  # Same ID - violates unique constraint
        device_type="server",
        certificate_serial="test-serial-2",
        certificate_pem="test-cert-2"
    )
    db_session.add(device2)

    # Attempt to commit (should fail)
    with pytest.raises(IntegrityError):
        await db_session.commit()

    # Roll back the failed transaction
    await db_session.rollback()

    # Session should still be usable after rollback
    from sqlalchemy import select
    result = await db_session.execute(
        select(Device).where(Device.device_id == device_id)
    )
    devices = result.scalars().all()

    # Only the first device should exist
    assert len(devices) == 1
    assert devices[0].device_type == "laptop"


@pytest.mark.asyncio
async def test_session_handles_integrity_error(db_session: AsyncSession):
    """Test proper handling of database integrity constraint violations"""
    # Create first device
    device1 = Device(
        device_id="unique-test-device",
        device_type="laptop",
        certificate_serial="unique-serial",
        certificate_pem="test-cert"
    )
    db_session.add(device1)
    await db_session.commit()

    # Try to create device with same serial number (unique constraint)
    device2 = Device(
        device_id="different-device",
        device_type="laptop",
        certificate_serial="unique-serial",  # Duplicate serial
        certificate_pem="test-cert"
    )
    db_session.add(device2)

    # Should raise IntegrityError due to unique constraint
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_session_transaction_isolation(db_session: AsyncSession):
    """Test that session changes are isolated until commit"""
    device_id = "isolation-test-device"

    # Add device but don't commit
    device = Device(
        device_id=device_id,
        device_type="laptop",
        certificate_serial="isolation-serial",
        certificate_pem="test-cert"
    )
    db_session.add(device)

    # Flush to database but don't commit
    await db_session.flush()

    # Device should be in session
    from sqlalchemy import select
    result = await db_session.execute(
        select(Device).where(Device.device_id == device_id)
    )
    found_device = result.scalar_one_or_none()
    assert found_device is not None
    assert found_device.device_id == device_id

    # Now commit
    await db_session.commit()

    # Should still exist after commit
    result = await db_session.execute(
        select(Device).where(Device.device_id == device_id)
    )
    committed_device = result.scalar_one_or_none()
    assert committed_device is not None
