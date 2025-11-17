"""Health reporting endpoint"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.health import HealthReportRequest, HealthReportResponse
from app.models.healthcheck import HealthCheck
from app.services.metrics import MetricsService
from app.db.session import get_db

router = APIRouter()


@router.post("/health", response_model=HealthReportResponse)
async def report_health(
    request: HealthReportRequest,
    db: AsyncSession = Depends(get_db)
) -> HealthReportResponse:
    """
    Receive health report from device

    Stores device health metrics in the database for monitoring
    and policy decisions.

    Args:
        request: Health report with metrics
        db: Database session

    Returns:
        Confirmation response
    """
    # Create health check record
    health_check = HealthCheck(
        device_id=request.device_id,
        status=request.status,
        metrics=request.metrics
    )

    db.add(health_check)
    await db.commit()

    # Record health check metric
    MetricsService.record_health_check()

    return HealthReportResponse(
        message="Health report received",
        device_id=request.device_id
    )
