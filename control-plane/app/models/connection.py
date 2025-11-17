"""Connection database model"""
from sqlalchemy import String, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional

from app.db.base import Base


class Connection(Base):
    """
    Connection model representing virtual tunnels

    Tracks authorized connections between devices/users and services.
    In production, this would represent actual WireGuard tunnels.
    For demo, it tracks virtual connection authorization.
    """

    __tablename__ = "connections"

    # Primary key (auto-increment)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Unique connection identifier
    connection_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # References
    device_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Service information
    service_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Connection status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="established"
    )

    # Timestamps
    established_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    terminated_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<Connection(id={self.connection_id}, device={self.device_id}, service={self.service_name}, status={self.status})>"
