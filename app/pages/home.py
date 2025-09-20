"""Home page for the Resume Bot application."""

import streamlit as st

from app.components.info_banner import top_info_banner
from app.services.experience_service import ExperienceService
from app.services.user_service import UserService
from src.logging_config import logger

# Experience-required banner at top if user lacks experiences
try:
    user = UserService.get_current_user()
    if user and user.id:
        if not ExperienceService.list_user_experiences(user.id):
            top_info_banner(
                "You don't have any work experience on your profile. Add experience to unlock resume generation.",
                button_label="Go to Profile",
                target_page="pages/profile.py",
                key="home_add_experience_nav",
            )
except Exception as e:  # noqa: BLE001
    logger.error(f"Failed to check user experiences: {e}")

# Main content area
st.subheader("Save Job")

# Input form
with st.form("resume_form"):
    user_input = st.text_area(
        "Job Description",
        placeholder="Enter your job description, skills, or any other requirements...",
        height=400,
    )

    # Action
    save_clicked = st.form_submit_button("Save Job", type="primary")

    # Handle Save Job flow
    if save_clicked:
        try:
            # Defer validation to the dialog; extraction may return empty fields
            from app.dialog.job_save_dialog import show_save_job_dialog
            from src.features.jobs.extraction import extract_title_company

            extracted = None
            try:
                extracted = extract_title_company(user_input or "")
            except Exception as e:  # noqa: BLE001
                logger.error(f"Title/Company extraction failed: {e}")

            initial_title = getattr(extracted, "title", None) if extracted else None
            initial_company = getattr(extracted, "company", None) if extracted else None

            show_save_job_dialog(
                initial_title=initial_title,
                initial_company=initial_company,
                initial_description=(user_input or ""),
                initial_favorite=False,
            )
        except Exception as e:  # noqa: BLE001
            st.error("Unable to open Save Job dialog.")
            logger.error(f"Error launching Save Job dialog: {e}")
