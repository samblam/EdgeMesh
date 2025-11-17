"""Tests for AuditLog database model"""
import pytest
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_create_audit_log(db_session):
    """Test creating an audit log entry"""
    from app.models.audit import AuditLog

    audit = AuditLog(
        event_type="authorization",
        device_id="device-001",
        user_id="user@example.com",
        service_name="database",
        action="connect",
        decision="allow",
        reason="Policy approved",
        policy_version="1.0"
    )

    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)

    assert audit.event_type == "authorization"
    assert audit.device_id == "device-001"
    assert audit.user_id == "user@example.com"
    assert audit.service_name == "database"
    assert audit.action == "connect"
    assert audit.decision == "allow"
    assert audit.reason == "Policy approved"
    assert audit.policy_version == "1.0"
    assert audit.timestamp is not None


@pytest.mark.asyncio
async def test_audit_log_timestamp_auto_populated(db_session):
    """Test timestamp is automatically set on creation"""
    from app.models.audit import AuditLog

    before = datetime.now(timezone.utc)

    audit = AuditLog(
        event_type="enrollment",
        device_id="device-002",
        action="enroll",
        decision="allow"
    )

    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)

    # timestamp should be set automatically and be recent
    assert audit.timestamp is not None
    time_diff = abs((datetime.now(timezone.utc) - audit.timestamp.replace(tzinfo=timezone.utc)).total_seconds())
    assert time_diff < 2, f"timestamp was set {time_diff} seconds ago, expected < 2 seconds"


@pytest.mark.asyncio
async def test_audit_log_optional_fields(db_session):
    """Test audit log works with optional fields"""
    from app.models.audit import AuditLog

    # Create with only required fields
    audit = AuditLog(
        event_type="health_check",
        action="report",
        decision="accept"
    )

    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)

    assert audit.event_type == "health_check"
    assert audit.action == "report"
    assert audit.decision == "accept"
    # Optional fields should be None
    assert audit.device_id is None
    assert audit.user_id is None
    assert audit.service_name is None
    assert audit.reason is None
    assert audit.policy_version is None
    assert audit.extra_data is None


@pytest.mark.asyncio
async def test_audit_log_with_metadata(db_session):
    """Test audit log can store JSON metadata"""
    from app.models.audit import AuditLog

    extra_data = {
        "device_health": {
            "cpu_usage": 45.5,
            "memory_usage": 62.3
        },
        "request_ip": "192.168.1.100",
        "user_agent": "EdgeMesh Client/1.0"
    }

    audit = AuditLog(
        event_type="authorization",
        device_id="device-003",
        action="connect",
        decision="deny",
        reason="Device unhealthy",
        extra_data=extra_data
    )

    db_session.add(audit)
    await db_session.commit()
    await db_session.refresh(audit)

    assert audit.extra_data == extra_data
    assert audit.extra_data["device_health"]["cpu_usage"] == 45.5
    assert audit.extra_data["request_ip"] == "192.168.1.100"


@pytest.mark.asyncio
async def test_audit_log_can_be_queried_by_device(db_session):
    """Test audit logs can be queried by device_id"""
    from app.models.audit import AuditLog
    from sqlalchemy import select

    # Create multiple audit entries for same device
    for i in range(3):
        audit = AuditLog(
            event_type="authorization",
            device_id="audit-device",
            action=f"action-{i}",
            decision="allow" if i < 2 else "deny"
        )
        db_session.add(audit)

    await db_session.commit()

    # Query all entries for device
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.device_id == "audit-device")
    )
    audits = result.scalars().all()

    assert len(audits) == 3
    assert all(a.device_id == "audit-device" for a in audits)


@pytest.mark.asyncio
async def test_audit_log_can_be_queried_by_decision(db_session):
    """Test audit logs can be queried by decision"""
    from app.models.audit import AuditLog
    from sqlalchemy import select

    # Create mix of allow/deny decisions
    for i in range(5):
        audit = AuditLog(
            event_type="authorization",
            action="connect",
            decision="allow" if i % 2 == 0 else "deny"
        )
        db_session.add(audit)

    await db_session.commit()

    # Query only denials
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.decision == "deny")
    )
    denials = result.scalars().all()

    assert len(denials) == 2
    assert all(a.decision == "deny" for a in denials)
