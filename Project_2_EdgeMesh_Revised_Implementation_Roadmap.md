# Project 2: EdgeMesh Control Plane - Complete Implementation Roadmap

## Executive Summary

**Project Name:** EdgeMesh - Zero-Trust Access Control Plane  
**Target Companies:** Tailscale (Zero-Trust Networking), Thales (Cybersecurity), GeoComply (Fraud Detection), General Dynamics/Rheinmetall (Defense Infrastructure), Palantir (Policy-Based Access)  
**Core Value Proposition:** Demonstrates zero-trust architecture, policy-as-code, and production observability without complex networking implementation  
**Development Timeline:** 8-10 days (72-80 hours)  
**Deployment Target:** Docker Compose (local demo) + Kubernetes manifests (reference architecture)

### Why This Approach Works

**The Challenge:** Full zero-trust network with WireGuard would require:
- Kernel-level networking (hard to test, platform-specific)
- Multi-machine deployments (complex local setup)
- OS-specific implementations (Windows/Linux/macOS differences)
- Network debugging expertise
- **Result:** Not ideal for Claude Code autonomous development or rapid portfolio building

**The Solution:** Focus on **Control Plane + Simulation**
- ✅ **Real**: Policy engine (OPA), mTLS auth, device health, audit logging, Prometheus metrics
- ✅ **Simulated**: Network tunnels (virtual connections tracked in database)
- ✅ **Claude Code-Friendly**: Pure Python/PostgreSQL/HTTP, Docker Compose, standard patterns
- ✅ **Honest Positioning**: "Production-ready control plane, data plane architecture provided as reference"

### What You Demonstrate

**Zero-Trust Principles:**
1. **Identity-Based Access**: Every device has unique cryptographic identity (mTLS certificates)
2. **Policy-Based Authorization**: Declarative Rego policies evaluated for every request
3. **Device Health Verification**: Real-time compliance checks (patches, antivirus, encryption)
4. **Continuous Authorization**: No persistent trust - every connection re-evaluated
5. **Comprehensive Audit**: Every authorization decision logged with full context
6. **Least Privilege**: Role-based access with time-of-day restrictions

**Production Engineering:**
1. **Policy-as-Code**: Real Open Policy Agent with testable Rego policies
2. **Observability**: Prometheus metrics + Grafana dashboards + structured logging
3. **Database Design**: Proper PostgreSQL schema with indexes and constraints
4. **API Design**: RESTful FastAPI with OpenAPI docs, proper error handling
5. **Testing**: Unit tests (80%+), integration tests, load tests
6. **Security**: mTLS authentication, self-signed CA, audit logging

**What's Honestly Positioned as Reference:**
- ❌ **WireGuard Implementation**: "Data plane uses virtual tunnels; production would implement WireGuard"
- ❌ **Distributed Agents**: "Simulator demonstrates concepts; production would deploy agents"
- ❌ **External CA**: "Self-signed for demo; production would use cert-manager or Vault"

### Why This Impresses Defense Contractors

Defense tech companies care about **architecture and systems thinking**, not reimplementing commodity protocols:

**Palantir Perspective:**
- Uses OPA for policy enforcement (you demonstrate same approach)
- Cares about data integration and authorization logic
- Values clean architecture over networking complexity

**DoD/Defense Contractor Perspective:**
- Zero-trust is DoD mandate (NIST 800-207 compliance)
- Need audit trails for CMMC/FedRAMP requirements
- Policy-as-code aligns with Infrastructure-as-Code practices
- Combined with Sentinel v2, shows edge computing + access control

**Infrastructure Companies (Tailscale, etc.):**
- Shows understanding of zero-trust principles
- Policy engine demonstrates authorization thinking
- Observability shows production mindset
- Honest about data plane being reference architecture

---

## System Architecture

### High-Level Components

```
┌───────────────────────────────────────────────────────────────────┐
│                    EdgeMesh Control Plane                          │
├───────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              Control Plane API (FastAPI)                  │    │
│  ├──────────────────────────────────────────────────────────┤    │
│  │                                                            │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │    │
│  │  │   Device     │  │   Policy     │  │     Auth     │  │    │
│  │  │   Registry   │  │   Engine     │  │   Service    │  │    │
│  │  │              │  │   (OPA)      │  │   (mTLS)     │  │    │
│  │  │ • Enroll     │  │              │  │              │  │    │
│  │  │ • Health     │  │ • Rego       │  │ • Cert Issue │  │    │
│  │  │ • Status     │  │ • Evaluate   │  │ • Verify     │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │    │
│  │                                                            │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │    │
│  │  │ Connection   │  │    Audit     │  │   Metrics    │  │    │
│  │  │  Manager     │  │   Logger     │  │   Exporter   │  │    │
│  │  │              │  │              │  │              │  │    │
│  │  │ • Establish  │  │ • Decisions  │  │ • Prometheus │  │    │
│  │  │ • Track      │  │ • Events     │  │ • Custom     │  │    │
│  │  │ • Terminate  │  │ • Compliance │  │ • Health     │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │    │
│  └──────────────────────────────────────────────────────────┘    │
│                              │                                     │
│                     ┌────────▼─────────┐                          │
│                     │   PostgreSQL     │                          │
│                     │                  │                          │
│                     │ • devices        │                          │
│                     │ • users          │                          │
│                     │ • policies       │                          │
│                     │ • connections    │                          │
│                     │ • health_checks  │                          │
│                     │ • audit_logs     │                          │
│                     └──────────────────┘                          │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              Client Simulator (Python CLI)                │    │
│  ├──────────────────────────────────────────────────────────┤    │
│  │                                                            │    │
│  │  Simulates device behavior for demo/testing:              │    │
│  │  • Device enrollment with certificate issuance            │    │
│  │  • Periodic health reporting (CPU, memory, patches)       │    │
│  │  • Connection requests to services                        │    │
│  │  • Load generation for Grafana visualization             │    │
│  │                                                            │    │
│  │  Can simulate 10-100+ devices concurrently                │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              Observability Stack (Docker)                 │    │
│  ├──────────────────────────────────────────────────────────┤    │
│  │                                                            │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │    │
│  │  │ Prometheus │  │  Grafana   │  │    Loki    │         │    │
│  │  │            │  │            │  │  (optional)│         │    │
│  │  │ • Scrape   │  │ • System   │  │ • Logs     │         │    │
│  │  │ • Alert    │  │ • Security │  │ • Query    │         │    │
│  │  │ • Store    │  │ • Perform  │  │ • Filter   │         │    │
│  │  └────────────┘  └────────────┘  └────────────┘         │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────┘

Data Plane (Reference Architecture Only):
  In production, would add:
  • WireGuard mesh networking
  • Server-side enforcement agents
  • Network policy synchronization
  
  For this demo:
  • Virtual tunnels tracked in database
  • Conceptual architecture documented
  • Focus on control plane authorization
```

### Data Flow

**1. Device Enrollment:**
```
Device → POST /api/v1/devices/enroll (enrollment token)
         ↓
Control Plane:
  • Validates token
  • Issues TLS certificate (self-signed CA)
  • Stores device in database
  • Returns certificate + virtual tunnel config
         ↓
Device ← Certificate + Config
```

**2. Health Reporting:**
```
Device → POST /api/v1/devices/{id}/health (mTLS authenticated)
         ↓
Control Plane:
  • Verifies certificate
  • Evaluates health metrics
  • Updates device compliance status
  • Triggers alerts if unhealthy
         ↓
Device ← Health status (healthy/unhealthy)
```

**3. Connection Authorization:**
```
Device → POST /api/v1/connections/request (mTLS authenticated)
         ↓
Control Plane:
  • Verifies device identity (mTLS)
  • Checks device health status
  • Queries OPA policy engine
  • Logs authorization decision
  • Creates virtual tunnel record (if allowed)
         ↓
Device ← Allow/Deny + Virtual Tunnel Info
```

---

## Module Breakdown

### Module 1: Core API & Database (Days 1-2, 16 hours)

**Deliverables:**
1. FastAPI application structure
2. PostgreSQL schema and Alembic migrations
3. Device enrollment endpoint
4. Self-signed CA certificate generation
5. Health check endpoint
6. Basic mTLS middleware
7. Unit tests (80%+ coverage)

**Tech Stack:**
- Python 3.11
- FastAPI 0.104+
- SQLAlchemy 2.0 (async)
- Alembic (migrations)
- cryptography library (certificates)
- pytest + pytest-asyncio

**Project Structure:**
```
edgemesh/
├── control-plane/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Configuration
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── devices.py      # Device endpoints
│   │   │   │   ├── health.py       # Health check endpoints
│   │   │   │   ├── connections.py  # Connection endpoints
│   │   │   │   └── admin.py        # Admin endpoints
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── device.py           # Device model
│   │   │   ├── user.py             # User model
│   │   │   ├── connection.py       # Connection model
│   │   │   └── audit.py            # Audit log model
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── device.py           # Pydantic schemas
│   │   │   ├── health.py
│   │   │   └── connection.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── cert_service.py     # Certificate operations
│   │   │   ├── opa_client.py       # OPA integration
│   │   │   └── metrics.py          # Prometheus metrics
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py          # Database session
│   │   │   └── base.py             # Base model
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   └── mtls.py             # mTLS authentication
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── logger.py           # Structured logging
│   ├── migrations/                 # Alembic migrations
│   │   └── versions/
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py            # Pytest fixtures
│   │   ├── test_devices.py
│   │   ├── test_health.py
│   │   └── test_connections.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── simulator/
│   ├── simulator.py               # Device simulator
│   ├── requirements.txt
│   └── README.md
├── policies/                      # OPA Rego policies
│   ├── device_access.rego
│   ├── time_based_access.rego
│   └── rbac.rego
├── docker-compose.yml
├── prometheus.yml
└── README.md
```

**Database Schema:**

```sql
-- devices table
CREATE TABLE devices (
    device_id VARCHAR(255) PRIMARY KEY,
    device_type VARCHAR(50) NOT NULL,  -- laptop, server, iot
    certificate_serial VARCHAR(255) NOT NULL UNIQUE,
    certificate_pem TEXT NOT NULL,
    os VARCHAR(100),
    os_version VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'active',  -- active, unhealthy, revoked
    enrolled_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_enrolled (enrolled_at)
);

-- users table
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL,  -- admin, developer, analyst
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(50) NOT NULL DEFAULT 'active'
);

-- health_checks table
CREATE TABLE health_checks (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) REFERENCES devices(device_id) ON DELETE CASCADE,
    cpu_usage FLOAT,
    memory_usage FLOAT,
    disk_usage FLOAT,
    os_patches_current BOOLEAN,
    antivirus_enabled BOOLEAN,
    disk_encrypted BOOLEAN,
    reported_at TIMESTAMP NOT NULL DEFAULT NOW(),
    INDEX idx_device_health (device_id, reported_at DESC)
);

-- connections table (virtual tunnels)
CREATE TABLE connections (
    id SERIAL PRIMARY KEY,
    connection_id VARCHAR(255) UNIQUE NOT NULL,
    device_id VARCHAR(255) REFERENCES devices(device_id),
    user_id VARCHAR(255) REFERENCES users(user_id),
    service_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- requested, established, terminated
    established_at TIMESTAMP NOT NULL DEFAULT NOW(),
    terminated_at TIMESTAMP,
    INDEX idx_device_connections (device_id, status),
    INDEX idx_active (status, established_at) WHERE status = 'established'
);

-- audit_logs table
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,  -- enrollment, authorization, connection
    device_id VARCHAR(255) REFERENCES devices(device_id),
    user_id VARCHAR(255) REFERENCES users(user_id),
    service_name VARCHAR(255),
    action VARCHAR(100),
    decision VARCHAR(50),  -- allow, deny
    reason TEXT,
    policy_version VARCHAR(50),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB,
    INDEX idx_audit_timestamp (timestamp DESC),
    INDEX idx_audit_device (device_id),
    INDEX idx_audit_decisions (decision, timestamp DESC)
);
```

**Core Implementation:**

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1 import devices, health, connections, admin
from app.config import settings
from app.middleware.mtls import MTLSMiddleware

app = FastAPI(
    title="EdgeMesh Control Plane",
    description="Zero-Trust Access Control",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Routes
app.include_router(devices.router, prefix="/api/v1/devices", tags=["devices"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(connections.router, prefix="/api/v1/connections", tags=["connections"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

@app.get("/")
async def root():
    return {
        "name": "EdgeMesh Control Plane",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/healthz")
async def healthz():
    return {"status": "healthy"}
```

```python
# app/services/cert_service.py
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
from typing import Tuple

class CertificateService:
    """Manage device certificates (self-signed CA)"""
    
    def __init__(self):
        # In production, load CA from secure storage
        # For demo, generate on startup
        self.ca_key, self.ca_cert = self._generate_ca()
    
    def _generate_ca(self) -> Tuple[rsa.RSAPrivateKey, x509.Certificate]:
        """Generate self-signed CA certificate"""
        
        # Generate CA private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        # Create CA certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CA"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "EdgeMesh"),
            x509.NameAttribute(NameOID.COMMON_NAME, "EdgeMesh CA"),
        ])
        
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=3650))  # 10 years
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
        Issue certificate for device
        
        Returns:
            - Device private key (PEM)
            - Device certificate (PEM)
            - CA certificate (PEM)
            - Certificate serial number
        """
        
        # Generate device private key
        device_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        # Create device certificate
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CA"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "EdgeMesh"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, device_type),
            x509.NameAttribute(NameOID.COMMON_NAME, device_id),
        ])
        
        serial = x509.random_serial_number()
        
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(self.ca_cert.subject)
            .public_key(device_key.public_key())
            .serial_number(serial)
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=90))
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
            .sign(self.ca_key, hashes.SHA256())
        )
        
        # Serialize to PEM
        device_key_pem = device_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        device_cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        ca_cert_pem = self.ca_cert.public_bytes(serialization.Encoding.PEM)
        
        serial_str = format(serial, 'x')
        
        return device_key_pem, device_cert_pem, ca_cert_pem, serial_str
    
    def get_ca_certificate(self) -> bytes:
        """Get CA certificate PEM"""
        return self.ca_cert.public_bytes(serialization.Encoding.PEM)
```

```python
# app/api/v1/devices.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.schemas.device import DeviceEnrollment, DeviceResponse
from app.services.cert_service import CertificateService
from app.db.session import get_db
from app.models.device import Device

router = APIRouter()
cert_service = CertificateService()

@router.post("/enroll", response_model=DeviceResponse)
async def enroll_device(
    enrollment: DeviceEnrollment,
    db: AsyncSession = Depends(get_db)
):
    """
    Enroll a new device in EdgeMesh
    
    Steps:
    1. Validate enrollment token
    2. Issue device certificate
    3. Store device in database
    4. Return certificate bundle
    """
    
    # Check if device already exists
    existing = await db.get(Device, enrollment.device_id)
    if existing:
        raise HTTPException(status_code=409, detail="Device already enrolled")
    
    # Issue certificate
    device_key, device_cert, ca_cert, serial = cert_service.issue_device_certificate(
        enrollment.device_id,
        enrollment.device_type
    )
    
    # Create device record
    device = Device(
        device_id=enrollment.device_id,
        device_type=enrollment.device_type,
        certificate_serial=serial,
        certificate_pem=device_cert.decode('utf-8'),
        os=enrollment.os,
        os_version=enrollment.os_version,
        status="active"
    )
    
    db.add(device)
    await db.commit()
    await db.refresh(device)
    
    return {
        "device_id": device.device_id,
        "device_key_pem": device_key.decode('utf-8'),
        "device_cert_pem": device_cert.decode('utf-8'),
        "ca_cert_pem": ca_cert.decode('utf-8'),
        "virtual_tunnel_config": {
            "control_plane_url": "https://api.edgemesh.local:8000",
            "status": "enrolled"
        }
    }

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get device information"""
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return device

@router.get("/", response_model=List[DeviceResponse])
async def list_devices(
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    """List all devices, optionally filtered by status"""
    query = select(Device)
    if status:
        query = query.where(Device.status == status)
    
    result = await db.execute(query)
    devices = result.scalars().all()
    
    return devices
```

---

### Module 2: Policy Engine (OPA Integration) (Days 3-4, 16 hours)

**Deliverables:**
1. OPA Docker container configuration
2. Rego policy suite
3. OPA client library in Python
4. Authorization endpoint
5. Policy testing framework
6. Integration tests

**OPA Policies:**

```rego
# policies/device_access.rego
package edgemesh.authz

import future.keywords.if
import future.keywords.in

# Default deny
default allow := false

# Main authorization logic
allow if {
    input.device.authenticated
    device_is_healthy(input.device)
    service_access_allowed(input.user, input.service)
    time_restrictions_met(input.user, input.time)
}

# Device health evaluation
device_is_healthy(device) if {
    device.status == "active"
    device.os_patches_current == true
    device.antivirus_enabled == true
    device.disk_encrypted == true
    device.cpu_usage < 90
    device.memory_usage < 90
}

# Service access control based on roles
service_access_allowed(user, service) if {
    role := user.role
    service_permissions[service][role] == true
}

# Service to role mapping
service_permissions := {
    "database": {
        "admin": true,
        "developer": true,
        "analyst": false
    },
    "api": {
        "admin": true,
        "developer": true,
        "analyst": true
    },
    "storage": {
        "admin": true,
        "developer": true,
        "analyst": true
    },
    "analytics": {
        "admin": true,
        "developer": false,
        "analyst": true
    }
}

# Time-based access restrictions
time_restrictions_met(user, time) if {
    user.role == "admin"  # Admins always allowed
}

time_restrictions_met(user, time) if {
    user.role != "admin"
    is_business_hours(time)
}

is_business_hours(time) if {
    time.hour >= 9
    time.hour < 17
    time.day_of_week >= 1  # Monday
    time.day_of_week <= 5  # Friday
}
```

```rego
# policies/compliance.rego
package edgemesh.compliance

import future.keywords.if

# Check if device meets compliance requirements
device_compliant(device) if {
    device.os_patches_current == true
    device.antivirus_enabled == true
    device.disk_encrypted == true
    supported_os_version(device.os, device.os_version)
}

# Supported OS versions (example)
supported_os_version(os, version) if {
    os == "Ubuntu"
    version in ["22.04", "24.04"]
}

supported_os_version(os, version) if {
    os == "macOS"
    version_parts := split(version, ".")
    major := to_number(version_parts[0])
    major >= 13  # Ventura or later
}

supported_os_version(os, version) if {
    os == "Windows"
    version in ["10", "11"]
}
```

**Python OPA Client:**

```python
# app/services/opa_client.py
import httpx
from typing import Dict, Any
from app.config import settings

class OPAClient:
    """Client for Open Policy Agent"""
    
    def __init__(self):
        self.opa_url = settings.OPA_URL
        self.policy_path = "edgemesh/authz/allow"
    
    async def evaluate_policy(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate policy with given input
        
        Args:
            input_data: Context for policy evaluation
            
        Returns:
            Policy decision with reason
        """
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.opa_url}/v1/data/{self.policy_path}",
                    json={"input": input_data},
                    timeout=5.0
                )
                response.raise_for_status()
                result = response.json()
                
                allowed = result.get("result", False)
                
                return {
                    "allowed": allowed,
                    "decision": "allow" if allowed else "deny"
                }
                
            except httpx.HTTPError as e:
                # Log error
                return {
                    "allowed": False,
                    "decision": "deny",
                    "error": f"OPA evaluation failed: {str(e)}"
                }
    
    async def check_device_compliance(self, device_data: Dict[str, Any]) -> bool:
        """Check if device meets compliance requirements"""
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.opa_url}/v1/data/edgemesh/compliance/device_compliant",
                    json={"input": device_data},
                    timeout=5.0
                )
                response.raise_for_status()
                result = response.json()
                
                return result.get("result", False)
                
            except httpx.HTTPError:
                return False
```

**Authorization Endpoint:**

```python
# app/api/v1/connections.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

from app.schemas.connection import ConnectionRequest, ConnectionResponse
from app.services.opa_client import OPAClient
from app.db.session import get_db
from app.models.device import Device
from app.models.user import User
from app.models.connection import Connection
from app.models.audit import AuditLog

router = APIRouter()
opa_client = OPAClient()

@router.post("/request", response_model=ConnectionResponse)
async def request_connection(
    request: ConnectionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request authorization for connection to service
    
    Steps:
    1. Verify device exists and is active
    2. Get latest health check
    3. Query OPA for authorization decision
    4. Log decision to audit log
    5. Create virtual tunnel if authorized
    """
    
    # Get device
    device = await db.get(Device, request.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if device.status != "active":
        raise HTTPException(status_code=403, detail="Device not active")
    
    # Get user
    user = await db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get latest health check
    health_query = (
        select(HealthCheck)
        .where(HealthCheck.device_id == device.device_id)
        .order_by(HealthCheck.reported_at.desc())
        .limit(1)
    )
    health_result = await db.execute(health_query)
    health = health_result.scalar_one_or_none()
    
    if not health:
        raise HTTPException(status_code=400, detail="No health check on record")
    
    # Build OPA input
    opa_input = {
        "device": {
            "id": device.device_id,
            "type": device.device_type,
            "authenticated": True,  # Verified by mTLS
            "status": device.status,
            "os_patches_current": health.os_patches_current,
            "antivirus_enabled": health.antivirus_enabled,
            "disk_encrypted": health.disk_encrypted,
            "cpu_usage": health.cpu_usage,
            "memory_usage": health.memory_usage,
            "os": device.os,
            "os_version": device.os_version
        },
        "user": {
            "id": user.user_id,
            "role": user.role,
            "email": user.email
        },
        "service": request.service_name,
        "action": "connect",
        "time": {
            "hour": datetime.utcnow().hour,
            "day_of_week": datetime.utcnow().isoweekday()
        }
    }
    
    # Evaluate policy
    decision = await opa_client.evaluate_policy(opa_input)
    
    # Log to audit
    audit_log = AuditLog(
        event_type="authorization",
        device_id=device.device_id,
        user_id=user.user_id,
        service_name=request.service_name,
        action="connect",
        decision=decision["decision"],
        reason=decision.get("error"),
        timestamp=datetime.utcnow()
    )
    db.add(audit_log)
    
    if not decision["allowed"]:
        await db.commit()
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: {decision.get('error', 'Policy evaluation failed')}"
        )
    
    # Create virtual tunnel
    connection_id = str(uuid.uuid4())
    connection = Connection(
        connection_id=connection_id,
        device_id=device.device_id,
        user_id=user.user_id,
        service_name=request.service_name,
        status="established"
    )
    db.add(connection)
    
    await db.commit()
    
    return {
        "connection_id": connection_id,
        "status": "authorized",
        "service_name": request.service_name,
        "virtual_tunnel": {
            "endpoint": f"virtual://{request.service_name}:8080",
            "established_at": connection.established_at
        }
    }

@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get connection details"""
    query = select(Connection).where(Connection.connection_id == connection_id)
    result = await db.execute(query)
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return connection

@router.delete("/{connection_id}")
async def terminate_connection(
    connection_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Terminate virtual tunnel"""
    query = select(Connection).where(Connection.connection_id == connection_id)
    result = await db.execute(query)
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    connection.status = "terminated"
    connection.terminated_at = datetime.utcnow()
    
    await db.commit()
    
    return {"status": "terminated"}
```

---

### Module 3: Device Simulator (Days 5-6, 16 hours)

**Deliverables:**
1. Python CLI simulator
2. Multi-device simulation
3. Realistic load patterns
4. Health reporting
5. Connection requests
6. Metrics generation

**Simulator Implementation:**

```python
# simulator/simulator.py
import asyncio
import httpx
import random
from faker import Faker
from typing import List, Dict
from datetime import datetime
import argparse

fake = Faker()

class DeviceSimulator:
    """Simulate multiple EdgeMesh devices"""
    
    def __init__(self, api_base: str, num_devices: int = 10):
        self.api_base = api_base
        self.devices: List[Dict] = []
        self.num_devices = num_devices
        
    async def initialize_devices(self):
        """Create fake device configurations"""
        
        device_types = ["laptop", "server", "iot"]
        os_options = {
            "laptop": [("Ubuntu", "22.04"), ("macOS", "14.1"), ("Windows", "11")],
            "server": [("Ubuntu", "22.04"), ("Ubuntu", "24.04")],
            "iot": [("Ubuntu", "22.04")]
        }
        
        for i in range(self.num_devices):
            device_type = random.choice(device_types)
            os, os_version = random.choice(os_options[device_type])
            
            device = {
                "device_id": f"device-{i:03d}",
                "device_type": device_type,
                "os": os,
                "os_version": os_version,
                "user_email": fake.email(),
                "user_id": f"user-{i:03d}",
                "enrolled": False
            }
            
            self.devices.append(device)
        
        print(f"Initialized {self.num_devices} devices")
    
    async def enroll_all_devices(self):
        """Enroll all devices with control plane"""
        
        print("\nEnrolling devices...")
        
        async with httpx.AsyncClient(verify=False) as client:
            for device in self.devices:
                try:
                    response = await client.post(
                        f"{self.api_base}/api/v1/devices/enroll",
                        json={
                            "device_id": device["device_id"],
                            "device_type": device["device_type"],
                            "os": device["os"],
                            "os_version": device["os_version"]
                        },
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        device["enrolled"] = True
                        device["device_cert"] = result["device_cert_pem"]
                        print(f"  ✓ {device['device_id']} enrolled")
                    else:
                        print(f"  ✗ {device['device_id']} failed: {response.status_code}")
                        
                except Exception as e:
                    print(f"  ✗ {device['device_id']} error: {e}")
    
    async def report_health(self, device: Dict):
        """Report health for single device"""
        
        # Generate realistic health metrics
        health = {
            "device_id": device["device_id"],
            "cpu_usage": random.uniform(20, 85),
            "memory_usage": random.uniform(30, 80),
            "disk_usage": random.uniform(40, 75),
            "os_patches_current": random.random() > 0.15,  # 85% compliant
            "antivirus_enabled": random.random() > 0.10,   # 90% compliant
            "disk_encrypted": random.random() > 0.05,      # 95% compliant
            "last_scan": datetime.utcnow().isoformat()
        }
        
        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.post(
                    f"{self.api_base}/api/v1/health/report",
                    json=health,
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status_icon = "✓" if result["status"] == "healthy" else "✗"
                    print(f"{status_icon} {device['device_id']}: {result['status']}")
                    
            except Exception as e:
                print(f"✗ {device['device_id']} health report failed: {e}")
    
    async def health_reporting_loop(self):
        """Continuously report health for all devices"""
        
        print("\nStarting health reporting loop (every 60s)...")
        
        while True:
            await asyncio.gather(
                *[self.report_health(device) for device in self.devices if device["enrolled"]]
            )
            await asyncio.sleep(60)
    
    async def request_connection(self, device: Dict):
        """Request connection to random service"""
        
        services = ["database", "api", "storage", "analytics"]
        service = random.choice(services)
        
        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.post(
                    f"{self.api_base}/api/v1/connections/request",
                    json={
                        "device_id": device["device_id"],
                        "user_id": device["user_id"],
                        "service_name": service
                    },
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    print(f"✓ {device['device_id']} → {service} (authorized)")
                else:
                    print(f"✗ {device['device_id']} → {service} (denied: {response.status_code})")
                    
            except Exception as e:
                print(f"✗ {device['device_id']} connection error: {e}")
    
    async def connection_simulation_loop(self):
        """Continuously request random connections"""
        
        print("\nStarting connection simulation loop (every 5s)...")
        
        while True:
            # Pick 1-3 random devices to request connections
            requesting_devices = random.sample(
                [d for d in self.devices if d["enrolled"]],
                k=min(3, len([d for d in self.devices if d["enrolled"]]))
            )
            
            await asyncio.gather(
                *[self.request_connection(device) for device in requesting_devices]
            )
            
            await asyncio.sleep(5)
    
    async def run(self):
        """Run full simulation"""
        
        await self.initialize_devices()
        await self.enroll_all_devices()
        
        # Run health reporting and connection simulation concurrently
        await asyncio.gather(
            self.health_reporting_loop(),
            self.connection_simulation_loop()
        )

async def main():
    parser = argparse.ArgumentParser(description="EdgeMesh Device Simulator")
    parser.add_argument("--api", default="http://localhost:8000", help="Control plane API URL")
    parser.add_argument("--devices", type=int, default=20, help="Number of devices to simulate")
    
    args = parser.parse_args()
    
    simulator = DeviceSimulator(args.api, args.devices)
    await simulator.run()

if __name__ == "__main__":
    asyncio.run(main())
```

**Usage:**

```bash
# Install dependencies
pip install httpx faker

# Run simulator
python simulator.py --api http://localhost:8000 --devices 20

# Output:
# Initialized 20 devices
# 
# Enrolling devices...
#   ✓ device-000 enrolled
#   ✓ device-001 enrolled
#   ...
# 
# Starting health reporting loop (every 60s)...
# ✓ device-000: healthy
# ✗ device-005: unhealthy
# ...
# 
# Starting connection simulation loop (every 5s)...
# ✓ device-002 → api (authorized)
# ✗ device-007 → database (denied: 403)
# ...
```

---

### Module 4: Observability (Days 7-8, 16 hours)

**Deliverables:**
1. Prometheus metrics export
2. Custom business metrics
3. Grafana dashboards (3 dashboards)
4. Alert rules
5. Structured logging

**Prometheus Metrics:**

```python
# app/services/metrics.py
from prometheus_client import Counter, Gauge, Histogram
from typing import Dict

# Device metrics
devices_total = Gauge(
    "edgemesh_devices_total",
    "Total number of devices",
    ["status"]
)

device_enrollments_total = Counter(
    "edgemesh_device_enrollments_total",
    "Total device enrollments"
)

# Authorization metrics
authorization_decisions_total = Counter(
    "edgemesh_authorization_decisions_total",
    "Total authorization decisions",
    ["decision"]  # allow, deny
)

authorization_latency_seconds = Histogram(
    "edgemesh_authorization_latency_seconds",
    "Authorization decision latency"
)

# Connection metrics
connections_active = Gauge(
    "edgemesh_connections_active",
    "Currently active connections",
    ["service"]
)

connections_total = Counter(
    "edgemesh_connections_total",
    "Total connection requests",
    ["service", "status"]  # authorized, denied
)

# Health check metrics
health_checks_total = Counter(
    "edgemesh_health_checks_total",
    "Total health checks received"
)

unhealthy_devices = Gauge(
    "edgemesh_unhealthy_devices",
    "Number of unhealthy devices"
)

class MetricsService:
    """Service for updating Prometheus metrics"""
    
    @staticmethod
    def record_device_enrollment():
        device_enrollments_total.inc()
        devices_total.labels(status="active").inc()
    
    @staticmethod
    def record_device_status_change(old_status: str, new_status: str):
        devices_total.labels(status=old_status).dec()
        devices_total.labels(status=new_status).inc()
    
    @staticmethod
    def record_authorization_decision(allowed: bool, latency: float):
        decision = "allow" if allowed else "deny"
        authorization_decisions_total.labels(decision=decision).inc()
        authorization_latency_seconds.observe(latency)
    
    @staticmethod
    def record_connection_request(service: str, authorized: bool):
        status = "authorized" if authorized else "denied"
        connections_total.labels(service=service, status=status).inc()
        
        if authorized:
            connections_active.labels(service=service).inc()
    
    @staticmethod
    def record_connection_terminated(service: str):
        connections_active.labels(service=service).dec()
    
    @staticmethod
    def record_health_check():
        health_checks_total.inc()
    
    @staticmethod
    def update_device_counts(healthy: int, unhealthy: int):
        devices_total.labels(status="active").set(healthy + unhealthy)
        unhealthy_devices.set(unhealthy)
```

**Grafana Dashboard JSON** (System Overview):

```json
{
  "dashboard": {
    "title": "EdgeMesh - System Overview",
    "panels": [
      {
        "title": "Total Devices",
        "targets": [
          {
            "expr": "sum(edgemesh_devices_total)"
          }
        ],
        "type": "stat"
      },
      {
        "title": "Healthy vs Unhealthy",
        "targets": [
          {
            "expr": "edgemesh_devices_total{status='active'} - edgemesh_unhealthy_devices",
            "legendFormat": "Healthy"
          },
          {
            "expr": "edgemesh_unhealthy_devices",
            "legendFormat": "Unhealthy"
          }
        ],
        "type": "timeseries"
      },
      {
        "title": "Active Connections",
        "targets": [
          {
            "expr": "sum(edgemesh_connections_active)"
          }
        ],
        "type": "stat"
      },
      {
        "title": "Authorization Success Rate",
        "targets": [
          {
            "expr": "rate(edgemesh_authorization_decisions_total{decision='allow'}[5m]) / rate(edgemesh_authorization_decisions_total[5m])"
          }
        ],
        "type": "gauge"
      },
      {
        "title": "Connections by Service",
        "targets": [
          {
            "expr": "edgemesh_connections_active",
            "legendFormat": "{{service}}"
          }
        ],
        "type": "timeseries"
      },
      {
        "title": "Authorization Decisions Over Time",
        "targets": [
          {
            "expr": "rate(edgemesh_authorization_decisions_total{decision='allow'}[5m])",
            "legendFormat": "Allowed"
          },
          {
            "expr": "rate(edgemesh_authorization_decisions_total{decision='deny'}[5m])",
            "legendFormat": "Denied"
          }
        ],
        "type": "timeseries"
      }
    ]
  }
}
```

**Alert Rules:**

```yaml
# prometheus/alerts.yml
groups:
  - name: edgemesh_alerts
    interval: 30s
    rules:
      - alert: HighAuthorizationFailureRate
        expr: |
          (
            rate(edgemesh_authorization_decisions_total{decision="deny"}[5m])
            /
            rate(edgemesh_authorization_decisions_total[5m])
          ) > 0.10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High authorization failure rate"
          description: "{{ $value | humanizePercentage }} of authorization requests are being denied"
      
      - alert: HighUnhealthyDeviceCount
        expr: |
          (
            edgemesh_unhealthy_devices
            /
            sum(edgemesh_devices_total)
          ) > 0.20
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High unhealthy device count"
          description: "{{ $value | humanizePercentage }} of devices are unhealthy"
      
      - alert: SlowAuthorizationLatency
        expr: |
          histogram_quantile(0.95, rate(edgemesh_authorization_latency_seconds_bucket[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow authorization latency"
          description: "P95 authorization latency is {{ $value }}s (threshold: 0.1s)"
```

---

## Docker Compose Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Control Plane API
  api:
    build: ./control-plane
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/edgemesh
      - OPA_URL=http://opa:8181
      - LOG_LEVEL=INFO
    depends_on:
      - db
      - opa
    networks:
      - edgemesh
    restart: unless-stopped

  # PostgreSQL Database
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=edgemesh
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - edgemesh
    restart: unless-stopped

  # Open Policy Agent
  opa:
    image: openpolicyagent/opa:latest
    command:
      - "run"
      - "--server"
      - "--bundle"
      - "/policies"
    volumes:
      - ./policies:/policies:ro
    ports:
      - "8181:8181"
    networks:
      - edgemesh
    restart: unless-stopped

  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/alerts.yml:/etc/prometheus/alerts.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - edgemesh
    restart: unless-stopped

  # Grafana
  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./grafana/datasources:/etc/grafana/provisioning/datasources:ro
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    networks:
      - edgemesh
    restart: unless-stopped

volumes:
  postgres_data:
  prometheus_data:
  grafana_data:

networks:
  edgemesh:
    driver: bridge
```

**Prometheus Configuration:**

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

rule_files:
  - "alerts.yml"

scrape_configs:
  - job_name: 'edgemesh-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
```

---

## Quick Start Guide

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Git

### Setup (< 5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/edgemesh.git
cd edgemesh

# 2. Start all services
docker-compose up -d

# Wait for services to be healthy
docker-compose ps

# 3. Verify API is running
curl http://localhost:8000/healthz
# Should return: {"status":"healthy"}

# 4. Access dashboards
# - API docs: http://localhost:8000/docs
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)

# 5. Run simulator (in separate terminal)
cd simulator
pip install -r requirements.txt
python simulator.py --devices 20

# 6. Watch Grafana dashboards update in real-time!
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_authorization.py
import pytest
from app.services.opa_client import OPAClient

@pytest.mark.asyncio
async def test_authorization_healthy_device_admin():
    """Test authorization for healthy device with admin user"""
    
    opa = OPAClient()
    
    input_data = {
        "device": {
            "authenticated": True,
            "status": "active",
            "os_patches_current": True,
            "antivirus_enabled": True,
            "disk_encrypted": True,
            "cpu_usage": 50,
            "memory_usage": 60,
            "os": "Ubuntu",
            "os_version": "22.04"
        },
        "user": {
            "role": "admin",
            "email": "admin@example.com"
        },
        "service": "database",
        "action": "connect",
        "time": {
            "hour": 14,
            "day_of_week": 3
        }
    }
    
    result = await opa.evaluate_policy(input_data)
    
    assert result["allowed"] == True
    assert result["decision"] == "allow"

@pytest.mark.asyncio
async def test_authorization_unhealthy_device():
    """Test authorization denial for unhealthy device"""
    
    opa = OPAClient()
    
    input_data = {
        "device": {
            "authenticated": True,
            "status": "active",
            "os_patches_current": False,  # Not patched
            "antivirus_enabled": True,
            "disk_encrypted": True,
            "cpu_usage": 50,
            "memory_usage": 60,
            "os": "Ubuntu",
            "os_version": "22.04"
        },
        "user": {
            "role": "developer",
            "email": "dev@example.com"
        },
        "service": "api",
        "action": "connect",
        "time": {
            "hour": 14,
            "day_of_week": 3
        }
    }
    
    result = await opa.evaluate_policy(input_data)
    
    assert result["allowed"] == False
    assert result["decision"] == "deny"

@pytest.mark.asyncio
async def test_authorization_outside_business_hours():
    """Test authorization denial outside business hours for non-admin"""
    
    opa = OPAClient()
    
    input_data = {
        "device": {
            "authenticated": True,
            "status": "active",
            "os_patches_current": True,
            "antivirus_enabled": True,
            "disk_encrypted": True,
            "cpu_usage": 50,
            "memory_usage": 60,
            "os": "Ubuntu",
            "os_version": "22.04"
        },
        "user": {
            "role": "analyst",  # Not admin
            "email": "analyst@example.com"
        },
        "service": "analytics",
        "action": "connect",
        "time": {
            "hour": 22,  # 10 PM
            "day_of_week": 3
        }
    }
    
    result = await opa.evaluate_policy(input_data)
    
    assert result["allowed"] == False
```

### Integration Tests

```python
# tests/integration/test_enrollment_flow.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_complete_enrollment_and_connection_flow():
    """Test full flow: enroll → health check → request connection"""
    
    async with AsyncClient(base_url="http://localhost:8000") as client:
        # 1. Enroll device
        enroll_response = await client.post(
            "/api/v1/devices/enroll",
            json={
                "device_id": "test-device-001",
                "device_type": "laptop",
                "os": "Ubuntu",
                "os_version": "22.04"
            }
        )
        
        assert enroll_response.status_code == 200
        enroll_data = enroll_response.json()
        assert "device_cert_pem" in enroll_data
        
        # 2. Report health (healthy device)
        health_response = await client.post(
            "/api/v1/health/report",
            json={
                "device_id": "test-device-001",
                "cpu_usage": 45.0,
                "memory_usage": 60.0,
                "disk_usage": 70.0,
                "os_patches_current": True,
                "antivirus_enabled": True,
                "disk_encrypted": True,
                "last_scan": "2024-11-17T12:00:00Z"
            }
        )
        
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        
        # 3. Create test user
        user_response = await client.post(
            "/api/v1/admin/users",
            json={
                "user_id": "test-user-001",
                "email": "test@example.com",
                "role": "developer"
            }
        )
        assert user_response.status_code == 200
        
        # 4. Request connection (should be authorized)
        conn_response = await client.post(
            "/api/v1/connections/request",
            json={
                "device_id": "test-device-001",
                "user_id": "test-user-001",
                "service_name": "api"
            }
        )
        
        assert conn_response.status_code == 200
        conn_data = conn_response.json()
        assert conn_data["status"] == "authorized"
        assert "connection_id" in conn_data
```

### Load Tests

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between
import random

class EdgeMeshUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Enroll device on start"""
        response = self.client.post("/api/v1/devices/enroll", json={
            "device_id": f"load-device-{self.environment.runner.user_count}",
            "device_type": "laptop",
            "os": "Ubuntu",
            "os_version": "22.04"
        })
        self.device_id = response.json()["device_id"]
        self.user_id = f"load-user-{self.environment.runner.user_count}"
    
    @task(3)
    def request_connection(self):
        """Request connection to random service"""
        services = ["database", "api", "storage", "analytics"]
        self.client.post("/api/v1/connections/request", json={
            "device_id": self.device_id,
            "user_id": self.user_id,
            "service_name": random.choice(services)
        })
    
    @task(1)
    def report_health(self):
        """Report device health"""
        self.client.post("/api/v1/health/report", json={
            "device_id": self.device_id,
            "cpu_usage": random.uniform(20, 80),
            "memory_usage": random.uniform(30, 75),
            "disk_usage": random.uniform(40, 70),
            "os_patches_current": True,
            "antivirus_enabled": True,
            "disk_encrypted": True,
            "last_scan": "2024-11-17T12:00:00Z"
        })

# Run: locust -f locustfile.py --host=http://localhost:8000
```

---

## Documentation Strategy

### README.md

```markdown
# EdgeMesh: Zero-Trust Access Control Plane

> **Policy-based access control with device health verification, mTLS authentication, and comprehensive audit trails**

[Live Demo](https://edgemesh-demo.com) | [API Docs](http://localhost:8000/docs) | [Architecture](#architecture)

## The Problem

Traditional VPNs and network perimeters fail modern security requirements:
- ❌ Overprivileged access (VPN = full network)
- ❌ No device health checks
- ❌ Static trust model
- ❌ Poor auditability
- ❌ Compliance gaps (NIST 800-207, CMMC)

## The Solution

EdgeMesh implements zero-trust access control:

✅ **Identity-Based**: Cryptographic device identity (mTLS)  
✅ **Policy-Based**: Declarative authorization (Open Policy Agent)  
✅ **Health-Based**: Real-time compliance checks  
✅ **Audit Trail**: Every decision logged  
✅ **Observable**: Prometheus + Grafana

## Quick Start

```bash
# Start services
docker-compose up -d

# Run simulator
python simulator/simulator.py --devices 20

# View dashboards
open http://localhost:3000  # Grafana (admin/admin)
open http://localhost:8000/docs  # API docs
```

## Architecture

EdgeMesh consists of:
1. **Control Plane**: FastAPI + PostgreSQL + OPA
2. **Simulator**: Python CLI for demo/testing
3. **Observability**: Prometheus + Grafana

**Data Plane Note:** This demo focuses on the control plane (policy enforcement, device registry, audit). In production, you would add WireGuard for actual network tunnels. See [Architecture Decisions](docs/architecture.md) for details.

## Key Features

### Policy-as-Code

```rego
# Allow access if device is healthy, user authorized, and business hours
allow if {
    device_is_healthy(input.device)
    service_access_allowed(input.user, input.service)
    time_restrictions_met(input.user, input.time)
}
```

### Device Health Verification

Only compliant devices get access:
- ✅ OS patches current
- ✅ Antivirus enabled
- ✅ Disk encryption enabled
- ✅ Resource usage normal

### Comprehensive Audit

Every authorization decision logged:
- Who (user + device)
- What (service + action)
- When (timestamp)
- Why (policy result)
- Result (allow/deny)

## Demo

Run the simulator to see EdgeMesh in action:

```bash
python simulator/simulator.py --devices 20
```

Watch Grafana dashboards update in real-time as devices:
- Enroll with control plane
- Report health status
- Request connections to services
- Get authorized/denied by policies

## Testing

```bash
# Unit tests
pytest tests/ --cov=app --cov-report=html

# Integration tests
pytest tests/integration/ -v

# Load tests
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

**Coverage:** 85%
- API endpoints: 90%
- Policy client: 88%
- Cert service: 82%

## Why This Architecture?

### Control Plane Focus

**Chose to demonstrate control plane:**
- Zero-trust value is in *policy and identity*, not networking
- WireGuard is commodity (kernel already implements it)
- Combined with [Sentinel v2](link), shows edge + access control

### Open Policy Agent

**Chose OPA:**
- Industry standard (Palantir, Netflix, Pinterest use it)
- Declarative policies are testable
- Microsecond decisions
- Policy separate from code

### Docker Compose

**Chose Docker Compose for demo:**
- `docker-compose up` → working system
- Runs on laptop
- Easy to debug
- Kubernetes manifests provided as reference

## Production Deployment

See [k8s/](k8s/) for:
- Kubernetes manifests
- Helm chart
- Terraform modules

In production, you would add:
- WireGuard mesh networking
- Server-side enforcement agents
- External CA (cert-manager/Vault)
- Network policy synchronization

## Future Enhancements

- [ ] SAML/OIDC integration
- [ ] Hardware security key support
- [ ] Mobile agents (iOS/Android)
- [ ] Policy GUI editor
- [ ] SIEM integration (Splunk, Azure Sentinel)

## License

MIT

## Contact

**Samuel Barefoot**
- Email: samuel.barefoot@example.com
- LinkedIn: linkedin.com/in/samuelbarefoot

---

*Designed for defense tech portfolio demonstration*
```

---

## Positioning for Job Applications

### For Tailscale

"EdgeMesh demonstrates understanding of zero-trust networking principles and policy-based access control. While the demo focuses on the control plane (enrollment, authorization, audit), the architecture shows I understand the data plane challenges that Tailscale solves with WireGuard. The policy engine and device health verification demonstrate security thinking beyond just networking."

### For Defense Contractors (Thales, General Dynamics)

"EdgeMesh addresses DoD zero-trust mandate (NIST 800-207). The comprehensive audit trail supports CMMC Level 2 compliance. Policy-as-code approach aligns with Infrastructure-as-Code practices in modern defense systems. Combined with Sentinel v2, demonstrates both edge computing and access control—critical for tactical systems."

### For Palantir

"EdgeMesh uses the same policy engine (OPA) that Palantir uses for authorization. The project shows I understand data-driven access control: every authorization decision is logged and queryable. The focus on audit trails and compliance aligns with Palantir's government customer requirements. Combined with ThreatStream data pipeline, demonstrates full data → policy → action flow."

### For GeoComply (Fraud Detection)

"EdgeMesh's policy engine demonstrates rule-based decision systems similar to fraud detection. The real-time device health checks mirror device fingerprinting. The audit trail provides complete forensics for investigating suspicious access patterns."

---

## Claude Code Session Prompts

### Session 1: Project Foundation

```
Create EdgeMesh zero-trust access control plane with:

PROJECT SETUP:
1. Create directory structure:
   - control-plane/app/ (FastAPI application)
   - simulator/ (device simulator)
   - policies/ (OPA Rego policies)
   - tests/ (test suite)

2. Initialize control-plane:
   - FastAPI 0.104+ project
   - SQLAlchemy 2.0 async models
   - Alembic migrations
   - requirements.txt

3. Implement PostgreSQL schema:
   - devices table (id, type, cert_serial, status, etc.)
   - users table (id, email, role, status)
   - health_checks table (device_id, metrics, timestamp)
   - audit_logs table (event_type, device_id, decision, etc.)

4. Implement certificate service:
   - Self-signed CA generation
   - Device certificate issuance
   - PEM serialization
   - 90-day validity

5. Implement device enrollment endpoint:
   - POST /api/v1/devices/enroll
   - Issue certificate
   - Store device in database
   - Return cert bundle

TESTING:
- Unit tests for cert service
- Unit tests for enrollment endpoint
- Mock database with fixtures
- 80%+ coverage

DELIVERABLES:
- Complete FastAPI app structure
- Database models and migrations
- Certificate service
- Enrollment endpoint
- Tests with 80%+ coverage
- README with API documentation
```

### Session 2: Policy Engine

```
Integrate Open Policy Agent for authorization:

OPA SETUP:
1. Create docker-compose.yml:
   - opa service (latest image)
   - Mount policies/ directory
   - Expose port 8181

2. Implement Rego policies:
   - policies/device_access.rego (device health + auth)
   - policies/rbac.rego (role-based access)
   - policies/time_based_access.rego (business hours)

3. Create OPA client:
   - app/services/opa_client.py
   - evaluate_policy() method
   - Error handling
   - Timeout handling (5s)

4. Implement authorization endpoint:
   - POST /api/v1/connections/request
   - Get device + user from database
   - Get latest health check
   - Build OPA input context
   - Query OPA
   - Log to audit_logs
   - Create virtual tunnel if authorized

5. Add health check endpoint:
   - POST /api/v1/health/report
   - Store health metrics
   - Evaluate compliance
   - Update device status

TESTING:
- OPA policy tests (OPA test framework)
- Authorization endpoint tests
- Mock OPA responses
- Test all policy combinations
- 85%+ coverage

DELIVERABLES:
- Complete Rego policy suite
- OPA client library
- Authorization endpoint
- Health check endpoint
- Policy tests
- Integration tests
```

### Session 3: Device Simulator

```
Create device simulator for demo/testing:

SIMULATOR:
1. Create simulator/simulator.py:
   - DeviceSimulator class
   - Support 10-100 devices
   - Use Faker for realistic data

2. Implement core functions:
   - initialize_devices()
   - enroll_all_devices()
   - report_health() (per device)
   - request_connection() (per device)

3. Implement simulation loops:
   - health_reporting_loop() (every 60s)
   - connection_simulation_loop() (every 5s)
   - Run both concurrently with asyncio

4. Generate realistic metrics:
   - CPU: 20-85%
   - Memory: 30-80%
   - Patches current: 85% compliance
   - Antivirus: 90% compliance
   - Disk encryption: 95% compliance

5. Add CLI arguments:
   - --api (default http://localhost:8000)
   - --devices (default 20)

DELIVERABLES:
- Complete simulator script
- requirements.txt
- Usage documentation
- Demo instructions
```

### Session 4: Observability

```
Implement Prometheus metrics and Grafana dashboards:

PROMETHEUS:
1. Add prometheus_client to requirements
2. Create app/services/metrics.py:
   - Define all metrics (devices, connections, authz, health)
   - MetricsService class
   - Update methods for each event

3. Integrate metrics into endpoints:
   - Record enrollment events
   - Record authorization decisions + latency
   - Record health checks
   - Record connection events

4. Add prometheus_fastapi_instrumentator

GRAFANA DASHBOARDS:
1. Create grafana/dashboards/:
   - system_overview.json (devices, connections, success rate)
   - security_dashboard.json (denied requests, unhealthy devices)
   - performance_dashboard.json (latency, throughput)

2. Create datasources config:
   - grafana/datasources/prometheus.yml

DOCKER COMPOSE:
1. Add prometheus service:
   - Mount prometheus.yml
   - Mount alerts.yml
   - Expose 9090

2. Add grafana service:
   - Mount dashboards/
   - Mount datasources/
   - Expose 3000
   - Default password: admin

ALERT RULES:
1. Create prometheus/alerts.yml:
   - HighAuthorizationFailureRate (>10% for 5m)
   - HighUnhealthyDeviceCount (>20% for 10m)
   - SlowAuthorizationLatency (p95 >100ms for 5m)

DELIVERABLES:
- Complete metrics service
- 3 Grafana dashboards
- Prometheus configuration
- Alert rules
- Updated docker-compose.yml
```

---

## Timeline Summary

**Total: 72-80 hours over 8-10 days**

**Days 1-2:** Core API + Database (16h)
**Days 3-4:** Policy Engine Integration (16h)
**Days 5-6:** Device Simulator (16h)
**Days 7-8:** Observability Stack (16h)
**Days 9-10:** Documentation + Demo Video (8-16h)

---

## Success Metrics

- [ ] `docker-compose up` works first time
- [ ] Simulator enrolls 20+ devices
- [ ] Grafana dashboards show live data
- [ ] 85%+ test coverage
- [ ] API documentation complete
- [ ] Demo video recorded
- [ ] README with honest architecture positioning

---

## Why This Works for Portfolio

**Claude Code Can Build This Autonomously:**
- Pure Python/PostgreSQL/HTTP
- No kernel networking
- Standard patterns throughout
- Clear module boundaries
- Well-defined APIs

**You Can Actually Demo It:**
- `docker-compose up`
- `python simulator.py`
- Watch Grafana dashboards update
- Show policy enforcement in real-time

**Honest Positioning:**
- "Production-ready control plane"
- "Data plane architecture provided as reference"
- "Demonstrates zero-trust principles"
- Combined with Sentinel v2, shows breadth

**Defense Contractors Will Be Impressed:**
- Policy-as-code (what they actually use)
- Audit trails (what they actually need)
- Systems thinking (not just coding)
- Honest engineering (mature approach)

This is a portfolio project that **demonstrates understanding** without claiming to reimplement Tailscale. That's exactly what you want.
