"""User database model"""
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.db.base import Base


class User(Base):
    """
    User model representing a user in EdgeMesh

    Users are associated with devices and can request connections
    to services based on their authorization policies.
    """

    __tablename__ = "users"

    # Primary key
    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)

    # Associated device
    device_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # User information
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status and timestamps
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, device={self.device_id}, status={self.status})>"
