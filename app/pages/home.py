"""Home page for the Resume Bot application."""

import streamlit as st

from app.services.experience_service import ExperienceService
from app.services.resume_service import ResumeService
from app.services.user_service import UserService
from src.logging_config import logger

st.title("🏠 Home")

st.markdown("---")

# Main content area
st.subheader("Generate Resume")

# Input form
with st.form("resume_form"):
    user_input = st.text_area(
        "Describe what you need:",
        placeholder="Enter your job description, skills, or any other requirements...",
        height=100,
    )

    submitted = st.form_submit_button("Generate Resume", type="primary")

    if submitted:
        if user_input.strip():
            with st.spinner("Generating your resume..."):
                try:
                    user = UserService.get_current_user()
                    user_id = user.id if user else None
                    experiences = ExperienceService.list_user_experiences(user_id) if user_id else []

                    response = ResumeService.generate_resume(
                        job_description=user_input,
                        experiences=experiences,
                        responses="",
                        user_id=user_id,
                    )
                    st.success("Resume generated successfully!")

                    # Display the response
                    st.subheader("Generated Content:")
                    st.text_area("Result:", value=response, height=200, disabled=True)

                except Exception as e:
                    st.error(f"Error generating resume: {str(e)}")
                    logger.error(f"Error in home page: {e}")
        else:
            st.warning("Please enter some input before generating a resume.")
