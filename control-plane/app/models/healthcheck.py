"""HealthCheck database model"""
from sqlalchemy import String, Integer, JSON, Float, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Dict, Any, Optional

from app.db.base import Base


class HealthCheck(Base):
    """
    HealthCheck model representing device health reports

    Devices periodically report their health status (CPU, memory, disk, etc.)
    which is stored for monitoring and policy decisions.
    """

    __tablename__ = "healthchecks"

    # Primary key (auto-increment)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Device reference
    device_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Health status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="healthy"
    )

    # Resource usage metrics (for OPA policy evaluation)
    cpu_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    disk_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Compliance fields (for OPA policy evaluation)
    os_patches_current: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    antivirus_enabled: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    disk_encrypted: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Additional metrics as JSON (backward compatible, now optional)
    metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Timestamp
    reported_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), index=True
    )

    def __repr__(self) -> str:
        return f"<HealthCheck(device={self.device_id}, status={self.status}, reported_at={self.reported_at})>"
