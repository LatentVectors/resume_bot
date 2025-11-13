# FastAPI Backend Migration Spec

## Overview

This sprint focuses on migrating the backend logic from the current Streamlit monolith to a FastAPI-based REST API. This is the first step in a larger architectural migration that will eventually include:

1. **Current Sprint**: FastAPI backend with SQLite database
2. **Future**: Migration to Supabase database
3. **Future**: Next.js frontend replacing Streamlit

The goal is to achieve clean separation between frontend and backend concerns, with all business logic, LLM workflows, database operations, and API keys moved behind secure API endpoints.

## Problem Statement

The current application architecture mixes frontend and backend concerns throughout the codebase:

1. **Mixed Responsibilities**: The `app/services/` directory contains both frontend-facing logic and backend operations (database calls, LLM workflows)
2. **Security Issues**: Sensitive API keys and LLM operations are exposed in the frontend layer
3. **Tight Coupling**: Direct database access from UI code makes it difficult to scale or change data stores
4. **No API Layer**: External clients cannot integrate with the application
5. **Testing Challenges**: Business logic is tightly coupled to Streamlit UI components

## Current Architecture

### Directory Structure

```
resume/
├── app/                          # Streamlit frontend (mixed concerns)
│   ├── main.py                   # Streamlit entry point
│   ├── pages/                    # UI pages
│   ├── components/               # UI components
│   ├── dialog/                   # UI dialogs
│   └── services/                 # MIXED: frontend + backend logic
│       ├── job_service.py
│       ├── resume_service.py
│       ├── cover_letter_service.py
│       ├── experience_service.py
│       ├── education_service.py
│       ├── certificate_service.py
│       ├── user_service.py
│       ├── template_service.py
│       ├── chat_message_service.py
│       ├── render_pdf.py
│       └── job_intake_service/
│           ├── service.py
│           └── workflows/         # Backend LLM workflows
│               ├── gap_analysis.py
│               ├── stakeholder_analysis.py
│               ├── experience_extraction.py
│               └── resume_refinement.py
├── src/                          # Backend logic (should move to API)
│   ├── agents/                   # LangGraph agents
│   │   └── main/                 # Resume generation agent
│   ├── core/                     # Core utilities
│   │   ├── prompts/             # Prompt management
│   │   ├── models.py            # LLM model definitions
│   │   └── get_model.py         # LLM initialization
│   ├── features/                 # Feature modules
│   │   ├── resume/
│   │   ├── cover_letter/
│   │   └── jobs/
│   ├── database.py              # Database models and manager
│   └── config.py                # Configuration
└── run.py                        # Application runner
```

### Key Components to Migrate

#### 1. LLM Workflows (MUST move to backend)

Located in `app/services/job_intake_service/workflows/`:

- **Gap Analysis**: Analyzes job-experience fit
- **Stakeholder Analysis**: Identifies key stakeholders in job description
- **Experience Extraction**: Extracts experience updates from conversation
- **Resume Refinement**: Interactive chat for resume improvements

#### 2. LangGraph Agent (MUST move to backend)

Located in `src/agents/main/`:

- Resume generation agent with parallel node execution
- Nodes: generate_summary, generate_experience, generate_skills
- Uses structured outputs and LLM calls

#### 3. Database Operations (MUST be behind API)

All database operations currently in services:

- Direct SQLModel/SQLAlchemy queries
- `db_manager` calls
- Transaction management

#### 4. PDF Rendering (SHOULD move to backend)

Located in `app/services/render_pdf.py`:

- Resume PDF generation
- Cover letter PDF generation
- Uses WeasyPrint

#### 5. Business Logic in Services

Services that mix frontend and backend concerns:

- `JobService`: Job CRUD, status management
- `ResumeService`: Version management, generation
- `CoverLetterService`: Version management, generation
- `ExperienceService`: Experience CRUD, proposal management
- `EducationService`, `CertificateService`: Profile CRUD
- `UserService`: User management
- `ChatMessageService`: Message persistence

## Target Architecture

### New Directory Structure

```
resume/
├── api/                          # NEW: FastAPI backend
│   ├── main.py                   # FastAPI app initialization
│   ├── config.py                 # API configuration
│   ├── dependencies.py           # Dependency injection
│   ├── middleware.py             # Middleware (CORS, logging, etc.)
│   ├── routes/                   # API route handlers
│   │   ├── __init__.py
│   │   ├── users.py
│   │   ├── jobs.py
│   │   ├── experiences.py
│   │   ├── education.py
│   │   ├── certificates.py
│   │   ├── resumes.py
│   │   ├── cover_letters.py
│   │   ├── templates.py
│   │   ├── messages.py
│   │   ├── responses.py
│   │   └── workflows.py          # LLM workflow endpoints
│   ├── services/                 # Backend services (moved from app/)
│   │   ├── __init__.py
│   │   ├── job_service.py
│   │   ├── resume_service.py
│   │   ├── cover_letter_service.py
│   │   ├── experience_service.py
│   │   ├── education_service.py
│   │   ├── certificate_service.py
│   │   ├── user_service.py
│   │   ├── template_service.py
│   │   ├── chat_message_service.py
│   │   ├── pdf_service.py        # Renamed from render_pdf
│   │   └── job_intake_service/
│   │       ├── __init__.py
│   │       ├── service.py
│   │       └── workflows/
│   │           ├── gap_analysis.py
│   │           ├── stakeholder_analysis.py
│   │           ├── experience_extraction.py
│   │           └── resume_refinement.py
│   ├── schemas/                  # Pydantic request/response models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── job.py
│   │   ├── experience.py
│   │   ├── education.py
│   │   ├── certificate.py
│   │   ├── resume.py
│   │   ├── cover_letter.py
│   │   ├── template.py
│   │   ├── message.py
│   │   ├── response.py
│   │   └── workflow.py
│   └── utils/                    # API utilities
│       ├── __init__.py
│       └── errors.py             # Error handling
├── app/                          # Streamlit frontend (cleaned up)
│   ├── main.py
│   ├── pages/                    # UI pages
│   ├── components/               # UI components
│   ├── dialog/                   # UI dialogs
│   ├── api_client/               # NEW: API client for backend calls
│   │   ├── __init__.py
│   │   ├── client.py             # Base HTTP client
│   │   └── endpoints/            # Endpoint-specific clients
│   │       ├── users.py
│   │       ├── jobs.py
│   │       ├── experiences.py
│   │       ├── resumes.py
│   │       └── workflows.py
│   ├── shared/                   # Shared frontend utilities
│   │   ├── diff_utils.py
│   │   ├── filenames.py
│   │   └── formatters.py
│   └── utils/
├── src/                          # Shared backend logic
│   ├── agents/                   # Stays here (used by API)
│   ├── core/                     # Stays here (used by API)
│   ├── features/                 # Stays here (used by API)
│   ├── database.py              # Stays here (used by API)
│   ├── config.py                # Stays here (shared config)
│   ├── exceptions.py            # NEW: Shared exceptions (moved from app/exceptions.py)
│   └── logging_config.py        # Stays here (shared logging)
└── run.py                        # UPDATED: Runs both API and Streamlit
```

## API Design

### API Endpoints

#### User Management

```
GET    /api/v1/users                # List users
GET    /api/v1/users/{id}           # Get user
POST   /api/v1/users                # Create user
PATCH  /api/v1/users/{id}           # Update user
DELETE /api/v1/users/{id}           # Delete user
GET    /api/v1/users/current        # Get current user (for single-user mode)
```

#### Jobs

```
GET    /api/v1/jobs                          # List jobs (with filters)
GET    /api/v1/jobs/{id}                     # Get job
POST   /api/v1/jobs                          # Create job
PATCH  /api/v1/jobs/{id}                     # Update job
DELETE /api/v1/jobs/{id}                     # Delete job
PATCH  /api/v1/jobs/{id}/favorite            # Toggle favorite
PATCH  /api/v1/jobs/{id}/status              # Update status
POST   /api/v1/jobs/{id}/apply               # Mark as applied
GET    /api/v1/jobs/{id}/intake-session      # Get intake session
POST   /api/v1/jobs/{id}/intake-session      # Create intake session
PATCH  /api/v1/jobs/{id}/intake-session      # Update intake session
```

#### Experiences

```
GET    /api/v1/experiences                   # List experiences
GET    /api/v1/experiences/{id}              # Get experience
POST   /api/v1/experiences                   # Create experience
PATCH  /api/v1/experiences/{id}              # Update experience
DELETE /api/v1/experiences/{id}              # Delete experience
GET    /api/v1/experiences/{id}/achievements # List achievements
POST   /api/v1/experiences/{id}/achievements # Create achievement
PATCH  /api/v1/achievements/{id}             # Update achievement
DELETE /api/v1/achievements/{id}             # Delete achievement
GET    /api/v1/experiences/{id}/proposals    # List proposals
POST   /api/v1/experiences/proposals         # Create proposal
PATCH  /api/v1/proposals/{id}/accept         # Accept proposal
PATCH  /api/v1/proposals/{id}/reject         # Reject proposal
DELETE /api/v1/proposals/{id}                # Delete proposal
```

#### Education & Certificates

```
GET    /api/v1/education                     # List education
POST   /api/v1/education                     # Create education
PATCH  /api/v1/education/{id}                # Update education
DELETE /api/v1/education/{id}                # Delete education
GET    /api/v1/certificates                  # List certificates
POST   /api/v1/certificates                  # Create certificate
PATCH  /api/v1/certificates/{id}             # Update certificate
DELETE /api/v1/certificates/{id}             # Delete certificate
```

#### Resumes

```
GET    /api/v1/jobs/{job_id}/resumes                    # List resume versions
GET    /api/v1/jobs/{job_id}/resumes/current           # Get current resume
GET    /api/v1/jobs/{job_id}/resumes/{version_id}      # Get specific version
POST   /api/v1/jobs/{job_id}/resumes                   # Create resume version
PATCH  /api/v1/jobs/{job_id}/resumes/{version_id}/pin  # Pin version
GET    /api/v1/jobs/{job_id}/resumes/{version_id}/pdf  # Download PDF
POST   /api/v1/jobs/{job_id}/resumes/{version_id}/preview  # Preview PDF
GET    /api/v1/jobs/{job_id}/resumes/compare           # Compare versions
```

#### Cover Letters

```
GET    /api/v1/jobs/{job_id}/cover-letters                    # List versions
GET    /api/v1/jobs/{job_id}/cover-letters/current           # Get current
GET    /api/v1/jobs/{job_id}/cover-letters/{version_id}      # Get version
POST   /api/v1/jobs/{job_id}/cover-letters                   # Create version
PATCH  /api/v1/jobs/{job_id}/cover-letters/{version_id}/pin  # Pin version
GET    /api/v1/jobs/{job_id}/cover-letters/{version_id}/pdf  # Download PDF
```

#### Templates

```
GET    /api/v1/templates/resumes              # List resume templates
GET    /api/v1/templates/resumes/{id}         # Get resume template
GET    /api/v1/templates/cover-letters        # List cover letter templates
GET    /api/v1/templates/cover-letters/{id}   # Get cover letter template
```

#### Chat Messages

```
GET    /api/v1/jobs/{job_id}/messages         # List messages
POST   /api/v1/jobs/{job_id}/messages         # Create message
DELETE /api/v1/jobs/{job_id}/messages/{id}    # Delete message
```

#### Interview Responses

```
GET    /api/v1/responses                      # List responses
GET    /api/v1/responses/{id}                 # Get response
POST   /api/v1/responses                      # Create response
PATCH  /api/v1/responses/{id}                 # Update response
DELETE /api/v1/responses/{id}                 # Delete response
```

#### LLM Workflows (Backend-only)

```
POST   /api/v1/workflows/gap-analysis                # Run gap analysis
POST   /api/v1/workflows/stakeholder-analysis        # Run stakeholder analysis
POST   /api/v1/workflows/experience-extraction       # Extract experience updates
POST   /api/v1/workflows/resume-chat                 # Resume refinement chat
POST   /api/v1/workflows/resume-generation           # Generate resume (LangGraph agent)
```

### Request/Response Schemas

All endpoints will use Pydantic models for request validation and response serialization. These schemas will be defined in `api/schemas/` and will mirror or extend the SQLModel definitions in `src/database.py`.

#### Example Schema Structure

All schemas use Pydantic models for strong typing. The API client will use these same models to ensure type safety end-to-end.

```python
# api/schemas/job.py
from pydantic import BaseModel, Field
from datetime import datetime

class JobCreate(BaseModel):
    """Schema for creating a job."""
    title: str = Field(..., min_length=1, description="Job title")
    company: str = Field(..., min_length=1, description="Company name")
    description: str = Field(..., min_length=1, description="Job description")
    favorite: bool = Field(default=False, description="Mark as favorite")

class JobUpdate(BaseModel):
    """Schema for updating a job."""
    title: str | None = Field(None, min_length=1, description="Job title")
    company: str | None = Field(None, min_length=1, description="Company name")
    description: str | None = Field(None, min_length=1, description="Job description")
    favorite: bool | None = Field(None, description="Mark as favorite")
    status: str | None = Field(None, description="Job status")

class JobResponse(BaseModel):
    """Schema for job response - used by both API and frontend."""
    id: int
    user_id: int
    job_title: str
    company_name: str
    job_description: str
    is_favorite: bool
    status: str
    has_resume: bool
    has_cover_letter: bool
    created_at: datetime
    updated_at: datetime
    applied_at: datetime | None = None

    class Config:
        from_attributes = True  # Allows conversion from SQLModel
```

**Important**: These Pydantic models are shared between API and frontend. The frontend API client imports these models to ensure type safety when calling the API.

### Error Handling

All API endpoints will return consistent error responses:

```python
# api/utils/errors.py
from fastapi import HTTPException, status

class APIError(BaseModel):
    """Standard error response."""
    detail: str
    error_code: str | None = None
    field_errors: dict[str, list[str]] | None = None

# Common errors
class NotFoundError(HTTPException):
    def __init__(self, resource: str, id: int | str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with id {id} not found"
        )

class ValidationError(HTTPException):
    def __init__(self, field_errors: dict[str, list[str]]):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Validation error",
            headers={"X-Error-Code": "VALIDATION_ERROR"}
        )

class QuotaExceededError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="OpenAI API quota exceeded"
        )
```

## Migration Strategy

### Phase 1: Setup FastAPI Infrastructure (This Sprint)

1. **Create FastAPI Application**

   - Initialize FastAPI app in `api/main.py`
   - Configure CORS for Streamlit frontend
   - Add logging middleware
   - Set up error handlers
   - Configure OpenAPI docs

2. **Move Services to API**

   - Copy all services from `app/services/` to `api/services/`
   - Update imports to use `src.database` instead of relative imports
   - Remove Streamlit dependencies (session state, st.error, etc.)
   - Convert service methods to be API-friendly (return data, not UI)

3. **Create API Routes**

   - Implement all route handlers in `api/routes/`
   - Use dependency injection for database sessions
   - Add request validation using Pydantic schemas
   - Add response serialization

4. **Move LLM Workflows to API**

   - Move workflow files to `api/services/job_intake_service/workflows/`
   - Move `OpenAIQuotaExceededError` from `app/exceptions.py` to `src/exceptions.py` (shared)
   - Update workflow imports to use `src.exceptions` instead of `app.exceptions`
   - Create workflow API endpoints
   - Remove any Streamlit-specific error handling
   - Use FastAPI background tasks for long-running workflows

5. **Create API Client for Frontend**

   - Build HTTP client in `app/api_client/`
   - Implement endpoint-specific client methods
   - Handle errors and convert to Streamlit-friendly formats
   - Add retry logic and timeout handling

6. **Update Streamlit Frontend**

   - Replace direct service calls with API client calls
   - Update error handling to work with API responses
   - Remove database operations from frontend
   - Keep UI-specific logic (session state, page rendering)

7. **Update Application Runner**
   - Modify `run.py` to start both FastAPI and Streamlit
   - Use `uvicorn` for FastAPI
   - Run Streamlit as subprocess or use multiprocessing
   - Configure ports (FastAPI: 8000, Streamlit: 8501)

### Phase 2: Testing & Validation

**Important**: Before running any tests, copy the production database to avoid modifying live data.

1. **Database Setup for Tests**

   - Copy production database to test location
   - Configure test environment to use copied database
   - Run tests against copied database
   - Clean up test database after tests

2. **Minimal Unit Tests**

   - Create minimal API tests in `tests/api/`
   - Focus on critical endpoints only
   - Test basic CRUD operations
   - Test error cases
   - Keep tests simple and fast

3. **Manual Testing**
   - Test all UI flows manually with API backend
   - Verify data consistency
   - Test error handling
   - Validate functionality:
     - Job intake flow
     - Resume generation
     - Cover letter generation
     - Profile management
     - Template management

## Implementation Details

### FastAPI Application Setup

```python
# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import (
    users,
    jobs,
    experiences,
    education,
    certificates,
    resumes,
    cover_letters,
    templates,
    messages,
    responses,
    workflows,
)
from api.utils.errors import APIError
from src.config import settings
from src.logging_config import logger

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
    allow_origins=["http://localhost:8501"],  # Streamlit default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# Include routers
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

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
```

### Dependency Injection

```python
# api/dependencies.py
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from src.database import db_manager

def get_session() -> Generator[Session, None, None]:
    """Dependency for database session."""
    with db_manager.get_session() as session:
        yield session

# Type alias for dependency injection
DBSession = Annotated[Session, Depends(get_session)]
```

### Example Route Implementation

```python
# api/routes/jobs.py
from fastapi import APIRouter, HTTPException, status
from typing import Annotated

from api.dependencies import DBSession
from api.schemas.job import JobCreate, JobUpdate, JobResponse, JobListResponse
from api.services.job_service import JobService
from api.utils.errors import NotFoundError

router = APIRouter()

@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(
    session: DBSession,
    user_id: int,
    status_filter: str | None = None,
    favorite_only: bool = False,
):
    """List all jobs for a user."""
    jobs = JobService.list_jobs(
        user_id=user_id,
        statuses=[status_filter] if status_filter else None,
    )
    if favorite_only:
        jobs = [j for j in jobs if j.is_favorite]
    return jobs

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, session: DBSession):
    """Get a specific job."""
    job = JobService.get_job(job_id)
    if not job:
        raise NotFoundError("Job", job_id)
    return job

@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(job_data: JobCreate, session: DBSession):
    """Create a new job."""
    job = JobService.save_job(
        title=job_data.title,
        company=job_data.company,
        description=job_data.description,
        favorite=job_data.favorite,
    )
    return job

@router.patch("/jobs/{job_id}", response_model=JobResponse)
async def update_job(job_id: int, job_data: JobUpdate, session: DBSession):
    """Update a job."""
    job = JobService.update_job(job_id, **job_data.model_dump(exclude_unset=True))
    if not job:
        raise NotFoundError("Job", job_id)
    return job

@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: int, session: DBSession):
    """Delete a job."""
    JobService.delete_job(job_id)
```

### API Client for Frontend

The API client uses Pydantic models for strong typing. All endpoints return typed Pydantic models, not generic dicts.

```python
# app/api_client/client.py
from typing import Any, TypeVar
import httpx
from pydantic import BaseModel, ValidationError
from src.config import settings
from src.logging_config import logger

T = TypeVar("T", bound=BaseModel)

class APIClient:
    """Base HTTP client for API calls with typed responses."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 30.0

    async def _request(
        self,
        method: str,
        path: str,
        response_model: type[T] | None = None,
        **kwargs: Any,
    ) -> T | list[T] | dict[str, Any] | list[Any]:
        """Make HTTP request to API with optional response model validation."""
        url = f"{self.base_url}{path}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                data = response.json()

                # Validate response with Pydantic model if provided
                if response_model:
                    if isinstance(data, list):
                        return [response_model.model_validate(item) for item in data]
                    return response_model.model_validate(data)

                return data
        except ValidationError as e:
            logger.error(f"Response validation failed: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"API request failed: {e.response.status_code} {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"API request error: {e}")
            raise

    async def get(
        self,
        path: str,
        response_model: type[T] | None = None,
        **kwargs: Any
    ) -> T | list[T] | dict[str, Any] | list[Any]:
        """GET request with optional response model."""
        return await self._request("GET", path, response_model=response_model, **kwargs)

    async def post(
        self,
        path: str,
        response_model: type[T] | None = None,
        **kwargs: Any
    ) -> T | dict[str, Any]:
        """POST request with optional response model."""
        return await self._request("POST", path, response_model=response_model, **kwargs)

    async def patch(
        self,
        path: str,
        response_model: type[T] | None = None,
        **kwargs: Any
    ) -> T | dict[str, Any]:
        """PATCH request with optional response model."""
        return await self._request("PATCH", path, response_model=response_model, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> None:
        """DELETE request."""
        await self._request("DELETE", path, **kwargs)

# Global client instance
api_client = APIClient()
```

```python
# app/api_client/endpoints/jobs.py
from app.api_client.client import api_client
from api.schemas.job import JobResponse, JobCreate, JobUpdate

class JobsAPI:
    """API client for job endpoints with typed responses."""

    @staticmethod
    async def list_jobs(
        user_id: int,
        status_filter: str | None = None
    ) -> list[JobResponse]:
        """List jobs. Returns list of JobResponse models."""
        params = {"user_id": user_id}
        if status_filter:
            params["status_filter"] = status_filter
        return await api_client.get(
            "/api/v1/jobs",
            params=params,
            response_model=JobResponse  # Will validate each item in list
        )

    @staticmethod
    async def get_job(job_id: int) -> JobResponse:
        """Get a job. Returns JobResponse model."""
        return await api_client.get(
            f"/api/v1/jobs/{job_id}",
            response_model=JobResponse
        )

    @staticmethod
    async def create_job(
        title: str,
        company: str,
        description: str,
        favorite: bool = False
    ) -> JobResponse:
        """Create a job. Returns JobResponse model."""
        return await api_client.post(
            "/api/v1/jobs",
            json=JobCreate(
                title=title,
                company=company,
                description=description,
                favorite=favorite,
            ).model_dump(),
            response_model=JobResponse
        )

    @staticmethod
    async def update_job(
        job_id: int,
        **updates
    ) -> JobResponse:
        """Update a job. Returns JobResponse model."""
        update_data = JobUpdate(**updates).model_dump(exclude_unset=True)
        return await api_client.patch(
            f"/api/v1/jobs/{job_id}",
            json=update_data,
            response_model=JobResponse
        )

    @staticmethod
    async def delete_job(job_id: int) -> None:
        """Delete a job."""
        await api_client.delete(f"/api/v1/jobs/{job_id}")
```

### Workflow Endpoints

```python
# api/routes/workflows.py
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from api.dependencies import DBSession
from api.services.job_intake_service.workflows import (
    analyze_job_experience_fit,
    analyze_stakeholders,
    extract_experience_updates,
    run_resume_chat,
)
from api.utils.errors import QuotaExceededError
from src.database import db_manager
from src.exceptions import OpenAIQuotaExceededError

router = APIRouter()

class GapAnalysisRequest(BaseModel):
    job_description: str
    experience_ids: list[int]

class GapAnalysisResponse(BaseModel):
    analysis: str

@router.post("/workflows/gap-analysis", response_model=GapAnalysisResponse)
async def gap_analysis(request: GapAnalysisRequest, session: DBSession):
    """Run gap analysis workflow."""
    # Fetch experiences
    experiences = [
        db_manager.get_experience(exp_id)
        for exp_id in request.experience_ids
    ]
    experiences = [e for e in experiences if e is not None]

    try:
        analysis = analyze_job_experience_fit(
            job_description=request.job_description,
            experiences=experiences,
        )
        return GapAnalysisResponse(analysis=analysis)
    except OpenAIQuotaExceededError:
        raise QuotaExceededError()

class StakeholderAnalysisRequest(BaseModel):
    job_description: str

class StakeholderAnalysisResponse(BaseModel):
    analysis: str

@router.post("/workflows/stakeholder-analysis", response_model=StakeholderAnalysisResponse)
async def stakeholder_analysis(request: StakeholderAnalysisRequest):
    """Run stakeholder analysis workflow."""
    try:
        analysis = analyze_stakeholders(request.job_description)
        return StakeholderAnalysisResponse(analysis=analysis)
    except OpenAIQuotaExceededError:
        raise QuotaExceededError()

# Similar endpoints for other workflows...
```

### Updated Application Runner

```python
# run.py
#!/usr/bin/env python3
"""Run both FastAPI backend and Streamlit frontend."""

import multiprocessing
import sys
from pathlib import Path

import uvicorn
import streamlit.web.cli as stcli


def run_api():
    """Run FastAPI backend."""
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )


def run_streamlit():
    """Run Streamlit frontend."""
    app_path = Path(__file__).parent / "app" / "main.py"
    sys.argv = ["streamlit", "run", str(app_path)]
    stcli.main()


def main():
    """Run both services."""
    # Start API in separate process
    api_process = multiprocessing.Process(target=run_api)
    api_process.start()

    # Run Streamlit in main process
    try:
        run_streamlit()
    finally:
        # Clean up API process
        api_process.terminate()
        api_process.join()


if __name__ == "__main__":
    main()
```

## Service Migration Examples

### Before: Direct Service in Streamlit

```python
# app/pages/jobs.py (BEFORE)
import streamlit as st
from app.services.job_service import JobService

def show_jobs_page():
    user = st.session_state.current_user

    # Direct service call
    jobs = JobService.list_jobs(user.id, statuses=["Saved"])

    for job in jobs:
        st.write(f"{job.job_title} at {job.company_name}")
```

### After: API Client in Streamlit

```python
# app/pages/jobs.py (AFTER)
import streamlit as st
import asyncio
from app.api_client.endpoints.jobs import JobsAPI
from api.schemas.job import JobResponse  # Typed models

def show_jobs_page():
    user = st.session_state.current_user

    # API call returns list[JobResponse] - strongly typed!
    jobs: list[JobResponse] = asyncio.run(
        JobsAPI.list_jobs(user.id, status_filter="Saved")
    )

    # Type-safe access to attributes
    for job in jobs:
        st.write(f"{job.job_title} at {job.company_name}")  # Type-checked!
```

### Service Logic Cleanup

```python
# BEFORE: app/services/job_service.py
class JobService:
    @staticmethod
    def save_job(title: str, company: str, description: str, favorite: bool = False) -> DbJob:
        # Validation
        if not title or not title.strip():
            raise ValueError("title is required")

        # Get user from Streamlit session
        from app.services.user_service import UserService
        current_user = UserService.get_current_user()  # Uses st.session_state

        # Database operation
        job = DbJob(
            user_id=current_user.id,
            job_description=description.strip(),
            company_name=company.strip(),
            job_title=title.strip(),
            is_favorite=bool(favorite),
            status="Saved",
        )
        db_manager.add_job(job)
        return job

# AFTER: api/services/job_service.py
class JobService:
    @staticmethod
    def save_job(
        user_id: int,  # Explicit parameter, not from session
        title: str,
        company: str,
        description: str,
        favorite: bool = False
    ) -> DbJob:
        # Validation
        if not title or not title.strip():
            raise ValueError("title is required")
        if not user_id:
            raise ValueError("user_id is required")

        # Database operation (same as before)
        job = DbJob(
            user_id=user_id,
            job_description=description.strip(),
            company_name=company.strip(),
            job_title=title.strip(),
            is_favorite=bool(favorite),
            status="Saved",
        )
        db_manager.add_job(job)
        return job
```

## Configuration Changes

### Environment Variables

Add new API-specific configuration to `.env`:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:8501,http://localhost:3000

# API Keys (already exist)
OPENROUTER_API_KEY=...
LANGCHAIN_API_KEY=...
```

### Update Settings

```python
# src/config.py (additions)
class Settings(BaseSettings):
    # ... existing settings ...

    # API settings
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_reload: bool = Field(default=True)
    cors_origins: list[str] = Field(default=["http://localhost:8501"])
```

## Dependencies

### New Dependencies

Add to `pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "httpx>=0.26.0",  # For API client
]
```

## Testing Requirements

### Database Setup for Tests

**CRITICAL**: Always copy the production database before running tests to avoid modifying live data.

```python
# tests/conftest.py
import shutil
from pathlib import Path
import pytest
from sqlmodel import Session

from src.config import settings
from src.database import db_manager, create_engine

@pytest.fixture(scope="session")
def test_database_path(tmp_path_factory):
    """Copy production database to test location."""
    prod_db_path = Path(settings.database_url.replace("sqlite:///", ""))
    test_db_path = tmp_path_factory.mktemp("test_data") / "test_resume_bot.db"

    if prod_db_path.exists():
        shutil.copy2(prod_db_path, test_db_path)
        print(f"Copied database from {prod_db_path} to {test_db_path}")
    else:
        # Create empty test database if production doesn't exist
        test_db_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(f"sqlite:///{test_db_path}")
        # Create tables
        from src.database import SQLModel
        SQLModel.metadata.create_all(engine)

    return test_db_path

@pytest.fixture(scope="function")
def test_session(test_database_path, monkeypatch):
    """Provide test database session."""
    test_db_url = f"sqlite:///{test_database_path}"

    # Temporarily override database URL
    monkeypatch.setattr(settings, "database_url", test_db_url)

    # Get session from test database
    with db_manager.get_session() as session:
        yield session
        session.rollback()  # Rollback any changes after test
```

### Minimal API Tests

Keep tests minimal - just enough to verify basic functionality works:

```python
# tests/api/test_jobs.py
import pytest
from fastapi.testclient import TestClient

from api.main import app
from tests.conftest import test_session

client = TestClient(app)

def test_create_job(test_session):
    """Minimal test: verify job creation works."""
    response = client.post(
        "/api/v1/jobs",
        json={
            "title": "Software Engineer",
            "company": "Acme Corp",
            "description": "Great job",
            "favorite": False,
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["job_title"] == "Software Engineer"
    assert data["company_name"] == "Acme Corp"

def test_get_job_not_found():
    """Minimal test: verify 404 handling."""
    response = client.get("/api/v1/jobs/99999")
    assert response.status_code == 404
```

**Note**: Integration tests are skipped. Manual testing will be used instead to verify frontend-backend integration.

## Migration Checklist

### Pre-Migration

- [ ] Review and understand current architecture
- [ ] Identify all service dependencies
- [ ] Plan API endpoint structure
- [ ] Create migration strategy

### Implementation

- [ ] Create `api/` directory structure
- [ ] Set up FastAPI application (`api/main.py`)
- [ ] Create dependency injection (`api/dependencies.py`)
- [ ] Define API schemas (`api/schemas/`)
- [ ] Implement error handling (`api/utils/errors.py`)
- [ ] Move services to `api/services/`
- [ ] Create route handlers (`api/routes/`)
- [ ] Build API client (`app/api_client/`)
- [ ] Update Streamlit pages to use API client
- [ ] Update `run.py` to start both services
- [ ] Update configuration
- [ ] Add new dependencies

### Testing

- [ ] Set up test database copying mechanism (`tests/conftest.py`)
- [ ] Write minimal API endpoint tests (critical paths only)
- [ ] Test basic CRUD operations
- [ ] Test error cases
- [ ] Manual testing of all UI flows
- [ ] Manual testing of LLM workflows

### Documentation

- [ ] Update README with new architecture
- [ ] Document API endpoints
- [ ] Document deployment process
- [ ] Create API usage examples

### Deployment

- [ ] Update deployment scripts
- [ ] Configure production environment
- [ ] Set up monitoring
- [ ] Deploy and validate

## Success Criteria

1. **Clean Separation**: All backend logic is behind API endpoints
2. **No Direct Database Access**: Frontend only accesses data via API
3. **Security**: API keys and sensitive operations are server-side only
4. **Functional Parity**: All existing features work with new architecture
5. **Performance**: No significant performance degradation
6. **Testability**: Minimal test coverage with database isolation
7. **Documentation**: Clear API documentation and usage examples

## Future Considerations

### Phase 2: Supabase Migration

- Replace SQLite with Supabase PostgreSQL
- Implement Row-Level Security (RLS)
- Add authentication (Supabase Auth)
- Migrate database schema
- Update connection management

### Phase 3: Next.js Frontend

- Build React-based UI
- Implement authentication
- Use API client from frontend
- Migrate all Streamlit pages
- Improve UX/UI

## Technical Decisions & Rationale

### Why FastAPI?

- **Performance**: Async support, fast execution
- **Modern Python**: Type hints, Pydantic validation
- **OpenAPI**: Auto-generated documentation
- **Ecosystem**: Great tooling and middleware
- **Future-proof**: Easy to scale and deploy

### Why Keep SQLite (For Now)?

- **Incremental Migration**: Focus on API layer first
- **Less Risk**: Don't change multiple things at once
- **Testing**: Easier to test with SQLite
- **Future**: Clear path to Supabase later

### Why Separate Services Directory?

- **Organization**: Clear separation of concerns
- **Reusability**: Services can be used by multiple routes
- **Testing**: Easier to unit test services
- **Maintenance**: Easier to find and update logic

### Why Keep `src/` Directory?

- **Shared Logic**: Database models, agents, features used by API
- **Minimal Changes**: Don't restructure everything at once
- **Clear Purpose**: `src/` = shared backend, `api/` = HTTP layer
- **Future Flexibility**: Can extract to shared library later

## Files to Create

### New Files

```
api/
├── main.py
├── config.py
├── dependencies.py
├── middleware.py
├── routes/
│   ├── __init__.py
│   ├── users.py
│   ├── jobs.py
│   ├── experiences.py
│   ├── education.py
│   ├── certificates.py
│   ├── resumes.py
│   ├── cover_letters.py
│   ├── templates.py
│   ├── messages.py
│   ├── responses.py
│   └── workflows.py
├── schemas/
│   ├── __init__.py
│   ├── user.py
│   ├── job.py
│   ├── experience.py
│   ├── education.py
│   ├── certificate.py
│   ├── resume.py
│   ├── cover_letter.py
│   ├── template.py
│   ├── message.py
│   ├── response.py
│   └── workflow.py
├── services/
│   ├── __init__.py
│   ├── job_service.py
│   ├── resume_service.py
│   ├── cover_letter_service.py
│   ├── experience_service.py
│   ├── education_service.py
│   ├── certificate_service.py
│   ├── user_service.py
│   ├── template_service.py
│   ├── chat_message_service.py
│   ├── pdf_service.py
│   └── job_intake_service/
│       ├── __init__.py
│       ├── service.py
│       └── workflows/
│           ├── __init__.py
│           ├── gap_analysis.py
│           ├── stakeholder_analysis.py
│           ├── experience_extraction.py
│           └── resume_refinement.py
└── utils/
    ├── __init__.py
    └── errors.py

src/
└── exceptions.py  # NEW: Move OpenAIQuotaExceededError here from app/exceptions.py

app/api_client/
├── __init__.py
├── client.py
└── endpoints/
    ├── __init__.py
    ├── users.py
    ├── jobs.py
    ├── experiences.py
    ├── education.py
    ├── certificates.py
    ├── resumes.py
    ├── cover_letters.py
    ├── templates.py
    ├── messages.py
    ├── responses.py
    └── workflows.py

tests/
├── conftest.py  # Database copying and test fixtures
└── api/
    ├── __init__.py
    ├── test_jobs.py  # Minimal tests only
    └── test_workflows.py  # Minimal tests only
```

### Files to Move

```
app/exceptions.py            # Move OpenAIQuotaExceededError to src/exceptions.py
app/services/ → api/services/ (copy with modifications)
```

### Files to Update

```
run.py                        # Run both API and Streamlit
pyproject.toml               # Add FastAPI dependencies
src/config.py                # Add API configuration
app/pages/*.py               # Update to use API client with typed models
app/dialog/*.py              # Update to use API client with typed models
app/services/*.py            # Update imports to use src.exceptions
```

### Files to Delete (After Migration)

```
app/services/                # Keep temporarily for reference
```

## Notes

### Strong Typing with Pydantic

- **All API responses use Pydantic models**: Never return generic `dict` types
- **Frontend uses same models**: Import from `api.schemas` for type safety
- **Type checking**: Use mypy or similar to validate types across API and frontend
- **Example**: `JobsAPI.list_jobs()` returns `list[JobResponse]`, not `list[dict]`

### Shared Code Organization

- **No frontend imports in backend**: API should never import from `app/`
- **Shared exceptions**: Move `OpenAIQuotaExceededError` to `src/exceptions.py`
- **Shared schemas**: API schemas in `api/schemas/` can be imported by frontend
- **Clear boundaries**: `src/` = shared backend, `api/` = HTTP layer, `app/` = frontend

### Testing Strategy

- **Database isolation**: Always copy production DB before tests
- **Minimal tests**: Only test critical paths, keep tests simple
- **Manual testing**: Use manual testing for integration, skip automated integration tests
- **Test cleanup**: Rollback or cleanup test database after each test

### Implementation Best Practices

- **Backward Compatibility**: Keep old service files temporarily for reference
- **Incremental Development**: Test each endpoint as it's implemented
- **Error Handling**: Ensure all error cases are handled gracefully
- **Logging**: Add comprehensive logging to API and client
- **Performance**: Monitor performance and add caching where needed
- **Security**: Validate all inputs, sanitize outputs, protect sensitive data
- **Documentation**: Keep API docs updated as endpoints are added

## Questions & Clarifications Needed

None at this time. The spec provides a complete blueprint for migrating to FastAPI while maintaining all existing functionality.
