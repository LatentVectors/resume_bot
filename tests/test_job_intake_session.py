"""Tests for job intake session management."""

from __future__ import annotations

import os
import tempfile

from app.services.job_service import JobService
from src.database import DatabaseManager, Job, User


class TestJobIntakeSession:
    """Test cases for job intake session lifecycle."""

    def test_intake_session_lifecycle(self):
        """Test session lifecycle: create → update steps → save analysis/summary → complete."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_url = f"sqlite:///{tmp.name}"

        try:
            db_manager = DatabaseManager(db_url)

            # Create a user
            user = User(first_name="John", last_name="Doe")
            user_id = db_manager.add_user(user)

            # Create a job
            job = Job(
                user_id=user_id,
                job_description="Test job description",
                company_name="Test Company",
                job_title="Software Engineer",
                status="Saved",
            )
            job_id = db_manager.add_job(job)

            # Step 1: Create intake session
            session = JobService.create_intake_session(job_id)
            assert session is not None
            assert session.job_id == job_id
            assert session.current_step == 1
            assert session.step1_completed is False
            assert session.step2_completed is False
            assert session.step3_completed is False
            assert session.completed_at is None

            # Step 2: Update to step 1 and mark as completed
            session = JobService.update_session_step(session.id, step=1, completed=True)  # type: ignore[arg-type]
            assert session is not None
            assert session.step1_completed is True
            assert session.current_step == 1

            # Step 3: Move to step 2
            session = JobService.update_session_step(session.id, step=2, completed=False)  # type: ignore[arg-type]
            assert session is not None
            assert session.current_step == 2
            assert session.step2_completed is False

            # Step 4: Save gap analysis
            gap_analysis_json = '{"matched_requirements": [], "gaps": []}'
            session = JobService.save_gap_analysis(session.id, gap_analysis_json)  # type: ignore[arg-type]
            assert session is not None
            assert session.gap_analysis_json == gap_analysis_json

            # Step 5: Mark step 2 as completed
            session = JobService.update_session_step(session.id, step=2, completed=True)  # type: ignore[arg-type]
            assert session is not None
            assert session.step2_completed is True

            # Step 6: Move to step 3
            session = JobService.update_session_step(session.id, step=3, completed=False)  # type: ignore[arg-type]
            assert session is not None
            assert session.current_step == 3

            # Step 7: Save conversation summary
            summary = "User wants to highlight leadership experience and technical skills."
            session = JobService.save_conversation_summary(session.id, summary)  # type: ignore[arg-type]
            assert session is not None
            assert session.conversation_summary == summary

            # Step 8: Mark step 3 as completed
            session = JobService.update_session_step(session.id, step=3, completed=True)  # type: ignore[arg-type]
            assert session is not None
            assert session.step3_completed is True

            # Step 9: Complete the session
            session = JobService.complete_session(session.id)  # type: ignore[arg-type]
            assert session is not None
            assert session.completed_at is not None

            # Verify we can retrieve the session
            retrieved_session = JobService.get_intake_session(job_id)
            assert retrieved_session is not None
            assert retrieved_session.id == session.id
            assert retrieved_session.gap_analysis_json == gap_analysis_json
            assert retrieved_session.conversation_summary == summary
            assert retrieved_session.completed_at is not None

        finally:
            os.unlink(tmp.name)

    def test_create_intake_session_idempotent(self):
        """Test that creating a session for an existing job returns the existing session."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_url = f"sqlite:///{tmp.name}"

        try:
            db_manager = DatabaseManager(db_url)

            # Create a user
            user = User(first_name="Jane", last_name="Smith")
            user_id = db_manager.add_user(user)

            # Create a job
            job = Job(
                user_id=user_id,
                job_description="Another test job",
                company_name="Another Company",
                job_title="Data Scientist",
                status="Saved",
            )
            job_id = db_manager.add_job(job)

            # Create first session
            session1 = JobService.create_intake_session(job_id)
            assert session1 is not None
            session1_id = session1.id

            # Attempt to create second session for same job
            session2 = JobService.create_intake_session(job_id)
            assert session2 is not None
            assert session2.id == session1_id  # Should return the same session

        finally:
            os.unlink(tmp.name)

    def test_get_intake_session_nonexistent(self):
        """Test that getting a non-existent session returns None."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_url = f"sqlite:///{tmp.name}"

        try:
            DatabaseManager(db_url)

            # Try to get session for non-existent job
            session = JobService.get_intake_session(999)
            assert session is None

        finally:
            os.unlink(tmp.name)

    def test_update_session_step_validation(self):
        """Test that update_session_step validates step values."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_url = f"sqlite:///{tmp.name}"

        try:
            db_manager = DatabaseManager(db_url)

            # Create a user and job
            user = User(first_name="Test", last_name="User")
            user_id = db_manager.add_user(user)
            job = Job(
                user_id=user_id,
                job_description="Test",
                status="Saved",
            )
            job_id = db_manager.add_job(job)

            # Create session
            session = JobService.create_intake_session(job_id)

            # Try invalid step values
            try:
                JobService.update_session_step(session.id, step=0)  # type: ignore[arg-type]
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Step must be 1, 2, or 3" in str(e)

            try:
                JobService.update_session_step(session.id, step=4)  # type: ignore[arg-type]
                raise AssertionError("Should have raised ValueError")
            except ValueError as e:
                assert "Step must be 1, 2, or 3" in str(e)

        finally:
            os.unlink(tmp.name)

    def test_step1_job_creation_and_session_initialization(self):
        """Test Step 1: job creation and session initialization flow."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_url = f"sqlite:///{tmp.name}"

        try:
            db_manager = DatabaseManager(db_url)

            # Create a user (simulating existing user)
            user = User(first_name="Step1", last_name="Tester")
            user_id = db_manager.add_user(user)

            # Simulate Step 1: Save job with provided details
            description = "We are looking for a Senior Python Developer with 5+ years experience."
            job = JobService.save_job(
                title="Senior Python Developer",
                company="Tech Corp",
                description=description,
                favorite=True,
            )
            assert job is not None
            assert job.job_description == description
            assert job.is_favorite is True
            assert job.status == "Saved"

            # Verify updates
            updated_job = JobService.get_job(job.id)
            assert updated_job is not None
            assert updated_job.job_title == "Senior Python Developer"
            assert updated_job.company_name == "Tech Corp"

            # Create intake session (as Step 1 does)
            session = JobService.create_intake_session(job.id)
            assert session is not None
            assert session.job_id == job.id
            assert session.current_step == 1
            assert session.step1_completed is False

            # Update to step 2 (as Step 1 does when clicking Next)
            session = JobService.update_session_step(session.id, step=2, completed=False)  # type: ignore[arg-type]
            assert session is not None
            assert session.current_step == 2

            # Verify session can be retrieved
            retrieved_session = JobService.get_intake_session(job.id)
            assert retrieved_session is not None
            assert retrieved_session.id == session.id
            assert retrieved_session.current_step == 2

        finally:
            os.unlink(tmp.name)
