"""Connection request and management endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timezone, timedelta
import uuid

from app.schemas.connection import ConnectionRequest, ConnectionResponse
from app.models.device import Device
from app.models.user import User
from app.models.healthcheck import HealthCheck
from app.models.connection import Connection
from app.models.audit import AuditLog
from app.services.opa_client import OPAClient
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
    opa_client = OPAClient()
    policy_result = await opa_client.evaluate_policy(
        policy_path="edgemesh/authz/allow",
        input_data=opa_input
    )

    # Extract decision
    decision = "allow" if policy_result.get("allow", False) else "deny"

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
