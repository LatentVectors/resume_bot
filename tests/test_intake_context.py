"""Tests for intake context summarization and resume generation."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest

from app.services.job_intake_service import generate_resume_from_conversation
from src.database import Achievement, Experience, Job, User, db_manager
from src.features.resume.types import ResumeData


@pytest.fixture
def sample_messages() -> list[dict]:
    """Create sample LangChain-format messages for testing."""
    return [
        {"type": "ai", "content": "I see you have strong Python experience. Can you tell me more about your ML work?"},
        {
            "type": "human",
            "content": "I've worked with pandas and numpy extensively for data analysis, but haven't used deep learning frameworks in production.",
        },
        {
            "type": "ai",
            "content": "That's helpful context. Have you worked with any cloud deployment technologies?",
        },
        {
            "type": "human",
            "content": "Yes, I've deployed applications on AWS using ECS, but not Kubernetes specifically.",
        },
    ]


@pytest.fixture
def test_user() -> User:
    """Create a test user."""
    user = User(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        phone_number="555-0100",
        linkedin_url="https://linkedin.com/in/testuser",
    )
    user_id = db_manager.add_user(user)
    user.id = user_id
    yield user
    # Cleanup
    db_manager.delete_user(user_id)


@pytest.fixture
def test_experience(test_user: User) -> Experience:
    """Create a test experience for the user."""
    exp = Experience(
        user_id=test_user.id,
        company_name="TechCorp",
        job_title="Senior Developer",
        location="San Francisco, CA",
        start_date=date(2020, 1, 1),
        end_date=None,
        content="Developed Python applications and data pipelines using pandas and numpy.",
        company_overview="Leading technology company",
        role_overview="Led backend development team",
        skills=["Python", "pandas", "numpy", "AWS"],
    )
    exp_id = db_manager.add_experience(exp)
    exp.id = exp_id
    return exp


@pytest.fixture
def test_achievement(test_experience: Experience) -> Achievement:
    """Create a test achievement."""
    achievement = Achievement(
        experience_id=test_experience.id,
        title="Data Pipeline Optimization",
        content="Optimized data pipeline reducing processing time by 50%",
        order=0,
    )
    achievement_id = db_manager.add_achievement(achievement)
    achievement.id = achievement_id
    return achievement


@pytest.fixture
def test_job(test_user: User) -> Job:
    """Create a test job."""
    job = Job(
        user_id=test_user.id,
        job_description="Looking for a Senior Python Developer with ML experience and Kubernetes knowledge.",
        company_name="DataCorp",
        job_title="Senior ML Engineer",
        status="Saved",
    )
    job_id = db_manager.add_job(job)
    job.id = job_id
    return job


class TestGenerateResumeFromConversation:
    """Tests for resume generation from conversation context."""

    @patch("app.services.job_intake_service.workflows.resume_generation._chain")
    def test_successful_resume_generation(self, mock_chain, test_user, test_experience, test_achievement, test_job):
        """Test successful resume generation with conversation context."""
        # Mock the chain response
        mock_resume_data = ResumeData(
            name=f"{test_user.first_name} {test_user.last_name}",
            title="Senior ML Engineer",
            email=test_user.email,
            phone=test_user.phone_number,
            linkedin_url=test_user.linkedin_url,
            professional_summary="Experienced Python developer with data analysis expertise",
            experience=[],
            education=[],
            skills=["Python", "pandas", "numpy", "AWS"],
            certifications=[],
        )

        mock_chain.invoke.return_value = mock_resume_data

        # Create sample messages
        from langchain_core.messages import AIMessage as LCAIMessage
        from langchain_core.messages import HumanMessage

        messages = [
            LCAIMessage(content="Gap analysis shows strong Python experience."),
            HumanMessage(content="I have Python experience with data pipelines."),
        ]

        result = generate_resume_from_conversation(
            job_id=test_job.id,
            user_id=test_user.id,
            messages=messages,
        )

        assert isinstance(result, ResumeData)
        assert result.name == f"{test_user.first_name} {test_user.last_name}"
        assert result.email == test_user.email

        # Verify chain was called
        mock_chain.invoke.assert_called_once()

    def test_resume_generation_invalid_job(self, test_user):
        """Test error handling for invalid job ID."""
        from langchain_core.messages import HumanMessage

        with pytest.raises(ValueError, match="Job .* not found"):
            generate_resume_from_conversation(
                job_id=99999,
                user_id=test_user.id,
                messages=[HumanMessage(content="Test")],
            )

    def test_resume_generation_invalid_user(self, test_job):
        """Test error handling for invalid user ID."""
        from langchain_core.messages import HumanMessage

        with pytest.raises(ValueError, match="User .* not found"):
            generate_resume_from_conversation(
                job_id=test_job.id,
                user_id=99999,
                messages=[HumanMessage(content="Test")],
            )

    def test_resume_generation_no_experience(self, test_user, test_job):
        """Test error handling when user has no experience records."""
        from langchain_core.messages import HumanMessage

        with pytest.raises(ValueError, match="At least one experience"):
            generate_resume_from_conversation(
                job_id=test_job.id,
                user_id=test_user.id,
                messages=[HumanMessage(content="Test")],
            )

    @patch("app.services.job_intake_service.workflows.resume_generation._chain")
    def test_resume_generation_chain_error(self, mock_chain, test_user, test_experience, test_job):
        """Test error handling when chain fails."""
        from langchain_core.messages import HumanMessage

        mock_chain.invoke.side_effect = Exception("Chain processing error")

        with pytest.raises(Exception, match="Chain processing error"):
            generate_resume_from_conversation(
                job_id=test_job.id,
                user_id=test_user.id,
                messages=[HumanMessage(content="Test")],
            )

    @patch("app.services.job_intake_service.workflows.resume_generation._chain")
    def test_resume_generation_no_resume_data_returned(self, mock_chain, test_user, test_experience, test_job):
        """Test error handling when chain doesn't return resume_data."""
        from langchain_core.messages import HumanMessage

        # Chain returns None
        mock_chain.invoke.return_value = None

        with pytest.raises(ValueError, match="Failed to generate resume data"):
            generate_resume_from_conversation(
                job_id=test_job.id,
                user_id=test_user.id,
                messages=[HumanMessage(content="Test")],
            )
