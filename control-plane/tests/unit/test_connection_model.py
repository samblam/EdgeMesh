"""Tests for Connection database model"""
import pytest
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_create_connection(db_session):
    """Test creating a connection in database"""
    from app.models.connection import Connection

    connection = Connection(
        connection_id="conn-123",
        device_id="device-001",
        user_id="user@example.com",
        service_name="database",
        status="established"
    )

    db_session.add(connection)
    await db_session.commit()
    await db_session.refresh(connection)

    assert connection.connection_id == "conn-123"
    assert connection.device_id == "device-001"
    assert connection.user_id == "user@example.com"
    assert connection.service_name == "database"
    assert connection.status == "established"
    assert connection.established_at is not None
    assert connection.terminated_at is None


@pytest.mark.asyncio
async def test_connection_default_status(db_session):
    """Test connection gets default status='established' if not specified"""
    from app.models.connection import Connection

    connection = Connection(
        connection_id="conn-456",
        device_id="device-002",
        user_id="user2@example.com",
        service_name="api"
    )

    db_session.add(connection)
    await db_session.commit()
    await db_session.refresh(connection)

    # Should have default status
    assert connection.status == "established"


@pytest.mark.asyncio
async def test_connection_established_at_auto_populated(db_session):
    """Test established_at is automatically set on creation"""
    from app.models.connection import Connection

    before = datetime.now(timezone.utc)

    connection = Connection(
        connection_id="conn-789",
        device_id="device-003",
        user_id="user3@example.com",
        service_name="storage"
    )

    db_session.add(connection)
    await db_session.commit()
    await db_session.refresh(connection)

    # established_at should be set automatically and be recent
    assert connection.established_at is not None
    time_diff = abs((datetime.now(timezone.utc) - connection.established_at.replace(tzinfo=timezone.utc)).total_seconds())
    assert time_diff < 2, f"established_at was set {time_diff} seconds ago, expected < 2 seconds"


@pytest.mark.asyncio
async def test_connection_id_is_unique(db_session):
    """Test connection_id must be unique"""
    from app.models.connection import Connection
    from sqlalchemy.exc import IntegrityError

    # Create first connection
    conn1 = Connection(
        connection_id="same-id",
        device_id="device-1",
        user_id="user1@example.com",
        service_name="api"
    )
    db_session.add(conn1)
    await db_session.commit()

    # Try to create second connection with same connection_id
    conn2 = Connection(
        connection_id="same-id",  # Duplicate!
        device_id="device-2",
        user_id="user2@example.com",
        service_name="database"
    )
    db_session.add(conn2)

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_connection_can_be_queried(db_session):
    """Test connections can be queried from database"""
    from app.models.connection import Connection
    from sqlalchemy import select

    # Create test connection
    connection = Connection(
        connection_id="query-conn",
        device_id="query-device",
        user_id="query@example.com",
        service_name="analytics"
    )
    db_session.add(connection)
    await db_session.commit()

    # Query it back
    result = await db_session.execute(
        select(Connection).where(Connection.connection_id == "query-conn")
    )
    found = result.scalar_one_or_none()

    assert found is not None
    assert found.connection_id == "query-conn"
    assert found.device_id == "query-device"
    assert found.service_name == "analytics"


@pytest.mark.asyncio
async def test_connection_terminated_at_optional(db_session):
    """Test terminated_at is optional and can be set"""
    from app.models.connection import Connection

    connection = Connection(
        connection_id="term-test",
        device_id="device-999",
        user_id="user@example.com",
        service_name="api"
    )

    db_session.add(connection)
    await db_session.commit()
    await db_session.refresh(connection)

    # Initially null
    assert connection.terminated_at is None

    # Can be set
    connection.status = "terminated"
    connection.terminated_at = datetime.now(timezone.utc)
    await db_session.commit()
    await db_session.refresh(connection)

    assert connection.status == "terminated"
    assert connection.terminated_at is not None
