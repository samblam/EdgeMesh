"""
Tests for connection retrieval, termination, and listing endpoints
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import uuid

from app.models.connection import Connection
from app.models.device import Device
from app.models.user import User


@pytest.mark.asyncio
async def test_get_connection_success(client: AsyncClient, db_session: AsyncSession):
    """Test retrieving connection details by ID"""
    # Create device and user
    device = Device(
        device_id="test-device-001",
        device_type="laptop",
        certificate_serial="123456",
        certificate_pem="fake-cert",
        os="Ubuntu",
        os_version="22.04",
        status="active"
    )
    db_session.add(device)

    user = User(
        user_id="test-user-001",
        device_id="test-device-001",
        full_name="Test User",
        email="test@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)

    # Create connection
    connection_id = str(uuid.uuid4())
    connection = Connection(
        connection_id=connection_id,
        device_id="test-device-001",
        user_id="test-user-001",
        service_name="database",
        status="established"
    )
    db_session.add(connection)
    await db_session.commit()

    # Get connection
    response = await client.get(f"/api/v1/connections/{connection_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["connection_id"] == connection_id
    assert data["device_id"] == "test-device-001"
    assert data["user_id"] == "test-user-001"
    assert data["service_name"] == "database"
    assert data["status"] == "established"
    assert "established_at" in data
    assert data["terminated_at"] is None


@pytest.mark.asyncio
async def test_get_connection_not_found(client: AsyncClient):
    """Test retrieving non-existent connection returns 404"""
    fake_id = str(uuid.uuid4())
    response = await client.get(f"/api/v1/connections/{fake_id}")

    assert response.status_code == 404
    assert "Connection not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_terminated_connection(client: AsyncClient, db_session: AsyncSession):
    """Test retrieving terminated connection shows termination time"""
    # Create device and user
    device = Device(
        device_id="test-device-002",
        device_type="laptop",
        certificate_serial="123457",
        certificate_pem="fake-cert",
        os="Ubuntu",
        os_version="22.04",
        status="active"
    )
    db_session.add(device)

    user = User(
        user_id="test-user-002",
        device_id="test-device-002",
        full_name="Test User",
        email="test2@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)

    # Create terminated connection
    connection_id = str(uuid.uuid4())
    connection = Connection(
        connection_id=connection_id,
        device_id="test-device-002",
        user_id="test-user-002",
        service_name="api",
        status="terminated",
        terminated_at=datetime.now(timezone.utc)
    )
    db_session.add(connection)
    await db_session.commit()

    # Get connection
    response = await client.get(f"/api/v1/connections/{connection_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "terminated"
    assert data["terminated_at"] is not None


@pytest.mark.asyncio
async def test_terminate_connection_success(client: AsyncClient, db_session: AsyncSession):
    """Test successfully terminating an active connection"""
    # Create device and user
    device = Device(
        device_id="test-device-003",
        device_type="laptop",
        certificate_serial="123458",
        certificate_pem="fake-cert",
        os="Ubuntu",
        os_version="22.04",
        status="active"
    )
    db_session.add(device)

    user = User(
        user_id="test-user-003",
        device_id="test-device-003",
        full_name="Test User",
        email="test3@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)

    # Create active connection
    connection_id = str(uuid.uuid4())
    connection = Connection(
        connection_id=connection_id,
        device_id="test-device-003",
        user_id="test-user-003",
        service_name="cache",
        status="established"
    )
    db_session.add(connection)
    await db_session.commit()

    # Terminate connection
    response = await client.delete(f"/api/v1/connections/{connection_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Connection terminated"
    assert data["connection_id"] == connection_id

    # Verify connection is terminated in database
    await db_session.refresh(connection)
    assert connection.status == "terminated"
    assert connection.terminated_at is not None


@pytest.mark.asyncio
async def test_terminate_connection_not_found(client: AsyncClient):
    """Test terminating non-existent connection returns 404"""
    fake_id = str(uuid.uuid4())
    response = await client.delete(f"/api/v1/connections/{fake_id}")

    assert response.status_code == 404
    assert "Connection not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_terminate_already_terminated_connection(client: AsyncClient, db_session: AsyncSession):
    """Test terminating already terminated connection returns 400"""
    # Create device and user
    device = Device(
        device_id="test-device-004",
        device_type="laptop",
        certificate_serial="123459",
        certificate_pem="fake-cert",
        os="Ubuntu",
        os_version="22.04",
        status="active"
    )
    db_session.add(device)

    user = User(
        user_id="test-user-004",
        device_id="test-device-004",
        full_name="Test User",
        email="test4@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)

    # Create already terminated connection
    connection_id = str(uuid.uuid4())
    connection = Connection(
        connection_id=connection_id,
        device_id="test-device-004",
        user_id="test-user-004",
        service_name="database",
        status="terminated",
        terminated_at=datetime.now(timezone.utc)
    )
    db_session.add(connection)
    await db_session.commit()

    # Try to terminate again
    response = await client.delete(f"/api/v1/connections/{connection_id}")

    assert response.status_code == 400
    assert "already terminated" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_connections_no_filters(client: AsyncClient, db_session: AsyncSession):
    """Test listing all connections without filters"""
    # Create devices and users
    for i in range(3):
        device = Device(
            device_id=f"list-device-{i}",
            device_type="laptop",
            certificate_serial=f"12345{i}",
            certificate_pem="fake-cert",
            os="Ubuntu",
            os_version="22.04",
            status="active"
        )
        db_session.add(device)

        user = User(
            user_id=f"list-user-{i}",
            device_id=f"list-device-{i}",
            full_name=f"User {i}",
            email=f"user{i}@example.com",
            role="developer",
            status="active"
        )
        db_session.add(user)

        connection = Connection(
            connection_id=str(uuid.uuid4()),
            device_id=f"list-device-{i}",
            user_id=f"list-user-{i}",
            service_name="database",
            status="established"
        )
        db_session.add(connection)

    await db_session.commit()

    # List all connections
    response = await client.get("/api/v1/connections")

    assert response.status_code == 200
    data = response.json()
    assert "connections" in data
    assert data["total"] >= 3
    assert len(data["connections"]) >= 3


@pytest.mark.asyncio
async def test_list_connections_filter_by_device(client: AsyncClient, db_session: AsyncSession):
    """Test listing connections filtered by device ID"""
    # Create device and user
    device = Device(
        device_id="filter-device-001",
        device_type="laptop",
        certificate_serial="999001",
        certificate_pem="fake-cert",
        os="Ubuntu",
        os_version="22.04",
        status="active"
    )
    db_session.add(device)

    user = User(
        user_id="filter-user-001",
        device_id="filter-device-001",
        full_name="Filter User",
        email="filter@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)

    # Create connections for this device
    for i in range(2):
        connection = Connection(
            connection_id=str(uuid.uuid4()),
            device_id="filter-device-001",
            user_id="filter-user-001",
            service_name=f"service-{i}",
            status="established"
        )
        db_session.add(connection)

    await db_session.commit()

    # Filter by device
    response = await client.get("/api/v1/connections?device_id=filter-device-001")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    for conn in data["connections"]:
        assert conn["device_id"] == "filter-device-001"


@pytest.mark.asyncio
async def test_list_connections_filter_by_user(client: AsyncClient, db_session: AsyncSession):
    """Test listing connections filtered by user ID"""
    # Create device and user
    device = Device(
        device_id="filter-device-002",
        device_type="laptop",
        certificate_serial="999002",
        certificate_pem="fake-cert",
        os="Ubuntu",
        os_version="22.04",
        status="active"
    )
    db_session.add(device)

    user = User(
        user_id="filter-user-002",
        device_id="filter-device-002",
        full_name="Filter User",
        email="filter2@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)

    # Create connections
    for i in range(3):
        connection = Connection(
            connection_id=str(uuid.uuid4()),
            device_id="filter-device-002",
            user_id="filter-user-002",
            service_name=f"service-{i}",
            status="established"
        )
        db_session.add(connection)

    await db_session.commit()

    # Filter by user
    response = await client.get("/api/v1/connections?user_id=filter-user-002")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    for conn in data["connections"]:
        assert conn["user_id"] == "filter-user-002"


@pytest.mark.asyncio
async def test_list_connections_filter_by_status(client: AsyncClient, db_session: AsyncSession):
    """Test listing connections filtered by status"""
    # Create device and user
    device = Device(
        device_id="filter-device-003",
        device_type="laptop",
        certificate_serial="999003",
        certificate_pem="fake-cert",
        os="Ubuntu",
        os_version="22.04",
        status="active"
    )
    db_session.add(device)

    user = User(
        user_id="filter-user-003",
        device_id="filter-device-003",
        full_name="Filter User",
        email="filter3@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)

    # Create established and terminated connections
    for i in range(2):
        connection = Connection(
            connection_id=str(uuid.uuid4()),
            device_id="filter-device-003",
            user_id="filter-user-003",
            service_name=f"service-{i}",
            status="established"
        )
        db_session.add(connection)

    terminated_conn = Connection(
        connection_id=str(uuid.uuid4()),
        device_id="filter-device-003",
        user_id="filter-user-003",
        service_name="terminated-service",
        status="terminated",
        terminated_at=datetime.now(timezone.utc)
    )
    db_session.add(terminated_conn)

    await db_session.commit()

    # Filter by established status
    response = await client.get("/api/v1/connections?status=established")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    for conn in data["connections"]:
        assert conn["status"] == "established"


@pytest.mark.asyncio
async def test_list_connections_multiple_filters(client: AsyncClient, db_session: AsyncSession):
    """Test listing connections with multiple filters combined"""
    # Create device and user
    device = Device(
        device_id="multi-filter-device",
        device_type="laptop",
        certificate_serial="999999",
        certificate_pem="fake-cert",
        os="Ubuntu",
        os_version="22.04",
        status="active"
    )
    db_session.add(device)

    user = User(
        user_id="multi-filter-user",
        device_id="multi-filter-device",
        full_name="Multi Filter User",
        email="multi@example.com",
        role="developer",
        status="active"
    )
    db_session.add(user)

    # Create connections
    connection = Connection(
        connection_id=str(uuid.uuid4()),
        device_id="multi-filter-device",
        user_id="multi-filter-user",
        service_name="database",
        status="established"
    )
    db_session.add(connection)

    await db_session.commit()

    # Filter by device, user, and status
    response = await client.get(
        "/api/v1/connections"
        "?device_id=multi-filter-device"
        "&user_id=multi-filter-user"
        "&status=established"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    conn = data["connections"][0]
    assert conn["device_id"] == "multi-filter-device"
    assert conn["user_id"] == "multi-filter-user"
    assert conn["status"] == "established"


@pytest.mark.asyncio
async def test_list_connections_empty_result(client: AsyncClient):
    """Test listing connections with filters that match nothing"""
    response = await client.get("/api/v1/connections?device_id=nonexistent-device")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["connections"] == []
