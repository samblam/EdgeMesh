"""Connection request and management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import uuid
import time

from app.schemas.connection import ConnectionRequest, ConnectionResponse
from app.models.device import Device
from app.models.user import User
from app.models.healthcheck import HealthCheck
from app.models.connection import Connection
from app.models.audit import AuditLog
from app.services.opa_client import OPAClient
from app.services.metrics import MetricsService
from app.db.session import get_db

router = APIRouter()


@router.post("/connections/request", response_model=ConnectionResponse)
async def request_connection(
    request: ConnectionRequest,
    db: AsyncSession = Depends(get_db)
) -> ConnectionResponse:
    """
    Request authorization for a connection to a service

    Validates device, user, and health status, then queries OPA for
    authorization decision. If authorized, creates a virtual tunnel.

    Args:
        request: Connection request with device, user, and service info
        db: Database session

    Returns:
        Connection response with authorization result

    Raises:
        HTTPException 404: Device or user not found
        HTTPException 403: Device not active or access denied
        HTTPException 503: Health check data is stale
    """
    # Verify device exists and is active
    result = await db.execute(
        select(Device).where(Device.device_id == request.device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if device.status != "active":
        raise HTTPException(
            status_code=403,
            detail="Device is not active"
        )

    # Verify user exists
    result = await db.execute(
        select(User).where(User.user_id == request.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get latest health check
    result = await db.execute(
        select(HealthCheck)
        .where(HealthCheck.device_id == request.device_id)
        .order_by(desc(HealthCheck.reported_at))
        .limit(1)
    )
    healthcheck = result.scalar_one_or_none()

    if not healthcheck:
        raise HTTPException(
            status_code=503,
            detail="No health check data available for device"
        )

    # Verify health check is recent (< 5 minutes)
    now = datetime.now(timezone.utc)
    health_age = now - healthcheck.reported_at.replace(tzinfo=timezone.utc)
    if health_age > timedelta(minutes=5):
        raise HTTPException(
            status_code=503,
            detail="Health check data is stale (older than 5 minutes)"
        )

    # Build OPA input document
    current_time = datetime.now(timezone.utc)
    opa_input = {
        "device": {
            "device_id": device.device_id,
            "authenticated": True,
            "status": device.status,
            "os_patches_current": healthcheck.os_patches_current or False,
            "antivirus_enabled": healthcheck.antivirus_enabled or False,
            "disk_encrypted": healthcheck.disk_encrypted or False,
            "cpu_usage": healthcheck.cpu_usage or 0.0,
            "memory_usage": healthcheck.memory_usage or 0.0
        },
        "user": {
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role
        },
        "service": {
            "name": request.service_name
        },
        "time": {
            "hour": current_time.hour,
            "day_of_week": current_time.isoweekday()  # 1=Monday, 7=Sunday
        }
    }

    # Query OPA for authorization decision
    start_time = time.time()
    opa_client = OPAClient()
    policy_result = await opa_client.evaluate_policy(input_data=opa_input)
    latency = time.time() - start_time

    # Extract decision (support both old and new format for backward compatibility)
    # New format: {"allowed": True, "decision": "allow"}
    # Old format: {"allow": True} (used by some test mocks)
    allowed = policy_result.get("allowed", policy_result.get("allow", False))
    decision = policy_result.get("decision", "allow" if allowed else "deny")

    # Record authorization decision metrics
    MetricsService.record_authorization_decision(allowed=allowed, latency=latency)

    # Log decision to audit log
    audit = AuditLog(
        event_type="connection_request",
        action="request_connection",
        device_id=request.device_id,
        user_id=request.user_id,
        service_name=request.service_name,
        decision=decision,
        policy_version="v1.0",
        extra_data={"opa_result": policy_result}
    )
    db.add(audit)
    await db.commit()

    # If denied, return 403
    if decision == "deny":
        # Record denied connection request
        MetricsService.record_connection_request(service=request.service_name, authorized=False)
        raise HTTPException(
            status_code=403,
            detail="Access denied by policy"
        )

    # If authorized, create connection record
    connection_id = str(uuid.uuid4())
    connection = Connection(
        connection_id=connection_id,
        device_id=request.device_id,
        user_id=request.user_id,
        service_name=request.service_name,
        status="established"
    )
    db.add(connection)
    await db.commit()

    # Record authorized connection request
    MetricsService.record_connection_request(service=request.service_name, authorized=True)

    # Return success response with virtual tunnel details
    return ConnectionResponse(
        connection_id=connection_id,
        status="authorized",
        service_name=request.service_name,
        virtual_tunnel={
            "type": "wireguard",
            "endpoint": f"wg://{request.service_name}.edgemesh.local",
            "public_key": "mock-public-key",
            "allowed_ips": ["10.0.0.0/8"]
        }
    )

@router.get("/connections/{connection_id}")
async def get_connection(
    connection_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get connection details

    Retrieves information about a specific connection.

    Args:
        connection_id: Connection identifier
        db: Database session

    Returns:
        Connection details

    Raises:
        HTTPException 404: Connection not found
    """
    result = await db.execute(
        select(Connection).where(Connection.connection_id == connection_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    return {
        "connection_id": connection.connection_id,
        "device_id": connection.device_id,
        "user_id": connection.user_id,
        "service_name": connection.service_name,
        "status": connection.status,
        "established_at": connection.established_at.isoformat(),
        "terminated_at": connection.terminated_at.isoformat() if connection.terminated_at else None
    }


@router.delete("/connections/{connection_id}")
async def terminate_connection(
    connection_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Terminate a connection

    Marks a connection as terminated and records the termination time.

    Args:
        connection_id: Connection identifier
        db: Database session

    Returns:
        Termination confirmation

    Raises:
        HTTPException 404: Connection not found
        HTTPException 400: Connection already terminated
    """
    result = await db.execute(
        select(Connection).where(Connection.connection_id == connection_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    if connection.status == "terminated":
        raise HTTPException(
            status_code=400,
            detail="Connection already terminated"
        )

    # Update connection status
    connection.status = "terminated"
    connection.terminated_at = datetime.now(timezone.utc)
    await db.commit()

    # Record connection termination
    MetricsService.record_connection_terminated(service=connection.service_name)

    return {
        "message": "Connection terminated",
        "connection_id": connection_id
    }


@router.get("/connections")
async def list_connections(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    List connections

    Retrieves a list of connections, optionally filtered by device, user, or status.

    Args:
        device_id: Optional device ID filter
        user_id: Optional user ID filter
        status: Optional status filter
        db: Database session

    Returns:
        List of connections
    """
    query = select(Connection)

    if device_id:
        query = query.where(Connection.device_id == device_id)
    if user_id:
        query = query.where(Connection.user_id == user_id)
    if status:
        query = query.where(Connection.status == status)

    query = query.order_by(desc(Connection.established_at))

    result = await db.execute(query)
    connections = result.scalars().all()

    return {
        "connections": [
            {
                "connection_id": conn.connection_id,
                "device_id": conn.device_id,
                "user_id": conn.user_id,
                "service_name": conn.service_name,
                "status": conn.status,
                "established_at": conn.established_at.isoformat(),
                "terminated_at": conn.terminated_at.isoformat() if conn.terminated_at else None
            }
            for conn in connections
        ],
        "total": len(connections)
    }
