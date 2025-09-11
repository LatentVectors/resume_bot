"""Home page for the Resume Bot application."""

import streamlit as st
from loguru import logger

from app.services.resume_service import ResumeService
from app.services.user_service import UserService

"""Display the home page."""
st.title("🏠 Home")
st.markdown("Welcome to the Resume Bot! Generate AI-powered resumes with ease.")

st.markdown("---")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
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
                        response = ResumeService.generate_resume(user_input)
                        st.success("Resume generated successfully!")

                        # Display the response
                        st.subheader("Generated Content:")
                        st.text_area("Result:", value=response, height=200, disabled=True)

                    except Exception as e:
                        st.error(f"Error generating resume: {str(e)}")
                        logger.error(f"Error in home page: {e}")
            else:
                st.warning("Please enter some input before generating a resume.")

with col2:
    st.subheader("Quick Actions")

    if st.button("View All Users"):
        st.switch_page("pages/users.py")

    st.markdown("---")

    st.subheader("Info")
    st.info("""
    This is a simple example of the Resume Bot in action.
    Click the button to test the LangGraph workflow!
    """)

    # Display user count
    users = UserService.list_users()
    st.metric("Total Users", len(users))
