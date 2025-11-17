"""Connection-related Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import Any, Dict


class ConnectionRequest(BaseModel):
    """
    Connection request schema

    Devices/users request authorization to connect to a service.
    """
    device_id: str = Field(..., description="Device requesting connection")
    user_id: str = Field(..., description="User requesting connection")
    service_name: str = Field(..., description="Target service name")


class ConnectionResponse(BaseModel):
    """
    Connection response schema

    Returns connection authorization result with virtual tunnel details.
    """
    connection_id: str = Field(..., description="Unique connection identifier")
    status: str = Field(..., description="Connection status (authorized, denied)")
    service_name: str = Field(..., description="Service name")
    virtual_tunnel: Dict[str, Any] = Field(..., description="Virtual tunnel configuration")
