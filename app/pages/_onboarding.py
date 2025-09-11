"""Onboarding page for first-time users."""

import re
from datetime import date

import streamlit as st
from loguru import logger

from app.services.education_service import EducationService
from app.services.experience_service import ExperienceService
from app.services.user_service import UserService


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_url(url: str) -> bool:
    """Validate URL format."""
    pattern = r"^https?://.+"
    return re.match(pattern, url) is not None


def initialize_onboarding_state():
    """Initialize onboarding session state."""
    if "onboarding_step" not in st.session_state:
        st.session_state.onboarding_step = 1

    if "onboarding_data" not in st.session_state:
        st.session_state.onboarding_data = {"user": {}, "experiences": [], "educations": []}


def render_progress_indicator():
    """Render the progress indicator."""
    st.progress(st.session_state.onboarding_step / 3)
    st.markdown(f"**Step {st.session_state.onboarding_step} of 3**")


def render_step1_basic_info():
    """Render Step 1: Basic User Information form."""
    st.subheader("👤 Basic Information")
    st.markdown("Let's start with your basic information. Only first and last name are required.")

    with st.form("basic_info_form"):
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input(
                "First Name *", value=st.session_state.onboarding_data["user"].get("first_name", "")
            )
            last_name = st.text_input(
                "Last Name *", value=st.session_state.onboarding_data["user"].get("last_name", "")
            )
            phone_number = st.text_input(
                "Phone Number", value=st.session_state.onboarding_data["user"].get("phone_number", "")
            )
            email = st.text_input("Email", value=st.session_state.onboarding_data["user"].get("email", ""))
            address = st.text_input("Address", value=st.session_state.onboarding_data["user"].get("address", ""))

        with col2:
            city = st.text_input("City", value=st.session_state.onboarding_data["user"].get("city", ""))
            state = st.text_input("State", value=st.session_state.onboarding_data["user"].get("state", ""))
            zip_code = st.text_input("ZIP Code", value=st.session_state.onboarding_data["user"].get("zip_code", ""))
            linkedin_url = st.text_input(
                "LinkedIn Profile URL", value=st.session_state.onboarding_data["user"].get("linkedin_url", "")
            )
            github_url = st.text_input(
                "GitHub Profile URL", value=st.session_state.onboarding_data["user"].get("github_url", "")
            )
            website_url = st.text_input(
                "Website URL", value=st.session_state.onboarding_data["user"].get("website_url", "")
            )

        submitted = st.form_submit_button("Continue to Experience", type="primary")

        if submitted:
            # Validate required fields
            errors = []
            if not first_name.strip():
                errors.append("First name is required")
            if not last_name.strip():
                errors.append("Last name is required")

            # Validate optional fields
            if email and not validate_email(email):
                errors.append("Please enter a valid email address")

            url_fields = [("LinkedIn URL", linkedin_url), ("GitHub URL", github_url), ("Website URL", website_url)]

            for field_name, field_value in url_fields:
                if field_value and not validate_url(field_value):
                    errors.append(f"{field_name} must be a valid URL (starting with http:// or https://)")

            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Save form data to session state
                st.session_state.onboarding_data["user"] = {
                    "first_name": first_name.strip(),
                    "last_name": last_name.strip(),
                    "phone_number": phone_number.strip() if phone_number.strip() else None,
                    "email": email.strip() if email.strip() else None,
                    "address": address.strip() if address.strip() else None,
                    "city": city.strip() if city.strip() else None,
                    "state": state.strip() if state.strip() else None,
                    "zip_code": zip_code.strip() if zip_code.strip() else None,
                    "linkedin_url": linkedin_url.strip() if linkedin_url.strip() else None,
                    "github_url": github_url.strip() if github_url.strip() else None,
                    "website_url": website_url.strip() if website_url.strip() else None,
                }

                # Create user and move to next step
                try:
                    user_id = UserService.create_user(**st.session_state.onboarding_data["user"])
                    st.session_state.current_user_id = user_id
                    st.session_state.onboarding_step = 2
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating user: {str(e)}")
                    logger.error(f"Error creating user during onboarding: {e}")


def render_step2_experience():
    """Render Step 2: Work Experience setup."""
    st.subheader("💼 Work Experience")
    st.markdown("Add your work experience (optional). You can skip this step and add experience later.")

    # Display existing experiences
    if st.session_state.onboarding_data["experiences"]:
        st.markdown("**Added Experiences:**")
        for i, exp in enumerate(st.session_state.onboarding_data["experiences"]):
            with st.expander(f"{exp['job_title']} at {exp['company_name']}"):
                st.write(f"**Company:** {exp['company_name']}")
                st.write(f"**Job Title:** {exp['job_title']}")
                st.write(f"**Start Date:** {exp['start_date']}")
                if exp.get("end_date"):
                    st.write(f"**End Date:** {exp['end_date']}")
                else:
                    st.write("**End Date:** Current")
                st.write(f"**Description:** {exp['content']}")

                if st.button(f"Remove Experience {i + 1}", key=f"remove_exp_{i}"):
                    st.session_state.onboarding_data["experiences"].pop(i)
                    st.rerun()

    # Add new experience form
    with st.expander("Add New Experience", expanded=not st.session_state.onboarding_data["experiences"]):
        with st.form("experience_form"):
            col1, col2 = st.columns(2)

            with col1:
                company_name = st.text_input("Company Name")
                job_title = st.text_input("Job Title")
                start_date = st.date_input(
                    "Start Date", value=date.today(), min_value=date(1950, 1, 1), max_value=date(2050, 12, 31)
                )

            with col2:
                end_date = st.date_input(
                    "End Date (leave empty if current)",
                    value=None,
                    min_value=date(1950, 1, 1),
                    max_value=date(2050, 12, 31),
                )
                is_current = st.checkbox("This is my current position")

            content = st.text_area("Job Description", height=100)

            col1, col2 = st.columns(2)
            with col1:
                add_experience = st.form_submit_button("Add Experience", type="primary")
            with col2:
                skip_experience = st.form_submit_button("Skip This Step")

            if add_experience:
                if not company_name.strip() or not job_title.strip() or not content.strip():
                    st.error("Company name, job title, and description are required")
                else:
                    experience_data = {
                        "company_name": company_name.strip(),
                        "job_title": job_title.strip(),
                        "start_date": start_date.isoformat(),
                        "end_date": None if is_current else end_date.isoformat() if end_date else None,
                        "content": content.strip(),
                    }

                    # Validate dates
                    if not is_current and end_date and start_date > end_date:
                        st.error("Start date must be before end date")
                    else:
                        st.session_state.onboarding_data["experiences"].append(experience_data)
                        st.rerun()

            if skip_experience:
                st.session_state.onboarding_step = 3
                st.rerun()

    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Previous"):
            st.session_state.onboarding_step = 1
            st.rerun()
    with col3:
        if st.button("Next →"):
            st.session_state.onboarding_step = 3
            st.rerun()


def render_step3_education():
    """Render Step 3: Education setup."""
    st.subheader("🎓 Education")
    st.markdown("Add your education (optional). You can skip this step and add education later.")

    # Display existing educations
    if st.session_state.onboarding_data["educations"]:
        st.markdown("**Added Education:**")
        for i, edu in enumerate(st.session_state.onboarding_data["educations"]):
            with st.expander(f"{edu['degree']} from {edu['school']}"):
                st.write(f"**School:** {edu['school']}")
                st.write(f"**Degree:** {edu['degree']}")
                st.write(f"**Start Date:** {edu['start_date']}")
                st.write(f"**End Date:** {edu['end_date']}")

                if st.button(f"Remove Education {i + 1}", key=f"remove_edu_{i}"):
                    st.session_state.onboarding_data["educations"].pop(i)
                    st.rerun()

    # Add new education form
    with st.expander("Add New Education", expanded=not st.session_state.onboarding_data["educations"]):
        with st.form("education_form"):
            col1, col2 = st.columns(2)

            with col1:
                school = st.text_input("School/Institution")
                degree = st.text_input("Degree")

            with col2:
                start_date = st.date_input(
                    "Start Date", value=date.today(), min_value=date(1950, 1, 1), max_value=date(2050, 12, 31)
                )
                end_date = st.date_input(
                    "End Date", value=date.today(), min_value=date(1950, 1, 1), max_value=date(2050, 12, 31)
                )

            col1, col2 = st.columns(2)
            with col1:
                add_education = st.form_submit_button("Add Education", type="primary")
            with col2:
                skip_education = st.form_submit_button("Skip This Step")

            if add_education:
                if not school.strip() or not degree.strip():
                    st.error("School and degree are required")
                elif start_date > end_date:
                    st.error("Start date must be before end date")
                else:
                    education_data = {
                        "school": school.strip(),
                        "degree": degree.strip(),
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    }

                    st.session_state.onboarding_data["educations"].append(education_data)
                    st.rerun()

            if skip_education:
                complete_onboarding()

    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("← Previous"):
            st.session_state.onboarding_step = 2
            st.rerun()
    with col3:
        if st.button("Complete Setup", type="primary"):
            complete_onboarding()


def complete_onboarding():
    """Complete the onboarding process."""
    try:
        user_id = st.session_state.current_user_id

        # Add experiences to database
        for exp_data in st.session_state.onboarding_data["experiences"]:
            ExperienceService.create_experience(user_id, **exp_data)

        # Add educations to database
        for edu_data in st.session_state.onboarding_data["educations"]:
            EducationService.create_education(user_id, **edu_data)

        # Clear onboarding state
        if "onboarding_step" in st.session_state:
            del st.session_state.onboarding_step
        if "onboarding_data" in st.session_state:
            del st.session_state.onboarding_data

        st.success("🎉 Welcome! Your profile has been set up successfully.")
        st.balloons()

        # Redirect to home page
        st.switch_page("pages/home.py")

    except Exception as e:
        st.error(f"Error completing onboarding: {str(e)}")
        logger.error(f"Error completing onboarding: {e}")


def main():
    """Main onboarding page function."""
    st.title("🚀 Welcome to Resume Bot!")
    st.markdown("Let's set up your profile in just a few steps.")

    # Initialize session state
    initialize_onboarding_state()

    # Render progress indicator
    render_progress_indicator()

    st.markdown("---")

    # Render current step
    if st.session_state.onboarding_step == 1:
        render_step1_basic_info()
    elif st.session_state.onboarding_step == 2:
        render_step2_experience()
    elif st.session_state.onboarding_step == 3:
        render_step3_education()


main()
