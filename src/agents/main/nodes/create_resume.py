from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from src.config import settings
from src.features.resume.types import ResumeData, ResumeEducation, ResumeExperience
from src.features.resume.utils import render_template_to_pdf
from src.logging_config import logger

from ..state import Experience, InternalState, PartialInternalState


def create_resume(state: InternalState) -> PartialInternalState:
    """
    Generate a PDF resume from template and return filename.

    Process:
    1. Validate inputs (professional_summary, experiences, skills)
    2. Transform data to ResumeData-compatible structure
    3. Render HTML template (resume_000.html)
    4. Convert HTML to PDF and save to data/resumes/{UUID}.pdf
    5. Return filename for downstream storage
    """
    logger.debug("NODE: create_resume")

    # 1) Validate required inputs
    if not state.professional_summary:
        raise ValueError("professional_summary is required for resume creation")
    if not state.experiences:
        raise ValueError("experiences list cannot be empty for resume creation")
    if not state.skills:
        raise ValueError("skills list cannot be empty for resume creation")

    # 2) Transform data to ResumeData-like structure
    def _fmt(date_obj: object) -> str:
        try:
            # date_obj is expected to be a datetime.date or None
            from datetime import date as _date

            if not date_obj:
                return "Present"
            if isinstance(date_obj, _date):
                return date_obj.strftime("%b %Y")
            return str(date_obj)
        except Exception:
            return ""

    resume_experiences: list[ResumeExperience] = []
    for exp in state.experiences:
        assert isinstance(exp, Experience)
        resume_experiences.append(
            ResumeExperience(
                title=exp.title,
                company=exp.company,
                location="",
                start_date=_fmt(exp.start_date),
                end_date=_fmt(exp.end_date) if exp.end_date else "Present",
                points=list(exp.points or []),
            )
        )

    resume_education: list[ResumeEducation] = []
    if state.user_education:
        for edu in state.user_education:
            # Input keys come from DB adapter: school, degree, start_date, end_date
            resume_education.append(
                ResumeEducation(
                    degree=str(edu.get("degree", "")),
                    major="",
                    institution=str(edu.get("school", "")),
                    grad_date=_fmt(edu.get("end_date")),
                )
            )

    resume_data = ResumeData(
        name=state.user_name or "",
        title="",
        email=state.user_email or "",
        phone=state.user_phone or "",
        linkedin_url=state.user_linkedin_url or "",
        professional_summary=state.professional_summary or "",
        experience=resume_experiences,
        education=resume_education,
        skills=list(state.skills or []),
        certifications=[],
    )

    context = resume_data.model_dump()

    # 3) Render to PDF using template and save
    templates_dir = Path(__file__).resolve().parents[3] / "features" / "resume" / "templates"
    output_dir = (settings.data_dir / "resumes").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4()}.pdf"
    output_path = output_dir / filename

    render_template_to_pdf(
        template_name="resume_000.html",
        context=context,
        output_path=output_path,
        templates_dir=templates_dir,
    )

    # 5) Return only the filename (not full path)
    return PartialInternalState(resume=filename)
