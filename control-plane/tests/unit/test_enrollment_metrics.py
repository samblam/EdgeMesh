"""Tests for enrollment endpoint metrics recording"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
async def test_enrollment_records_metrics_on_success(client: AsyncClient):
    """Test that successful enrollment records metrics"""
    # Mock MetricsService to verify it's called
    with patch('app.api.v1.enrollment.MetricsService') as mock_metrics:
        mock_metrics.record_device_enrollment = MagicMock()

        response = await client.post(
            "/api/v1/enroll",
            json={
                "device_id": "metrics-test-device",
                "device_type": "laptop",
                "enrollment_token": "change-me-in-production",
                "os": "Ubuntu",
                "os_version": "22.04"
            }
        )

        # Verify successful enrollment
        assert response.status_code == 200

        # Verify metrics were recorded
        mock_metrics.record_device_enrollment.assert_called_once()


@pytest.mark.asyncio
async def test_enrollment_does_not_record_metrics_on_invalid_token(client: AsyncClient):
    """Test that metrics are NOT recorded when enrollment fails due to invalid token"""
    with patch('app.api.v1.enrollment.MetricsService') as mock_metrics:
        mock_metrics.record_device_enrollment = MagicMock()

        response = await client.post(
            "/api/v1/enroll",
            json={
                "device_id": "invalid-token-device",
                "device_type": "laptop",
                "enrollment_token": "wrong-token",
                "os": "Ubuntu",
                "os_version": "22.04"
            }
        )

        # Verify enrollment failed
        assert response.status_code == 401

        # Verify metrics were NOT recorded
        mock_metrics.record_device_enrollment.assert_not_called()


@pytest.mark.asyncio
async def test_enrollment_does_not_record_metrics_on_duplicate(client: AsyncClient, db_session):
    """Test that metrics are NOT recorded when enrollment fails due to duplicate device"""
    from app.models.device import Device

    # Pre-create device to cause duplicate conflict
    existing_device = Device(
        device_id="duplicate-metrics-device",
        device_type="laptop",
        certificate_serial="existing-serial",
        certificate_pem="existing-cert"
    )
    db_session.add(existing_device)
    await db_session.commit()

    with patch('app.api.v1.enrollment.MetricsService') as mock_metrics:
        mock_metrics.record_device_enrollment = MagicMock()

        response = await client.post(
            "/api/v1/enroll",
            json={
                "device_id": "duplicate-metrics-device",
                "device_type": "laptop",
                "enrollment_token": "change-me-in-production"
            }
        )

        # Verify enrollment failed with 409 Conflict
        assert response.status_code == 409

        # Verify metrics were NOT recorded for failed enrollment
        mock_metrics.record_device_enrollment.assert_not_called()


@pytest.mark.asyncio
async def test_enrollment_returns_all_certificates(client: AsyncClient):
    """Test that enrollment response includes all required certificate components"""
    response = await client.post(
        "/api/v1/enroll",
        json={
            "device_id": "cert-test-device",
            "device_type": "laptop",
            "enrollment_token": "change-me-in-production",
            "os": "Ubuntu",
            "os_version": "22.04"
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verify all certificate components are present
    assert "device_id" in data
    assert "certificate" in data
    assert "private_key" in data
    assert "ca_certificate" in data

    # Verify they contain PEM-formatted data
    assert "BEGIN CERTIFICATE" in data["certificate"]
    assert "BEGIN PRIVATE KEY" in data["private_key"]
    assert "BEGIN CERTIFICATE" in data["ca_certificate"]

    # Verify device_id matches request
    assert data["device_id"] == "cert-test-device"
