"""Tests for Pydantic schemas"""
import pytest
from pydantic import ValidationError


def test_device_enrollment_request_schema():
    """Test DeviceEnrollmentRequest schema validation"""
    from app.schemas.device import DeviceEnrollmentRequest

    # Valid request
    request = DeviceEnrollmentRequest(
        device_id="laptop-001",
        device_type="laptop",
        enrollment_token="secret-token-123",
        os="Ubuntu",
        os_version="22.04"
    )

    assert request.device_id == "laptop-001"
    assert request.device_type == "laptop"
    assert request.enrollment_token == "secret-token-123"
    assert request.os == "Ubuntu"
    assert request.os_version == "22.04"


def test_device_enrollment_request_requires_fields():
    """Test DeviceEnrollmentRequest requires device_id, device_type, enrollment_token"""
    from app.schemas.device import DeviceEnrollmentRequest

    # Missing required fields should raise ValidationError
    with pytest.raises(ValidationError):
        DeviceEnrollmentRequest(
            device_id="laptop-001"
            # Missing device_type and enrollment_token
        )


def test_device_enrollment_request_optional_os_fields():
    """Test DeviceEnrollmentRequest allows optional os and os_version"""
    from app.schemas.device import DeviceEnrollmentRequest

    # Should work without os fields
    request = DeviceEnrollmentRequest(
        device_id="iot-001",
        device_type="iot",
        enrollment_token="token-456"
    )

    assert request.device_id == "iot-001"
    assert request.os is None
    assert request.os_version is None


def test_device_enrollment_response_schema():
    """Test DeviceEnrollmentResponse schema"""
    from app.schemas.device import DeviceEnrollmentResponse

    response = DeviceEnrollmentResponse(
        device_id="laptop-001",
        certificate="-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----",
        private_key="-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
        ca_certificate="-----BEGIN CERTIFICATE-----\nca\n-----END CERTIFICATE-----"
    )

    assert response.device_id == "laptop-001"
    assert "BEGIN CERTIFICATE" in response.certificate
    assert "BEGIN PRIVATE KEY" in response.private_key
    assert "BEGIN CERTIFICATE" in response.ca_certificate


def test_health_report_request_schema():
    """Test HealthReportRequest schema validation"""
    from app.schemas.health import HealthReportRequest

    request = HealthReportRequest(
        device_id="laptop-001",
        status="healthy",
        metrics={
            "cpu_percent": 45.5,
            "memory_percent": 62.3,
            "disk_percent": 78.1
        }
    )

    assert request.device_id == "laptop-001"
    assert request.status == "healthy"
    assert request.metrics["cpu_percent"] == 45.5


def test_health_report_request_requires_device_and_metrics():
    """Test HealthReportRequest requires device_id and metrics"""
    from app.schemas.health import HealthReportRequest

    with pytest.raises(ValidationError):
        HealthReportRequest(
            device_id="laptop-001"
            # Missing metrics
        )


def test_health_report_request_default_status():
    """Test HealthReportRequest has default status='healthy'"""
    from app.schemas.health import HealthReportRequest

    request = HealthReportRequest(
        device_id="laptop-001",
        metrics={"cpu_percent": 30.0}
    )

    assert request.status == "healthy"


def test_health_report_request_accepts_complex_metrics():
    """Test HealthReportRequest accepts nested dict metrics"""
    from app.schemas.health import HealthReportRequest

    complex_metrics = {
        "cpu": {"percent": 45.5, "cores": 4},
        "memory": {"percent": 62.3, "total_gb": 16},
        "services": ["nginx", "postgres"]
    }

    request = HealthReportRequest(
        device_id="server-001",
        metrics=complex_metrics
    )

    assert request.metrics["cpu"]["cores"] == 4
    assert request.metrics["services"] == ["nginx", "postgres"]


def test_health_report_response_schema():
    """Test HealthReportResponse schema"""
    from app.schemas.health import HealthReportResponse

    response = HealthReportResponse(
        message="Health report received",
        device_id="laptop-001"
    )

    assert response.message == "Health report received"
    assert response.device_id == "laptop-001"
