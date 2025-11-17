"""EdgeMesh Control Plane API"""
from fastapi import FastAPI, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.api.v1 import enrollment, health, connections
from app.middleware.mtls import MTLSMiddleware
# Import metrics to register them with Prometheus
import app.services.metrics  # noqa: F401

app = FastAPI(
    title="EdgeMesh Control Plane",
    description="Zero-Trust Access Control",
    version="1.0.0"
)

# Add mTLS authentication middleware
app.add_middleware(MTLSMiddleware)

# Register API v1 routers
app.include_router(enrollment.router, prefix="/api/v1", tags=["enrollment"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(connections.router, prefix="/api/v1", tags=["connections"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {"name": "EdgeMesh Control Plane", "status": "operational"}


@app.get("/healthz")
async def healthz():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
