"""Tests for User model with email and role fields"""
import pytest


@pytest.mark.asyncio
async def test_user_with_email_and_role(db_session):
    """Test User stores email and role for OPA"""
    from app.models.user import User

    user = User(
        user_id="alice@example.com",
        device_id="device-001",
        full_name="Alice Smith",
        email="alice@example.com",
        role="developer"
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.email == "alice@example.com"
    assert user.role == "developer"


@pytest.mark.asyncio
async def test_user_email_unique(db_session):
    """Test user email must be unique"""
    from app.models.user import User
    from sqlalchemy.exc import IntegrityError

    # Create first user
    user1 = User(
        user_id="user1",
        device_id="device-1",
        full_name="User One",
        email="same@example.com",
        role="admin"
    )
    db_session.add(user1)
    await db_session.commit()

    # Try second user with same email
    user2 = User(
        user_id="user2",
        device_id="device-2",
        full_name="User Two",
        email="same@example.com",  # Duplicate!
        role="developer"
    )
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        await db_session.commit()
