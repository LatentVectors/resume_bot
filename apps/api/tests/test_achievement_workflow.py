"""Test achievement management workflow."""

from __future__ import annotations

import pytest

from app.services.experience_service import ExperienceService
from src.database import db_manager


@pytest.fixture
def user_id(tmp_path):
    """Create a test user and return their ID."""
    from src.database import User

    user = User(first_name="Test", last_name="User")
    user_id = db_manager.add_user(user)
    return user_id


@pytest.fixture
def experience_id(user_id):
    """Create a test experience and return its ID."""
    experience_data = {
        "company_name": "Test Company",
        "job_title": "Test Engineer",
        "start_date": "2020-01-01",
        "content": "Test content",
    }
    exp_id = ExperienceService.create_experience(user_id, **experience_data)
    return exp_id


def test_add_achievement(experience_id):
    """Test adding an achievement to an experience."""
    achievement_id = ExperienceService.add_achievement(
        experience_id, "Efficiency Improvement", "Increased efficiency by 50%"
    )

    assert achievement_id > 0

    _, achievements = ExperienceService.get_experience_with_achievements(experience_id)
    assert len(achievements) == 1
    assert achievements[0].title == "Efficiency Improvement"
    assert achievements[0].content == "Increased efficiency by 50%"
    assert achievements[0].order == 0


def test_update_achievement(experience_id):
    """Test updating an achievement."""
    achievement_id = ExperienceService.add_achievement(experience_id, "Original Title", "Original content")

    updated = ExperienceService.update_achievement(achievement_id, "Updated Title", "Updated content")

    assert updated is not None
    assert updated.title == "Updated Title"
    assert updated.content == "Updated content"
    assert updated.id == achievement_id


def test_delete_achievement(experience_id):
    """Test deleting an achievement."""
    achievement_id = ExperienceService.add_achievement(experience_id, "Delete Title", "To be deleted")

    success = ExperienceService.delete_achievement(achievement_id)
    assert success is True

    _, achievements = ExperienceService.get_experience_with_achievements(experience_id)
    assert len(achievements) == 0


def test_reorder_achievements(experience_id):
    """Test reordering achievements."""
    # Add multiple achievements
    ach1_id = ExperienceService.add_achievement(experience_id, "First", "First achievement")
    ach2_id = ExperienceService.add_achievement(experience_id, "Second", "Second achievement")
    ach3_id = ExperienceService.add_achievement(experience_id, "Third", "Third achievement")

    # Verify initial order
    _, achievements = ExperienceService.get_experience_with_achievements(experience_id)
    assert len(achievements) == 3
    assert achievements[0].id == ach1_id
    assert achievements[1].id == ach2_id
    assert achievements[2].id == ach3_id

    # Reorder: move third to first
    new_order = [ach3_id, ach1_id, ach2_id]
    success = ExperienceService.reorder_achievements(experience_id, new_order)
    assert success is True

    # Verify new order
    _, achievements = ExperienceService.get_experience_with_achievements(experience_id)
    assert achievements[0].id == ach3_id
    assert achievements[1].id == ach1_id
    assert achievements[2].id == ach2_id


def test_add_achievement_with_order(experience_id):
    """Test adding achievements with explicit order."""
    # Add achievements with specific order
    ach1_id = ExperienceService.add_achievement(experience_id, "First", "First achievement", order=0)
    ach2_id = ExperienceService.add_achievement(experience_id, "Second", "Second achievement", order=1)

    _, achievements = ExperienceService.get_experience_with_achievements(experience_id)
    assert len(achievements) == 2
    assert achievements[0].order == 0
    assert achievements[1].order == 1


def test_achievement_validation(experience_id):
    """Test achievement validation."""
    # Test empty content
    with pytest.raises(ValueError, match="Achievement content is required"):
        ExperienceService.add_achievement(experience_id, "Title", "")

    with pytest.raises(ValueError, match="Achievement content is required"):
        ExperienceService.add_achievement(experience_id, "Title", "   ")

    # Test invalid experience ID
    with pytest.raises(ValueError, match="Experience .* not found"):
        ExperienceService.add_achievement(99999, "Title", "Test achievement")

    # Test invalid achievement ID
    with pytest.raises(ValueError, match="Invalid achievement ID"):
        ExperienceService.update_achievement(0, "Title", "Test")

    with pytest.raises(ValueError, match="Invalid achievement ID"):
        ExperienceService.delete_achievement(-1)


def test_reorder_validation(experience_id):
    """Test reorder achievements validation."""
    ach1_id = ExperienceService.add_achievement(experience_id, "First", "First achievement")
    ach2_id = ExperienceService.add_achievement(experience_id, "Second", "Second achievement")

    # Test with missing IDs
    with pytest.raises(ValueError, match="do not match existing achievements"):
        ExperienceService.reorder_achievements(experience_id, [ach1_id])

    # Test with wrong IDs
    with pytest.raises(ValueError, match="do not match existing achievements"):
        ExperienceService.reorder_achievements(experience_id, [ach1_id, 99999])

    # Test with empty list
    with pytest.raises(ValueError, match="Achievement IDs list is required"):
        ExperienceService.reorder_achievements(experience_id, [])


def test_get_experience_with_achievements(experience_id):
    """Test getting experience with achievements."""
    # Add some achievements
    ExperienceService.add_achievement(experience_id, "Achievement 1", "First achievement content")
    ExperienceService.add_achievement(experience_id, "Achievement 2", "Second achievement content")

    experience, achievements = ExperienceService.get_experience_with_achievements(experience_id)

    assert experience is not None
    assert experience.id == experience_id
    assert len(achievements) == 2

    # Test with non-existent experience
    experience, achievements = ExperienceService.get_experience_with_achievements(99999)
    assert experience is None
    assert len(achievements) == 0
