# EdgeMesh - Zero-Trust Access Control Platform

EdgeMesh is a modern zero-trust network access (ZTNA) control plane that provides device enrollment, continuous health monitoring, and policy-based access control for distributed edge networks.

## Overview

EdgeMesh implements a zero-trust architecture where every connection request is authenticated, authorized, and continuously validated. It combines mutual TLS authentication, device health attestation, and policy-based access control to ensure secure access to services.

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Devices    │─────▶│ Control Plane│─────▶│   Services   │
│ (mTLS + Health)      │  (FastAPI)   │      │  (Protected) │
└──────────────┘      └──────────────┘      └──────────────┘
                             │
                   ┌─────────┴─────────┐
                   │                   │
              ┌────▼────┐         ┌───▼────┐
              │   OPA   │         │Postgres│
              │ Policies│         │  DB    │
              └────┬────┘         └────────┘
                   │
          ┌────────┴────────┐
          │                 │
     ┌────▼────┐       ┌───▼────┐
     │Prometheus│      │Grafana │
     │ Metrics  │      │Dashboard│
     └──────────┘      └────────┘
```

## Key Features

### 1. Device Enrollment & Authentication
- **mTLS-based enrollment**: Devices receive X.509 certificates during enrollment
- **Certificate management**: Automated certificate issuance and rotation
- **Device inventory**: Track all enrolled devices with metadata

### 2. Continuous Health Monitoring
- **Real-time health reports**: Devices report CPU, memory, disk metrics
- **Compliance checking**: Validate OS patches, antivirus, encryption status
- **Health-based access**: Deny access to unhealthy or non-compliant devices
- **Stale data detection**: Reject authorization if health data is >5 minutes old

### 3. Policy-Based Access Control
- **Open Policy Agent (OPA)**: Flexible, declarative policy engine
- **Context-aware decisions**: Consider device health, user role, time of day
- **Audit logging**: Complete audit trail of all authorization decisions
- **Fine-grained policies**: Control access by service, user role, device state

### 4. Observability & Monitoring
- **Prometheus metrics**: Device counts, connection rates, authorization decisions
- **Grafana dashboards**: Real-time visualization of system health
- **Alert rules**: Proactive alerting for high failure rates, unhealthy devices
- **Performance tracking**: P95 latency monitoring for authorization decisions

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Git

### Running with Docker Compose

1. Clone the repository:
```bash
git clone <repository-url>
cd EdgeMesh
```

2. Start all services:
```bash
docker compose up -d
```

This will start:
- **Control Plane API** on `http://localhost:8000`
- **OPA** on `http://localhost:8181`
- **PostgreSQL** on `localhost:5432`
- **Prometheus** on `http://localhost:9090`
- **Grafana** on `http://localhost:3000`

3. Verify services are running:
```bash
docker compose ps
```

4. Access the Grafana dashboard:
- URL: `http://localhost:3000`
- Username: `admin`
- Password: `admin`
- Navigate to "EdgeMesh - System Overview" dashboard

### API Health Check

```bash
curl http://localhost:8000/healthz
```

Expected response:
```json
{
  "status": "healthy"
}
```

## Core API Workflows

### 1. Enroll a Device

```bash
curl -X POST http://localhost:8000/api/v1/enroll \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "laptop-001",
    "device_type": "laptop",
    "os": "Ubuntu",
    "os_version": "22.04",
    "enrollment_token": "change-me-in-production"
  }'
```

Response includes:
- Device certificate (PEM)
- Private key (PEM)
- CA certificate (PEM)

### 2. Report Device Health

```bash
curl -X POST http://localhost:8000/api/v1/health \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "laptop-001",
    "status": "healthy",
    "metrics": {
      "cpu_usage": 45.0,
      "memory_usage": 60.0,
      "disk_usage": 70.0,
      "os_patches_current": true,
      "antivirus_enabled": true,
      "disk_encrypted": true
    }
  }'
```

### 3. Request Connection Authorization

```bash
curl -X POST http://localhost:8000/api/v1/connections/request \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "laptop-001",
    "user_id": "user@example.com",
    "service_name": "database"
  }'
```

Response (if authorized):
```json
{
  "connection_id": "uuid-here",
  "status": "authorized",
  "service_name": "database",
  "virtual_tunnel": {
    "type": "wireguard",
    "endpoint": "wg://database.edgemesh.local",
    "public_key": "...",
    "allowed_ips": ["10.0.0.0/8"]
  }
}
```

## Development Setup

### Local Development (without Docker)

1. Create virtual environment:
```bash
cd control-plane
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. Run OPA locally (required for policy decisions):
```bash
docker run -d -p 8181:8181 \
  -v $(pwd)/../policies:/policies:ro \
  openpolicyagent/opa:latest-rootless \
  run --server --log-level=debug /policies
```

4. Start the API server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test modules
pytest tests/unit/
pytest tests/integration/

# Run with verbose output
pytest -v

# Run a specific test
pytest tests/integration/test_end_to_end_flow.py::test_complete_enrollment_to_connection_flow
```

Current test coverage: **138 tests**
- **Unit tests**: 132 tests covering models, services, and endpoints
- **Integration tests**: 6 end-to-end workflow tests

### Code Quality

```bash
# Format code
black app/ tests/

# Type checking
mypy app/

# Linting
ruff check app/ tests/
```

## API Documentation

### Interactive API Docs

When the server is running, access:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Core Endpoints

#### Enrollment
- `POST /api/v1/enroll` - Enroll a new device

#### Health Monitoring
- `POST /api/v1/health` - Report device health
- `GET /api/v1/health/{device_id}/latest` - Get latest health report

#### Connection Management
- `POST /api/v1/connections/request` - Request connection authorization
- `GET /api/v1/connections/{connection_id}` - Get connection details
- `DELETE /api/v1/connections/{connection_id}` - Terminate connection
- `GET /api/v1/connections` - List connections (with filters)

#### Metrics
- `GET /metrics` - Prometheus metrics endpoint

## Observability

### Prometheus Metrics

EdgeMesh exposes the following metrics:

- `edgemesh_devices_total` - Total number of enrolled devices
- `edgemesh_unhealthy_devices` - Number of unhealthy devices
- `edgemesh_connections_active` - Active connections by service
- `edgemesh_authorization_decisions_total` - Authorization decisions (allow/deny)
- `edgemesh_authorization_latency_seconds` - P95 authorization latency

### Grafana Dashboards

The "EdgeMesh - System Overview" dashboard provides:
- Total devices and active connections
- Authorization success rate (gauge)
- Healthy vs unhealthy devices (timeseries)
- Connections by service (timeseries)
- Authorization decisions over time

### Alert Rules

Configured alerts in Prometheus:
1. **HighAuthorizationFailureRate**: >10% of requests denied for 5 minutes
2. **HighUnhealthyDeviceCount**: >20% of devices unhealthy for 10 minutes
3. **SlowAuthorizationLatency**: P95 latency >100ms for 5 minutes

## Security Considerations

### Production Deployment

1. **Change default secrets**:
   ```bash
   export ENROLLMENT_TOKEN_SECRET="your-secure-token-here"
   ```

2. **Enable TLS for all services**:
   - Configure TLS certificates for API endpoint
   - Use secure PostgreSQL connections
   - Enable Grafana HTTPS

3. **Restrict network access**:
   - Use firewall rules to limit access
   - Deploy in private VPC/network
   - Use authentication for Grafana/Prometheus

4. **Certificate rotation**:
   - Implement automated certificate renewal
   - Monitor certificate expiration dates
   - Revoke compromised certificates immediately

5. **Database security**:
   - Use strong PostgreSQL passwords
   - Enable SSL for database connections
   - Regular backups and encryption at rest

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `sqlite+aiosqlite:///:memory:` |
| `OPA_URL` | OPA server URL | `http://opa:8181` |
| `ENROLLMENT_TOKEN_SECRET` | Token for device enrollment | `change-me-in-production` |
| `CERT_VALIDITY_DAYS` | Device certificate validity | `90` |
| `HEALTH_CHECK_MAX_AGE_MINUTES` | Max age for health data | `5` |
| `LOG_LEVEL` | Logging level | `INFO` |

### OPA Policies

Policies are located in `/policies`:
- `device_access.rego` - Main authorization policy
- `compliance.rego` - Device compliance rules

To update policies:
1. Edit `.rego` files in `/policies`
2. Restart OPA container: `docker compose restart opa`
3. Verify policy loaded: `curl http://localhost:8181/v1/policies`

## Project Structure

```
EdgeMesh/
├── control-plane/          # FastAPI application
│   ├── app/
│   │   ├── api/v1/        # API endpoints
│   │   ├── models/        # Database models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   ├── middleware/    # Custom middleware
│   │   └── db/           # Database configuration
│   ├── tests/
│   │   ├── unit/         # Unit tests
│   │   └── integration/  # Integration tests
│   ├── Dockerfile        # API container image
│   └── requirements.txt  # Python dependencies
├── policies/             # OPA policy files
├── prometheus/           # Prometheus configuration
│   └── alerts.yml       # Alert rules
├── grafana/             # Grafana configuration
│   ├── dashboards/      # Dashboard definitions
│   └── datasources/     # Data source config
├── docker-compose.yml   # Multi-service orchestration
└── README.md           # This file
```

## Troubleshooting

### Common Issues

**1. Device enrollment fails with 401 Unauthorized**
- Verify `ENROLLMENT_TOKEN_SECRET` matches in request and server
- Check API logs: `docker compose logs api`

**2. Connection requests denied unexpectedly**
- Verify device health data is recent (<5 minutes)
- Check OPA policy evaluation: `docker compose logs opa`
- Ensure device status is "active"

**3. Metrics not appearing in Grafana**
- Verify Prometheus is scraping API: `http://localhost:9090/targets`
- Check datasource configuration in Grafana
- Restart Grafana: `docker compose restart grafana`

**4. Tests failing locally**
- Ensure OPA is running on port 8181
- Check database migrations are applied
- Verify Python version is 3.11+

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f opa

# Last 100 lines
docker compose logs --tail=100 api
```

## Contributing

### Development Workflow

1. Create feature branch
2. Write tests first (TDD)
3. Implement feature
4. Ensure all tests pass: `pytest`
5. Format code: `black app/ tests/`
6. Commit with descriptive message
7. Create pull request

### Testing Guidelines

- Maintain >90% code coverage
- Write unit tests for all business logic
- Add integration tests for end-to-end workflows
- Use fixtures for common test setup

## License

[Add your license here]

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [documentation-url]
- Email: [support-email]

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Open Policy Agent](https://www.openpolicyagent.org/) - Policy engine
- [PostgreSQL](https://www.postgresql.org/) - Database
- [Prometheus](https://prometheus.io/) - Metrics and monitoring
- [Grafana](https://grafana.com/) - Visualization
