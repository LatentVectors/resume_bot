"""Home page for the Resume Bot application."""

import streamlit as st

from app.services.experience_service import ExperienceService
from app.services.resume_service import ResumeService
from app.services.user_service import UserService
from src.config import settings
from src.logging_config import logger

st.title("Home")

st.markdown("---")

# Main content area
st.subheader("Generate Resume")

# Input form
with st.form("resume_form"):
    user_input = st.text_area(
        "Job Description",
        placeholder="Enter your job description, skills, or any other requirements...",
        height=100,
    )

    # Actions
    col_left, col_right = st.columns(2)
    with col_left:
        save_clicked = st.form_submit_button("Save Job")
    with col_right:
        submitted = st.form_submit_button("Generate Resume", type="primary")

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

    # Handle Generate Resume flow
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
                    st.page_link("pages/jobs.py", label="Go to Jobs", icon=":material/work:")

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
