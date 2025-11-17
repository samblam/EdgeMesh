"""EdgeMesh Control Plane API"""
from fastapi import FastAPI

app = FastAPI(
    title="EdgeMesh Control Plane",
    description="Zero-Trust Access Control",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"name": "EdgeMesh Control Plane", "status": "operational"}


@app.get("/healthz")
async def healthz():
    """Health check endpoint"""
    return {"status": "healthy"}
