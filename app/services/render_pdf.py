"""PDF rendering service for resumes (persisted and previews)."""

from __future__ import annotations

from pathlib import Path

from src.features.resume.types import ResumeData
from src.features.resume.utils import render_template_to_pdf
from src.logging_config import logger


def _resume_templates_dir() -> Path:
    """Return the path to bundled resume templates directory."""
    # Resolve absolute path from repository root to avoid CWD-dependent failures
    project_root = Path(__file__).resolve().parents[2]
    return (project_root / "src" / "features" / "resume" / "templates").resolve()


def render_resume_pdf(resume_data: ResumeData, template_name: str, dest_path: Path) -> Path:
    """Render the canonical resume PDF to the destination path.

    Args:
        resume_data: `ResumeData` object to render
        template_name: HTML template filename (e.g., 'resume_000.html')
        dest_path: Target PDF path (will be created/overwritten)

    Returns:
        Path to the rendered PDF
    """
    try:
        pdf_path = Path(dest_path)
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        templates_dir = _resume_templates_dir()
        logger.info(
            "Rendering resume PDF",
            extra={
                "template": template_name,
                "dest": str(pdf_path),
            },
        )
        result = render_template_to_pdf(
            template_name=template_name,
            context=resume_data.model_dump(),
            output_path=pdf_path,
            templates_dir=templates_dir,
        )
        return result
    except Exception as e:  # noqa: BLE001
        logger.exception(e)
        raise


def render_preview_pdf(resume_data: ResumeData, template_name: str, preview_path: Path) -> Path:
    """Render a preview PDF for display only; does not update any DB state.

    Args:
        resume_data: `ResumeData` object
        template_name: HTML template filename
        preview_path: Desired preview PDF path

    Returns:
        Path to the rendered preview PDF
    """
    try:
        preview_pdf = Path(preview_path)
        # Ensure previews directory exists under data/resumes/previews by default if caller passed a dir
        preview_pdf.parent.mkdir(parents=True, exist_ok=True)
        templates_dir = _resume_templates_dir()
        logger.info(
            "Rendering preview PDF",
            extra={
                "template": template_name,
                "dest": str(preview_pdf),
            },
        )
        result = render_template_to_pdf(
            template_name=template_name,
            context=resume_data.model_dump(),
            output_path=preview_pdf,
            templates_dir=templates_dir,
        )
        return result
    except Exception as e:  # noqa: BLE001
        logger.exception(e)
        raise
