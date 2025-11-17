"""Tests for connection management endpoints (GET, DELETE)"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_connection_endpoint_exists(client: AsyncClient):
    """Test GET /api/v1/connections/{id} endpoint exists"""
    response = await client.get("/api/v1/connections/test-conn-id")
    # Should not return 404 for missing route (might be 404 for missing connection)
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_get_connection_success(client: AsyncClient, db_session):
    """Test retrieving existing connection"""
    from app.models.connection import Connection
    from app.models.device import Device
    from app.models.user import User

    # Create test data
    device = Device(
        device_id="device-get",
        device_type="laptop",
        certificate_serial="CERT-get",
        certificate_pem="-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----",
        status="active"
    )
    db_session.add(device)

    user = User(
        user_id="get@example.com",
        device_id="device-get",
        full_name="Get User",
        email="get@example.com",
        role="developer"
    )
    db_session.add(user)

    # Create connection
    connection = Connection(
        connection_id="conn-123",
        device_id="device-get",
        user_id="get@example.com",
        service_name="database",
        status="established"
    )
    db_session.add(connection)
    await db_session.commit()

    # Retrieve connection
    response = await client.get("/api/v1/connections/conn-123")

    assert response.status_code == 200
    data = response.json()
    assert data["connection_id"] == "conn-123"
    assert data["device_id"] == "device-get"
    assert data["user_id"] == "get@example.com"
    assert data["service_name"] == "database"
    assert data["status"] == "established"
    assert "established_at" in data


@pytest.mark.asyncio
async def test_get_connection_not_found(client: AsyncClient, db_session):
    """Test retrieving non-existent connection returns 404"""
    response = await client.get("/api/v1/connections/nonexistent")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_delete_connection_endpoint_exists(client: AsyncClient):
    """Test DELETE /api/v1/connections/{id} endpoint exists"""
    response = await client.delete("/api/v1/connections/test-conn-id")
    # Should not return 405 (method not allowed)
    assert response.status_code != 405


@pytest.mark.asyncio
async def test_delete_connection_success(client: AsyncClient, db_session):
    """Test terminating an existing connection"""
    from app.models.connection import Connection
    from app.models.device import Device
    from app.models.user import User
    from sqlalchemy import select

    # Create test data
    device = Device(
        device_id="device-del",
        device_type="laptop",
        certificate_serial="CERT-del",
        certificate_pem="-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----",
        status="active"
    )
    db_session.add(device)

    user = User(
        user_id="del@example.com",
        device_id="device-del",
        full_name="Delete User",
        email="del@example.com",
        role="developer"
    )
    db_session.add(user)

    # Create connection
    connection = Connection(
        connection_id="conn-del-123",
        device_id="device-del",
        user_id="del@example.com",
        service_name="database",
        status="established"
    )
    db_session.add(connection)
    await db_session.commit()

    # Delete connection
    response = await client.delete("/api/v1/connections/conn-del-123")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Connection terminated"
    assert data["connection_id"] == "conn-del-123"

    # Verify connection status updated to terminated
    result = await db_session.execute(
        select(Connection).where(Connection.connection_id == "conn-del-123")
    )
    conn = result.scalar_one_or_none()
    assert conn is not None
    assert conn.status == "terminated"
    assert conn.terminated_at is not None


@pytest.mark.asyncio
async def test_delete_connection_not_found(client: AsyncClient, db_session):
    """Test deleting non-existent connection returns 404"""
    response = await client.delete("/api/v1/connections/nonexistent")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_delete_already_terminated_connection(client: AsyncClient, db_session):
    """Test deleting already terminated connection returns 400"""
    from app.models.connection import Connection
    from app.models.device import Device
    from app.models.user import User
    from datetime import datetime, timezone

    # Create test data
    device = Device(
        device_id="device-term",
        device_type="laptop",
        certificate_serial="CERT-term",
        certificate_pem="-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----",
        status="active"
    )
    db_session.add(device)

    user = User(
        user_id="term@example.com",
        device_id="device-term",
        full_name="Term User",
        email="term@example.com",
        role="developer"
    )
    db_session.add(user)

    # Create already terminated connection
    connection = Connection(
        connection_id="conn-term-123",
        device_id="device-term",
        user_id="term@example.com",
        service_name="database",
        status="terminated",
        terminated_at=datetime.now(timezone.utc)
    )
    db_session.add(connection)
    await db_session.commit()

    # Try to delete already terminated connection
    response = await client.delete("/api/v1/connections/conn-term-123")

    assert response.status_code == 400
    data = response.json()
    assert "already terminated" in data["detail"].lower()


@pytest.mark.asyncio
async def test_list_connections_for_device(client: AsyncClient, db_session):
    """Test listing all connections for a device"""
    from app.models.connection import Connection
    from app.models.device import Device
    from app.models.user import User

    # Create test data
    device = Device(
        device_id="device-list",
        device_type="laptop",
        certificate_serial="CERT-list",
        certificate_pem="-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----",
        status="active"
    )
    db_session.add(device)

    user = User(
        user_id="list@example.com",
        device_id="device-list",
        full_name="List User",
        email="list@example.com",
        role="developer"
    )
    db_session.add(user)

    # Create multiple connections
    conn1 = Connection(
        connection_id="conn-list-1",
        device_id="device-list",
        user_id="list@example.com",
        service_name="database",
        status="established"
    )
    conn2 = Connection(
        connection_id="conn-list-2",
        device_id="device-list",
        user_id="list@example.com",
        service_name="api",
        status="established"
    )
    db_session.add(conn1)
    db_session.add(conn2)
    await db_session.commit()

    # List connections
    response = await client.get("/api/v1/connections?device_id=device-list")

    assert response.status_code == 200
    data = response.json()
    assert len(data["connections"]) == 2
    assert data["total"] == 2
