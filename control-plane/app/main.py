"""EdgeMesh Control Plane API"""
from fastapi import FastAPI
from app.api.v1 import enrollment

app = FastAPI(
    title="EdgeMesh Control Plane",
    description="Zero-Trust Access Control",
    version="1.0.0"
)

# Register API v1 routers
app.include_router(enrollment.router, prefix="/api/v1", tags=["enrollment"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {"name": "EdgeMesh Control Plane", "status": "operational"}


@app.get("/healthz")
async def healthz():
    """Health check endpoint"""
    return {"status": "healthy"}
