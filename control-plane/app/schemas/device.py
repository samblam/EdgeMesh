"""Device-related Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import Optional


class DeviceEnrollmentRequest(BaseModel):
    """
    Device enrollment request schema

    Devices provide their ID, type, and enrollment token to register
    with the control plane and receive certificates.
    """
    device_id: str = Field(..., description="Unique device identifier")
    device_type: str = Field(..., description="Type of device (laptop, server, iot, etc.)")
    enrollment_token: str = Field(..., description="Secret token for enrollment authorization")
    os: Optional[str] = Field(None, description="Operating system name")
    os_version: Optional[str] = Field(None, description="Operating system version")


class DeviceEnrollmentResponse(BaseModel):
    """
    Device enrollment response schema

    Returns the device certificate, private key, and CA certificate
    needed for mTLS authentication.
    """
    device_id: str = Field(..., description="Enrolled device identifier")
    certificate: str = Field(..., description="Device certificate (PEM format)")
    private_key: str = Field(..., description="Device private key (PEM format)")
    ca_certificate: str = Field(..., description="CA certificate for verification (PEM format)")
