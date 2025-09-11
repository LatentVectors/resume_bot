"""Main Streamlit application entry point."""

import streamlit as st
from loguru import logger


def main() -> None:
    """Main application entry point."""
    # Configure Streamlit page
    st.set_page_config(page_title="Resume Bot", page_icon="📄", layout="wide", initial_sidebar_state="expanded")

    # Initialize session state
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        logger.info("Streamlit app initialized")

    # Define pages using the new Streamlit navigation API
    home_page = st.Page("pages/home.py", title="Home", icon="🏠")
    users_page = st.Page("pages/users.py", title="Users", icon="👥")

    # Create navigation
    pg = st.navigation([home_page, users_page])

    # Run the selected page
    pg.run()


if __name__ == "__main__":
    main()
