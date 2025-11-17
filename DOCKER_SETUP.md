# EdgeMesh Docker Setup

This document describes how to run EdgeMesh using Docker Compose.

## Architecture

The Docker Compose setup includes:

- **OPA (Open Policy Agent)**: Policy engine for authorization decisions
- **Control Plane API**: FastAPI application for device management and authorization
- **PostgreSQL**: Database for persistent storage

## Prerequisites

- Docker 20.10+
- Docker Compose 1.29+

## Quick Start

1. **Set environment variables** (optional):
   ```bash
   export ENROLLMENT_TOKEN_SECRET="your-secret-token"
   ```

2. **Start all services**:
   ```bash
   docker-compose up -d
   ```

3. **Verify services are running**:
   ```bash
   docker-compose ps
   ```

4. **Check OPA policies are loaded**:
   ```bash
   curl http://localhost:8181/v1/policies
   ```

5. **Access Control Plane API**:
   ```bash
   curl http://localhost:8000/healthz
   ```

## Service Endpoints

- **Control Plane API**: http://localhost:8000
  - API Documentation: http://localhost:8000/docs
  - Health Check: http://localhost:8000/healthz

- **OPA Server**: http://localhost:8181
  - Health Check: http://localhost:8181/health
  - Policy API: http://localhost:8181/v1/policies

- **PostgreSQL**: localhost:5432
  - Database: `edgemesh`
  - User: `edgemesh`
  - Password: `edgemesh`

## Testing OPA Policies

Test the device access policy:

```bash
curl -X POST http://localhost:8181/v1/data/edgemesh/authz/allow \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "device": {
        "device_id": "test-device",
        "authenticated": true,
        "status": "active",
        "os_patches_current": true,
        "antivirus_enabled": true,
        "disk_encrypted": true,
        "cpu_usage": 50,
        "memory_usage": 60
      },
      "user": {
        "user_id": "alice@example.com",
        "email": "alice@example.com",
        "role": "developer"
      },
      "service": {
        "name": "database"
      },
      "time": {
        "hour": 14,
        "day_of_week": 3
      }
    }
  }'
```

## Development

### Rebuild images after code changes:
```bash
docker-compose build
docker-compose up -d
```

### View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f control-plane
docker-compose logs -f opa
```

### Run database migrations:
```bash
docker-compose exec control-plane alembic upgrade head
```

## Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

## Troubleshooting

### OPA policies not loading

Check OPA logs:
```bash
docker-compose logs opa
```

Verify policy files are mounted:
```bash
docker-compose exec opa ls -la /policies
```

### Control Plane cannot connect to database

Ensure PostgreSQL is healthy:
```bash
docker-compose ps postgres
```

Check database logs:
```bash
docker-compose logs postgres
```

### Port conflicts

If ports 8000, 8181, or 5432 are already in use, edit `docker-compose.yml` to use different ports.

## Production Considerations

Before deploying to production:

1. **Change default secrets**:
   - Set `ENROLLMENT_TOKEN_SECRET` to a secure value
   - Change PostgreSQL password

2. **Enable TLS**:
   - Configure HTTPS for Control Plane
   - Use secure PostgreSQL connections

3. **Resource limits**:
   - Add CPU and memory limits to services
   - Configure appropriate PostgreSQL settings

4. **Monitoring**:
   - Add Prometheus metrics
   - Configure log aggregation
   - Set up health check alerts

5. **Backup**:
   - Configure PostgreSQL backups
   - Implement disaster recovery plan
