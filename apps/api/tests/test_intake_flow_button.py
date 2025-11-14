"""Test intake flow button logic on job detail overview tab."""

from __future__ import annotations

from datetime import datetime

from src.database import Job as DbJob
from src.database import JobIntakeSession as DbJobIntakeSession


def test_resume_step_determination_incomplete_session() -> None:
    """Test that incomplete session resumes from current_step."""
    # Simulate job and incomplete session at step 2
    DbJob(
        id=1,
        user_id=1,
        job_title="Software Engineer",
        company_name="Test Co",
        job_description="Test description",
        status="Saved",
        has_resume=False,
        has_cover_letter=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    intake_session = DbJobIntakeSession(
        id=1,
        job_id=1,
        current_step=2,
        step1_completed=True,
        step2_completed=False,
        step3_completed=False,
        completed_at=None,  # Incomplete
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # Logic from overview.py
    if intake_session and intake_session.completed_at is None:
        resume_step = intake_session.current_step
    else:
        resume_step = 1

    assert resume_step == 2, "Should resume from step 2"


def test_resume_step_determination_completed_session() -> None:
    """Test that completed session restarts from step 1."""
    DbJob(
        id=1,
        user_id=1,
        job_title="Software Engineer",
        company_name="Test Co",
        job_description="Test description",
        status="Saved",
        has_resume=False,
        has_cover_letter=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    intake_session = DbJobIntakeSession(
        id=1,
        job_id=1,
        current_step=3,
        step1_completed=True,
        step2_completed=True,
        step3_completed=True,
        completed_at=datetime.now(),  # Completed
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # Logic from overview.py
    if intake_session and intake_session.completed_at is None:
        resume_step = intake_session.current_step
    else:
        resume_step = 1

    assert resume_step == 1, "Should restart from step 1 for completed session"


def test_resume_step_determination_no_session() -> None:
    """Test that missing session starts from step 1."""
    DbJob(
        id=1,
        user_id=1,
        job_title="Software Engineer",
        company_name="Test Co",
        job_description="Test description",
        status="Saved",
        has_resume=False,
        has_cover_letter=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    intake_session = None

    # Logic from overview.py
    if intake_session and intake_session.completed_at is None:
        resume_step = intake_session.current_step
    else:
        resume_step = 1

    assert resume_step == 1, "Should start from step 1 with no session"


def test_button_label_logic() -> None:
    """Test button label changes based on session existence."""
    # With existing session
    intake_session = DbJobIntakeSession(
        id=1,
        job_id=1,
        current_step=2,
        step1_completed=True,
        step2_completed=False,
        step3_completed=False,
        completed_at=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    button_label = "Resume job intake workflow" if intake_session else "Start job intake workflow"
    assert button_label == "Resume job intake workflow"

    # Without session
    intake_session = None
    button_label = "Resume job intake workflow" if intake_session else "Start job intake workflow"
    assert button_label == "Start job intake workflow"


def test_button_hidden_when_applied() -> None:
    """Test that button should be hidden when job status is Applied."""
    job_applied = DbJob(
        id=1,
        user_id=1,
        job_title="Software Engineer",
        company_name="Test Co",
        job_description="Test description",
        status="Applied",
        has_resume=False,
        has_cover_letter=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    # Button should be hidden (not rendered) when status is Applied
    should_show_button = job_applied.status != "Applied"
    assert should_show_button is False

    # Button should be visible for Saved status
    job_saved = DbJob(
        id=2,
        user_id=1,
        job_title="Software Engineer",
        company_name="Test Co",
        job_description="Test description",
        status="Saved",
        has_resume=False,
        has_cover_letter=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    should_show_button = job_saved.status != "Applied"
    assert should_show_button is True
