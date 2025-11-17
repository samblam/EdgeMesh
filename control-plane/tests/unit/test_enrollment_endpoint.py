"""Tests for device enrollment endpoint"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_enrollment_endpoint_exists(client: AsyncClient):
    """Test POST /api/v1/enroll endpoint exists"""
    response = await client.post(
        "/api/v1/enroll",
        json={
            "device_id": "test-device",
            "device_type": "laptop",
            "enrollment_token": "wrong-token"
        }
    )

    # Should not return 404
    assert response.status_code != 404


@pytest.mark.asyncio
async def test_enrollment_with_valid_token(client: AsyncClient, db_session):
    """Test device enrollment with valid token"""
    from app.config import settings

    response = await client.post(
        "/api/v1/enroll",
        json={
            "device_id": "laptop-001",
            "device_type": "laptop",
            "enrollment_token": settings.ENROLLMENT_TOKEN_SECRET,
            "os": "Ubuntu",
            "os_version": "22.04"
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Should return enrollment response with certificates
    assert data["device_id"] == "laptop-001"
    assert "certificate" in data
    assert "private_key" in data
    assert "ca_certificate" in data
    assert "BEGIN CERTIFICATE" in data["certificate"]
    assert "BEGIN PRIVATE KEY" in data["private_key"]


@pytest.mark.asyncio
async def test_enrollment_with_invalid_token(client: AsyncClient):
    """Test device enrollment rejects invalid token"""
    response = await client.post(
        "/api/v1/enroll",
        json={
            "device_id": "laptop-002",
            "device_type": "laptop",
            "enrollment_token": "invalid-token-123"
        }
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_enrollment_creates_device_in_database(client: AsyncClient, db_session):
    """Test enrollment creates device record in database"""
    from app.config import settings
    from app.models.device import Device
    from sqlalchemy import select

    response = await client.post(
        "/api/v1/enroll",
        json={
            "device_id": "server-001",
            "device_type": "server",
            "enrollment_token": settings.ENROLLMENT_TOKEN_SECRET,
            "os": "Ubuntu",
            "os_version": "20.04"
        }
    )

    assert response.status_code == 200

    # Verify device was created in database
    result = await db_session.execute(
        select(Device).where(Device.device_id == "server-001")
    )
    device = result.scalar_one_or_none()

    assert device is not None
    assert device.device_id == "server-001"
    assert device.device_type == "server"
    assert device.os == "Ubuntu"
    assert device.os_version == "20.04"
    assert device.status == "active"
    assert device.certificate_serial is not None


@pytest.mark.asyncio
async def test_enrollment_rejects_duplicate_device_id(client: AsyncClient, db_session):
    """Test enrollment rejects duplicate device_id"""
    from app.config import settings

    # First enrollment should succeed
    response1 = await client.post(
        "/api/v1/enroll",
        json={
            "device_id": "iot-001",
            "device_type": "iot",
            "enrollment_token": settings.ENROLLMENT_TOKEN_SECRET
        }
    )
    assert response1.status_code == 200

    # Second enrollment with same device_id should fail
    response2 = await client.post(
        "/api/v1/enroll",
        json={
            "device_id": "iot-001",
            "device_type": "iot",
            "enrollment_token": settings.ENROLLMENT_TOKEN_SECRET
        }
    )
    assert response2.status_code == 409  # Conflict


@pytest.mark.asyncio
async def test_enrollment_validates_request_body(client: AsyncClient):
    """Test enrollment validates required fields"""
    from app.config import settings

    # Missing device_type
    response = await client.post(
        "/api/v1/enroll",
        json={
            "device_id": "test-device",
            "enrollment_token": settings.ENROLLMENT_TOKEN_SECRET
        }
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_enrollment_works_without_optional_os_fields(client: AsyncClient, db_session):
    """Test enrollment works without optional os and os_version"""
    from app.config import settings
    from app.models.device import Device
    from sqlalchemy import select

    response = await client.post(
        "/api/v1/enroll",
        json={
            "device_id": "minimal-device",
            "device_type": "iot",
            "enrollment_token": settings.ENROLLMENT_TOKEN_SECRET
        }
    )

    assert response.status_code == 200

    # Verify device in database has NULL os fields
    result = await db_session.execute(
        select(Device).where(Device.device_id == "minimal-device")
    )
    device = result.scalar_one_or_none()

    assert device is not None
    assert device.os is None
    assert device.os_version is None
