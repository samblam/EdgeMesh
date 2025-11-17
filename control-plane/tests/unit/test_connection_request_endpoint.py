"""Tests for connection request endpoint with OPA integration"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_connection_request_endpoint_exists(client: AsyncClient):
    """Test that POST /api/v1/connections/request endpoint exists"""
    response = await client.post(
        "/api/v1/connections/request",
        json={
            "device_id": "device-123",
            "user_id": "alice@example.com",
            "service_name": "database"
        }
    )
    # Endpoint exists and returns 404 because device doesn't exist (not route not found)
    # This proves the endpoint is registered and working
    assert response.status_code == 404
    assert "device" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_connection_request_authorized(client: AsyncClient, db_session):
    """Test successful authorization and connection creation"""
    from app.models.device import Device
    from app.models.user import User
    from app.models.healthcheck import HealthCheck

    # Create test device
    device = Device(
        device_id="device-123",
        device_type="laptop",
        certificate_serial="CERT-123",
        certificate_pem="-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----",
        status="active"
    )
    db_session.add(device)

    # Create test user
    user = User(
        user_id="alice@example.com",
        device_id="device-123",
        full_name="Alice Smith",
        email="alice@example.com",
        role="developer"
    )
    db_session.add(user)

    # Create recent health check with compliant device
    healthcheck = HealthCheck(
        device_id="device-123",
        status="healthy",
        cpu_usage=45.5,
        memory_usage=62.3,
        disk_usage=78.1,
        os_patches_current=True,
        antivirus_enabled=True,
        disk_encrypted=True
    )
    db_session.add(healthcheck)
    await db_session.commit()

    # Mock OPA to return allow decision
    with patch('app.services.opa_client.OPAClient.evaluate_policy') as mock_opa:
        mock_opa.return_value = {"allow": True}

        response = await client.post(
            "/api/v1/connections/request",
            json={
                "device_id": "device-123",
                "user_id": "alice@example.com",
                "service_name": "database"
            }
        )

    assert response.status_code == 200
    data = response.json()

    # Should return ConnectionResponse
    assert "connection_id" in data
    assert data["status"] == "authorized"
    assert data["service_name"] == "database"
    assert "virtual_tunnel" in data


@pytest.mark.asyncio
async def test_connection_request_denied(client: AsyncClient, db_session):
    """Test denied authorization returns 403"""
    from app.models.device import Device
    from app.models.user import User
    from app.models.healthcheck import HealthCheck

    # Create test device
    device = Device(
        device_id="device-456",
        device_type="laptop",
        certificate_serial="CERT-456",
        certificate_pem="-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----",
        status="active"
    )
    db_session.add(device)

    # Create test user with analyst role (not allowed for database service)
    user = User(
        user_id="bob@example.com",
        device_id="device-456",
        full_name="Bob Jones",
        email="bob@example.com",
        role="analyst"
    )
    db_session.add(user)

    # Create recent health check
    healthcheck = HealthCheck(
        device_id="device-456",
        status="healthy",
        cpu_usage=45.5,
        memory_usage=62.3,
        os_patches_current=True,
        antivirus_enabled=True,
        disk_encrypted=True
    )
    db_session.add(healthcheck)
    await db_session.commit()

    # Mock OPA to return deny decision
    with patch('app.services.opa_client.OPAClient.evaluate_policy') as mock_opa:
        mock_opa.return_value = {"allow": False}

        response = await client.post(
            "/api/v1/connections/request",
            json={
                "device_id": "device-456",
                "user_id": "bob@example.com",
                "service_name": "database"
            }
        )

    assert response.status_code == 403
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_connection_request_device_not_found(client: AsyncClient, db_session):
    """Test request with non-existent device returns 404"""
    response = await client.post(
        "/api/v1/connections/request",
        json={
            "device_id": "nonexistent",
            "user_id": "alice@example.com",
            "service_name": "database"
        }
    )

    assert response.status_code == 404
    data = response.json()
    assert "device" in data["detail"].lower()


@pytest.mark.asyncio
async def test_connection_request_inactive_device(client: AsyncClient, db_session):
    """Test request with inactive device returns 403"""
    from app.models.device import Device

    # Create inactive device
    device = Device(
        device_id="device-inactive",
        device_type="laptop",
        certificate_serial="CERT-inactive",
        certificate_pem="-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----",
        status="suspended"
    )
    db_session.add(device)
    await db_session.commit()

    response = await client.post(
        "/api/v1/connections/request",
        json={
            "device_id": "device-inactive",
            "user_id": "alice@example.com",
            "service_name": "database"
        }
    )

    assert response.status_code == 403
    data = response.json()
    assert "inactive" in data["detail"].lower() or "not active" in data["detail"].lower()


@pytest.mark.asyncio
async def test_connection_request_stale_health_check(client: AsyncClient, db_session):
    """Test request with stale health check (> 5 min old) returns 503"""
    from app.models.device import Device
    from app.models.user import User
    from app.models.healthcheck import HealthCheck

    # Create test device
    device = Device(
        device_id="device-stale",
        device_type="laptop",
        certificate_serial="CERT-stale",
        certificate_pem="-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----",
        status="active"
    )
    db_session.add(device)

    # Create test user
    user = User(
        user_id="charlie@example.com",
        device_id="device-stale",
        full_name="Charlie Brown",
        email="charlie@example.com",
        role="developer"
    )
    db_session.add(user)

    # Create old health check (10 minutes ago)
    old_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    healthcheck = HealthCheck(
        device_id="device-stale",
        status="healthy",
        cpu_usage=45.5,
        memory_usage=62.3
    )
    db_session.add(healthcheck)
    await db_session.commit()

    # Manually update the reported_at timestamp (simulating old data)
    from sqlalchemy import update
    await db_session.execute(
        update(HealthCheck)
        .where(HealthCheck.device_id == "device-stale")
        .values(reported_at=old_time)
    )
    await db_session.commit()

    response = await client.post(
        "/api/v1/connections/request",
        json={
            "device_id": "device-stale",
            "user_id": "charlie@example.com",
            "service_name": "database"
        }
    )

    assert response.status_code == 503
    data = response.json()
    assert "health" in data["detail"].lower()


@pytest.mark.asyncio
async def test_connection_request_logs_to_audit(client: AsyncClient, db_session):
    """Test that connection request creates audit log entry"""
    from app.models.device import Device
    from app.models.user import User
    from app.models.healthcheck import HealthCheck
    from app.models.audit import AuditLog
    from sqlalchemy import select

    # Create test data
    device = Device(
        device_id="device-audit",
        device_type="laptop",
        certificate_serial="CERT-audit",
        certificate_pem="-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----",
        status="active"
    )
    db_session.add(device)

    user = User(
        user_id="audit@example.com",
        device_id="device-audit",
        full_name="Audit User",
        email="audit@example.com",
        role="developer"
    )
    db_session.add(user)

    healthcheck = HealthCheck(
        device_id="device-audit",
        status="healthy",
        cpu_usage=45.5,
        memory_usage=62.3,
        os_patches_current=True,
        antivirus_enabled=True,
        disk_encrypted=True
    )
    db_session.add(healthcheck)
    await db_session.commit()

    # Mock OPA
    with patch('app.services.opa_client.OPAClient.evaluate_policy') as mock_opa:
        mock_opa.return_value = {"allow": True}

        response = await client.post(
            "/api/v1/connections/request",
            json={
                "device_id": "device-audit",
                "user_id": "audit@example.com",
                "service_name": "database"
            }
        )

    assert response.status_code == 200

    # Verify audit log was created
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.device_id == "device-audit")
    )
    audit = result.scalar_one_or_none()

    assert audit is not None
    assert audit.user_id == "audit@example.com"
    assert audit.service_name == "database"
    assert audit.decision == "allow"
    assert audit.policy_version is not None


@pytest.mark.asyncio
async def test_connection_request_validates_request_body(client: AsyncClient, db_session):
    """Test that invalid request body returns 422"""
    response = await client.post(
        "/api/v1/connections/request",
        json={
            "device_id": "device-123"
            # Missing user_id and service_name
        }
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_connection_request_creates_connection_record(client: AsyncClient, db_session):
    """Test that successful authorization creates Connection record"""
    from app.models.device import Device
    from app.models.user import User
    from app.models.healthcheck import HealthCheck
    from app.models.connection import Connection
    from sqlalchemy import select

    # Create test data
    device = Device(
        device_id="device-conn",
        device_type="laptop",
        certificate_serial="CERT-conn",
        certificate_pem="-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----",
        status="active"
    )
    db_session.add(device)

    user = User(
        user_id="conn@example.com",
        device_id="device-conn",
        full_name="Connection User",
        email="conn@example.com",
        role="developer"
    )
    db_session.add(user)

    healthcheck = HealthCheck(
        device_id="device-conn",
        status="healthy",
        cpu_usage=45.5,
        memory_usage=62.3,
        os_patches_current=True,
        antivirus_enabled=True,
        disk_encrypted=True
    )
    db_session.add(healthcheck)
    await db_session.commit()

    # Mock OPA
    with patch('app.services.opa_client.OPAClient.evaluate_policy') as mock_opa:
        mock_opa.return_value = {"allow": True}

        response = await client.post(
            "/api/v1/connections/request",
            json={
                "device_id": "device-conn",
                "user_id": "conn@example.com",
                "service_name": "database"
            }
        )

    assert response.status_code == 200
    data = response.json()

    # Verify Connection record was created
    result = await db_session.execute(
        select(Connection).where(Connection.connection_id == data["connection_id"])
    )
    connection = result.scalar_one_or_none()

    assert connection is not None
    assert connection.device_id == "device-conn"
    assert connection.user_id == "conn@example.com"
    assert connection.service_name == "database"
    assert connection.status == "established"
