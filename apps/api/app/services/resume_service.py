"""Service for resume draft generation, versioning, and preview rendering."""

from __future__ import annotations

import hashlib
from collections import OrderedDict

import streamlit as st
from langchain_core.runnables import RunnableConfig
from sqlmodel import select

from app.constants import LLMTag
from app.services.render_pdf import _resume_templates_dir
from app.shared.formatters import format_experience_with_achievements
from src.database import Resume as DbResume
from src.database import ResumeVersion as DbResumeVersion
from src.database import ResumeVersionEvent, db_manager
from src.features.resume.data_adapter import (
    detect_missing_required_data,
    fetch_experience_data,
    fetch_user_data,
    transform_user_to_resume_data,
)
from src.features.resume.types import ResumeData
from src.features.resume.utils import render_template_to_html
from src.logging_config import logger

from .job_service import JobService
from .render_pdf import render_preview_pdf_bytes, render_resume_pdf_bytes


class ResumeService:
    """Service class for resume-related operations."""

    # ---- New APIs per spec ----
    @staticmethod
    def create_version(
        job_id: int,
        resume_data: ResumeData,
        template_name: str,
        event_type: ResumeVersionEvent,
        parent_version_id: int | None = None,
    ) -> DbResumeVersion:
        """Create and persist a new ResumeVersion row.

        - Computes the next monotonic version_index for the job
        - Stores JSON and template snapshot
        - Sets created_by_user_id from the owning Job
        - Links to parent_version_id if provided; if None, uses current head if it exists
        """
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")
        if not template_name or not template_name.strip():
            raise ValueError("template_name is required")

        job = JobService.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        with db_manager.get_session() as session:
            # Determine next version index and current head id
            head_row: DbResumeVersion | None = session.exec(
                select(DbResumeVersion)
                .where(DbResumeVersion.job_id == job_id)
                .order_by(DbResumeVersion.version_index.desc())
            ).first()

            next_index = 1 if head_row is None else int(head_row.version_index) + 1
            effective_parent_id = (
                parent_version_id if parent_version_id is not None else (head_row.id if head_row is not None else None)
            )

            row = DbResumeVersion(
                job_id=job_id,
                version_index=next_index,
                parent_version_id=effective_parent_id,
                event_type=event_type,
                template_name=template_name,
                resume_json=resume_data.model_dump_json(),
                created_by_user_id=int(job.user_id),
            )

            session.add(row)
            session.commit()
            session.refresh(row)
            logger.info(
                "Created ResumeVersion",
                extra={
                    "job_id": job_id,
                    "version_index": next_index,
                    "event_type": str(event_type),
                },
            )
            return row

    @staticmethod
    def list_versions(job_id: int) -> list[DbResumeVersion]:
        """List all versions for a job ordered by version_index ascending."""
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")
        with db_manager.get_session() as session:
            rows = session.exec(
                select(DbResumeVersion)
                .where(DbResumeVersion.job_id == job_id)
                .order_by(DbResumeVersion.version_index.asc())
            ).all()
            return list(rows)

    @staticmethod
    def get_version(version_id: int) -> DbResumeVersion | None:
        """Get a specific version by id."""
        if not isinstance(version_id, int) or version_id <= 0:
            raise ValueError("Invalid version_id")
        with db_manager.get_session() as session:
            return session.get(DbResumeVersion, version_id)

    @staticmethod
    def pin_canonical(job_id: int, version_id: int) -> DbResume:
        """Set the canonical Resume row for a job from a version snapshot.

        Writes template_name and resume_json to the single canonical Resume row.
        Does not render or persist any PDFs.
        """
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")
        if not isinstance(version_id, int) or version_id <= 0:
            raise ValueError("Invalid version_id")

        with db_manager.get_session() as session:
            version = session.get(DbResumeVersion, version_id)
            if version is None or version.job_id != job_id:
                raise ValueError("Version not found for job")

            existing = session.exec(select(DbResume).where(DbResume.job_id == job_id)).first()
            if existing:
                existing.template_name = version.template_name
                existing.resume_json = version.resume_json
                session.add(existing)
            else:
                existing = DbResume(
                    job_id=job_id,
                    template_name=version.template_name,
                    resume_json=version.resume_json,
                    locked=False,
                )
                session.add(existing)

            session.commit()
            session.refresh(existing)

        # Update job flags (Section 4 will refine has_resume computation)
        try:
            JobService.refresh_denorm_flags(job_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception(exc)

        return existing

    @staticmethod
    def unpin_canonical(job_id: int) -> None:
        """Clear the canonical Resume row for a job (unpin).
        
        Args:
            job_id: The job ID to unpin the resume for.
        """
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")
        
        with db_manager.get_session() as session:
            existing = session.exec(select(DbResume).where(DbResume.job_id == job_id)).first()
            if existing:
                session.delete(existing)
                session.commit()
        
        # Update job flags
        try:
            JobService.refresh_denorm_flags(job_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception(exc)

    @staticmethod
    def get_canonical(job_id: int) -> DbResume | None:
        """Return canonical Resume row for a job if present."""
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")
        with db_manager.get_session() as session:
            return session.exec(select(DbResume).where(DbResume.job_id == job_id)).first()

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
                # Fetch achievements for this experience
                achievements = db_manager.list_experience_achievements(exp.id)

                # Use the standardized formatter to create content string
                full_content = format_experience_with_achievements(exp, achievements)

                agent_experiences.append(
                    create_experience(
                        id=str(exp.id or ""),
                        company=exp.company_name,
                        title=exp.job_title,
                        start_date=exp.start_date,
                        end_date=exp.end_date,
                        content=full_content,
                        points=[],
                        location=exp.location or "",
                    )
                )

            # Build InputState from current draft and job context
            initial_state = InputState(
                job_description=job.job_description,
                experiences=agent_experiences,
                responses="",
                special_instructions=prompt or None,
                resume_draft=draft,
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

            # Create a new version (event_type=generate). Parent links to current head.
            try:
                canonical = ResumeService.get_canonical(job_id)
                template_for_version = canonical.template_name if canonical else "resume_000.html"
                ResumeService.create_version(
                    job_id=job_id,
                    resume_data=updated,
                    template_name=template_for_version,
                    event_type=ResumeVersionEvent.generate,
                )
            except Exception as e:  # noqa: BLE001
                # Log but do not fail the generate flow; version history is best-effort here
                logger.exception(e)

            return updated
        except Exception as e:  # noqa: BLE001
            logger.exception(e)
            raise

    @staticmethod
    def save_resume(job_id: int, resume_data: ResumeData, template_name: str) -> DbResumeVersion:
        """Create a new version with event_type='save'.

        - Does not modify the canonical Resume row
        - Does not render or write any PDFs
        - Returns the newly created ResumeVersion
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
                "Creating resume version (save)",
                extra={"job_id": job_id, "template_name": template_name},
            )
            return ResumeService.create_version(
                job_id=job_id,
                resume_data=resume_data,
                template_name=template_name,
                event_type=ResumeVersionEvent.save,
            )
        except Exception as e:  # noqa: BLE001
            logger.exception(e)
            raise

    @staticmethod
    def render_preview(job_id: int, resume_data: ResumeData, template_name: str) -> bytes:
        """Render a temporary preview PDF and return bytes (no disk I/O).

        Uses an in-session LRU cache of up to 25 rendered PDFs per job. The
        cache key is a SHA-256 hash of the fully-populated HTML (template +
        content), so different content or template selections produce distinct
        entries. Cache is cleared on job change in the job page.
        """
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")
        if not template_name or not template_name.strip():
            raise ValueError("template_name is required")

        try:
            # Initialize cache container in session_state as dict[job_id -> OrderedDict[key -> bytes]]
            cache_root = st.session_state.get("resume_pdf_cache")
            if not isinstance(cache_root, dict):
                cache_root = {}
                st.session_state["resume_pdf_cache"] = cache_root

            job_cache = cache_root.get(job_id)
            if not isinstance(job_cache, OrderedDict):
                job_cache = OrderedDict()
                cache_root[job_id] = job_cache

            # Build HTML and compute stable hash key
            templates_dir = _resume_templates_dir()
            html = render_template_to_html(
                template_name=template_name,
                context=resume_data.model_dump(),
                templates_dir=templates_dir,
            )
            key = hashlib.sha256(html.encode("utf-8")).hexdigest()

            # Cache hit: move to end (most-recent) and return
            if key in job_cache:
                try:
                    job_cache.move_to_end(key)
                except Exception:
                    pass
                return job_cache[key]

            # Miss: render and insert with LRU eviction
            pdf_bytes = render_preview_pdf_bytes(resume_data, template_name)
            job_cache[key] = pdf_bytes
            # Enforce capacity 25 per job
            while len(job_cache) > 25:
                try:
                    job_cache.popitem(last=False)
                except Exception:
                    break

            return pdf_bytes
        except Exception as e:  # noqa: BLE001
            logger.exception(e)
            raise

    @staticmethod
    def render_canonical_pdf_bytes(job_id: int) -> bytes:
        """Render the canonical resume for a job and return PDF bytes.

        Reads the canonical `Resume` row (template + JSON) and renders to bytes
        without any disk I/O. Raises if no canonical resume exists.
        """
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")

        resume = ResumeService.get_canonical(job_id)
        if not resume or not (resume.resume_json or "").strip():
            raise ValueError("No canonical resume found for this job")

        try:
            data = ResumeData.model_validate_json(resume.resume_json)  # type: ignore[arg-type]
            template = (resume.template_name or "resume_000.html").strip() or "resume_000.html"
            return render_resume_pdf_bytes(data, template)
        except Exception as e:  # noqa: BLE001
            logger.exception(e)
            raise
