"""Device database model"""
from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional

from app.db.base import Base


class Device(Base):
    """
    Device model representing an enrolled device in EdgeMesh

    A device must enroll to receive a certificate and be able to
    request connections to services.
    """

    __tablename__ = "devices"

    # Primary key
    device_id: Mapped[str] = mapped_column(String(255), primary_key=True)

    # Device information
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Certificate information
    certificate_serial: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    certificate_pem: Mapped[str] = mapped_column(Text, nullable=False)

    # System information (optional)
    os: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    os_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Status and timestamps
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="active"
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    last_seen: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<Device(device_id={self.device_id}, type={self.device_type}, status={self.status})>"
