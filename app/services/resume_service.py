"""Service for resume draft generation, saving, and preview rendering."""

from pathlib import Path
from uuid import uuid4

from langchain_core.runnables import RunnableConfig
from sqlmodel import select

from app.constants import LLMTag
from src.config import settings
from src.database import Resume as DbResume
from src.database import db_manager
from src.features.resume.data_adapter import (
    detect_missing_required_data,
    fetch_experience_data,
    fetch_user_data,
    transform_user_to_resume_data,
)
from src.features.resume.types import ResumeData
from src.logging_config import logger

from .job_service import JobService
from .render_pdf import render_preview_pdf, render_resume_pdf


class ResumeService:
    """Service class for resume-related operations."""

    # ---- New APIs per spec ----
    @staticmethod
    def generate_resume_for_job(
        user_id: int, job_id: int, prompt: str, existing_draft: ResumeData | None
    ) -> ResumeData:
        """Return an updated ResumeData draft via the agent.

        - Validates job exists and is not Applied.
        - Builds a base ResumeData from user/profile and merges with existing draft.
        - Calls the agent graph to update AI-editable fields.
        - Returns the draft (no persistence).
        """
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("Invalid user_id")
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")

        job = JobService.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        if job.applied_at is not None:
            raise PermissionError("Job is applied; resume generation is locked")

        # Build base ResumeData from DB
        user_data = fetch_user_data(user_id)
        missing_required = detect_missing_required_data(user_data)
        if missing_required:
            raise ValueError(f"Missing required identity fields: {', '.join(missing_required)}")

        experiences = fetch_experience_data(user_id)
        if not experiences:
            # Agent requires at least one non-empty experience; fail fast with a clear error
            raise ValueError("At least one experience on your profile is required to generate a resume")
        base_resume = transform_user_to_resume_data(
            user_data=user_data,
            experience_data=experiences,
            job_title=job.job_title or "",
        )

        # Merge existing draft over base for user-editable identity and any prior AI fields
        draft = existing_draft or base_resume
        if existing_draft is not None:
            draft = ResumeData.model_validate({**base_resume.model_dump(), **existing_draft.model_dump()})

        # Call agent nodes to update AI-editable fields
        try:
            from src.agents.main import InputState, OutputState, create_experience, main_agent
            from src.agents.main.state import Experience as AgentExperience

            agent_experiences: list[AgentExperience] = []
            # Use user's raw experiences; points may be empty initially
            for exp in experiences:
                agent_experiences.append(
                    create_experience(
                        id=str(exp.id or ""),
                        company=exp.company_name,
                        title=exp.job_title,
                        start_date=exp.start_date,
                        end_date=exp.end_date,
                        content=exp.content,
                        points=[],
                    )
                )

            # Build InputState from current draft and job context
            initial_state = InputState(
                job_description=job.job_description,
                experiences=agent_experiences,
                responses=prompt or "",
                user_name=draft.name,
                user_email=draft.email,
                user_phone=draft.phone or None,
                user_linkedin_url=draft.linkedin_url or None,
                user_education=[
                    {"school": edu.institution, "degree": edu.degree, "start_date": None, "end_date": edu.grad_date}
                    for edu in draft.education
                ]
                or None,
            )

            config = RunnableConfig(
                tags=[LLMTag.RESUME_GENERATION.value],
                metadata={"job_id": job_id, "user_id": user_id},
            )
            result = main_agent.invoke(initial_state, config=config)
            out = OutputState.model_validate(result)

            # Apply AI-editable fields to draft (read from out.resume_data)
            updated = draft.model_copy(deep=True)
            rd = out.resume_data
            if rd is not None:
                if rd.title:
                    updated.title = rd.title
                if rd.professional_summary:
                    updated.professional_summary = rd.professional_summary
                if rd.skills:
                    updated.skills = rd.skills

                # Merge experience bullet points from rd into existing draft experiences.
                # Preserve user-entered fields like location and dates from the current draft.
                try:
                    if rd.experience:
                        # Build a lookup of points by (title, company) normalized
                        def _key(title: str, company: str) -> tuple[str, str]:
                            return (title.strip().lower(), company.strip().lower())

                        rd_map = {
                            _key(exp.title or "", exp.company or ""): list(exp.points or []) for exp in rd.experience
                        }

                        merged_experiences = []
                        for idx, exp in enumerate(updated.experience or []):
                            pts: list[str] | None = None
                            k = _key(exp.title or "", exp.company or "")
                            if k in rd_map and rd_map[k]:
                                pts = rd_map[k]
                            elif idx < len(rd.experience) and (rd.experience[idx].points or []):
                                pts = list(rd.experience[idx].points or [])

                            merged_experiences.append(
                                type(exp)(
                                    title=exp.title,
                                    company=exp.company,
                                    location=getattr(exp, "location", ""),
                                    start_date=exp.start_date,
                                    end_date=exp.end_date,
                                    points=list(pts or exp.points or []),
                                )
                            )

                        # If rd has more experiences than current draft, append them
                        if len(rd.experience) > len(merged_experiences):
                            for extra in rd.experience[len(merged_experiences) :]:
                                merged_experiences.append(
                                    type(exp)(
                                        title=extra.title,
                                        company=extra.company,
                                        location=getattr(extra, "location", ""),
                                        start_date=extra.start_date,
                                        end_date=extra.end_date,
                                        points=list(extra.points or []),
                                    )
                                )

                        updated.experience = merged_experiences
                except Exception as e:  # noqa: BLE001
                    # Log and proceed with whatever we currently have; do not fail generation
                    logger.exception(e)

            return updated
        except Exception as e:  # noqa: BLE001
            logger.exception(e)
            raise

    @staticmethod
    def save_resume(job_id: int, resume_data: ResumeData, template_name: str) -> DbResume:
        """Persist Resume JSON and render/overwrite PDF for the job.

        - Creates or updates the single Resume row per job.
        - If a pdf_filename exists, overwrite the same file; else create a new UUID.
        - Recomputes job denorm flags.
        """
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")
        if not template_name or not template_name.strip():
            raise ValueError("template_name is required")

        job = JobService.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        if job.applied_at is not None:
            raise PermissionError("Job is applied; resume save is locked")

        try:
            logger.info(
                "Saving resume",
                extra={
                    "job_id": job_id,
                    "template_name": template_name,
                },
            )
            payload_json = resume_data.model_dump_json()

            with db_manager.get_session() as session:
                # Find existing resume
                existing = session.exec(
                    select(DbResume).where(DbResume.job_id == job_id)  # type: ignore[name-defined]
                ).first()

                if existing:
                    existing.template_name = template_name
                    existing.resume_json = payload_json
                    pdf_filename = existing.pdf_filename or f"{uuid4()}.pdf"
                else:
                    existing = DbResume(
                        job_id=job_id,
                        template_name=template_name,
                        resume_json=payload_json,
                        pdf_filename=None,
                        locked=False,
                    )
                    session.add(existing)
                    pdf_filename = f"{uuid4()}.pdf"

                # Render PDF to canonical location
                output_dir = (settings.data_dir / "resumes").resolve()
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / pdf_filename

                try:
                    render_resume_pdf(resume_data, template_name, output_path)
                    existing.pdf_filename = pdf_filename
                except Exception as e:  # noqa: BLE001
                    # Log and keep JSON changes; clear pdf filename so denorm reflects missing PDF
                    logger.exception(e)
                    existing.pdf_filename = None

                session.add(existing)
                session.commit()
                session.refresh(existing)

            # Refresh denorm flags on parent job
            JobService.refresh_denorm_flags(job_id)
            return existing
        except Exception as e:  # noqa: BLE001
            logger.exception(e)
            raise

    @staticmethod
    def render_preview(job_id: int, resume_data: ResumeData, template_name: str) -> Path:
        """Render a temporary preview PDF for this job; does not persist or update DB.

        Returns the preview file path.
        """
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")
        if not template_name or not template_name.strip():
            raise ValueError("template_name is required")

        try:
            preview_dir = (settings.data_dir / "resumes" / "previews").resolve()
            preview_dir.mkdir(parents=True, exist_ok=True)
            preview_path = preview_dir / f"{job_id}.pdf"
            return render_preview_pdf(resume_data, template_name, preview_path)
        except Exception as e:  # noqa: BLE001
            logger.exception(e)
            raise
