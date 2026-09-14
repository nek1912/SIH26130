"""FastAPI application for Gujarat Industrial Approval Intelligence."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import applications, approvals, health, projects, workflow

app = FastAPI(
    title="SIH 26130 Gujarat MVP",
    description="Gujarat Industrial Approval Intelligence API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(projects.router, tags=["projects"])
app.include_router(approvals.router, tags=["approvals"])
app.include_router(applications.router, tags=["applications"])
app.include_router(workflow.router, tags=["workflow"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Gujarat Industrial Approval Intelligence API"}