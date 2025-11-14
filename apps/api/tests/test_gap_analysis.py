"""Tests for gap analysis feature."""

from __future__ import annotations

from datetime import date

import pytest

from app.services.job_intake_service import analyze_job_experience_fit
from src.database import Experience


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

    # Should return a non-empty string (formatted markdown report)
    assert isinstance(report, str)
    assert len(report) > 0

    # Should contain key sections from the gap analysis format
    assert "Strategic Report" in report or "Areas of Strong Alignment" in report


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

    # Should return a non-empty string report
    assert isinstance(report, str)
    assert len(report) > 0

    # Should likely identify gaps since experience is technical
    assert "Gap" in report or "missing" in report.lower()


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

    # Should return a non-empty string report
    assert isinstance(report, str)
    assert len(report) > 0


def test_senior_role_with_mixed_experience(sample_experience: Experience, legacy_experience: Experience) -> None:
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

    report = analyze_job_experience_fit(job_description, [sample_experience, legacy_experience])

    # Should return a non-empty string report
    assert isinstance(report, str)
    assert len(report) > 0


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

    # Should return a non-empty string report
    assert isinstance(report, str)
    assert len(report) > 0


def test_no_experience() -> None:
    """Test gap analysis with no experience."""
    job_description = """
    Software Engineer
    
    Requirements:
    - 3+ years Python experience
    - AWS knowledge
    """

    report = analyze_job_experience_fit(job_description, [])

    # Should return a string report (may be empty or indicate no experience)
    assert isinstance(report, str)


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

    # Should return a comprehensive non-empty string report
    assert isinstance(report, str)
    assert len(report) > 0


def test_error_handling_with_invalid_description() -> None:
    """Test error handling with problematic input."""
    # Empty job description should still work, just may have different results
    report = analyze_job_experience_fit("", [])

    # Should return a string (even if empty or error message)
    assert isinstance(report, str)
