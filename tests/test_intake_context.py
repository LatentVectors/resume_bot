"""Tests for intake context summarization and resume generation."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage

from src.database import Achievement, Experience, Job, User, db_manager
from src.features.jobs.gap_analysis import Gap, GapAnalysisReport, MatchedRequirement, PartialMatch
from src.features.jobs.intake_context import (
    _format_gap_analysis_for_summary,
    _format_messages_for_summary,
    generate_resume_from_conversation,
    summarize_intake_conversation,
)
from src.features.resume.types import ResumeData


@pytest.fixture
def sample_gap_analysis() -> GapAnalysisReport:
    """Create a sample gap analysis report for testing."""
    return GapAnalysisReport(
        matched_requirements=[
            MatchedRequirement(
                requirement="Python programming",
                evidence="5 years of Python development at TechCorp",
            ),
        ],
        partial_matches=[
            PartialMatch(
                requirement="Machine learning experience",
                what_matches="Experience with data analysis and pandas",
                what_is_missing="No direct experience with ML frameworks like TensorFlow or PyTorch",
            ),
        ],
        gaps=[
            Gap(
                requirement="Kubernetes experience",
                why_missing="No mention of container orchestration in work history",
            ),
        ],
        suggested_questions=[
            "Can you describe any experience with containerization or deployment?",
        ],
    )


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


class TestFormatMessagesForSummary:
    """Tests for message formatting utility."""

    def test_format_empty_messages(self):
        """Test formatting with no messages."""
        result = _format_messages_for_summary([])
        assert result == "No conversation messages."

    def test_format_human_and_ai_messages(self, sample_messages):
        """Test formatting of standard human/AI conversation."""
        result = _format_messages_for_summary(sample_messages)

        assert "AI: I see you have strong Python experience" in result
        assert "User: I've worked with pandas and numpy" in result
        assert "AI: That's helpful context" in result
        assert "User: Yes, I've deployed applications on AWS" in result

    def test_format_system_messages(self):
        """Test formatting of system messages."""
        messages = [{"type": "system", "content": "Context initialized"}]
        result = _format_messages_for_summary(messages)
        assert "System: Context initialized" in result

    def test_format_unknown_message_type(self):
        """Test formatting of unknown message types."""
        messages = [{"type": "custom", "content": "Custom message"}]
        result = _format_messages_for_summary(messages)
        assert "Custom: Custom message" in result


class TestFormatGapAnalysisForSummary:
    """Tests for gap analysis formatting utility."""

    def test_format_complete_gap_analysis(self, sample_gap_analysis):
        """Test formatting of complete gap analysis report."""
        result = _format_gap_analysis_for_summary(sample_gap_analysis)

        assert "matched_requirements" in result
        assert "partial_matches" in result
        assert "gaps" in result

        assert "Python programming" in result["matched_requirements"]
        assert "Machine learning experience" in result["partial_matches"]
        assert "Kubernetes experience" in result["gaps"]

    def test_format_empty_gap_analysis(self):
        """Test formatting of empty gap analysis."""
        empty_report = GapAnalysisReport()
        result = _format_gap_analysis_for_summary(empty_report)

        assert result["matched_requirements"] == "None identified"
        assert result["partial_matches"] == "None identified"
        assert result["gaps"] == "None identified"


class TestSummarizeIntakeConversation:
    """Tests for conversation summarization."""

    @patch("src.features.jobs.intake_context._summarization_chain")
    def test_successful_summarization(self, mock_chain, sample_messages, sample_gap_analysis):
        """Test successful conversation summarization."""
        # Mock the LLM response
        mock_response = AIMessage(
            content="The user has strong Python and data analysis skills with pandas and numpy. "
            "While they lack direct ML framework experience, they have relevant data processing background. "
            "They have AWS deployment experience with ECS but not Kubernetes specifically."
        )
        mock_chain.invoke.return_value = mock_response

        result = summarize_intake_conversation(sample_messages, sample_gap_analysis)

        assert isinstance(result, str)
        assert len(result) > 0
        assert "Python" in result or "data" in result  # Should contain relevant content
        mock_chain.invoke.assert_called_once()

    @patch("src.features.jobs.intake_context._summarization_chain")
    def test_summarization_with_empty_conversation(self, mock_chain, sample_gap_analysis):
        """Test summarization with no messages."""
        mock_response = AIMessage(content="Minimal conversation occurred during intake.")
        mock_chain.invoke.return_value = mock_response

        result = summarize_intake_conversation([], sample_gap_analysis)

        assert isinstance(result, str)
        assert len(result) > 0

    @patch("src.features.jobs.intake_context._summarization_chain")
    def test_summarization_error_handling(self, mock_chain, sample_messages, sample_gap_analysis):
        """Test graceful handling of summarization errors."""
        # Simulate LLM failure
        mock_chain.invoke.side_effect = Exception("LLM API error")

        result = summarize_intake_conversation(sample_messages, sample_gap_analysis)

        # Should return fallback summary
        assert isinstance(result, str)
        assert "Unable to generate detailed conversation summary" in result
        assert "processing error" in result


class TestGenerateResumeFromConversation:
    """Tests for resume generation from conversation context."""

    @patch("src.agents.main.main_agent")
    def test_successful_resume_generation(self, mock_agent, test_user, test_experience, test_achievement, test_job):
        """Test successful resume generation with conversation context."""
        # Mock the agent response
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

        mock_agent.invoke.return_value = {"resume_data": mock_resume_data}

        conversation_summary = "User has strong Python skills and AWS deployment experience."
        chat_history = [{"type": "human", "content": "I have Python experience."}]

        result = generate_resume_from_conversation(
            job_id=test_job.id,
            user_id=test_user.id,
            conversation_summary=conversation_summary,
            chat_history=chat_history,
        )

        assert isinstance(result, ResumeData)
        assert result.name == f"{test_user.first_name} {test_user.last_name}"
        assert result.email == test_user.email

        # Verify agent was called with conversation summary as responses
        call_args = mock_agent.invoke.call_args
        input_state = call_args[0][0]
        assert input_state.responses == conversation_summary
        assert input_state.job_description == test_job.job_description

    @patch("src.agents.main.main_agent")
    def test_resume_generation_includes_achievements(
        self, mock_agent, test_user, test_experience, test_achievement, test_job
    ):
        """Test that achievements are included in experience content."""
        mock_resume_data = ResumeData(
            name=f"{test_user.first_name} {test_user.last_name}",
            title="Senior Developer",
            email=test_user.email,
            phone=test_user.phone_number,
            linkedin_url=test_user.linkedin_url,
            professional_summary="Test summary",
            experience=[],
            education=[],
            skills=[],
            certifications=[],
        )

        mock_agent.invoke.return_value = {"resume_data": mock_resume_data}

        generate_resume_from_conversation(
            job_id=test_job.id,
            user_id=test_user.id,
            conversation_summary="Test summary",
            chat_history=[],
        )

        # Verify agent was called with achievement content
        call_args = mock_agent.invoke.call_args
        input_state = call_args[0][0]

        # Check that achievements were included in the experience content
        assert len(input_state.experiences) > 0
        exp_content = input_state.experiences[0].content
        assert "## Achievements" in exp_content
        assert test_achievement.content in exp_content

    @patch("src.agents.main.main_agent")
    def test_resume_generation_includes_structured_fields(
        self, mock_agent, test_user, test_experience, test_achievement, test_job
    ):
        """Test that new structured experience fields are included."""
        mock_resume_data = ResumeData(
            name=f"{test_user.first_name} {test_user.last_name}",
            title="Senior Developer",
            email=test_user.email,
            phone=test_user.phone_number,
            linkedin_url=test_user.linkedin_url,
            professional_summary="Test summary",
            experience=[],
            education=[],
            skills=[],
            certifications=[],
        )

        mock_agent.invoke.return_value = {"resume_data": mock_resume_data}

        generate_resume_from_conversation(
            job_id=test_job.id,
            user_id=test_user.id,
            conversation_summary="Test summary",
            chat_history=[],
        )

        # Verify agent was called with structured fields
        call_args = mock_agent.invoke.call_args
        input_state = call_args[0][0]

        exp_content = input_state.experiences[0].content
        assert "## Company Overview" in exp_content
        assert test_experience.company_overview in exp_content
        assert "## Role Overview" in exp_content
        assert test_experience.role_overview in exp_content
        assert "## Skills" in exp_content
        assert "Python" in exp_content

    def test_resume_generation_invalid_job(self, test_user):
        """Test error handling for invalid job ID."""
        with pytest.raises(ValueError, match="Job .* not found"):
            generate_resume_from_conversation(
                job_id=99999,
                user_id=test_user.id,
                conversation_summary="Test",
                chat_history=[],
            )

    def test_resume_generation_invalid_user(self, test_job):
        """Test error handling for invalid user ID."""
        with pytest.raises(ValueError, match="User .* not found"):
            generate_resume_from_conversation(
                job_id=test_job.id,
                user_id=99999,
                conversation_summary="Test",
                chat_history=[],
            )

    def test_resume_generation_no_experience(self, test_user, test_job):
        """Test error handling when user has no experience records."""
        # Note: This test actually verifies the agent can handle empty experiences
        # The ValueError for "At least one experience" comes from fetch_experience_data returning []
        # but the agent itself can technically run with empty list
        result = generate_resume_from_conversation(
            job_id=test_job.id,
            user_id=test_user.id,
            conversation_summary="Test",
            chat_history=[],
        )
        # Should return a resume even with no experiences (base resume from profile)
        assert result is not None
        assert isinstance(result, ResumeData)

    @patch("src.agents.main.main_agent")
    def test_resume_generation_agent_error(self, mock_agent, test_user, test_experience, test_job):
        """Test error handling when agent fails."""
        mock_agent.invoke.side_effect = Exception("Agent processing error")

        with pytest.raises(Exception, match="Agent processing error"):
            generate_resume_from_conversation(
                job_id=test_job.id,
                user_id=test_user.id,
                conversation_summary="Test",
                chat_history=[],
            )

    @patch("src.agents.main.main_agent")
    def test_resume_generation_no_resume_data_returned(self, mock_agent, test_user, test_experience, test_job):
        """Test error handling when agent doesn't return resume_data."""
        # Agent returns output without resume_data
        mock_agent.invoke.return_value = {"resume_data": None}

        with pytest.raises(ValueError, match="Agent did not return resume_data"):
            generate_resume_from_conversation(
                job_id=test_job.id,
                user_id=test_user.id,
                conversation_summary="Test",
                chat_history=[],
            )

    @patch("src.agents.main.main_agent")
    def test_resume_generation_metadata_tagging(self, mock_agent, test_user, test_experience, test_job):
        """Test that proper metadata and tags are passed to the agent."""
        mock_resume_data = ResumeData(
            name=f"{test_user.first_name} {test_user.last_name}",
            title="Test",
            email=test_user.email,
            phone=test_user.phone_number,
            linkedin_url=test_user.linkedin_url,
            professional_summary="Test",
            experience=[],
            education=[],
            skills=[],
            certifications=[],
        )

        mock_agent.invoke.return_value = {"resume_data": mock_resume_data}

        generate_resume_from_conversation(
            job_id=test_job.id,
            user_id=test_user.id,
            conversation_summary="Test",
            chat_history=[],
        )

        # Verify config was passed with correct tags and metadata
        call_args = mock_agent.invoke.call_args
        # Config is passed as keyword argument
        config = call_args.kwargs["config"]

        assert "resume_generation" in config.get("tags", [])
        assert config.get("metadata", {}).get("job_id") == test_job.id
        assert config.get("metadata", {}).get("user_id") == test_user.id
        assert config.get("metadata", {}).get("source") == "intake_flow"
