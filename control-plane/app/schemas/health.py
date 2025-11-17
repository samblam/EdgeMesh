"""Health-related Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import Dict, Any


class HealthReportRequest(BaseModel):
    """
    Health report request schema

    Devices periodically send health metrics (CPU, memory, disk, etc.)
    to the control plane for monitoring.
    """
    device_id: str = Field(..., description="Device identifier sending the report")
    status: str = Field("healthy", description="Overall health status (healthy, degraded, unhealthy)")
    metrics: Dict[str, Any] = Field(..., description="Health metrics as JSON (CPU, memory, disk, etc.)")


class HealthReportResponse(BaseModel):
    """
    Health report response schema

    Confirms receipt of health report.
    """
    message: str = Field(..., description="Confirmation message")
    device_id: str = Field(..., description="Device identifier that sent the report")
