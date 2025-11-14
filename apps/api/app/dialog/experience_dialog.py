"""Experience dialog components for adding and editing experience entries."""

import asyncio
from datetime import date

import streamlit as st

from app.api_client.endpoints.experiences import ExperiencesAPI
from app.components.confirm_delete import confirm_delete
from app.constants import MIN_DATE
from app.services.experience_service import ExperienceService
from src.logging_config import logger


def display_achievements_management(experience_id: int) -> None:
    """Display and manage achievements for a specific experience in edit mode."""
    st.subheader("Achievements")

    # Add achievement button
    if st.button("Add Achievement", key=f"add_achievement_{experience_id}", type="primary"):
        show_add_achievement_dialog(experience_id)

    # Fetch achievements for this experience
    try:
        achievements = asyncio.run(ExperiencesAPI.list_achievements(experience_id))
    except Exception as e:
        st.error(f"Error loading achievements: {str(e)}")
        logger.exception(f"Error loading achievements for experience {experience_id}: {e}")
        return

    # Display achievements
    if achievements:
        for idx, achievement in enumerate(achievements):
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{achievement.title}**")
                    st.write(achievement.content)
                with col2:
                    with st.container(horizontal=True, horizontal_alignment="right"):
                        # Move up button (disabled for first item)
                        if st.button(
                            "",
                            key=f"move_up_achievement_{achievement.id}",
                            icon=":material/arrow_upward:",
                            help="Move up",
                            type="tertiary",
                            disabled=idx == 0,
                        ):
                            try:
                                # Swap with previous achievement
                                achievement_ids = [a.id for a in achievements]
                                achievement_ids[idx], achievement_ids[idx - 1] = (
                                    achievement_ids[idx - 1],
                                    achievement_ids[idx],
                                )
                                ExperienceService.reorder_achievements(experience_id, achievement_ids)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error reordering achievements: {str(e)}")
                                logger.exception(f"Error reordering achievements: {e}")

                        # Move down button (disabled for last item)
                        if st.button(
                            "",
                            key=f"move_down_achievement_{achievement.id}",
                            icon=":material/arrow_downward:",
                            help="Move down",
                            type="tertiary",
                            disabled=idx == len(achievements) - 1,
                        ):
                            try:
                                # Swap with next achievement
                                achievement_ids = [a.id for a in achievements]
                                achievement_ids[idx], achievement_ids[idx + 1] = (
                                    achievement_ids[idx + 1],
                                    achievement_ids[idx],
                                )
                                ExperienceService.reorder_achievements(experience_id, achievement_ids)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error reordering achievements: {str(e)}")
                                logger.exception(f"Error reordering achievements: {e}")

                        # Edit button
                        if st.button(
                            "",
                            key=f"edit_achievement_{achievement.id}",
                            icon=":material/edit:",
                            help="Edit",
                            type="tertiary",
                        ):
                            show_edit_achievement_dialog(achievement.id, achievement.title, achievement.content)

                        # Delete button
                        if st.button(
                            "",
                            key=f"delete_achievement_{achievement.id}",
                            icon=":material/delete:",
                            help="Delete",
                            type="tertiary",
                        ):
                            st.session_state[f"confirm_delete_achievement_{achievement.id}"] = True
                            st.rerun()

                # Delete confirmation
                if st.session_state.get(f"confirm_delete_achievement_{achievement.id}", False):

                    def _on_confirm(ach_id: int = achievement.id) -> None:
                        try:
                            asyncio.run(ExperiencesAPI.delete_achievement(ach_id))
                            st.success("Achievement deleted successfully!")
                        except Exception as e:
                            st.error(f"Error deleting achievement: {str(e)}")
                            logger.exception(f"Error deleting achievement {ach_id}: {e}")
                        finally:
                            st.session_state[f"confirm_delete_achievement_{ach_id}"] = False
                            st.rerun()

                    def _on_cancel(ach_id: int = achievement.id) -> None:
                        st.session_state[f"confirm_delete_achievement_{ach_id}"] = False
                        st.rerun()

                    confirm_delete("achievement", _on_confirm, _on_cancel)
    else:
        st.info("No achievements added yet. Click 'Add Achievement' to add your first achievement.")


@st.dialog("Add Experience", width="large")
def show_add_experience_dialog(user_id):
    """Show dialog for adding new experience entry."""
    st.subheader("Add New Experience")

    with st.form("add_experience_dialog_form"):
        # Company Name and Job Title in a single column
        company_name = st.text_input("Company Name *", help="Required")
        job_title = st.text_input("Job Title *", help="Required")

        # Location (optional)
        location = st.text_input("Location", help="Optional")

        # Start and End dates inline on the same row
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date *",
                value=date.today(),
                min_value=MIN_DATE,
                help="Required",
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=None,
                min_value=MIN_DATE,
                help="Leave empty for current position",
            )

        # Optional fields
        company_overview = st.text_area(
            "Company Overview",
            help="Optional - provide context about the company",
            height=100,
        )
        role_overview = st.text_area(
            "Role Overview",
            help="Optional - summarize your role and responsibilities",
            height=100,
        )

        # Skills as text input (comma-separated)
        skills_input = st.text_input(
            "Skills",
            help="Optional - enter skills separated by commas (e.g., Python, SQL, Project Management)",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Add", type="primary"):
                if not company_name.strip() or not job_title.strip():
                    st.error("Company name and job title are required.")
                elif end_date and start_date > end_date:
                    st.error("Start date must be before end date.")
                else:
                    try:
                        experience_data = {
                            "company_name": company_name.strip(),
                            "job_title": job_title.strip(),
                            "start_date": start_date.isoformat(),
                        }
                        if location is not None:
                            experience_data["location"] = location
                        if end_date:
                            experience_data["end_date"] = end_date.isoformat()

                        # Add new optional fields
                        if company_overview and company_overview.strip():
                            experience_data["company_overview"] = company_overview.strip()
                        if role_overview and role_overview.strip():
                            experience_data["role_overview"] = role_overview.strip()
                        if skills_input and skills_input.strip():
                            # Parse comma-separated skills
                            skills_list = [s.strip() for s in skills_input.split(",") if s.strip()]
                            if skills_list:
                                experience_data["skills"] = skills_list

                        asyncio.run(
                            ExperiencesAPI.create_experience(
                                user_id=user_id,
                                company_name=experience_data["company_name"],
                                job_title=experience_data["job_title"],
                                location=experience_data.get("location"),
                                start_date=experience_data["start_date"],
                                end_date=experience_data.get("end_date"),
                                company_overview=experience_data.get("company_overview"),
                                role_overview=experience_data.get("role_overview"),
                                skills=experience_data.get("skills", []),
                            )
                        )
                        st.success("Experience added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding experience: {str(e)}")
                        logger.error(f"Error adding experience: {e}")

        with col2:
            if st.form_submit_button("Cancel"):
                st.rerun()


@st.dialog("Edit Experience", width="large")
def show_edit_experience_dialog(experience, user_id):
    """Show dialog for editing existing experience entry."""
    st.subheader("Edit Experience")

    with st.form(f"edit_experience_dialog_form_{experience.id}"):
        # Company Name and Job Title in a single column
        company_name = st.text_input("Company Name *", value=experience.company_name, help="Required")
        job_title = st.text_input("Job Title *", value=experience.job_title, help="Required")

        # Location (optional)
        location = st.text_input("Location", value=getattr(experience, "location", None) or "", help="Optional")

        # Start and End dates inline on the same row
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date *",
                value=experience.start_date,
                min_value=MIN_DATE,
                help="Required",
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=experience.end_date,
                min_value=MIN_DATE,
                help="Leave empty for current position",
            )

        # Optional fields
        company_overview = st.text_area(
            "Company Overview",
            value=getattr(experience, "company_overview", None) or "",
            help="Optional - provide context about the company",
            height=100,
        )
        role_overview = st.text_area(
            "Role Overview",
            value=getattr(experience, "role_overview", None) or "",
            help="Optional - summarize your role and responsibilities",
            height=100,
        )

        # Skills as text input (comma-separated) - handle both new and legacy experiences
        existing_skills = getattr(experience, "skills", None) or []
        skills_str = ", ".join(existing_skills) if existing_skills else ""
        skills_input = st.text_input(
            "Skills",
            value=skills_str,
            help="Optional - enter skills separated by commas (e.g., Python, SQL, Project Management)",
        )

        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.form_submit_button("Cancel"):
                st.rerun()

            if st.form_submit_button("Save", type="primary"):
                if not company_name.strip() or not job_title.strip():
                    st.error("Company name and job title are required.")
                elif end_date and start_date > end_date:
                    st.error("Start date must be before end date.")
                else:
                    try:
                        update_data = {
                            "company_name": company_name.strip(),
                            "job_title": job_title.strip(),
                            "start_date": start_date.isoformat(),
                        }
                        update_data["location"] = location
                        if end_date:
                            update_data["end_date"] = end_date.isoformat()
                        else:
                            update_data["end_date"] = None

                        # Add new optional fields
                        if company_overview and company_overview.strip():
                            update_data["company_overview"] = company_overview.strip()
                        else:
                            update_data["company_overview"] = None

                        if role_overview and role_overview.strip():
                            update_data["role_overview"] = role_overview.strip()
                        else:
                            update_data["role_overview"] = None

                        if skills_input and skills_input.strip():
                            # Parse comma-separated skills
                            skills_list = [s.strip() for s in skills_input.split(",") if s.strip()]
                            update_data["skills"] = skills_list
                        else:
                            update_data["skills"] = []

                        asyncio.run(
                            ExperiencesAPI.update_experience(
                                experience_id=experience.id,
                                company_name=update_data["company_name"],
                                job_title=update_data["job_title"],
                                location=update_data.get("location"),
                                start_date=update_data["start_date"],
                                end_date=update_data.get("end_date"),
                                company_overview=update_data.get("company_overview"),
                                role_overview=update_data.get("role_overview"),
                                skills=update_data.get("skills", []),
                            )
                        )
                        st.success("Experience updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating experience: {str(e)}")
                        logger.error(f"Error updating experience: {e}")

    # Achievements section (outside the form)
    st.markdown("---")
    display_achievements_management(experience.id)


@st.dialog("Add Achievement", width="large")
def show_add_achievement_dialog(experience_id: int) -> None:
    """Show dialog for adding a new achievement to an experience."""

    with st.form("add_achievement_dialog_form"):
        title = st.text_input(
            "Achievement Title *",
            help="Required - a brief headline for the achievement",
        )

        content = st.text_area(
            "Achievement Description *",
            help="Required - describe the achievement or accomplishment",
            height=150,
        )

        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.form_submit_button("Cancel"):
                st.rerun()

            if st.form_submit_button("Save", type="primary"):
                if not title.strip():
                    st.error("Achievement title is required.")
                elif not content.strip():
                    st.error("Achievement description is required.")
                else:
                    try:
                        asyncio.run(
                            ExperiencesAPI.create_achievement(
                                experience_id=experience_id,
                                title=title.strip(),
                                content=content.strip(),
                            )
                        )
                        st.success("Achievement added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding achievement: {str(e)}")
                        logger.exception(f"Error adding achievement: {e}")


@st.dialog("Edit Achievement", width="large")
def show_edit_achievement_dialog(achievement_id: int, current_title: str, current_content: str) -> None:
    """Show dialog for editing an existing achievement."""
    st.subheader("Edit Achievement")

    with st.form(f"edit_achievement_dialog_form_{achievement_id}"):
        title = st.text_input(
            "Achievement Title *",
            value=current_title,
            help="Required - a brief headline for the achievement",
        )

        content = st.text_area(
            "Achievement Description *",
            value=current_content,
            help="Required - describe the achievement or accomplishment",
            height=150,
        )

        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.form_submit_button("Cancel"):
                st.rerun()

            if st.form_submit_button("Save", type="primary"):
                if not title.strip():
                    st.error("Achievement title is required.")
                elif not content.strip():
                    st.error("Achievement description is required.")
                else:
                    try:
                        asyncio.run(
                            ExperiencesAPI.update_achievement(
                                achievement_id=achievement_id,
                                title=title.strip(),
                                content=content.strip(),
                            )
                        )
                        st.success("Achievement updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating achievement: {str(e)}")
                        logger.exception(f"Error updating achievement: {e}")
