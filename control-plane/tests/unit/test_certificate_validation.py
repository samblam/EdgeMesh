"""Tests for certificate service validation and edge cases"""
import pytest
from app.services.cert_service import CertificateService
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import serialization
import datetime


def test_multiple_certificates_have_unique_serials():
    """Test that multiple certificates get unique serial numbers"""
    cert_service = CertificateService()

    # Issue multiple certificates
    _, cert1_pem, _, serial1 = cert_service.issue_device_certificate("device-001", "laptop")
    _, cert2_pem, _, serial2 = cert_service.issue_device_certificate("device-002", "laptop")
    _, cert3_pem, _, serial3 = cert_service.issue_device_certificate("device-003", "laptop")

    # All serial numbers should be unique
    serials = {serial1, serial2, serial3}
    assert len(serials) == 3, "Serial numbers should be unique"


def test_device_certificate_contains_device_id_in_common_name():
    """Test that device certificates include device ID in CN"""
    cert_service = CertificateService()

    device_id = "test-device-123"
    _, cert_pem, _, _ = cert_service.issue_device_certificate(device_id, "laptop")

    # Parse certificate
    cert = x509.load_pem_x509_certificate(cert_pem)

    # Extract CN from subject
    cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value

    # Should contain device ID
    assert device_id in cn


def test_device_certificate_validity_period():
    """Test that device certificates have correct validity period (90 days default)"""
    cert_service = CertificateService()

    _, cert_pem, _, _ = cert_service.issue_device_certificate("device-001", "laptop")

    # Parse certificate
    cert = x509.load_pem_x509_certificate(cert_pem)

    # Check validity period (default is 90 days)
    validity_days = (cert.not_valid_after - cert.not_valid_before).days
    assert 89 <= validity_days <= 91, "Certificate should be valid for approximately 90 days"


def test_ca_certificate_is_ca():
    """Test that CA certificate has proper CA extensions"""
    cert_service = CertificateService()

    # Get CA cert
    ca_key = cert_service.ca_key
    ca_cert = cert_service.ca_cert

    # Should have BasicConstraints extension with CA=true
    basic_constraints = ca_cert.extensions.get_extension_for_oid(
        ExtensionOID.BASIC_CONSTRAINTS
    )
    assert basic_constraints.value.ca is True


def test_private_key_is_valid_rsa():
    """Test that generated private keys are valid RSA keys"""
    cert_service = CertificateService()

    key_pem, _, _, _ = cert_service.issue_device_certificate("device-001", "laptop")

    # Should be able to load as RSA private key
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend

    key = serialization.load_pem_private_key(
        key_pem,
        password=None,
        backend=default_backend()
    )

    # Should be RSA key
    assert isinstance(key, rsa.RSAPrivateKey)
    # Should be 2048 bits
    assert key.key_size == 2048


def test_certificates_can_be_reloaded():
    """Test that issued certificates can be parsed and reloaded"""
    cert_service = CertificateService()

    key_pem, cert_pem, ca_pem, _ = cert_service.issue_device_certificate("device-001", "laptop")

    # All PEM data should be parseable
    from cryptography.hazmat.backends import default_backend

    # Reload private key
    key = serialization.load_pem_private_key(key_pem, password=None, backend=default_backend())
    assert key is not None

    # Reload device cert
    cert = x509.load_pem_x509_certificate(cert_pem)
    assert cert is not None

    # Reload CA cert
    ca = x509.load_pem_x509_certificate(ca_pem)
    assert ca is not None
