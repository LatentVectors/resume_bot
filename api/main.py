"""FastAPI application initialization."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.logging_config import logger

# Initialize FastAPI app
app = FastAPI(
    title="Resume Bot API",
    description="Backend API for Resume Bot",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS configuration for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unhandled exceptions globally."""
    logger.exception("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Include routers
from api.routes import (
    certificates,
    cover_letters,
    education,
    experiences,
    jobs,
    messages,
    responses,
    resumes,
    templates,
    users,
    workflows,
)

app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
app.include_router(experiences.router, prefix="/api/v1", tags=["experiences"])
app.include_router(education.router, prefix="/api/v1", tags=["education"])
app.include_router(certificates.router, prefix="/api/v1", tags=["certificates"])
app.include_router(resumes.router, prefix="/api/v1", tags=["resumes"])
app.include_router(cover_letters.router, prefix="/api/v1", tags=["cover_letters"])
app.include_router(templates.router, prefix="/api/v1", tags=["templates"])
app.include_router(messages.router, prefix="/api/v1", tags=["messages"])
app.include_router(responses.router, prefix="/api/v1", tags=["responses"])
app.include_router(workflows.router, prefix="/api/v1", tags=["workflows"])

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

