"""Unit tests for connection authorization endpoint"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device
from app.models.user import User
from app.models.healthcheck import HealthCheck
from app.models.connection import Connection
from app.models.audit import AuditLog


@pytest.mark.asyncio
async def test_request_connection_device_not_found(client: AsyncClient):
    """Test connection request when device doesn't exist"""
    response = await client.post(
        "/api/v1/connections/request",
        json={
            "device_id": "nonexistent-device",
            "user_id": "test-user-001",
            "service_name": "database"
        }
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Device not found"


@pytest.mark.asyncio
async def test_request_connection_inactive_device(client: AsyncClient, db_session: AsyncSession):
    """Test connection request when device is not active"""
    # Create inactive device
    device = Device(
        device_id="inactive-device-001",
        device_type="laptop",
        certificate_serial="inactive-serial",
        certificate_pem="inactive-cert-pem",
        os="Ubuntu",
        os_version="22.04",
        status="inactive"
    )
    db_session.add(device)
    await db_session.commit()

    response = await client.post(
        "/api/v1/connections/request",
        json={
            "device_id": "inactive-device-001",
            "user_id": "test-user-001",
            "service_name": "database"
        }
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Device is not active"


@pytest.mark.asyncio
async def test_request_connection_user_not_found(client: AsyncClient, db_session: AsyncSession):
    """Test connection request when user doesn't exist"""
    # Create active device
    device = Device(
        device_id="test-device-002",
        device_type="laptop",
        certificate_serial="test-serial-002",
        certificate_pem="test-cert-pem",
        os="Ubuntu",
        os_version="22.04",
        status="active"
    )
    db_session.add(device)
    await db_session.commit()

    response = await client.post(
        "/api/v1/connections/request",
        json={
            "device_id": "test-device-002",
            "user_id": "nonexistent-user",
            "service_name": "database"
        }
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_request_connection_no_health_check(client: AsyncClient, db_session: AsyncSession):
    """Test connection request when no health check data exists"""
    # Create active device
    device = Device(
        device_id="test-device-003",
        device_type="laptop",
        certificate_serial="test-serial-003",
        certificate_pem="test-cert-pem",
        os="Ubuntu",
        os_version="22.04",
        status="active"
    )
    db_session.add(device)

    # Create user
    user = User(
        user_id="test-user-003",
        device_id="test-device-003",
        full_name="Test User 3",
        email="test3@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/connections/request",
        json={
            "device_id": "test-device-003",
            "user_id": "test-user-003",
            "service_name": "database"
        }
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "No health check data available for device"


@pytest.mark.asyncio
async def test_request_connection_stale_health_check(client: AsyncClient, db_session: AsyncSession):
    """Test connection request when health check is stale (>5 minutes)"""
    # Create active device
    device = Device(
        device_id="test-device-004",
        device_type="laptop",
        certificate_serial="test-serial-004",
        certificate_pem="test-cert-pem",
        os="Ubuntu",
        os_version="22.04",
        status="active"
    )
    db_session.add(device)

    # Create user
    user = User(
        user_id="test-user-004",
        device_id="test-device-004",
        full_name="Test User 4",
        email="test4@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)

    # Create stale health check (6 minutes old)
    stale_time = datetime.now(timezone.utc) - timedelta(minutes=6)
    healthcheck = HealthCheck(
        device_id="test-device-004",
        os_patches_current=True,
        antivirus_enabled=True,
        disk_encrypted=True,
        cpu_usage=50.0,
        memory_usage=60.0,
        reported_at=stale_time
    )
    db_session.add(healthcheck)
    await db_session.commit()

    response = await client.post(
        "/api/v1/connections/request",
        json={
            "device_id": "test-device-004",
            "user_id": "test-user-004",
            "service_name": "database"
        }
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "Health check data is stale (older than 5 minutes)"


@pytest.mark.asyncio
async def test_request_connection_policy_denial(client: AsyncClient, db_session: AsyncSession):
    """Test connection request when OPA policy denies access"""
    # Create active device
    device = Device(
        device_id="test-device-005",
        device_type="laptop",
        certificate_serial="test-serial-005",
        certificate_pem="test-cert-pem",
        os="Ubuntu",
        os_version="22.04",
        status="active"
    )
    db_session.add(device)

    # Create user
    user = User(
        user_id="test-user-005",
        device_id="test-device-005",
        full_name="Test User 5",
        email="test5@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)

    # Create recent health check
    recent_time = datetime.now(timezone.utc) - timedelta(minutes=1)
    healthcheck = HealthCheck(
        device_id="test-device-005",
        os_patches_current=True,
        antivirus_enabled=True,
        disk_encrypted=True,
        cpu_usage=50.0,
        memory_usage=60.0,
        reported_at=recent_time
    )
    db_session.add(healthcheck)
    await db_session.commit()

    # Mock OPA client to return denial
    with patch('app.services.opa_client.OPAClient.evaluate_policy') as mock_opa:
        mock_opa.return_value = {
            "allowed": False,
            "decision": "deny"
        }

        response = await client.post(
            "/api/v1/connections/request",
            json={
                "device_id": "test-device-005",
                "user_id": "test-user-005",
                "service_name": "database"
            }
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Access denied by policy"

        # Verify OPA was called with correct input
        call_args = mock_opa.call_args
        assert call_args is not None
        opa_input = call_args.kwargs["input_data"]
        assert opa_input["device"]["device_id"] == "test-device-005"
        assert opa_input["user"]["user_id"] == "test-user-005"
        assert opa_input["service"]["name"] == "database"


@pytest.mark.asyncio
async def test_request_connection_successful_authorization(client: AsyncClient, db_session: AsyncSession):
    """Test successful connection request with policy approval"""
    # Create active device
    device = Device(
        device_id="test-device-006",
        device_type="laptop",
        certificate_serial="test-serial-006",
        certificate_pem="test-cert-pem",
        os="Ubuntu",
        os_version="22.04",
        status="active"
    )
    db_session.add(device)

    # Create user
    user = User(
        user_id="test-user-006",
        device_id="test-device-006",
        full_name="Test User 6",
        email="test6@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)

    # Create recent health check
    recent_time = datetime.now(timezone.utc) - timedelta(minutes=1)
    healthcheck = HealthCheck(
        device_id="test-device-006",
        os_patches_current=True,
        antivirus_enabled=True,
        disk_encrypted=True,
        cpu_usage=50.0,
        memory_usage=60.0,
        reported_at=recent_time
    )
    db_session.add(healthcheck)
    await db_session.commit()

    # Mock OPA client to return approval
    with patch('app.services.opa_client.OPAClient.evaluate_policy') as mock_opa:
        mock_opa.return_value = {
            "allowed": True,
            "decision": "allow"
        }

        response = await client.post(
            "/api/v1/connections/request",
            json={
                "device_id": "test-device-006",
                "user_id": "test-user-006",
                "service_name": "database"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "authorized"
        assert data["service_name"] == "database"
        assert "connection_id" in data
        assert "virtual_tunnel" in data
        assert data["virtual_tunnel"]["type"] == "wireguard"
        assert data["virtual_tunnel"]["endpoint"] == "wg://database.edgemesh.local"

        # Verify connection was created in database
        from sqlalchemy import select
        result = await db_session.execute(
            select(Connection).where(Connection.connection_id == data["connection_id"])
        )
        connection = result.scalar_one_or_none()
        assert connection is not None
        assert connection.device_id == "test-device-006"
        assert connection.user_id == "test-user-006"
        assert connection.service_name == "database"
        assert connection.status == "established"


@pytest.mark.asyncio
async def test_request_connection_creates_audit_log(client: AsyncClient, db_session: AsyncSession):
    """Test that connection request creates audit log entry"""
    # Create active device
    device = Device(
        device_id="test-device-007",
        device_type="laptop",
        certificate_serial="test-serial-007",
        certificate_pem="test-cert-pem",
        os="Ubuntu",
        os_version="22.04",
        status="active"
    )
    db_session.add(device)

    # Create user
    user = User(
        user_id="test-user-007",
        device_id="test-device-007",
        full_name="Test User 7",
        email="test7@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)

    # Create recent health check
    recent_time = datetime.now(timezone.utc) - timedelta(minutes=1)
    healthcheck = HealthCheck(
        device_id="test-device-007",
        os_patches_current=True,
        antivirus_enabled=True,
        disk_encrypted=True,
        cpu_usage=50.0,
        memory_usage=60.0,
        reported_at=recent_time
    )
    db_session.add(healthcheck)
    await db_session.commit()

    # Mock OPA client
    with patch('app.services.opa_client.OPAClient.evaluate_policy') as mock_opa:
        mock_opa.return_value = {
            "allowed": True,
            "decision": "allow"
        }

        await client.post(
            "/api/v1/connections/request",
            json={
                "device_id": "test-device-007",
                "user_id": "test-user-007",
                "service_name": "database"
            }
        )

        # Verify audit log was created
        from sqlalchemy import select
        result = await db_session.execute(
            select(AuditLog).where(
                AuditLog.device_id == "test-device-007",
                AuditLog.event_type == "connection_request"
            )
        )
        audit = result.scalar_one_or_none()
        assert audit is not None
        assert audit.action == "request_connection"
        assert audit.user_id == "test-user-007"
        assert audit.service_name == "database"
        assert audit.decision == "allow"
        assert audit.policy_version == "v1.0"


@pytest.mark.asyncio
async def test_request_connection_opa_input_structure(client: AsyncClient, db_session: AsyncSession):
    """Test that OPA receives correctly structured input data"""
    # Create active device
    device = Device(
        device_id="test-device-008",
        device_type="laptop",
        certificate_serial="test-serial-008",
        certificate_pem="test-cert-pem",
        os="Ubuntu",
        os_version="22.04",
        status="active"
    )
    db_session.add(device)

    # Create user with specific role
    user = User(
        user_id="test-user-008",
        device_id="test-device-008",
        full_name="Test User 8",
        email="test8@example.com",
        role="admin",
        status="active"
    )
    db_session.add(user)

    # Create health check with specific values
    recent_time = datetime.now(timezone.utc) - timedelta(minutes=1)
    healthcheck = HealthCheck(
        device_id="test-device-008",
        os_patches_current=True,
        antivirus_enabled=False,
        disk_encrypted=True,
        cpu_usage=75.5,
        memory_usage=82.3,
        reported_at=recent_time
    )
    db_session.add(healthcheck)
    await db_session.commit()

    # Mock OPA client to capture input
    with patch('app.services.opa_client.OPAClient.evaluate_policy') as mock_opa:
        mock_opa.return_value = {
            "allowed": True,
            "decision": "allow"
        }

        await client.post(
            "/api/v1/connections/request",
            json={
                "device_id": "test-device-008",
                "user_id": "test-user-008",
                "service_name": "analytics"
            }
        )

        # Verify OPA input structure
        call_args = mock_opa.call_args
        assert call_args is not None
        opa_input = call_args.kwargs["input_data"]

        # Verify device data
        assert opa_input["device"]["device_id"] == "test-device-008"
        assert opa_input["device"]["authenticated"] is True
        assert opa_input["device"]["status"] == "active"
        assert opa_input["device"]["os_patches_current"] is True
        assert opa_input["device"]["antivirus_enabled"] is False
        assert opa_input["device"]["disk_encrypted"] is True
        assert opa_input["device"]["cpu_usage"] == 75.5
        assert opa_input["device"]["memory_usage"] == 82.3

        # Verify user data
        assert opa_input["user"]["user_id"] == "test-user-008"
        assert opa_input["user"]["email"] == "test8@example.com"
        assert opa_input["user"]["role"] == "admin"

        # Verify service data
        assert opa_input["service"]["name"] == "analytics"

        # Verify time data
        assert "hour" in opa_input["time"]
        assert "day_of_week" in opa_input["time"]
        assert 0 <= opa_input["time"]["hour"] <= 23
        assert 1 <= opa_input["time"]["day_of_week"] <= 7


@pytest.mark.asyncio
async def test_request_connection_handles_null_health_fields(client: AsyncClient, db_session: AsyncSession):
    """Test that connection request handles null health check fields gracefully"""
    # Create active device
    device = Device(
        device_id="test-device-009",
        device_type="laptop",
        certificate_serial="test-serial-009",
        certificate_pem="test-cert-pem",
        os="Ubuntu",
        os_version="22.04",
        status="active"
    )
    db_session.add(device)

    # Create user
    user = User(
        user_id="test-user-009",
        device_id="test-device-009",
        full_name="Test User 9",
        email="test9@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)

    # Create health check with NULL values
    recent_time = datetime.now(timezone.utc) - timedelta(minutes=1)
    healthcheck = HealthCheck(
        device_id="test-device-009",
        os_patches_current=None,
        antivirus_enabled=None,
        disk_encrypted=None,
        cpu_usage=None,
        memory_usage=None,
        reported_at=recent_time
    )
    db_session.add(healthcheck)
    await db_session.commit()

    # Mock OPA client
    with patch('app.services.opa_client.OPAClient.evaluate_policy') as mock_opa:
        mock_opa.return_value = {
            "allowed": False,
            "decision": "deny"
        }

        await client.post(
            "/api/v1/connections/request",
            json={
                "device_id": "test-device-009",
                "user_id": "test-user-009",
                "service_name": "database"
            }
        )

        # Verify OPA was called with default values for NULL fields
        call_args = mock_opa.call_args
        assert call_args is not None
        opa_input = call_args.kwargs["input_data"]
        assert opa_input["device"]["os_patches_current"] is False
        assert opa_input["device"]["antivirus_enabled"] is False
        assert opa_input["device"]["disk_encrypted"] is False
        assert opa_input["device"]["cpu_usage"] == 0.0
        assert opa_input["device"]["memory_usage"] == 0.0


@pytest.mark.asyncio
async def test_request_connection_backward_compatible_opa_response(client: AsyncClient, db_session: AsyncSession):
    """Test that connection request handles old OPA response format (allow vs allowed)"""
    # Create active device
    device = Device(
        device_id="test-device-010",
        device_type="laptop",
        certificate_serial="test-serial-010",
        certificate_pem="test-cert-pem",
        os="Ubuntu",
        os_version="22.04",
        status="active"
    )
    db_session.add(device)

    # Create user
    user = User(
        user_id="test-user-010",
        device_id="test-device-010",
        full_name="Test User 10",
        email="test10@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)

    # Create recent health check
    recent_time = datetime.now(timezone.utc) - timedelta(minutes=1)
    healthcheck = HealthCheck(
        device_id="test-device-010",
        os_patches_current=True,
        antivirus_enabled=True,
        disk_encrypted=True,
        cpu_usage=50.0,
        memory_usage=60.0,
        reported_at=recent_time
    )
    db_session.add(healthcheck)
    await db_session.commit()

    # Mock OPA client with old format (allow instead of allowed)
    with patch('app.services.opa_client.OPAClient.evaluate_policy') as mock_opa:
        mock_opa.return_value = {
            "allow": True  # Old format without "allowed" or "decision"
        }

        response = await client.post(
            "/api/v1/connections/request",
            json={
                "device_id": "test-device-010",
                "user_id": "test-user-010",
                "service_name": "database"
            }
        )

        assert response.status_code == 200
        assert response.json()["status"] == "authorized"
