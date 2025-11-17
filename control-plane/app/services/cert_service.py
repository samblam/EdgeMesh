"""Certificate management service"""
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta, timezone
from typing import Tuple

from app.config import settings


class CertificateService:
    """
    Manage device certificates with self-signed CA

    This service generates a self-signed Certificate Authority (CA) and uses it
    to issue certificates for devices. In production, you would use an external
    CA like cert-manager, Vault, or AWS ACM.
    """

    def __init__(self):
        """Initialize service and generate CA certificate"""
        self.ca_key, self.ca_cert = self._generate_ca()

    def _generate_ca(self) -> Tuple[rsa.RSAPrivateKey, x509.Certificate]:
        """
        Generate self-signed CA certificate

        Returns:
            Tuple of (CA private key, CA certificate)
        """
        # Generate CA private key (2048-bit RSA)
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        # Create CA certificate subject/issuer (same for self-signed)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CA"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "EdgeMesh"),
            x509.NameAttribute(NameOID.COMMON_NAME, "EdgeMesh CA"),
        ])

        # Build certificate
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(timezone.utc))
            .not_valid_after(
                datetime.now(timezone.utc) +
                timedelta(days=settings.CA_CERT_VALIDITY_DAYS)
            )
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            )
            .sign(private_key, hashes.SHA256())
        )

        return private_key, cert

    def issue_device_certificate(
        self,
        device_id: str,
        device_type: str
    ) -> Tuple[bytes, bytes, bytes, str]:
        """
        Issue certificate for a device

        Args:
            device_id: Unique device identifier
            device_type: Type of device (laptop, server, iot, etc.)

        Returns:
            Tuple of:
            - Device private key (PEM-encoded bytes)
            - Device certificate (PEM-encoded bytes)
            - CA certificate (PEM-encoded bytes)
            - Certificate serial number (hex string)
        """
        # Generate device private key
        device_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        # Create device certificate subject
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CA"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "EdgeMesh"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, device_type),
            x509.NameAttribute(NameOID.COMMON_NAME, device_id),
        ])

        serial = x509.random_serial_number()

        # Build device certificate
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(self.ca_cert.subject)  # Signed by CA
            .public_key(device_key.public_key())
            .serial_number(serial)
            .not_valid_before(datetime.now(timezone.utc))
            .not_valid_after(
                datetime.now(timezone.utc) +
                timedelta(days=settings.CERT_VALIDITY_DAYS)
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    key_cert_sign=False,
                    key_agreement=False,
                    content_commitment=False,
                    data_encipherment=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.ExtendedKeyUsage([
                    x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
                    x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
                ]),
                critical=True,
            )
            .sign(self.ca_key, hashes.SHA256())  # Sign with CA key
        )

        # Serialize to PEM format
        device_key_pem = device_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        device_cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        ca_cert_pem = self.ca_cert.public_bytes(serialization.Encoding.PEM)
        serial_str = format(serial, 'x')  # Convert to hex string

        return device_key_pem, device_cert_pem, ca_cert_pem, serial_str

    def get_ca_certificate_pem(self) -> bytes:
        """
        Get CA certificate in PEM format

        Returns:
            CA certificate as PEM-encoded bytes
        """
        return self.ca_cert.public_bytes(serialization.Encoding.PEM)
