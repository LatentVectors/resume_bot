"""Main Streamlit application entry point."""

import streamlit as st

from app.services.user_service import UserService
from src.logging_config import logger


def main() -> None:
    """Main application entry point."""
    # Configure Streamlit page
    st.set_page_config(page_title="Resume Bot", page_icon="📄", layout="wide", initial_sidebar_state="expanded")

    # Initialize session state
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        logger.info("Streamlit app initialized")

    # Check if users exist in database
    try:
        has_users = UserService.has_users()

        if not has_users:
            # No users exist, redirect to onboarding
            logger.info("No users found, redirecting to onboarding")
            st.switch_page("pages/_onboarding.py")
            return
        else:
            # Users exist, check if we should redirect to home
            current_user = UserService.get_current_user()
            if current_user:
                # Set current user in session state for easy access
                st.session_state.current_user = current_user
                logger.info(f"Current user: {current_user.first_name} {current_user.last_name}")

    except Exception as e:
        logger.error(f"Error checking user existence: {e}")
        st.error("❌ Error connecting to database. Please check your connection and try again.")
        st.stop()

    # Define pages using the new Streamlit navigation API
    # Only show Home and User pages for single-user app
    home_page = st.Page("pages/home.py", title="Home", icon="🏠")
    user_page = st.Page("pages/user.py", title="Profile", icon="👤")  # Renamed from Users to Profile
    jobs_page = st.Page("pages/jobs.py", title="Jobs", icon="💼")
    job_detail_page = st.Page("pages/job.py", title="Job", icon="🔎")
    templates_page = st.Page("pages/templates.py", title="Templates", icon="🧩")
    responses_page = st.Page("pages/responses.py", title="Responses", icon="🗂️")

    # Create navigation
    pg = st.navigation([home_page, user_page, jobs_page, job_detail_page, templates_page, responses_page])

    # Run the selected page
    pg.run()


if __name__ == "__main__":
    main()
