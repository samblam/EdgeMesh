"""
End-to-end integration tests for complete workflows
"""
import pytest
from datetime import datetime, timezone
from app.models.healthcheck import HealthCheck


@pytest.mark.asyncio
async def test_complete_enrollment_to_connection_flow(client, db_session):
    """Test full flow: enroll → health check → request connection"""

    # 1. Enroll device
    enroll_response = await client.post(
        "/api/v1/enroll",
        json={
            "device_id": "e2e-device-001",
            "device_type": "laptop",
            "os": "Ubuntu",
            "os_version": "22.04",
            "enrollment_token": "change-me-in-production"
        }
    )

    assert enroll_response.status_code == 200
    enroll_data = enroll_response.json()
    assert "certificate" in enroll_data
    assert "private_key" in enroll_data
    assert "ca_certificate" in enroll_data
    assert enroll_data["device_id"] == "e2e-device-001"

    # 2. Report health (healthy device)
    health_response = await client.post(
        "/api/v1/health",
        json={
            "device_id": "e2e-device-001",
            "status": "healthy",
            "metrics": {
                "cpu_usage": 45.0,
                "memory_usage": 60.0,
                "disk_usage": 70.0,
                "os_patches_current": True,
                "antivirus_enabled": True,
                "disk_encrypted": True
            }
        }
    )

    assert health_response.status_code == 200
    health_data = health_response.json()
    assert health_data["message"] == "Health report received"
    assert health_data["device_id"] == "e2e-device-001"

    # 3. Create test user
    from app.models.user import User
    user = User(
        user_id="e2e-user-001",
        device_id="e2e-device-001",
        full_name="Test User",
        email="e2e@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)
    await db_session.commit()

    # 4. Request connection (should be authorized)
    conn_response = await client.post(
        "/api/v1/connections/request",
        json={
            "device_id": "e2e-device-001",
            "user_id": "e2e-user-001",
            "service_name": "api"
        }
    )

    assert conn_response.status_code == 200
    conn_data = conn_response.json()
    assert conn_data["status"] == "authorized"
    assert "connection_id" in conn_data
    assert conn_data["service_name"] == "api"
    assert "virtual_tunnel" in conn_data

    # 5. Verify connection was recorded
    connection_id = conn_data["connection_id"]
    get_response = await client.get(f"/api/v1/connections/{connection_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["device_id"] == "e2e-device-001"
    assert get_data["user_id"] == "e2e-user-001"
    assert get_data["service_name"] == "api"
    assert get_data["status"] == "established"

    # 6. Terminate connection
    delete_response = await client.delete(f"/api/v1/connections/{connection_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Connection terminated"

    # 7. Verify connection is terminated
    verify_response = await client.get(f"/api/v1/connections/{connection_id}")
    assert verify_response.status_code == 200
    verify_data = verify_response.json()
    assert verify_data["status"] == "terminated"
    assert verify_data["terminated_at"] is not None


@pytest.mark.asyncio
async def test_unhealthy_device_denied_access(client, db_session):
    """Test that unhealthy devices are denied access"""

    # 1. Enroll device
    enroll_response = await client.post(
        "/api/v1/enroll",
        json={
            "device_id": "unhealthy-device-001",
            "device_type": "laptop",
            "os": "Ubuntu",
            "os_version": "22.04",
            "enrollment_token": "change-me-in-production"
        }
    )
    assert enroll_response.status_code == 200

    # 2. Report unhealthy status (missing patches)
    health_response = await client.post(
        "/api/v1/health",
        json={
            "device_id": "unhealthy-device-001",
            "status": "healthy",
            "metrics": {
                "cpu_usage": 45.0,
                "memory_usage": 60.0,
                "disk_usage": 70.0,
                "os_patches_current": False,  # Not patched!
                "antivirus_enabled": True,
                "disk_encrypted": True
            }
        }
    )
    assert health_response.status_code == 200

    # 3. Create test user
    from app.models.user import User
    user = User(
        user_id="unhealthy-user-001",
        device_id="unhealthy-device-001",
        full_name="Test User",
        email="unhealthy@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)
    await db_session.commit()

    # 4. Request connection (should be denied)
    conn_response = await client.post(
        "/api/v1/connections/request",
        json={
            "device_id": "unhealthy-device-001",
            "user_id": "unhealthy-user-001",
            "service_name": "database"
        }
    )

    # Should be denied by OPA policy
    assert conn_response.status_code == 403
    assert "Access denied by policy" in conn_response.json()["detail"]


@pytest.mark.asyncio
async def test_stale_health_check_denied(client, db_session):
    """Test that devices with stale health checks are denied"""

    # 1. Enroll device
    enroll_response = await client.post(
        "/api/v1/enroll",
        json={
            "device_id": "stale-device-001",
            "device_type": "laptop",
            "os": "Ubuntu",
            "os_version": "22.04",
            "enrollment_token": "change-me-in-production"
        }
    )
    assert enroll_response.status_code == 200

    # 2. Create a stale health check (6 minutes old)
    from datetime import timedelta
    stale_time = datetime.now(timezone.utc) - timedelta(minutes=6)

    health_check = HealthCheck(
        device_id="stale-device-001",
        status="healthy",
        metrics={
            "cpu_usage": 45.0,
            "memory_usage": 60.0,
            "os_patches_current": True,
            "antivirus_enabled": True,
            "disk_encrypted": True
        },
        reported_at=stale_time
    )
    db_session.add(health_check)
    await db_session.commit()

    # 3. Create test user
    from app.models.user import User
    user = User(
        user_id="stale-user-001",
        device_id="stale-device-001",
        full_name="Test User",
        email="stale@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)
    await db_session.commit()

    # 4. Request connection (should be denied due to stale health check)
    conn_response = await client.post(
        "/api/v1/connections/request",
        json={
            "device_id": "stale-device-001",
            "user_id": "stale-user-001",
            "service_name": "api"
        }
    )

    # Should be denied with 503 status
    assert conn_response.status_code == 503
    assert "stale" in conn_response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_multiple_concurrent_connections(client, db_session):
    """Test multiple simultaneous connections for same device"""

    # 1. Enroll device
    enroll_response = await client.post(
        "/api/v1/enroll",
        json={
            "device_id": "multi-conn-device-001",
            "device_type": "laptop",
            "os": "Ubuntu",
            "os_version": "22.04",
            "enrollment_token": "change-me-in-production"
        }
    )
    assert enroll_response.status_code == 200

    # 2. Report health
    await client.post(
        "/api/v1/health",
        json={
            "device_id": "multi-conn-device-001",
            "status": "healthy",
            "metrics": {
                "cpu_usage": 45.0,
                "memory_usage": 60.0,
                "os_patches_current": True,
                "antivirus_enabled": True,
                "disk_encrypted": True
            }
        }
    )

    # 3. Create test user
    from app.models.user import User
    user = User(
        user_id="multi-conn-user-001",
        device_id="multi-conn-device-001",
        full_name="Test User",
        email="multiconn@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)
    await db_session.commit()

    # 4. Request multiple connections to different services
    services = ["database", "api", "storage"]
    connection_ids = []

    for service in services:
        conn_response = await client.post(
            "/api/v1/connections/request",
            json={
                "device_id": "multi-conn-device-001",
                "user_id": "multi-conn-user-001",
                "service_name": service
            }
        )
        assert conn_response.status_code == 200
        connection_ids.append(conn_response.json()["connection_id"])

    # 5. Verify all connections are active
    list_response = await client.get(
        "/api/v1/connections",
        params={"device_id": "multi-conn-device-001", "status": "established"}
    )
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 3

    # 6. Terminate all connections
    for conn_id in connection_ids:
        delete_response = await client.delete(f"/api/v1/connections/{conn_id}")
        assert delete_response.status_code == 200


@pytest.mark.asyncio
async def test_admin_user_access_outside_business_hours(client, db_session):
    """Test that admin users can access outside business hours"""

    # 1. Enroll device
    enroll_response = await client.post(
        "/api/v1/enroll",
        json={
            "device_id": "admin-device-001",
            "device_type": "laptop",
            "os": "Ubuntu",
            "os_version": "22.04",
            "enrollment_token": "change-me-in-production"
        }
    )
    assert enroll_response.status_code == 200

    # 2. Report health
    await client.post(
        "/api/v1/health",
        json={
            "device_id": "admin-device-001",
            "status": "healthy",
            "metrics": {
                "cpu_usage": 45.0,
                "memory_usage": 60.0,
                "os_patches_current": True,
                "antivirus_enabled": True,
                "disk_encrypted": True
            }
        }
    )

    # 3. Create admin user
    from app.models.user import User
    admin = User(
        user_id="admin-device-user-001",
        device_id="admin-device-device-001",
        full_name="Test User",
        email="admin-device@example.com",
        role="admin",
        status="active"
    )
    db_session.add(admin)
    await db_session.commit()

    # 4. Request connection (admin should always be allowed)
    conn_response = await client.post(
        "/api/v1/connections/request",
        json={
            "device_id": "admin-device-001",
            "user_id": "admin-device-user-001",
            "service_name": "database"
        }
    )

    # Admin should be authorized regardless of time
    assert conn_response.status_code == 200
    assert conn_response.json()["status"] == "authorized"


@pytest.mark.asyncio
async def test_duplicate_device_enrollment_rejected(client):
    """Test that duplicate device enrollment is rejected"""

    # 1. Enroll device first time
    first_response = await client.post(
        "/api/v1/enroll",
        json={
            "device_id": "duplicate-device-001",
            "device_type": "laptop",
            "os": "Ubuntu",
            "os_version": "22.04",
            "enrollment_token": "change-me-in-production"
        }
    )
    assert first_response.status_code == 200

    # 2. Try to enroll same device again
    second_response = await client.post(
        "/api/v1/enroll",
        json={
            "device_id": "duplicate-device-001",
            "device_type": "laptop",
            "os": "Ubuntu",
            "os_version": "22.04",
            "enrollment_token": "change-me-in-production"
        }
    )

    # Should be rejected with 409 Conflict
    assert second_response.status_code == 409
    assert "already enrolled" in second_response.json()["detail"].lower()
