"""mTLS Authentication Middleware"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)


class MTLSMiddleware(BaseHTTPMiddleware):
    """
    Middleware to verify client certificates for mTLS authentication

    Note: In production, configure your reverse proxy (nginx/traefik)
    to handle mTLS termination and pass client cert info via headers.

    Production Setup (nginx example):
    ```
    server {
        listen 443 ssl;

        # Client certificate verification
        ssl_client_certificate /path/to/ca.crt;
        ssl_verify_client on;

        # Pass client cert to backend
        proxy_set_header X-Client-Cert $ssl_client_escaped_cert;

        location / {
            proxy_pass http://control-plane:8000;
        }
    }
    ```

    The middleware then extracts device_id from the certificate CN.
    """

    # Paths that don't require mTLS authentication
    EXEMPT_PATHS = [
        "/",
        "/healthz",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/metrics",
        "/api/v1/enroll"  # Enrollment uses token auth instead
    ]

    async def dispatch(self, request: Request, call_next):
        """
        Process request with mTLS verification

        For exempt paths, allow through without verification.
        For other paths, verify client certificate (in production).

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint in chain

        Returns:
            Response from endpoint or 401 if authentication fails
        """
        # Skip mTLS for exempt paths
        if any(request.url.path.startswith(path) for path in self.EXEMPT_PATHS):
            return await call_next(request)

        # Production mode: Get client certificate from reverse proxy header
        # client_cert_pem = request.headers.get("X-Client-Cert")

        # For demo/development, we skip actual verification
        # This allows local testing without full mTLS infrastructure
        # In production deployment, uncomment the code below:

        # try:
        #     if not client_cert_pem:
        #         logger.warning(f"Missing client certificate for {request.url.path}")
        #         return JSONResponse(
        #             status_code=401,
        #             content={"detail": "Client certificate required"}
        #         )
        #
        #     # Parse certificate
        #     cert = x509.load_pem_x509_certificate(
        #         client_cert_pem.encode(),
        #         default_backend()
        #     )
        #
        #     # Extract device ID from certificate Common Name (CN)
        #     cn_attributes = cert.subject.get_attributes_for_oid(
        #         x509.oid.NameOID.COMMON_NAME
        #     )
        #     if not cn_attributes:
        #         logger.error("Certificate missing Common Name")
        #         return JSONResponse(
        #             status_code=401,
        #             content={"detail": "Invalid client certificate: missing CN"}
        #         )
        #
        #     device_id = cn_attributes[0].value
        #
        #     # Verify certificate is not expired
        #     from datetime import datetime, timezone
        #     now = datetime.now(timezone.utc)
        #     if cert.not_valid_before_utc > now or cert.not_valid_after_utc < now:
        #         logger.warning(f"Expired certificate for device {device_id}")
        #         return JSONResponse(
        #             status_code=401,
        #             content={"detail": "Certificate expired or not yet valid"}
        #         )
        #
        #     # Add authenticated device info to request state
        #     request.state.device_id = device_id
        #     request.state.authenticated = True
        #
        #     logger.info(f"mTLS authentication successful for device {device_id}")
        #
        # except Exception as e:
        #     logger.error(f"mTLS verification failed: {e}")
        #     return JSONResponse(
        #         status_code=401,
        #         content={"detail": "Invalid client certificate"}
        #     )

        # Demo mode: Allow all requests through
        # Endpoints can still check request.state.device_id if needed
        return await call_next(request)
