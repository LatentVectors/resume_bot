"""Service for cover letter versioning, data management, and preview rendering."""

from __future__ import annotations

import hashlib
from collections import OrderedDict
from pathlib import Path

import streamlit as st
from sqlmodel import select

from src.database import CoverLetter as DbCoverLetter
from src.database import CoverLetterVersion as DbCoverLetterVersion
from src.database import db_manager
from src.features.cover_letter.types import CoverLetterData
from src.features.cover_letter.utils import (
    list_available_templates as list_templates_from_dir,
)
from src.features.cover_letter.utils import (
    render_template_to_html,
    render_template_to_pdf_bytes,
)
from src.logging_config import logger

from .job_service import JobService


def _cover_letter_templates_dir() -> Path:
    """Return the path to the cover letter templates directory."""
    return Path(__file__).parent.parent.parent / "src" / "features" / "cover_letter" / "templates"


class CoverLetterService:
    """Service class for cover letter-related operations."""

    @staticmethod
    def save_cover_letter(job_id: int, cover_data: CoverLetterData, template_name: str) -> DbCoverLetterVersion:
        """Create a new cover letter version without auto-pinning.

        Creates a new CoverLetterVersion record with auto-incrementing version_index.
        Does NOT automatically update the canonical row - pinning must be done explicitly.

        Args:
            job_id: Parent job identifier
            cover_data: Cover letter data to save
            template_name: Template filename (e.g., "cover_000.html")

        Returns:
            Newly created DbCoverLetterVersion instance

        Raises:
            ValueError: If job_id is invalid or job not found
            PermissionError: If job is already applied (locked)
        """
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")
        if not template_name or not template_name.strip():
            raise ValueError("template_name is required")

        job = JobService.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        if job.applied_at is not None:
            raise PermissionError("Job is applied; cover letter save is locked")

        try:
            with db_manager.get_session() as session:
                # Get or create canonical cover letter row (for reference/linking only)
                canonical = session.exec(select(DbCoverLetter).where(DbCoverLetter.job_id == job_id)).first()

                if not canonical:
                    # Create initial canonical row only on first save
                    canonical = DbCoverLetter(
                        job_id=job_id,
                        cover_letter_json=cover_data.model_dump_json(),
                        template_name=template_name,
                        locked=False,
                    )
                    session.add(canonical)
                    session.commit()
                    session.refresh(canonical)
                # Note: Do NOT auto-update canonical on subsequent saves - user must pin explicitly

                # Determine next version index
                head_version = session.exec(
                    select(DbCoverLetterVersion)
                    .where(DbCoverLetterVersion.job_id == job_id)
                    .order_by(DbCoverLetterVersion.version_index.desc())
                ).first()

                next_index = 1 if head_version is None else int(head_version.version_index) + 1

                # Create new version
                version = DbCoverLetterVersion(
                    cover_letter_id=int(canonical.id),  # type: ignore[arg-type]
                    job_id=job_id,
                    version_index=next_index,
                    cover_letter_json=cover_data.model_dump_json(),
                    template_name=template_name,
                    created_by_user_id=int(job.user_id),
                )

                session.add(version)
                session.commit()
                session.refresh(version)

                logger.info(
                    "Created CoverLetterVersion",
                    extra={
                        "job_id": job_id,
                        "version_index": next_index,
                        "template_name": template_name,
                    },
                )

            # Update job flags
            try:
                JobService.refresh_denorm_flags(job_id)
            except Exception as exc:  # noqa: BLE001
                logger.exception(exc)

            return version

        except Exception as exc:  # noqa: BLE001
            logger.exception(exc)
            raise

    @staticmethod
    def list_versions(job_id: int) -> list[DbCoverLetterVersion]:
        """List all cover letter versions for a job ordered by version_index ascending.

        Args:
            job_id: Parent job identifier

        Returns:
            List of cover letter versions, oldest first

        Raises:
            ValueError: If job_id is invalid
        """
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")

        with db_manager.get_session() as session:
            rows = session.exec(
                select(DbCoverLetterVersion)
                .where(DbCoverLetterVersion.job_id == job_id)
                .order_by(DbCoverLetterVersion.version_index.asc())
            ).all()
            return list(rows)

    @staticmethod
    def get_canonical(job_id: int) -> DbCoverLetter | None:
        """Return canonical CoverLetter row for a job if present.

        Args:
            job_id: Parent job identifier

        Returns:
            Canonical cover letter or None if not found

        Raises:
            ValueError: If job_id is invalid
        """
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")

        with db_manager.get_session() as session:
            return session.exec(select(DbCoverLetter).where(DbCoverLetter.job_id == job_id)).first()

    @staticmethod
    def pin_canonical(job_id: int, version_id: int) -> DbCoverLetter:
        """Set the canonical CoverLetter row for a job from a version snapshot.

        Copies template_name and cover_letter_json from the specified version
        to the canonical CoverLetter row.

        Args:
            job_id: Parent job identifier
            version_id: Version to pin as canonical

        Returns:
            Updated canonical cover letter

        Raises:
            ValueError: If job_id or version_id is invalid, or version not found
        """
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")
        if not isinstance(version_id, int) or version_id <= 0:
            raise ValueError("Invalid version_id")

        with db_manager.get_session() as session:
            version = session.get(DbCoverLetterVersion, version_id)
            if version is None or version.job_id != job_id:
                raise ValueError("Version not found for job")

            existing = session.exec(select(DbCoverLetter).where(DbCoverLetter.job_id == job_id)).first()
            if existing:
                existing.template_name = version.template_name
                existing.cover_letter_json = version.cover_letter_json
                session.add(existing)
            else:
                existing = DbCoverLetter(
                    job_id=job_id,
                    template_name=version.template_name,
                    cover_letter_json=version.cover_letter_json,
                    locked=False,
                )
                session.add(existing)

            session.commit()
            session.refresh(existing)

        # Update job flags
        try:
            JobService.refresh_denorm_flags(job_id)
        except Exception as exc:  # noqa: BLE001
            logger.exception(exc)

        return existing

    @staticmethod
    def get_cover_letter_for_job(job_id: int) -> DbCoverLetter | None:
        """Retrieve canonical cover letter for a job.

        This is an alias for get_canonical() for consistency with spec naming.

        Args:
            job_id: Parent job identifier

        Returns:
            Canonical cover letter or None if not found
        """
        return CoverLetterService.get_canonical(job_id)

    @staticmethod
    def render_preview(job_id: int, cover_data: CoverLetterData, template_name: str) -> bytes:
        """Render a temporary preview PDF and return bytes (no disk I/O).

        Uses an in-session LRU cache of up to 25 rendered PDFs per job. The
        cache key is a SHA-256 hash of the fully-populated HTML (template +
        content), so different content or template selections produce distinct
        entries. Cache is cleared on job change in the job page.

        Args:
            job_id: Parent job identifier (for cache scoping)
            cover_data: Cover letter data to render
            template_name: Template filename to use

        Returns:
            PDF as bytes

        Raises:
            ValueError: If job_id or template_name is invalid
        """
        if not isinstance(job_id, int) or job_id <= 0:
            raise ValueError("Invalid job_id")
        if not template_name or not template_name.strip():
            raise ValueError("template_name is required")

        try:
            # Initialize cache container in session_state as dict[job_id -> OrderedDict[key -> bytes]]
            cache_root = st.session_state.get("cover_letter_pdf_cache")
            if not isinstance(cache_root, dict):
                cache_root = {}
                st.session_state["cover_letter_pdf_cache"] = cache_root

            job_cache = cache_root.get(job_id)
            if not isinstance(job_cache, OrderedDict):
                job_cache = OrderedDict()
                cache_root[job_id] = job_cache

            # Build HTML and compute stable hash key
            templates_dir = _cover_letter_templates_dir()
            html = render_template_to_html(
                template_name=template_name,
                context=cover_data.model_dump(),
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
            pdf_bytes = render_template_to_pdf_bytes(
                template_name=template_name,
                context=cover_data.model_dump(),
                templates_dir=templates_dir,
            )
            job_cache[key] = pdf_bytes
            # Enforce capacity 25 per job
            while len(job_cache) > 25:
                try:
                    job_cache.popitem(last=False)
                except Exception:
                    break

            return pdf_bytes
        except Exception as exc:  # noqa: BLE001
            logger.exception(exc)
            raise

    @staticmethod
    def list_available_templates() -> list[str]:
        """List cover letter templates from the templates directory.

        Returns:
            List of template filenames, sorted alphabetically

        Raises:
            FileNotFoundError: If templates directory doesn't exist
        """
        templates_dir = _cover_letter_templates_dir()
        return list_templates_from_dir(templates_dir)
