"""Experience dialog components for adding and editing experience entries."""

from datetime import date

import streamlit as st

from app.services.experience_service import ExperienceService
from src.logging_config import logger


@st.dialog("Add Experience", width="large")
def show_add_experience_dialog(user_id):
    """Show dialog for adding new experience entry."""
    st.subheader("Add New Experience")

    with st.form("add_experience_dialog_form"):
        # Company Name and Job Title in a single column
        company_name = st.text_input("Company Name *", help="Required")
        job_title = st.text_input("Job Title *", help="Required")

        # Start and End dates inline on the same row
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date *",
                value=date.today(),
                min_value=date(1950, 1, 1),
                max_value=date(2050, 12, 31),
                help="Required",
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=None,
                min_value=date(1950, 1, 1),
                max_value=date(2050, 12, 31),
                help="Leave empty for current position",
            )

        # Description with stretch height
        content = st.text_area("Description *", help="Required - describe your role and achievements", height=200)

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Add Experience", type="primary"):
                if not company_name.strip() or not job_title.strip() or not content.strip():
                    st.error("Company name, job title, and description are required.")
                elif end_date and start_date > end_date:
                    st.error("Start date must be before end date.")
                else:
                    try:
                        experience_data = {
                            "company_name": company_name.strip(),
                            "job_title": job_title.strip(),
                            "start_date": start_date.isoformat(),
                            "content": content.strip(),
                        }
                        if end_date:
                            experience_data["end_date"] = end_date.isoformat()

                        ExperienceService.create_experience(user_id, **experience_data)
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

        # Start and End dates inline on the same row
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date *",
                value=experience.start_date,
                min_value=date(1950, 1, 1),
                max_value=date(2050, 12, 31),
                help="Required",
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=experience.end_date,
                min_value=date(1950, 1, 1),
                max_value=date(2050, 12, 31),
                help="Leave empty for current position",
            )

        # Description with stretch height
        content = st.text_area(
            "Description *",
            value=experience.content,
            help="Required - describe your role and achievements",
            height=200,
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Save Changes", type="primary"):
                if not company_name.strip() or not job_title.strip() or not content.strip():
                    st.error("Company name, job title, and description are required.")
                elif end_date and start_date > end_date:
                    st.error("Start date must be before end date.")
                else:
                    try:
                        update_data = {
                            "company_name": company_name.strip(),
                            "job_title": job_title.strip(),
                            "start_date": start_date.isoformat(),
                            "content": content.strip(),
                        }
                        if end_date:
                            update_data["end_date"] = end_date.isoformat()
                        else:
                            update_data["end_date"] = None

                        ExperienceService.update_experience(experience.id, **update_data)
                        st.success("Experience updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating experience: {str(e)}")
                        logger.error(f"Error updating experience: {e}")

        with col2:
            if st.form_submit_button("Cancel"):
                st.rerun()
