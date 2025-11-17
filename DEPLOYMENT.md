# EdgeMesh Production Deployment Guide

This guide covers deploying EdgeMesh to production environments with security, reliability, and scalability best practices.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Infrastructure Setup](#infrastructure-setup)
- [Service Configuration](#service-configuration)
- [Security Hardening](#security-hardening)
- [Monitoring & Alerting](#monitoring--alerting)
- [Backup & Recovery](#backup--recovery)
- [Scaling Considerations](#scaling-considerations)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Infrastructure

- **Compute**: 4 CPU cores, 8GB RAM minimum (16GB recommended)
- **Storage**: 100GB SSD for database and metrics
- **Network**: Static IP address or load balancer
- **Operating System**: Ubuntu 22.04 LTS or similar
- **Docker**: Docker Engine 24.0+ and Docker Compose 2.20+
- **TLS Certificates**: Valid SSL/TLS certificates for HTTPS

### Required Access

- SSH access to production servers
- DNS management for domain configuration
- Secret management system (e.g., HashiCorp Vault, AWS Secrets Manager)
- Container registry access (if using private images)

## Pre-Deployment Checklist

### Configuration

- [ ] Generate strong secrets for all services
- [ ] Configure production database credentials
- [ ] Obtain and configure TLS certificates
- [ ] Set up DNS records for service endpoints
- [ ] Configure firewall rules
- [ ] Set up backup strategy
- [ ] Configure alerting destinations

### Security

- [ ] Review and update OPA policies
- [ ] Enable database encryption at rest
- [ ] Configure network segmentation
- [ ] Set up intrusion detection
- [ ] Enable audit logging
- [ ] Review and minimize exposed ports

### Monitoring

- [ ] Configure Prometheus retention
- [ ] Set up Grafana authentication
- [ ] Configure alert notification channels
- [ ] Set up log aggregation
- [ ] Configure metric retention policies

## Infrastructure Setup

### 1. Server Provisioning

For production deployments, use separate servers for different components:

```
┌─────────────────────────────────────┐
│   Load Balancer (Optional)          │
│   nginx/HAProxy                      │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼───────┐      ┌─────▼─────┐
│ API Server │      │ API Server│  (Multiple instances)
│ + OPA      │      │ + OPA     │
└───┬────────┘      └─────┬─────┘
    │                     │
    └──────────┬──────────┘
               │
    ┌──────────▼────────────┐
    │  PostgreSQL (Primary)  │
    │  + Read Replicas       │
    └────────────────────────┘

    ┌────────────────────────┐
    │  Prometheus + Grafana  │
    │  (Monitoring Server)   │
    └────────────────────────┘
```

### 2. Network Configuration

**Firewall Rules**:

```bash
# Allow HTTP/HTTPS from internet
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow API from trusted networks only
sudo ufw allow from 10.0.0.0/8 to any port 8000

# Allow PostgreSQL from API servers only
sudo ufw allow from 10.0.1.0/24 to any port 5432

# Allow Prometheus/Grafana from monitoring network
sudo ufw allow from 10.0.2.0/24 to any port 9090
sudo ufw allow from 10.0.2.0/24 to any port 3000

# Enable firewall
sudo ufw enable
```

### 3. DNS Configuration

Configure DNS records for services:

```
api.edgemesh.example.com      A      <API_SERVER_IP>
prometheus.edgemesh.example.com A    <MONITORING_SERVER_IP>
grafana.edgemesh.example.com   A    <MONITORING_SERVER_IP>
```

## Service Configuration

### 1. Environment Variables

Create a `.env.production` file:

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://edgemesh:STRONG_PASSWORD_HERE@postgres:5432/edgemesh
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# OPA Configuration
OPA_URL=http://opa:8181
OPA_TIMEOUT=5

# Security
ENROLLMENT_TOKEN_SECRET=GENERATE_STRONG_SECRET_HERE
CERT_VALIDITY_DAYS=90
CA_CERT_VALIDITY_DAYS=3650

# Rate Limiting
RATE_LIMIT_ENROLLMENTS=5/minute
RATE_LIMIT_CONNECTIONS=100/minute
RATE_LIMIT_HEALTH=10/minute

# Health Check
HEALTH_CHECK_MAX_AGE_MINUTES=5

# Observability
LOG_LEVEL=INFO
METRICS_PORT=9090

# API Configuration
API_TITLE=EdgeMesh Control Plane
API_VERSION=1.0.0
CORS_ORIGINS=[]  # Restrict CORS in production
```

**Generate Secrets**:

```bash
# Generate enrollment token secret (256-bit)
openssl rand -hex 32

# Generate database password
openssl rand -base64 32
```

### 2. PostgreSQL Production Configuration

Update `docker-compose.prod.yml`:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=edgemesh
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=edgemesh
      # Production settings
      - POSTGRES_INITDB_ARGS=--data-checksums
    command:
      - "postgres"
      - "-c"
      - "max_connections=200"
      - "-c"
      - "shared_buffers=256MB"
      - "-c"
      - "effective_cache_size=1GB"
      - "-c"
      - "maintenance_work_mem=64MB"
      - "-c"
      - "checkpoint_completion_target=0.9"
      - "-c"
      - "wal_buffers=16MB"
      - "-c"
      - "default_statistics_target=100"
      - "-c"
      - "random_page_cost=1.1"
      - "-c"
      - "effective_io_concurrency=200"
      - "-c"
      - "work_mem=2MB"
      - "-c"
      - "min_wal_size=1GB"
      - "-c"
      - "max_wal_size=4GB"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped
```

### 3. TLS/HTTPS Configuration

Use nginx as reverse proxy with TLS:

```nginx
# /etc/nginx/sites-available/edgemesh
upstream edgemesh_api {
    least_conn;
    server 10.0.1.10:8000;
    server 10.0.1.11:8000;
    server 10.0.1.12:8000;
}

server {
    listen 443 ssl http2;
    server_name api.edgemesh.example.com;

    ssl_certificate /etc/nginx/ssl/edgemesh.crt;
    ssl_certificate_key /etc/nginx/ssl/edgemesh.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API endpoints
    location / {
        proxy_pass http://edgemesh_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Rate limiting
        limit_req zone=api_limit burst=20 nodelay;
    }

    # Metrics endpoint (restrict access)
    location /metrics {
        allow 10.0.2.0/24;  # Monitoring network only
        deny all;
        proxy_pass http://edgemesh_api;
    }
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name api.edgemesh.example.com;
    return 301 https://$server_name$request_uri;
}

# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
```

## Security Hardening

### 1. Container Security

**Run containers as non-root**:

Update Dockerfile:

```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r edgemesh && useradd -r -g edgemesh edgemesh

# ... install dependencies ...

# Switch to non-root user
USER edgemesh

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Scan images for vulnerabilities**:

```bash
# Using Trivy
trivy image edgemesh/control-plane:latest

# Using Snyk
snyk container test edgemesh/control-plane:latest
```

### 2. Database Security

**Enable SSL/TLS for PostgreSQL**:

```yaml
# docker-compose.prod.yml
postgres:
  command:
    - "postgres"
    - "-c"
    - "ssl=on"
    - "-c"
    - "ssl_cert_file=/etc/ssl/certs/server.crt"
    - "-c"
    - "ssl_key_file=/etc/ssl/private/server.key"
  volumes:
    - ./ssl/server.crt:/etc/ssl/certs/server.crt:ro
    - ./ssl/server.key:/etc/ssl/private/server.key:ro
```

**Update connection string**:

```bash
DATABASE_URL=postgresql+asyncpg://edgemesh:PASSWORD@postgres:5432/edgemesh?ssl=require
```

### 3. OPA Policy Security

**Restrict policy updates**:

```yaml
opa:
  command:
    - "run"
    - "--server"
    - "--log-level=info"
    - "--authentication=token"
    - "--authorization=basic"
    - "/policies"
  environment:
    - OPA_BEARER_TOKEN=${OPA_ADMIN_TOKEN}
```

### 4. Secret Management

Use external secret management:

```bash
# Using AWS Secrets Manager
aws secretsmanager create-secret \
  --name edgemesh/enrollment-token \
  --secret-string "$(openssl rand -hex 32)"

# Using HashiCorp Vault
vault kv put secret/edgemesh/config \
  enrollment_token="$(openssl rand -hex 32)" \
  db_password="$(openssl rand -base64 32)"
```

## Monitoring & Alerting

### 1. Prometheus Configuration

**Production prometheus.yml**:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'production'
    environment: 'prod'

# Remote write for long-term storage
remote_write:
  - url: https://metrics.example.com/api/v1/write
    basic_auth:
      username: ${REMOTE_WRITE_USER}
      password: ${REMOTE_WRITE_PASS}

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

rule_files:
  - /etc/prometheus/alerts.yml
  - /etc/prometheus/recording_rules.yml

scrape_configs:
  - job_name: 'edgemesh-api'
    static_configs:
      - targets:
          - api-1:8000
          - api-2:8000
          - api-3:8000
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
```

### 2. Alertmanager Configuration

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: '${SLACK_WEBHOOK_URL}'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true
    - match:
        severity: warning
      receiver: 'slack'

receivers:
  - name: 'default'
    email_configs:
      - to: 'ops@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: '${SMTP_USER}'
        auth_password: '${SMTP_PASS}'

  - name: 'slack'
    slack_configs:
      - channel: '#edgemesh-alerts'
        title: 'EdgeMesh Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_SERVICE_KEY}'
        description: '{{ .GroupLabels.alertname }}'
```

### 3. Grafana Production Setup

```yaml
grafana:
  environment:
    # Authentication
    - GF_AUTH_ANONYMOUS_ENABLED=false
    - GF_AUTH_GENERIC_OAUTH_ENABLED=true
    - GF_AUTH_GENERIC_OAUTH_NAME=OAuth
    - GF_AUTH_GENERIC_OAUTH_CLIENT_ID=${OAUTH_CLIENT_ID}
    - GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET=${OAUTH_CLIENT_SECRET}
    - GF_AUTH_GENERIC_OAUTH_SCOPES=openid profile email
    - GF_AUTH_GENERIC_OAUTH_AUTH_URL=${OAUTH_AUTH_URL}
    - GF_AUTH_GENERIC_OAUTH_TOKEN_URL=${OAUTH_TOKEN_URL}

    # Security
    - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
    - GF_SECURITY_SECRET_KEY=${GRAFANA_SECRET_KEY}
    - GF_SECURITY_COOKIE_SECURE=true
    - GF_SECURITY_STRICT_TRANSPORT_SECURITY=true

    # Server
    - GF_SERVER_PROTOCOL=https
    - GF_SERVER_CERT_FILE=/etc/grafana/ssl/grafana.crt
    - GF_SERVER_CERT_KEY=/etc/grafana/ssl/grafana.key
```

## Backup & Recovery

### 1. Database Backups

**Automated backup script**:

```bash
#!/bin/bash
# /opt/edgemesh/backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="edgemesh_${DATE}.sql.gz"

# Create backup
docker exec edgemesh-postgres pg_dump -U edgemesh -d edgemesh | gzip > "${BACKUP_DIR}/${BACKUP_FILE}"

# Upload to S3
aws s3 cp "${BACKUP_DIR}/${BACKUP_FILE}" s3://edgemesh-backups/db/

# Retain last 30 days locally
find "${BACKUP_DIR}" -name "edgemesh_*.sql.gz" -mtime +30 -delete

# Verify backup
if [ $? -eq 0 ]; then
  echo "Backup successful: ${BACKUP_FILE}"
else
  echo "Backup failed!" | mail -s "EdgeMesh Backup Failed" ops@example.com
fi
```

**Cron schedule**:

```bash
# Daily at 2 AM
0 2 * * * /opt/edgemesh/backup.sh

# Weekly full backup
0 3 * * 0 /opt/edgemesh/backup_full.sh
```

### 2. Disaster Recovery Procedure

**Restore from backup**:

```bash
# Stop services
docker compose down

# Restore database
gunzip -c /backups/edgemesh_20250101_020000.sql.gz | \
  docker exec -i edgemesh-postgres psql -U edgemesh -d edgemesh

# Restart services
docker compose up -d

# Verify health
curl https://api.edgemesh.example.com/healthz
```

## Scaling Considerations

### 1. Horizontal Scaling

**API Servers**:

- Run multiple API instances behind load balancer
- Ensure stateless operation (no local file storage)
- Use connection pooling for database
- Consider container orchestration (Kubernetes)

**Database Scaling**:

```yaml
# Read replicas for scaling reads
postgres-replica:
  image: postgres:15-alpine
  environment:
    - POSTGRES_PRIMARY_HOST=postgres
    - POSTGRES_REPLICATION_MODE=slave
  command:
    - "postgres"
    - "-c"
    - "hot_standby=on"
```

### 2. Vertical Scaling

**Resource limits**:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

  postgres:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
```

### 3. Performance Optimization

**Database connection pooling**:

```python
# app/db/session.py
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,              # Connections to maintain
    max_overflow=10,           # Extra connections allowed
    pool_pre_ping=True,        # Verify connections
    pool_recycle=3600,         # Recycle connections hourly
    echo=False
)
```

**API optimization**:

```bash
# Increase worker processes
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --loop uvloop \
  --http httptools
```

## Troubleshooting

### Common Production Issues

**1. High database connections**:

```sql
-- Check active connections
SELECT count(*), state FROM pg_stat_activity GROUP BY state;

-- Kill idle connections
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle' AND state_change < NOW() - INTERVAL '10 minutes';
```

**2. Memory issues**:

```bash
# Check container memory usage
docker stats

# Increase memory limits in docker-compose.yml
mem_limit: 4g
memswap_limit: 4g
```

**3. Slow authorization decisions**:

```bash
# Check OPA logs
docker logs edgemesh-opa --tail=100

# Monitor authorization latency
curl http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(edgemesh_authorization_latency_seconds_bucket[5m]))
```

### Health Checks

```bash
# API health
curl -f https://api.edgemesh.example.com/healthz || echo "API down"

# Database health
docker exec edgemesh-postgres pg_isready -U edgemesh

# OPA health
curl http://localhost:8181/health

# Prometheus health
curl http://localhost:9090/-/healthy

# Grafana health
curl http://localhost:3000/api/health
```

## Maintenance

### Update Procedure

1. **Backup everything**
2. **Test in staging**
3. **Schedule maintenance window**
4. **Pull new images**:
   ```bash
   docker compose pull
   ```
5. **Rolling update**:
   ```bash
   # Update one API instance at a time
   docker compose up -d --no-deps --scale api=3 api
   ```
6. **Verify health**
7. **Monitor metrics for issues**
8. **Rollback if needed**:
   ```bash
   docker compose down
   docker compose up -d --force-recreate
   ```

### Log Rotation

```bash
# /etc/logrotate.d/docker-containers
/var/lib/docker/containers/*/*.log {
  daily
  rotate 7
  compress
  delaycompress
  notifempty
  copytruncate
  missingok
}
```

## Compliance & Auditing

- Enable audit logging for all API calls
- Retain logs for compliance period (typically 90 days+)
- Implement log aggregation (ELK, Splunk, etc.)
- Regular security audits
- Penetration testing
- Compliance scanning (SOC 2, HIPAA, etc.)

## Support

For production issues:
- Emergency: [on-call phone]
- Email: ops@example.com
- Slack: #edgemesh-production
- Runbook: [runbook-url]
