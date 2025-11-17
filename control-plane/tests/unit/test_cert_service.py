"""Tests for certificate service"""
import pytest
from cryptography import x509
from cryptography.x509.oid import NameOID
from app.config import settings


def test_ca_certificate_generated_on_init():
    """Test CA certificate is generated when service is initialized"""
    from app.services.cert_service import CertificateService

    service = CertificateService()

    assert service.ca_cert is not None
    assert service.ca_key is not None


def test_ca_certificate_is_self_signed():
    """Test CA certificate is self-signed"""
    from app.services.cert_service import CertificateService

    service = CertificateService()

    # Subject and issuer should be the same for self-signed
    assert service.ca_cert.issuer == service.ca_cert.subject


def test_ca_has_basic_constraints():
    """Test CA certificate has BasicConstraints extension with ca=True"""
    from app.services.cert_service import CertificateService

    service = CertificateService()

    basic_constraints = service.ca_cert.extensions.get_extension_for_class(
        x509.BasicConstraints
    )
    assert basic_constraints.value.ca is True


def test_ca_validity_period():
    """Test CA certificate valid for configured period (3650 days)"""
    from app.services.cert_service import CertificateService

    service = CertificateService()

    validity = service.ca_cert.not_valid_after - service.ca_cert.not_valid_before

    # Allow 1 day tolerance for test execution time
    assert abs(validity.days - settings.CA_CERT_VALIDITY_DAYS) <= 1


def test_ca_has_correct_subject():
    """Test CA certificate has expected subject"""
    from app.services.cert_service import CertificateService

    service = CertificateService()

    subject = service.ca_cert.subject

    # Check for expected attributes
    cn = subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    org = subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value

    assert cn == "EdgeMesh CA"
    assert org == "EdgeMesh"


def test_issue_device_certificate_returns_all_components():
    """Test issuing device certificate returns key, cert, CA cert, and serial"""
    from app.services.cert_service import CertificateService

    service = CertificateService()

    device_key, device_cert, ca_cert, serial = service.issue_device_certificate(
        device_id="test-device-001",
        device_type="laptop"
    )

    # All components should be present
    assert device_key is not None
    assert device_cert is not None
    assert ca_cert is not None
    assert serial is not None

    # Should be PEM encoded
    assert b"BEGIN PRIVATE KEY" in device_key
    assert b"BEGIN CERTIFICATE" in device_cert
    assert b"BEGIN CERTIFICATE" in ca_cert


def test_device_certificate_has_correct_validity():
    """Test device certificate has 90-day validity"""
    from app.services.cert_service import CertificateService
    from cryptography.hazmat.backends import default_backend

    service = CertificateService()

    _, device_cert_pem, _, _ = service.issue_device_certificate(
        "test-device", "laptop"
    )

    cert = x509.load_pem_x509_certificate(device_cert_pem, default_backend())

    validity = cert.not_valid_after - cert.not_valid_before
    assert abs(validity.days - settings.CERT_VALIDITY_DAYS) <= 1


def test_device_certificate_subject_contains_device_id():
    """Test device certificate CN is the device ID"""
    from app.services.cert_service import CertificateService
    from cryptography.hazmat.backends import default_backend

    service = CertificateService()

    device_id = "test-device-123"
    _, device_cert_pem, _, _ = service.issue_device_certificate(
        device_id, "laptop"
    )

    cert = x509.load_pem_x509_certificate(device_cert_pem, default_backend())

    cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    assert cn == device_id


def test_device_certificate_signed_by_ca():
    """Test device certificate is signed by CA"""
    from app.services.cert_service import CertificateService
    from cryptography.hazmat.backends import default_backend

    service = CertificateService()

    _, device_cert_pem, _, _ = service.issue_device_certificate(
        "test-device", "laptop"
    )

    device_cert = x509.load_pem_x509_certificate(device_cert_pem, default_backend())

    # Issuer should match CA subject
    assert device_cert.issuer == service.ca_cert.subject


def test_device_certificate_has_key_usage():
    """Test device certificate has correct KeyUsage extension"""
    from app.services.cert_service import CertificateService
    from cryptography.hazmat.backends import default_backend

    service = CertificateService()

    _, device_cert_pem, _, _ = service.issue_device_certificate(
        "test-device", "laptop"
    )

    cert = x509.load_pem_x509_certificate(device_cert_pem, default_backend())

    key_usage = cert.extensions.get_extension_for_class(x509.KeyUsage)

    assert key_usage.value.digital_signature is True
    assert key_usage.value.key_encipherment is True
    assert key_usage.value.key_cert_sign is False


def test_device_certificate_has_extended_key_usage():
    """Test device certificate has ExtendedKeyUsage for client/server auth"""
    from app.services.cert_service import CertificateService
    from cryptography.hazmat.backends import default_backend

    service = CertificateService()

    _, device_cert_pem, _, _ = service.issue_device_certificate(
        "test-device", "laptop"
    )

    cert = x509.load_pem_x509_certificate(device_cert_pem, default_backend())

    ext_key_usage = cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage)

    # Should have both client and server auth
    assert x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH in ext_key_usage.value
    assert x509.oid.ExtendedKeyUsageOID.SERVER_AUTH in ext_key_usage.value
