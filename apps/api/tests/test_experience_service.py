"""Tests for ExperienceService."""

from __future__ import annotations

from datetime import date

import pytest

from app.services.experience_service import ExperienceService
from src.database import db_manager


@pytest.fixture
def test_user_id():
    """Create a test user and return its ID."""
    from src.database import User

    user = User(first_name="Test", last_name="User", email="test@example.com")
    user_id = db_manager.add_user(user)
    yield user_id
    # Cleanup: delete user and all related data
    db_manager.delete_user(user_id)


@pytest.fixture
def test_experience_id(test_user_id):
    """Create a test experience and return its ID."""
    exp_id = ExperienceService.create_experience(
        user_id=test_user_id,
        company_name="Test Company",
        job_title="Test Engineer",
        start_date=date(2020, 1, 1),
        end_date=date(2021, 12, 31),
        location="Test Location",
    )
    yield exp_id
    # Cleanup handled by user deletion


class TestUpdateExperienceFields:
    """Tests for update_experience_fields method."""

    def test_update_company_overview(self, test_experience_id):
        """Test updating company_overview field."""
        overview = "A great company focused on innovation"
        result = ExperienceService.update_experience_fields(test_experience_id, company_overview=overview)
        assert result is not None
        assert result.company_overview == overview

    def test_update_role_overview(self, test_experience_id):
        """Test updating role_overview field."""
        overview = "Led engineering team and delivered products"
        result = ExperienceService.update_experience_fields(test_experience_id, role_overview=overview)
        assert result is not None
        assert result.role_overview == overview

    def test_update_skills(self, test_experience_id):
        """Test updating skills field."""
        skills = ["Python", "Django", "PostgreSQL"]
        result = ExperienceService.update_experience_fields(test_experience_id, skills=skills)
        assert result is not None
        assert result.skills == skills

    def test_update_all_fields(self, test_experience_id):
        """Test updating all enhanced fields at once."""
        company_overview = "Company overview"
        role_overview = "Role overview"
        skills = ["Skill1", "Skill2"]

        result = ExperienceService.update_experience_fields(
            test_experience_id,
            company_overview=company_overview,
            role_overview=role_overview,
            skills=skills,
        )
        assert result is not None
        assert result.company_overview == company_overview
        assert result.role_overview == role_overview
        assert result.skills == skills

    def test_update_with_empty_string(self, test_experience_id):
        """Test that empty strings are normalized to None."""
        result = ExperienceService.update_experience_fields(test_experience_id, company_overview="   ")
        assert result is not None
        assert result.company_overview is None

    def test_update_skills_filters_empty(self, test_experience_id):
        """Test that empty strings are filtered from skills list."""
        skills = ["Python", "", "  ", "Django"]
        result = ExperienceService.update_experience_fields(test_experience_id, skills=skills)
        assert result is not None
        assert result.skills == ["Python", "Django"]

    def test_invalid_experience_id(self):
        """Test with invalid experience ID."""
        with pytest.raises(ValueError, match="Invalid experience ID"):
            ExperienceService.update_experience_fields(0, company_overview="test")


class TestAddAchievement:
    """Tests for add_achievement method."""

    def test_add_achievement_basic(self, test_experience_id):
        """Test adding a basic achievement."""
        title = "Project Delivery"
        content = "Delivered major project on time"
        achievement_id = ExperienceService.add_achievement(test_experience_id, title, content)
        assert achievement_id > 0

        # Verify it was added
        achievement = db_manager.get_achievement(achievement_id)
        assert achievement is not None
        assert achievement.title == title
        assert achievement.content == content
        assert achievement.experience_id == test_experience_id

    def test_add_achievement_with_order(self, test_experience_id):
        """Test adding an achievement with specific order."""
        title = "First Achievement"
        content = "First achievement"
        achievement_id = ExperienceService.add_achievement(test_experience_id, title, content, order=0)
        achievement = db_manager.get_achievement(achievement_id)
        assert achievement.order == 0

    def test_add_achievement_auto_order(self, test_experience_id):
        """Test that achievements are auto-ordered when order not specified."""
        # Add first achievement
        id1 = ExperienceService.add_achievement(test_experience_id, "Achievement 1", "First achievement")
        # Add second achievement
        id2 = ExperienceService.add_achievement(test_experience_id, "Achievement 2", "Second achievement")

        a1 = db_manager.get_achievement(id1)
        a2 = db_manager.get_achievement(id2)
        assert a1.order == 0
        assert a2.order == 1

    def test_add_achievement_empty_content(self, test_experience_id):
        """Test that empty content raises error."""
        with pytest.raises(ValueError, match="Achievement content is required"):
            ExperienceService.add_achievement(test_experience_id, "Title", "")

    def test_add_achievement_invalid_experience(self):
        """Test adding achievement to non-existent experience."""
        with pytest.raises(ValueError, match="Experience .* not found"):
            ExperienceService.add_achievement(99999, "Title", "Some content")


class TestUpdateAchievement:
    """Tests for update_achievement method."""

    def test_update_achievement_content(self, test_experience_id):
        """Test updating achievement content."""
        # Create achievement
        achievement_id = ExperienceService.add_achievement(test_experience_id, "Original Title", "Original content")

        # Update it
        new_title = "Updated Title"
        new_content = "Updated content"
        result = ExperienceService.update_achievement(achievement_id, new_title, new_content)
        assert result is not None
        assert result.title == new_title
        assert result.content == new_content

    def test_update_achievement_empty_content(self, test_experience_id):
        """Test that empty content raises error."""
        achievement_id = ExperienceService.add_achievement(test_experience_id, "Original Title", "Original")
        with pytest.raises(ValueError, match="Achievement content is required"):
            ExperienceService.update_achievement(achievement_id, "Title", "")

    def test_update_nonexistent_achievement(self):
        """Test updating non-existent achievement."""
        result = ExperienceService.update_achievement(99999, "New Title", "New content")
        assert result is None


class TestDeleteAchievement:
    """Tests for delete_achievement method."""

    def test_delete_achievement(self, test_experience_id):
        """Test deleting an achievement."""
        achievement_id = ExperienceService.add_achievement(test_experience_id, "Delete Title", "To be deleted")

        result = ExperienceService.delete_achievement(achievement_id)
        assert result is True

        # Verify it's gone
        achievement = db_manager.get_achievement(achievement_id)
        assert achievement is None

    def test_delete_nonexistent_achievement(self):
        """Test deleting non-existent achievement."""
        result = ExperienceService.delete_achievement(99999)
        assert result is False

    def test_delete_invalid_id(self):
        """Test with invalid achievement ID."""
        with pytest.raises(ValueError, match="Invalid achievement ID"):
            ExperienceService.delete_achievement(0)


class TestReorderAchievements:
    """Tests for reorder_achievements method."""

    def test_reorder_achievements(self, test_experience_id):
        """Test reordering achievements."""
        # Create three achievements
        id1 = ExperienceService.add_achievement(test_experience_id, "First", "First achievement")
        id2 = ExperienceService.add_achievement(test_experience_id, "Second", "Second achievement")
        id3 = ExperienceService.add_achievement(test_experience_id, "Third", "Third achievement")

        # Reorder them
        new_order = [id3, id1, id2]
        result = ExperienceService.reorder_achievements(test_experience_id, new_order)
        assert result is True

        # Verify new order
        achievements = db_manager.list_experience_achievements(test_experience_id)
        assert achievements[0].id == id3
        assert achievements[1].id == id1
        assert achievements[2].id == id2

    def test_reorder_with_missing_ids(self, test_experience_id):
        """Test that reordering with incomplete ID list fails."""
        id1 = ExperienceService.add_achievement(test_experience_id, "First", "First achievement")
        ExperienceService.add_achievement(test_experience_id, "Second", "Second achievement")

        # Try to reorder with only one ID
        with pytest.raises(ValueError, match="do not match existing achievements"):
            ExperienceService.reorder_achievements(test_experience_id, [id1])

    def test_reorder_with_extra_ids(self, test_experience_id):
        """Test that reordering with extra IDs fails."""
        id1 = ExperienceService.add_achievement(test_experience_id, "First", "First achievement")

        with pytest.raises(ValueError, match="do not match existing achievements"):
            ExperienceService.reorder_achievements(test_experience_id, [id1, 99999])

    def test_reorder_empty_list(self, test_experience_id):
        """Test that empty list raises error."""
        with pytest.raises(ValueError, match="Achievement IDs list is required"):
            ExperienceService.reorder_achievements(test_experience_id, [])


class TestGetExperienceWithAchievements:
    """Tests for get_experience_with_achievements method."""

    def test_get_experience_with_achievements(self, test_experience_id):
        """Test getting experience with its achievements."""
        # Add some achievements
        id1 = ExperienceService.add_achievement(test_experience_id, "Achievement 1", "First achievement content")
        id2 = ExperienceService.add_achievement(test_experience_id, "Achievement 2", "Second achievement content")

        experience, achievements = ExperienceService.get_experience_with_achievements(test_experience_id)

        assert experience is not None
        assert experience.id == test_experience_id
        assert len(achievements) == 2
        assert achievements[0].id == id1
        assert achievements[1].id == id2

    def test_get_experience_no_achievements(self, test_experience_id):
        """Test getting experience with no achievements."""
        experience, achievements = ExperienceService.get_experience_with_achievements(test_experience_id)

        assert experience is not None
        assert len(achievements) == 0

    def test_get_nonexistent_experience(self):
        """Test getting non-existent experience."""
        experience, achievements = ExperienceService.get_experience_with_achievements(99999)

        assert experience is None
        assert len(achievements) == 0


class TestIntegrationScenarios:
    """Integration tests combining multiple operations."""

    def test_full_experience_workflow(self, test_user_id):
        """Test a complete workflow with experience and achievements."""
        # Create experience
        exp_id = ExperienceService.create_experience(
            user_id=test_user_id,
            company_name="Tech Corp",
            job_title="Senior Engineer",
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31),
        )

        # Update enhanced fields
        ExperienceService.update_experience_fields(
            exp_id,
            company_overview="Leading tech company",
            role_overview="Led development of core products",
            skills=["Python", "Django", "AWS"],
        )

        # Add achievements
        a1 = ExperienceService.add_achievement(exp_id, "Product Launch", "Launched product X")
        a2 = ExperienceService.add_achievement(exp_id, "Cost Reduction", "Reduced costs by 50%")
        a3 = ExperienceService.add_achievement(exp_id, "Mentorship", "Mentored 5 engineers")

        # Reorder achievements
        ExperienceService.reorder_achievements(exp_id, [a2, a3, a1])

        # Get everything
        exp, achievements = ExperienceService.get_experience_with_achievements(exp_id)

        # Verify
        assert exp is not None
        assert exp.company_overview == "Leading tech company"
        assert exp.role_overview == "Led development of core products"
        assert exp.skills == ["Python", "Django", "AWS"]
        assert len(achievements) == 3
        assert achievements[0].id == a2
        assert achievements[1].id == a3
        assert achievements[2].id == a1

    def test_backward_compatibility(self, test_user_id):
        """Test that legacy experiences work without new fields."""
        # Create experience without new fields
        exp_id = ExperienceService.create_experience(
            user_id=test_user_id,
            company_name="Old Corp",
            job_title="Developer",
            start_date=date(2018, 1, 1),
        )

        exp = db_manager.get_experience(exp_id)
        assert exp.company_overview is None
        assert exp.role_overview is None
        assert exp.skills == []

        # Can still add achievements
        achievement_id = ExperienceService.add_achievement(exp_id, "Legacy Achievement", "Did something")
        assert achievement_id > 0
