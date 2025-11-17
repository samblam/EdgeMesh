"""Tests for User database model"""
import pytest
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_create_user(db_session):
    """Test creating a user in database"""
    from app.models.user import User

    user = User(
        user_id="alice@example.com",
        device_id="device-123",
        full_name="Alice Smith",
        email="alice@example.com",
        role="developer",
        status="active"
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.user_id == "alice@example.com"
    assert user.device_id == "device-123"
    assert user.full_name == "Alice Smith"
    assert user.email == "alice@example.com"
    assert user.role == "developer"
    assert user.status == "active"
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_user_default_status(db_session):
    """Test user gets default status='active' if not specified"""
    from app.models.user import User

    user = User(
        user_id="bob@example.com",
        device_id="device-456",
        full_name="Bob Jones",
        email="bob@example.com",
        role="analyst"
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Should have default status
    assert user.status == "active"


@pytest.mark.asyncio
async def test_user_created_at_auto_populated(db_session):
    """Test created_at is automatically set on creation"""
    from app.models.user import User

    before = datetime.now(timezone.utc)

    user = User(
        user_id="charlie@example.com",
        device_id="device-789",
        full_name="Charlie Brown",
        email="charlie@example.com",
        role="admin"
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # created_at should be set automatically and be recent
    assert user.created_at is not None
    time_diff = abs((datetime.now(timezone.utc) - user.created_at.replace(tzinfo=timezone.utc)).total_seconds())
    assert time_diff < 2, f"created_at was set {time_diff} seconds ago, expected < 2 seconds"


@pytest.mark.asyncio
async def test_user_id_is_unique(db_session):
    """Test user_id must be unique"""
    from app.models.user import User
    from sqlalchemy.exc import IntegrityError

    # Create first user
    user1 = User(
        user_id="same@example.com",
        device_id="device-1",
        full_name="First User",
        email="first@example.com",
        role="developer"
    )
    db_session.add(user1)
    await db_session.commit()

    # Try to create second user with same user_id
    user2 = User(
        user_id="same@example.com",  # Duplicate!
        device_id="device-2",
        full_name="Second User",
        email="second@example.com",
        role="admin"
    )
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_user_can_be_queried(db_session):
    """Test users can be queried from database"""
    from app.models.user import User
    from sqlalchemy import select

    # Create test user
    user = User(
        user_id="query@example.com",
        device_id="device-query",
        full_name="Query Test",
        email="query@example.com",
        role="developer"
    )
    db_session.add(user)
    await db_session.commit()

    # Query it back
    result = await db_session.execute(
        select(User).where(User.user_id == "query@example.com")
    )
    found_user = result.scalar_one_or_none()

    assert found_user is not None
    assert found_user.user_id == "query@example.com"
    assert found_user.device_id == "device-query"
    assert found_user.full_name == "Query Test"
    assert found_user.email == "query@example.com"
    assert found_user.role == "developer"
