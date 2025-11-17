# Kubernetes Reference Architecture

This directory contains reference Kubernetes manifests for deploying EdgeMesh to production.

**Note:** These are reference examples for production deployment. The primary deployment method is Docker Compose (see `../docker-compose.yml`). These manifests demonstrate how EdgeMesh could be deployed to Kubernetes but are not required for the core implementation.

## Files

- `deployment.yaml` - API deployment, service, and ingress
- `postgres.yaml` - PostgreSQL StatefulSet with persistent storage
- `opa.yaml` - Open Policy Agent deployment
- `monitoring.yaml` - Prometheus and Grafana deployment
- `secrets.yaml.example` - Example secrets (must be customized)
- `namespace.yaml` - EdgeMesh namespace
- `values.yaml` - Helm chart values reference

## Quick Deploy

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Create secrets (customize first!)
cp secrets.yaml.example secrets.yaml
# Edit secrets.yaml with real values
kubectl apply -f secrets.yaml

# Deploy PostgreSQL
kubectl apply -f postgres.yaml

# Deploy OPA
kubectl apply -f opa.yaml

# Deploy Control Plane API
kubectl apply -f deployment.yaml

# Deploy Monitoring (optional)
kubectl apply -f monitoring.yaml
```

## Prerequisites

- Kubernetes 1.25+
- cert-manager (for TLS certificates)
- nginx-ingress-controller
- StorageClass with dynamic provisioning
- kubectl configured with cluster access

## Production Considerations

### High Availability

The API deployment uses:
- 3 replicas with pod anti-affinity
- RollingUpdate strategy (maxSurge: 1, maxUnavailable: 0)
- Health checks (liveness and readiness)

### Security

- Non-root containers
- Read-only root filesystem
- Dropped capabilities
- Network policies (add `networkpolicy.yaml`)
- Secrets for sensitive data

### Scaling

Enable HPA (Horizontal Pod Autoscaler):
```bash
kubectl autoscale deployment edgemesh-control-plane \
  --cpu-percent=80 \
  --min=3 \
  --max=10 \
  -n edgemesh
```

### Database

For production:
- Use managed PostgreSQL (AWS RDS, GCP Cloud SQL, Azure Database)
- Or deploy with replication (see Bitnami PostgreSQL Helm chart)
- Enable automated backups
- Use connection pooling (PgBouncer)

### Monitoring

- Prometheus ServiceMonitor for automatic scraping
- Grafana dashboards pre-configured
- Alert rules for critical metrics

## Helm Chart (Alternative)

Use the reference Helm values:

```bash
helm create edgemesh
cp values.yaml edgemesh/values.yaml
helm install edgemesh ./edgemesh -n edgemesh
```

## Troubleshooting

**Pods not starting:**
```bash
kubectl get pods -n edgemesh
kubectl describe pod <pod-name> -n edgemesh
kubectl logs <pod-name> -n edgemesh
```

**Database connectivity:**
```bash
kubectl exec -it <api-pod> -n edgemesh -- env | grep DATABASE
kubectl exec -it postgres-0 -n edgemesh -- psql -U postgres -d edgemesh -c '\l'
```

**Ingress issues:**
```bash
kubectl get ingress -n edgemesh
kubectl describe ingress edgemesh-ingress -n edgemesh
```

## Architecture Decisions

This is a **reference architecture**. The core EdgeMesh implementation focuses on:
- ✅ Control plane logic (policy enforcement, device registry, audit)
- ✅ Docker Compose for local development and demos
- ✅ Production-ready API code

These Kubernetes manifests demonstrate:
- How to deploy to production
- High availability patterns
- Security best practices
- Cloud-native architecture

For actual production deployment, consider:
- Using managed services (RDS, Cloud SQL, etc.)
- Implementing GitOps (ArgoCD, Flux)
- Adding observability (Jaeger, Loki)
- Implementing mTLS mesh (Istio, Linkerd)
