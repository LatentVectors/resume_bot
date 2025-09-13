"""Home page for the Resume Bot application."""

import streamlit as st

from app.services.experience_service import ExperienceService
from app.services.resume_service import ResumeService
from app.services.user_service import UserService
from src.config import settings
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

                    job = ResumeService.generate_resume(
                        job_description=user_input,
                        experiences=experiences,
                        responses="",
                        user_id=user_id,
                    )
                    st.success("Resume generated successfully! View it below or in Jobs.")

                    # Success link to Jobs page
                    st.page_link("pages/jobs.py", label="Go to Jobs 💼", icon="💼")

                    # Display the generated PDF inline
                    try:
                        if not job or not getattr(job, "resume_filename", None):
                            st.error("No PDF was generated. Please try again.")
                        else:
                            pdf_path = (settings.data_dir / "resumes" / job.resume_filename).resolve()
                            if not pdf_path.exists():
                                st.error(f"PDF file not found: {pdf_path}")
                            else:
                                pdf_bytes = pdf_path.read_bytes()
                                st.subheader("Preview")
                                st.pdf(data=pdf_bytes, height="stretch")
                                st.caption(f"Filename: {job.resume_filename}")
                                st.download_button(
                                    label="Download Resume",
                                    data=pdf_bytes,
                                    file_name=job.resume_filename,
                                    mime="application/pdf",
                                    type="primary",
                                    key=f"download_home_{job.resume_filename}",
                                )
                    except Exception as e:  # noqa: BLE001
                        st.error("Failed to display generated PDF.")
                        logger.error(f"Error displaying generated PDF: {e}")

                except Exception as e:
                    st.error(f"Error generating resume: {str(e)}")
                    logger.error(f"Error in home page: {e}")
        else:
            st.warning("Please enter some input before generating a resume.")
