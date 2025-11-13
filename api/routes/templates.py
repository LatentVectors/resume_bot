"""Template management API routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from api.dependencies import DBSession
from api.schemas.template import TemplateDetail, TemplateListItem, TemplateListResponse
from api.services.cover_letter_service import CoverLetterService
from src.features.resume.utils import list_available_templates

router = APIRouter()


def _resume_templates_dir() -> Path:
    """Return the path to the resume templates directory."""
    project_root = Path(__file__).resolve().parents[2]
    return (project_root / "src" / "features" / "resume" / "templates").resolve()


@router.get("/templates/resumes", response_model=TemplateListResponse)
async def list_resume_templates(session: DBSession = None) -> TemplateListResponse:  # noqa: ARG001
    """List all available resume templates."""
    try:
        templates_dir = _resume_templates_dir()
        template_names = list_available_templates(templates_dir)
        templates = [
            TemplateListItem(name=name, display_name=name.replace("_", " ").replace(".html", "").title())
            for name in template_names
        ]
        return TemplateListResponse(templates=templates)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/templates/resumes/{template_id}", response_model=TemplateDetail)
async def get_resume_template(template_id: str, session: DBSession = None) -> TemplateDetail:  # noqa: ARG001
    """Get a specific resume template."""
    try:
        templates_dir = _resume_templates_dir()
        template_path = templates_dir / template_id
        if not template_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Template {template_id} not found")

        content = template_path.read_text()
        display_name = template_id.replace("_", " ").replace(".html", "").title()
        return TemplateDetail(name=template_id, display_name=display_name, content=content)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/templates/cover-letters", response_model=TemplateListResponse)
async def list_cover_letter_templates(session: DBSession = None) -> TemplateListResponse:  # noqa: ARG001
    """List all available cover letter templates."""
    try:
        template_names = CoverLetterService.list_available_templates()
        templates = [
            TemplateListItem(name=name, display_name=name.replace("_", " ").replace(".html", "").title())
            for name in template_names
        ]
        return TemplateListResponse(templates=templates)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/templates/cover-letters/{template_id}", response_model=TemplateDetail)
async def get_cover_letter_template(template_id: str, session: DBSession = None) -> TemplateDetail:  # noqa: ARG001
    """Get a specific cover letter template."""
    try:
        # Use the same path resolution as CoverLetterService
        templates_dir = Path(__file__).parent.parent.parent / "src" / "features" / "cover_letter" / "templates"
        template_path = templates_dir / template_id
        if not template_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Template {template_id} not found")

        content = template_path.read_text()
        display_name = template_id.replace("_", " ").replace(".html", "").title()
        return TemplateDetail(name=template_id, display_name=display_name, content=content)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

