"""AuditLog database model"""
from sqlalchemy import String, Integer, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional, Dict, Any

from app.db.base import Base


class AuditLog(Base):
    """
    AuditLog model for tracking authorization decisions and events

    Provides comprehensive audit trail for compliance and security monitoring.
    All authorization decisions, enrollment events, and policy evaluations
    are logged here for forensic analysis and compliance reporting.
    """

    __tablename__ = "audit_logs"

    # Primary key (auto-increment)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Event information
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    decision: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # References (optional - not all events have all references)
    device_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    service_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Decision details
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    policy_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Additional context as JSON (using 'extra_data' instead of 'metadata' which is reserved)
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), index=True
    )

    def __repr__(self) -> str:
        return f"<AuditLog(event={self.event_type}, decision={self.decision}, device={self.device_id}, timestamp={self.timestamp})>"
