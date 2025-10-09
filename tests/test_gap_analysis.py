"""Tests for gap analysis feature."""

from __future__ import annotations

from datetime import date

import pytest

from src.database import Experience
from src.features.jobs.gap_analysis import analyze_job_experience_fit


@pytest.fixture
def sample_experience() -> Experience:
    """Create a sample experience with new fields."""
    return Experience(
        id=1,
        user_id=1,
        company_name="Tech Corp",
        job_title="Senior Software Engineer",
        location="San Francisco, CA",
        start_date=date(2020, 1, 1),
        end_date=date(2023, 12, 31),
        content="Led development of microservices architecture. Implemented CI/CD pipelines.",
        company_overview="Leading technology company focused on cloud infrastructure",
        role_overview="Led backend development team, architected scalable systems",
        skills=["Python", "AWS", "Docker", "Kubernetes", "PostgreSQL"],
    )


@pytest.fixture
def legacy_experience() -> Experience:
    """Create a legacy experience without new fields."""
    return Experience(
        id=2,
        user_id=1,
        company_name="StartupXYZ",
        job_title="Full Stack Developer",
        location="New York, NY",
        start_date=date(2018, 6, 1),
        end_date=date(2019, 12, 31),
        content="Built web applications using React and Node.js. Worked with MongoDB and Express.",
    )


@pytest.fixture
def entry_level_experience() -> Experience:
    """Create an entry-level experience."""
    return Experience(
        id=3,
        user_id=1,
        company_name="Consulting Firm",
        job_title="Junior Analyst",
        location="Boston, MA",
        start_date=date(2021, 1, 1),
        end_date=None,  # Current position
        content="Performed data analysis and created reports for clients.",
        company_overview="Management consulting firm serving Fortune 500 companies",
        role_overview="Supported senior consultants with data analysis and reporting",
        skills=["Excel", "PowerPoint", "SQL", "Tableau"],
    )


def test_technical_job_with_matching_experience(sample_experience: Experience) -> None:
    """Test gap analysis with a technical job that matches experience."""
    job_description = """
    Senior Backend Engineer
    
    We are looking for an experienced backend engineer to join our cloud infrastructure team.
    
    Requirements:
    - 5+ years of experience with Python
    - Strong experience with AWS and cloud architecture
    - Experience with containerization (Docker, Kubernetes)
    - Database design and optimization skills
    - Experience with microservices architecture
    """

    report = analyze_job_experience_fit(job_description, [sample_experience])

    # Should have no error
    assert not report.has_error

    # Should identify some matched requirements
    assert len(report.matched_requirements) > 0

    # May have partial matches or gaps
    # Just verify the structure is correct
    assert isinstance(report.partial_matches, list)
    assert isinstance(report.gaps, list)
    assert isinstance(report.suggested_questions, list)


def test_non_technical_job_with_gap(sample_experience: Experience) -> None:
    """Test gap analysis with a non-technical job showing gaps."""
    job_description = """
    Marketing Manager
    
    We need an experienced marketing professional to lead our digital marketing efforts.
    
    Requirements:
    - 5+ years in digital marketing
    - Experience with SEO/SEM
    - Social media marketing expertise
    - Content strategy development
    - Team management experience
    """

    report = analyze_job_experience_fit(job_description, [sample_experience])

    assert not report.has_error

    # Should identify significant gaps since experience is technical
    assert len(report.gaps) > 0

    # Should have suggested questions
    assert len(report.suggested_questions) > 0


def test_entry_level_job_with_limited_experience(
    entry_level_experience: Experience,
) -> None:
    """Test gap analysis for entry-level position."""
    job_description = """
    Data Analyst
    
    Join our analytics team to help derive insights from data.
    
    Requirements:
    - 1-2 years experience in data analysis
    - Proficiency in SQL and Excel
    - Experience with data visualization tools
    - Strong analytical and problem-solving skills
    """

    report = analyze_job_experience_fit(job_description, [entry_level_experience])

    assert not report.has_error

    # Should have some matches for SQL, Excel, Tableau
    assert len(report.matched_requirements) > 0 or len(report.partial_matches) > 0


def test_senior_role_with_mixed_experience(
    sample_experience: Experience, legacy_experience: Experience
) -> None:
    """Test gap analysis with multiple experiences for senior role."""
    job_description = """
    Engineering Manager
    
    Lead our engineering team building next-generation cloud applications.
    
    Requirements:
    - 8+ years software engineering experience
    - 2+ years in leadership/management
    - Full-stack development experience
    - Cloud infrastructure expertise (AWS/GCP/Azure)
    - Experience scaling engineering teams
    """

    report = analyze_job_experience_fit(
        job_description, [sample_experience, legacy_experience]
    )

    assert not report.has_error

    # Should identify both matches and gaps
    assert (
        len(report.matched_requirements) > 0
        or len(report.partial_matches) > 0
        or len(report.gaps) > 0
    )


def test_legacy_experience_format(legacy_experience: Experience) -> None:
    """Test that legacy experiences work correctly."""
    job_description = """
    Full Stack Developer
    
    Build modern web applications using React and Node.js.
    
    Requirements:
    - Experience with React and Node.js
    - Database experience (MongoDB or PostgreSQL)
    - RESTful API design
    """

    report = analyze_job_experience_fit(job_description, [legacy_experience])

    assert not report.has_error

    # Should process legacy content field correctly
    assert len(report.matched_requirements) > 0


def test_no_experience() -> None:
    """Test gap analysis with no experience."""
    job_description = """
    Software Engineer
    
    Requirements:
    - 3+ years Python experience
    - AWS knowledge
    """

    report = analyze_job_experience_fit(job_description, [])

    assert not report.has_error

    # Should identify all requirements as gaps
    assert len(report.gaps) > 0


def test_multiple_experiences_comprehensive(
    sample_experience: Experience,
    legacy_experience: Experience,
    entry_level_experience: Experience,
) -> None:
    """Test with all experience types combined."""
    job_description = """
    Technical Product Manager
    
    Bridge the gap between engineering and business.
    
    Requirements:
    - Strong technical background in software development
    - Experience with cloud technologies
    - Data analysis skills
    - Cross-functional collaboration experience
    - Product strategy and roadmap development
    """

    report = analyze_job_experience_fit(
        job_description,
        [sample_experience, legacy_experience, entry_level_experience],
    )

    assert not report.has_error

    # Should have a comprehensive analysis across all categories
    total_items = (
        len(report.matched_requirements)
        + len(report.partial_matches)
        + len(report.gaps)
    )
    assert total_items > 0

    # Should suggest relevant questions
    assert len(report.suggested_questions) > 0


def test_error_handling_with_invalid_description() -> None:
    """Test error handling with problematic input."""
    # Empty job description should still work, just may have different results
    report = analyze_job_experience_fit("", [])

    # Should not raise an error, should return report with or without error flag
    assert isinstance(report.matched_requirements, list)
    assert isinstance(report.partial_matches, list)
    assert isinstance(report.gaps, list)
    assert isinstance(report.suggested_questions, list)

