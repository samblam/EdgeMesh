"""Tests for Connection Pydantic schemas"""
import pytest
from pydantic import ValidationError


def test_connection_request_schema():
    """Test ConnectionRequest schema validation"""
    from app.schemas.connection import ConnectionRequest

    request = ConnectionRequest(
        device_id="laptop-001",
        user_id="user@example.com",
        service_name="database"
    )

    assert request.device_id == "laptop-001"
    assert request.user_id == "user@example.com"
    assert request.service_name == "database"


def test_connection_request_requires_fields():
    """Test ConnectionRequest requires all fields"""
    from app.schemas.connection import ConnectionRequest

    with pytest.raises(ValidationError):
        ConnectionRequest(
            device_id="laptop-001"
            # Missing user_id and service_name
        )


def test_connection_response_schema():
    """Test ConnectionResponse schema"""
    from app.schemas.connection import ConnectionResponse
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    response = ConnectionResponse(
        connection_id="conn-123",
        status="authorized",
        service_name="database",
        virtual_tunnel={
            "endpoint": "virtual://database:8080",
            "established_at": now
        }
    )

    assert response.connection_id == "conn-123"
    assert response.status == "authorized"
    assert response.service_name == "database"
    assert response.virtual_tunnel["endpoint"] == "virtual://database:8080"


def test_connection_response_requires_fields():
    """Test ConnectionResponse requires all fields"""
    from app.schemas.connection import ConnectionResponse

    with pytest.raises(ValidationError):
        ConnectionResponse(
            connection_id="conn-123"
            # Missing status, service_name, virtual_tunnel
        )
