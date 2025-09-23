from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Literal

from sqlmodel import select

from src.database import (
    CoverLetter as DbCoverLetter,
)
from src.database import (
    Job as DbJob,
)
from src.database import (
    Message as DbMessage,
)
from src.database import (
    Note as DbNote,
)
from src.database import (
    Response as DbResponse,
)
from src.database import (
    Resume as DbResume,
)
from src.database import (
    db_manager,
)
from src.features.jobs.extraction import extract_title_company
from src.logging_config import logger

AllowedStatus = Literal["Saved", "Applied", "Interviewing", "Not Selected", "No Offer", "Hired"]


class JobService:
    """Business logic for Jobs and related artifacts.

    UI layers should only call into this service for any Job-related operations.
    """

    # ---------- Core Job APIs ----------
    @staticmethod
    def save_job_with_extraction(description: str, favorite: bool) -> DbJob:
        """Create a Job from a freeform description using LLM extraction.

        Args:
            description: Raw job description text (required).
            favorite: Whether to mark the job as a favorite.

        Returns:
            Persisted DbJob with extracted title/company when available.
        """
        if not description or not description.strip():
            raise ValueError("description is required")

        # Single-user app: attach to the first/only user
        try:
            from app.services.user_service import UserService  # local import to avoid cycles at import time

            current_user = UserService.get_current_user()
            if not current_user or not current_user.id:
                raise ValueError("No user found. Create a user before saving a job.")

            extracted = extract_title_company(description)
            company = (extracted.company or "").strip() or None
            title = (extracted.title or "").strip() or None

            # Create Job without resume filename (single Resume per Job is modeled separately)
            job = DbJob(
                user_id=current_user.id,
                job_description=description.strip(),
                company_name=company,
                job_title=title,
                is_favorite=bool(favorite),
                status="Saved",
                has_resume=False,
                has_cover_letter=False,
            )
            db_manager.add_job(job)

            logger.info("Saved job with extraction: id=%s title=%s company=%s", job.id, job.job_title, job.company_name)
            return job
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to save job with extraction: %s", exc)
            raise

    @staticmethod
    def list_jobs(
        user_id: int,
        statuses: Iterable[AllowedStatus] | None = None,
        favorites_only: bool = False,
    ) -> list[DbJob]:
        """List jobs for a user with optional filters.

        Default sort: created_at desc.
        """
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("Invalid user_id")

        try:
            with db_manager.get_session() as session:
                stmt = select(DbJob).where(DbJob.user_id == user_id)

                if statuses:
                    status_values = list(statuses)
                    if status_values:
                        stmt = stmt.where(DbJob.status.in_(status_values))

                if favorites_only:
                    stmt = stmt.where(DbJob.is_favorite.is_(True))

                stmt = stmt.order_by(DbJob.created_at.desc())
                jobs = list(session.exec(stmt))

                # Keep denormalized flags reasonably fresh for UI rendering
                refreshed: list[DbJob] = []
                for job in jobs:
                    try:
                        updated = JobService.refresh_denorm_flags(job.id)  # type: ignore[arg-type]
                        refreshed.append(updated or job)
                    except Exception:  # noqa: BLE001
                        refreshed.append(job)
                return refreshed
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to list jobs for user %s: %s", user_id, exc)
            return []

    @staticmethod
    def get_job(job_id: int) -> DbJob | None:
        """Get a job by ID."""
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")
        try:
            return db_manager.get_job(job_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to get job %s: %s", job_id, exc)
            return None

    @staticmethod
    def update_job_fields(
        job_id: int,
        *,
        title: str | None = None,
        company: str | None = None,
        job_description: str | None = None,
        is_favorite: bool | None = None,
    ) -> DbJob | None:
        """Update basic editable fields for a job.

        Only provided fields are updated.
        """
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")

        updates: dict[str, object] = {}
        if title is not None:
            updates["job_title"] = title.strip() or None
        if company is not None:
            updates["company_name"] = company.strip() or None
        if job_description is not None:
            updates["job_description"] = job_description.strip() or None
        if is_favorite is not None:
            updates["is_favorite"] = bool(is_favorite)

        if not updates:
            return db_manager.get_job(job_id)

        try:
            job = db_manager.update_job(job_id, **updates)
            return job
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to update job %s: %s", job_id, exc)
            raise

    @staticmethod
    def set_status(job_id: int, status: AllowedStatus) -> DbJob | None:
        """Set job status and apply first-time Applied side-effects.

        - On first transition to Applied: set applied_at and lock Resume/CoverLetter/Response rows.
        - Transitions are idempotent; applied_at remains the first-set value.
        """
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")
        if status not in ("Saved", "Applied", "Interviewing", "Not Selected", "No Offer", "Hired"):
            raise ValueError("Invalid status value")

        try:
            with db_manager.get_session() as session:
                job = session.get(DbJob, job_id)
                if not job:
                    return None

                prior_applied_at = job.applied_at
                job.status = status
                # First time Applied: set applied_at and lock artifacts
                if status == "Applied" and job.applied_at is None:
                    job.applied_at = datetime.now()

                    # Lock child artifacts for this job
                    for model in (DbResume, DbCoverLetter, DbResponse):
                        rows = session.exec(select(model).where(model.job_id == job_id)).all()
                        for row in rows:
                            # Message.locked is derived; for others, set explicitly
                            if hasattr(row, "locked"):
                                row.locked = True
                            session.add(row)

                # Touch updated_at and persist
                session.add(job)
                session.commit()
                session.refresh(job)

                # Refresh child artifacts if we changed them
                if status == "Applied" and prior_applied_at is None:
                    # No additional side-effects needed for denorm flags here per spec
                    pass

                return job
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to set status for job %s: %s", job_id, exc)
            raise

    # ---------- Child entities ----------
    @staticmethod
    def get_resume_for_job(job_id: int) -> DbResume | None:
        """Return the single `Resume` row for a job, if present.

        Enforces the one-resume-per-job expectation by returning the first match.
        """
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")

        try:
            with db_manager.get_session() as session:
                return session.exec(select(DbResume).where(DbResume.job_id == job_id)).first()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to get resume for job %s: %s", job_id, exc)
            return None

    @staticmethod
    def create_resume(job_id: int) -> DbResume:
        """Create a canonical `Resume` row and refresh denormalized flags.

        Canonical `has_resume` depends only on the existence of this row, not on
        any persisted PDF filename (deprecated per specs/008-resume_history).

        Args:
            job_id: Parent job identifier.

        Returns:
            Persisted DbResume instance.
        """
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")

        try:
            with db_manager.get_session() as session:
                job = session.get(DbJob, job_id)
                if not job:
                    raise ValueError(f"Job {job_id} not found")

                # Create Resume (pdf_filename deprecated and unused)
                resume = DbResume(
                    job_id=job_id,
                    template_name="default",  # placeholder; should be set by ResumeService
                    resume_json="{}",  # placeholder; should be set by ResumeService
                    locked=False,
                )
                session.add(resume)
                session.commit()
                session.refresh(resume)

            JobService.refresh_denorm_flags(job_id)
            logger.info("Created resume %s for job %s", resume.id, job_id)
            return resume
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to create resume for job %s: %s", job_id, exc)
            raise

    @staticmethod
    def delete_resume(resume_id: int) -> bool:
        """Delete a Resume row and refresh parent job flags.

        Returns True if deleted, False otherwise.
        """
        if not isinstance(resume_id, int) or resume_id <= 0:
            raise ValueError("Invalid resume_id")

        try:
            with db_manager.get_session() as session:
                resume = session.get(DbResume, resume_id)
                if not resume:
                    return False
                parent_job_id = resume.job_id
                session.delete(resume)
                session.commit()

            JobService.refresh_denorm_flags(parent_job_id)
            logger.info("Deleted resume %s for job %s", resume_id, parent_job_id)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to delete resume %s: %s", resume_id, exc)
            raise

    @staticmethod
    def create_cover_letter(job_id: int, content: str) -> DbCoverLetter:
        """Create a CoverLetter row and refresh denormalized flags.

        Args:
            job_id: Parent job identifier.
            content: Plain text body of the cover letter.
        """
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")
        if not content or not content.strip():
            raise ValueError("content is required")

        try:
            with db_manager.get_session() as session:
                job = session.get(DbJob, job_id)
                if not job:
                    raise ValueError(f"Job {job_id} not found")

                cover = DbCoverLetter(job_id=job_id, content=content.strip(), locked=False)
                session.add(cover)
                session.commit()
                session.refresh(cover)

            JobService.refresh_denorm_flags(job_id)
            logger.info("Created cover letter %s for job %s", cover.id, job_id)
            return cover
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to create cover letter for job %s: %s", job_id, exc)
            raise

    @staticmethod
    def delete_cover_letter(cover_letter_id: int) -> bool:
        """Delete a CoverLetter row and refresh parent job flags.

        Returns True if deleted, False otherwise.
        """
        if not isinstance(cover_letter_id, int) or cover_letter_id <= 0:
            raise ValueError("Invalid cover_letter_id")

        try:
            with db_manager.get_session() as session:
                cover = session.get(DbCoverLetter, cover_letter_id)
                if not cover:
                    return False
                parent_job_id = cover.job_id
                session.delete(cover)
                session.commit()

            JobService.refresh_denorm_flags(parent_job_id)
            logger.info("Deleted cover letter %s for job %s", cover_letter_id, parent_job_id)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to delete cover letter %s: %s", cover_letter_id, exc)
            raise

    @staticmethod
    def create_message(job_id: int, channel: Literal["email", "linkedin"], body: str) -> DbMessage:
        """Create a new message linked to a job. Unsent/unlocked by default."""
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")
        if channel not in ("email", "linkedin"):
            raise ValueError("Invalid message channel")
        if not body or not body.strip():
            raise ValueError("body is required")

        try:
            with db_manager.get_session() as session:
                job = session.get(DbJob, job_id)
                if not job:
                    raise ValueError(f"Job {job_id} not found")

                message = DbMessage(job_id=job_id, channel=channel, body=body.strip(), sent_at=None)
                session.add(message)
                session.commit()
                session.refresh(message)
                logger.info("Created message %s for job %s", message.id, job_id)
                return message
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to create message for job %s: %s", job_id, exc)
            raise

    @staticmethod
    def add_note(job_id: int, content: str) -> DbNote:
        """Add a simple note to a job."""
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")
        if not content or not content.strip():
            raise ValueError("content is required")

        try:
            with db_manager.get_session() as session:
                job = session.get(DbJob, job_id)
                if not job:
                    raise ValueError(f"Job {job_id} not found")

                note = DbNote(job_id=job_id, content=content.strip())
                session.add(note)
                session.commit()
                session.refresh(note)
                logger.info("Created note %s for job %s", note.id, job_id)
                return note
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to add note for job %s: %s", job_id, exc)
            raise

    # ---------- Denormalized flags helpers ----------
    @staticmethod
    def refresh_denorm_flags(job_id: int) -> DbJob | None:
        """Recompute `has_resume` and `has_cover_letter` for a job.

        - has_resume is True iff a canonical `Resume` row exists for the job.
        - has_cover_letter is True if a `CoverLetter` row exists for the job.

        Note: No reliance on `pdf_filename` (deprecated per specs/008-resume_history).
        """
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")

        try:
            with db_manager.get_session() as session:
                job = session.get(DbJob, job_id)
                if not job:
                    return None

                # Presence-only check for canonical resume (do not inspect pdf_filename)
                has_resume = session.exec(select(DbResume.id).where(DbResume.job_id == job_id)).first() is not None
                has_cover_letter = (
                    session.exec(select(DbCoverLetter.id).where(DbCoverLetter.job_id == job_id)).first() is not None
                )

                changed = False
                if job.has_resume != has_resume:
                    job.has_resume = has_resume
                    changed = True
                if job.has_cover_letter != has_cover_letter:
                    job.has_cover_letter = has_cover_letter
                    changed = True

                if changed:
                    session.add(job)
                    session.commit()
                    session.refresh(job)

                return job
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to refresh denorm flags for job %s: %s", job_id, exc)
            raise

    # ---------- Counts for tab badges ----------
    @staticmethod
    def count_job_responses(job_id: int) -> int:
        """Return number of `Response` rows linked to this job."""
        if not isinstance(job_id, int) or job_id <= 0:
            return 0
        try:
            with db_manager.get_session() as session:
                stmt = select(DbResponse).where(DbResponse.job_id == job_id)
                return len(list(session.exec(stmt)))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to count responses for job %s: %s", job_id, exc)
            return 0

    @staticmethod
    def count_job_messages(job_id: int) -> int:
        """Return number of `Message` rows linked to this job."""
        if not isinstance(job_id, int) or job_id <= 0:
            return 0
        try:
            with db_manager.get_session() as session:
                stmt = select(DbMessage).where(DbMessage.job_id == job_id)
                return len(list(session.exec(stmt)))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to count messages for job %s: %s", job_id, exc)
            return 0

    # ---------- Notes helpers ----------
    @staticmethod
    def list_notes(job_id: int) -> list[DbNote]:
        """List notes for a job ordered by created_at desc.

        Args:
            job_id: Parent job identifier.

        Returns:
            A list of notes, newest first. Empty list on error/none.
        """
        if not isinstance(job_id, int) or job_id <= 0:
            return []
        try:
            with db_manager.get_session() as session:
                stmt = select(DbNote).where(DbNote.job_id == job_id).order_by(DbNote.created_at.desc())
                return list(session.exec(stmt))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to list notes for job %s: %s", job_id, exc)
            return []

    @staticmethod
    def count_job_notes(job_id: int) -> int:
        """Return number of `Note` rows linked to this job."""
        if not isinstance(job_id, int) or job_id <= 0:
            return 0
        try:
            with db_manager.get_session() as session:
                stmt = select(DbNote).where(DbNote.job_id == job_id)
                return len(list(session.exec(stmt)))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to count notes for job %s: %s", job_id, exc)
            return 0
