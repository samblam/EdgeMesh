"""Integration tests for Module 2: OPA Policy Engine

Tests the complete workflow from device enrollment through connection
authorization with OPA policy evaluation.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch


@pytest.mark.asyncio
async def test_complete_authorization_workflow(client: AsyncClient, db_session):
    """Test complete flow: enroll -> health -> user -> authorize"""
    from app.models.user import User
    from app.config import settings

    # Step 1: Enroll device
    enroll_response = await client.post(
        "/api/v1/enroll",
        json={
            "device_id": "integration-device-001",
            "device_type": "laptop",
            "enrollment_token": settings.ENROLLMENT_TOKEN_SECRET,
            "os": "Ubuntu",
            "os_version": "22.04"
        }
    )
    assert enroll_response.status_code == 200
    enroll_data = enroll_response.json()
    assert "certificate" in enroll_data
    assert "private_key" in enroll_data

    # Step 2: Create user for this device
    user = User(
        user_id="integra@example.com",
        device_id="integration-device-001",
        full_name="Integration Test User",
        email="integra@example.com",
        role="developer"
    )
    db_session.add(user)
    await db_session.commit()

    # Step 3: Submit health check
    health_response = await client.post(
        "/api/v1/health",
        json={
            "device_id": "integration-device-001",
            "status": "healthy",
            "metrics": {
                "cpu_usage": 45.5,
                "memory_usage": 62.3,
                "disk_usage": 78.1,
                "os_patches_current": True,
                "antivirus_enabled": True,
                "disk_encrypted": True
            }
        }
    )
    assert health_response.status_code == 200

    # Step 4: Request connection authorization (mock OPA)
    with patch('app.services.opa_client.OPAClient.evaluate_policy') as mock_opa:
        mock_opa.return_value = {"allow": True}

        auth_response = await client.post(
            "/api/v1/connections/request",
            json={
                "device_id": "integration-device-001",
                "user_id": "integra@example.com",
                "service_name": "database"
            }
        )

    assert auth_response.status_code == 200
    auth_data = auth_response.json()
    assert auth_data["status"] == "authorized"
    assert "connection_id" in auth_data
    assert auth_data["service_name"] == "database"
    assert "virtual_tunnel" in auth_data

    connection_id = auth_data["connection_id"]

    # Step 5: Retrieve connection details
    get_response = await client.get(f"/api/v1/connections/{connection_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["device_id"] == "integration-device-001"
    assert get_data["user_id"] == "integra@example.com"
    assert get_data["status"] == "established"

    # Step 6: List connections for device
    list_response = await client.get(
        "/api/v1/connections?device_id=integration-device-001"
    )
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["total"] >= 1

    # Step 7: Terminate connection
    delete_response = await client.delete(f"/api/v1/connections/{connection_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Connection terminated"

    # Verify connection is terminated
    verify_response = await client.get(f"/api/v1/connections/{connection_id}")
    assert verify_response.status_code == 200
    assert verify_response.json()["status"] == "terminated"


@pytest.mark.asyncio
async def test_authorization_denied_by_policy(client: AsyncClient, db_session):
    """Test that authorization is denied when OPA policy returns false"""
    from app.models.device import Device
    from app.models.user import User
    from app.models.healthcheck import HealthCheck

    # Create device
    device = Device(
        device_id="denied-device",
        device_type="laptop",
        certificate_serial="CERT-denied",
        certificate_pem="-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----",
        status="active"
    )
    db_session.add(device)

    # Create user (analyst trying to access database)
    user = User(
        user_id="analyst@example.com",
        device_id="denied-device",
        full_name="Analyst User",
        email="analyst@example.com",
        role="analyst"  # Analysts cannot access database service
    )
    db_session.add(user)

    # Submit health check
    healthcheck = HealthCheck(
        device_id="denied-device",
        status="healthy",
        cpu_usage=45.5,
        memory_usage=62.3,
        os_patches_current=True,
        antivirus_enabled=True,
        disk_encrypted=True
    )
    db_session.add(healthcheck)
    await db_session.commit()

    # Request connection (mock OPA to deny)
    with patch('app.services.opa_client.OPAClient.evaluate_policy') as mock_opa:
        mock_opa.return_value = {"allow": False}

        response = await client.post(
            "/api/v1/connections/request",
            json={
                "device_id": "denied-device",
                "user_id": "analyst@example.com",
                "service_name": "database"
            }
        )

    assert response.status_code == 403
    assert "denied" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_device_compliance_workflow(client: AsyncClient, db_session):
    """Test that non-compliant devices are rejected"""
    from app.models.device import Device
    from app.models.user import User
    from app.models.healthcheck import HealthCheck

    # Create device
    device = Device(
        device_id="non-compliant-device",
        device_type="laptop",
        certificate_serial="CERT-nc",
        certificate_pem="-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----",
        status="active"
    )
    db_session.add(device)

    # Create user
    user = User(
        user_id="user-nc@example.com",
        device_id="non-compliant-device",
        full_name="Non-compliant User",
        email="user-nc@example.com",
        role="developer"
    )
    db_session.add(user)

    # Submit health check with non-compliant device (missing antivirus)
    healthcheck = HealthCheck(
        device_id="non-compliant-device",
        status="healthy",
        cpu_usage=45.5,
        memory_usage=62.3,
        os_patches_current=True,
        antivirus_enabled=False,  # NON-COMPLIANT!
        disk_encrypted=True
    )
    db_session.add(healthcheck)
    await db_session.commit()

    # Mock OPA to deny based on compliance
    with patch('app.services.opa_client.OPAClient.evaluate_policy') as mock_opa:
        mock_opa.return_value = {"allow": False}

        response = await client.post(
            "/api/v1/connections/request",
            json={
                "device_id": "non-compliant-device",
                "user_id": "user-nc@example.com",
                "service_name": "database"
            }
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_audit_log_created_on_authorization(client: AsyncClient, db_session):
    """Test that audit logs are created for authorization decisions"""
    from app.models.device import Device
    from app.models.user import User
    from app.models.healthcheck import HealthCheck
    from app.models.audit import AuditLog
    from sqlalchemy import select

    # Create test data
    device = Device(
        device_id="audit-device",
        device_type="laptop",
        certificate_serial="CERT-audit",
        certificate_pem="-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----",
        status="active"
    )
    db_session.add(device)

    user = User(
        user_id="audit@example.com",
        device_id="audit-device",
        full_name="Audit User",
        email="audit@example.com",
        role="developer"
    )
    db_session.add(user)

    healthcheck = HealthCheck(
        device_id="audit-device",
        status="healthy",
        cpu_usage=45.5,
        memory_usage=62.3,
        os_patches_current=True,
        antivirus_enabled=True,
        disk_encrypted=True
    )
    db_session.add(healthcheck)
    await db_session.commit()

    # Request connection
    with patch('app.services.opa_client.OPAClient.evaluate_policy') as mock_opa:
        mock_opa.return_value = {"allow": True}

        await client.post(
            "/api/v1/connections/request",
            json={
                "device_id": "audit-device",
                "user_id": "audit@example.com",
                "service_name": "database"
            }
        )

    # Verify audit log was created
    result = await db_session.execute(
        select(AuditLog)
        .where(AuditLog.device_id == "audit-device")
        .where(AuditLog.event_type == "connection_request")
    )
    audit = result.scalar_one_or_none()

    assert audit is not None
    assert audit.user_id == "audit@example.com"
    assert audit.service_name == "database"
    assert audit.decision == "allow"
    assert audit.policy_version == "v1.0"


@pytest.mark.asyncio
async def test_multiple_concurrent_connections(client: AsyncClient, db_session):
    """Test that a device can have multiple active connections"""
    from app.models.device import Device
    from app.models.user import User
    from app.models.healthcheck import HealthCheck

    # Create device
    device = Device(
        device_id="multi-conn-device",
        device_type="laptop",
        certificate_serial="CERT-multi",
        certificate_pem="-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----",
        status="active"
    )
    db_session.add(device)

    # Create user
    user = User(
        user_id="multi@example.com",
        device_id="multi-conn-device",
        full_name="Multi User",
        email="multi@example.com",
        role="admin"
    )
    db_session.add(user)

    # Submit health check
    healthcheck = HealthCheck(
        device_id="multi-conn-device",
        status="healthy",
        cpu_usage=45.5,
        memory_usage=62.3,
        os_patches_current=True,
        antivirus_enabled=True,
        disk_encrypted=True
    )
    db_session.add(healthcheck)
    await db_session.commit()

    # Request multiple connections
    services = ["database", "api", "storage"]
    connection_ids = []

    with patch('app.services.opa_client.OPAClient.evaluate_policy') as mock_opa:
        mock_opa.return_value = {"allow": True}

        for service in services:
            response = await client.post(
                "/api/v1/connections/request",
                json={
                    "device_id": "multi-conn-device",
                    "user_id": "multi@example.com",
                    "service_name": service
                }
            )
            assert response.status_code == 200
            connection_ids.append(response.json()["connection_id"])

    # Verify all connections are listed
    list_response = await client.get(
        "/api/v1/connections?device_id=multi-conn-device&status=established"
    )
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["total"] == 3


@pytest.mark.asyncio
async def test_stale_health_check_prevents_authorization(client: AsyncClient, db_session):
    """Test that connections are denied if health check is too old"""
    from app.models.device import Device
    from app.models.user import User
    from app.models.healthcheck import HealthCheck
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import update

    # Create device
    device = Device(
        device_id="stale-device",
        device_type="laptop",
        certificate_serial="CERT-stale",
        certificate_pem="-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----",
        status="active"
    )
    db_session.add(device)

    # Create user
    user = User(
        user_id="stale@example.com",
        device_id="stale-device",
        full_name="Stale User",
        email="stale@example.com",
        role="developer"
    )
    db_session.add(user)

    # Create old health check
    healthcheck = HealthCheck(
        device_id="stale-device",
        status="healthy",
        cpu_usage=45.5,
        memory_usage=62.3,
        os_patches_current=True,
        antivirus_enabled=True,
        disk_encrypted=True
    )
    db_session.add(healthcheck)
    await db_session.commit()

    # Update health check to be 10 minutes old
    old_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    await db_session.execute(
        update(HealthCheck)
        .where(HealthCheck.device_id == "stale-device")
        .values(reported_at=old_time)
    )
    await db_session.commit()

    # Try to request connection
    response = await client.post(
        "/api/v1/connections/request",
        json={
            "device_id": "stale-device",
            "user_id": "stale@example.com",
            "service_name": "database"
        }
    )

    assert response.status_code == 503
    assert "health" in response.json()["detail"].lower()
    assert "stale" in response.json()["detail"].lower()
