"""HealthCheck database model"""
from sqlalchemy import String, Integer, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Dict, Any

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

    # Metrics as JSON (CPU, memory, disk, etc.)
    metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Timestamp
    reported_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), index=True
    )

    def __repr__(self) -> str:
        return f"<HealthCheck(device={self.device_id}, status={self.status}, reported_at={self.reported_at})>"
