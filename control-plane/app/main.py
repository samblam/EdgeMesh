"""EdgeMesh Control Plane API"""
from fastapi import FastAPI
from app.api.v1 import enrollment, health
from app.middleware.mtls import MTLSMiddleware

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


@app.get("/")
async def root():
    """Root endpoint"""
    return {"name": "EdgeMesh Control Plane", "status": "operational"}


@app.get("/healthz")
async def healthz():
    """Health check endpoint"""
    return {"status": "healthy"}
