"""Users page for managing users in the Resume Bot application."""

import streamlit as st
from loguru import logger

from app.services.user_service import UserService

"""Display the users page."""
st.title("👥 Users")
st.markdown("Manage users in the system.")

st.markdown("---")

# Add new user section
with st.expander("Add New User", expanded=False):
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input("First Name", placeholder="Enter first name")

        with col2:
            last_name = st.text_input("Last Name", placeholder="Enter last name")

        submitted = st.form_submit_button("Add User", type="primary")

        if submitted:
            if first_name.strip() and last_name.strip():
                try:
                    user_id = UserService.create_user(first_name, last_name)
                    st.success(f"User added successfully! ID: {user_id}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding user: {str(e)}")
                    logger.error(f"Error adding user: {e}")
            else:
                st.warning("Please enter both first and last name.")

st.markdown("---")

# Display users
st.subheader("All Users")

try:
    users = UserService.list_users()

    if users:
        # Create a table-like display
        for user in users:
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.write(f"**{user.first_name} {user.last_name}**")

                with col2:
                    st.write(f"ID: {user.id}")

                with col3:
                    if st.button("View", key=f"view_{user.id}"):
                        st.info(f"User details: {user.first_name} {user.last_name} (ID: {user.id})")

                st.divider()
    else:
        st.info("No users found. Add a user using the form above.")

except Exception as e:
    st.error(f"Error loading users: {str(e)}")
    logger.error(f"Error loading users: {e}")

# Back to home button
st.markdown("---")
if st.button("← Back to Home"):
    st.switch_page("pages/home.py")
