"""Device enrollment endpoint"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.schemas.device import DeviceEnrollmentRequest, DeviceEnrollmentResponse
from app.services.cert_service import CertificateService
from app.services.metrics import MetricsService
from app.models.device import Device
from app.db.session import get_db
from app.config import settings

router = APIRouter()


@router.post("/enroll", response_model=DeviceEnrollmentResponse)
async def enroll_device(
    request: DeviceEnrollmentRequest,
    db: AsyncSession = Depends(get_db)
) -> DeviceEnrollmentResponse:
    """
    Enroll a new device

    Validates the enrollment token, issues a certificate, and stores
    the device in the database.

    Args:
        request: Device enrollment request with token
        db: Database session

    Returns:
        Device enrollment response with certificates

    Raises:
        HTTPException 401: Invalid enrollment token
        HTTPException 409: Device already enrolled
    """
    # Validate enrollment token
    if request.enrollment_token != settings.ENROLLMENT_TOKEN_SECRET:
        raise HTTPException(status_code=401, detail="Invalid enrollment token")

    # Issue certificate
    cert_service = CertificateService()
    device_key, device_cert, ca_cert, serial = cert_service.issue_device_certificate(
        device_id=request.device_id,
        device_type=request.device_type
    )

    # Create device record
    device = Device(
        device_id=request.device_id,
        device_type=request.device_type,
        certificate_serial=serial,
        certificate_pem=device_cert.decode('utf-8'),
        os=request.os,
        os_version=request.os_version
    )

    try:
        db.add(device)
        await db.commit()
        # Record successful enrollment
        MetricsService.record_device_enrollment()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Device already enrolled")

    # Return certificates
    return DeviceEnrollmentResponse(
        device_id=request.device_id,
        certificate=device_cert.decode('utf-8'),
        private_key=device_key.decode('utf-8'),
        ca_certificate=ca_cert.decode('utf-8')
    )
