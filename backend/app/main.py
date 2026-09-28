"""FastAPI application for Gujarat Industrial Approval Intelligence."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    applications,
    approvals,
    consistency,
    documents,
    extraction,
    handoffs,
    health,
    incentives,
    orchestration,
    projects,
    regulatory,
    workflow,
)
from app.core.config import get_settings, parse_cors_origins

app = FastAPI(
    title="SIH 26130 Gujarat MVP",
    description="Gujarat Industrial Approval Intelligence API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(get_settings().cors_allow_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(projects.router, tags=["projects"])
app.include_router(approvals.router, tags=["approvals"])
app.include_router(applications.router, tags=["applications"])
app.include_router(documents.router, tags=["documents"])
app.include_router(handoffs.router, tags=["handoffs"])
app.include_router(extraction.router, tags=["extraction"])
app.include_router(workflow.router, tags=["workflow"])
app.include_router(consistency.router, tags=["consistency"])
app.include_router(orchestration.router, tags=["orchestration"])
app.include_router(regulatory.router, tags=["regulatory"])
app.include_router(incentives.router, tags=["incentives"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Gujarat Industrial Approval Intelligence API"}