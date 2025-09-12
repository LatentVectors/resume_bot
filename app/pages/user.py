"""User profile page for managing single user in the Resume Bot application."""

import streamlit as st

from app.dialog.education_dialog import show_add_education_dialog, show_edit_education_dialog
from app.dialog.experience_dialog import show_add_experience_dialog, show_edit_experience_dialog
from app.services.education_service import EducationService
from app.services.experience_service import ExperienceService
from app.services.user_service import UserService
from src.logging_config import logger


def display_user_profile():
    """Display the user profile page."""
    st.title("👤 User Profile")

    # Get current user
    user = UserService.get_current_user()
    if not user:
        st.error("No user found. Please complete onboarding first.")
        return

    # Initialize session state for edit mode
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False

    if "user_data" not in st.session_state:
        st.session_state.user_data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number or "",
            "email": user.email or "",
            "address": user.address or "",
            "city": user.city or "",
            "state": user.state or "",
            "zip_code": user.zip_code or "",
            "linkedin_url": user.linkedin_url or "",
            "github_url": user.github_url or "",
            "website_url": user.website_url or "",
        }

    # Display timestamps
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"Created: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    with col2:
        st.caption(f"Updated: {user.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")

    st.markdown("---")

    # Edit mode toggle
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("✏️ Edit Profile", type="primary"):
            st.session_state.edit_mode = True
            st.rerun()

    with col2:
        if st.session_state.edit_mode:
            if st.button("❌ Cancel"):
                st.session_state.edit_mode = False
                # Reset user data to original values
                st.session_state.user_data = {
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone_number": user.phone_number or "",
                    "email": user.email or "",
                    "address": user.address or "",
                    "city": user.city or "",
                    "state": user.state or "",
                    "zip_code": user.zip_code or "",
                    "linkedin_url": user.linkedin_url or "",
                    "github_url": user.github_url or "",
                    "website_url": user.website_url or "",
                }
                st.rerun()

    if st.session_state.edit_mode:
        display_edit_form(user)
    else:
        display_user_info(user)

    st.markdown("---")

    # Experience Management Section
    display_experience_section(user.id)

    st.markdown("---")

    # Education Management Section
    display_education_section(user.id)


def display_user_info(user):
    """Display user information in read-only mode."""
    st.subheader("Personal Information")

    # Name section - first and last name inline
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**First Name:** {user.first_name}")
    with col2:
        st.write(f"**Last Name:** {user.last_name}")

    # Email and phone below name
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Email:** {user.email or 'Not provided'}")
    with col2:
        st.write(f"**Phone:** {user.phone_number or 'Not provided'}")

    # Address section
    st.subheader("Address")
    if user.address or user.city or user.state or user.zip_code:
        # Street and city on one row
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Street:** {user.address or 'Not provided'}")
        with col2:
            st.write(f"**City:** {user.city or 'Not provided'}")

        # State and zip on row below
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**State:** {user.state or 'Not provided'}")
        with col2:
            st.write(f"**ZIP Code:** {user.zip_code or 'Not provided'}")
    else:
        st.write("No address information provided")

    # Online presence - single column
    st.subheader("Online Presence")
    if user.linkedin_url:
        st.write(f"**LinkedIn:** [{user.linkedin_url}]({user.linkedin_url})")
    else:
        st.write("**LinkedIn:** Not provided")

    if user.github_url:
        st.write(f"**GitHub:** [{user.github_url}]({user.github_url})")
    else:
        st.write("**GitHub:** Not provided")

    if user.website_url:
        st.write(f"**Website:** [{user.website_url}]({user.website_url})")
    else:
        st.write("**Website:** Not provided")


def display_edit_form(user):
    """Display user information in edit mode."""
    st.subheader("Edit Personal Information")

    with st.form("edit_user_form"):
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input(
                "First Name *", value=st.session_state.user_data["first_name"], help="Required field"
            )
            last_name = st.text_input(
                "Last Name *", value=st.session_state.user_data["last_name"], help="Required field"
            )
            phone_number = st.text_input(
                "Phone Number", value=st.session_state.user_data["phone_number"], help="Optional"
            )
            email = st.text_input(
                "Email", value=st.session_state.user_data["email"], help="Optional - must be valid email format"
            )
            address = st.text_input("Address", value=st.session_state.user_data["address"], help="Optional")

        with col2:
            city = st.text_input("City", value=st.session_state.user_data["city"], help="Optional")
            state = st.text_input("State", value=st.session_state.user_data["state"], help="Optional")
            zip_code = st.text_input("ZIP Code", value=st.session_state.user_data["zip_code"], help="Optional")
            linkedin_url = st.text_input(
                "LinkedIn URL",
                value=st.session_state.user_data["linkedin_url"],
                help="Optional - will add https:// if not provided",
            )
            github_url = st.text_input(
                "GitHub URL",
                value=st.session_state.user_data["github_url"],
                help="Optional - will add https:// if not provided",
            )
            website_url = st.text_input(
                "Website URL",
                value=st.session_state.user_data["website_url"],
                help="Optional - will add https:// if not provided",
            )

        # Check if any changes were made
        current_data = {
            "first_name": first_name,
            "last_name": last_name,
            "phone_number": phone_number,
            "email": email,
            "address": address,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "linkedin_url": linkedin_url,
            "github_url": github_url,
            "website_url": website_url,
        }

        has_changes = any(current_data[key] != st.session_state.user_data[key] for key in current_data)

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save Changes", disabled=not has_changes, type="primary"):
                if not first_name.strip() or not last_name.strip():
                    st.error("First name and last name are required.")
                else:
                    try:
                        # Update user data
                        UserService.update_user(user.id, **current_data)
                        st.success("Profile updated successfully!")
                        st.session_state.edit_mode = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating profile: {str(e)}")
                        logger.error(f"Error updating user profile: {e}")

        with col2:
            if st.form_submit_button("❌ Cancel"):
                st.session_state.edit_mode = False
                st.rerun()


def display_experience_section(user_id):
    """Display and manage work experience section."""
    st.subheader("Work Experience")

    # Add new experience button
    if st.button("➕ Add New Experience", type="primary"):
        show_add_experience_dialog(user_id)

    # Display existing experiences
    try:
        experiences = ExperienceService.list_user_experiences(user_id)

        if experiences:
            for exp in experiences:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.write(f"**{exp.job_title}** at **{exp.company_name}**")
                        st.write(
                            f"*{exp.start_date.strftime('%B %Y')} - {exp.end_date.strftime('%B %Y') if exp.end_date else 'Present'}*"
                        )
                        st.write(exp.content)

                    with col2:
                        if st.button("✏️", key=f"edit_exp_{exp.id}", help="Edit experience"):
                            show_edit_experience_dialog(exp, user_id)

                    with col3:
                        if st.button("🗑️", key=f"delete_exp_{exp.id}", help="Delete experience"):
                            st.session_state[f"confirm_delete_exp_{exp.id}"] = True
                            st.rerun()

                    # Delete confirmation
                    if st.session_state.get(f"confirm_delete_exp_{exp.id}", False):
                        display_delete_confirmation("experience", exp.id, exp.company_name)

                    st.divider()
        else:
            st.info("No work experience added yet. Click 'Add New Experience' to add your first experience.")

    except Exception as e:
        st.error(f"Error loading experiences: {str(e)}")
        logger.error(f"Error loading experiences: {e}")


def display_education_section(user_id):
    """Display and manage education section."""
    st.subheader("Education")

    # Add new education button
    if st.button("➕ Add New Education", type="primary"):
        show_add_education_dialog(user_id)

    # Display existing educations
    try:
        educations = EducationService.list_user_educations(user_id)

        if educations:
            for edu in educations:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.write(f"**{edu.degree}** from **{edu.school}**")
                        st.write(f"*{edu.start_date.strftime('%B %Y')} - {edu.end_date.strftime('%B %Y')}*")

                    with col2:
                        if st.button("✏️", key=f"edit_edu_{edu.id}", help="Edit education"):
                            show_edit_education_dialog(edu, user_id)

                    with col3:
                        if st.button("🗑️", key=f"delete_edu_{edu.id}", help="Delete education"):
                            st.session_state[f"confirm_delete_edu_{edu.id}"] = True
                            st.rerun()

                    # Delete confirmation
                    if st.session_state.get(f"confirm_delete_edu_{edu.id}", False):
                        display_delete_confirmation("education", edu.id, edu.school)

                    st.divider()
        else:
            st.info("No education added yet. Click 'Add New Education' to add your first education.")

    except Exception as e:
        st.error(f"Error loading educations: {str(e)}")
        logger.error(f"Error loading educations: {e}")


def display_delete_confirmation(item_type, item_id, item_name):
    """Display delete confirmation dialog."""
    st.warning(f"Are you sure you want to delete this {item_type}: **{item_name}**?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, Delete", type="primary"):
            try:
                if item_type == "experience":
                    success = ExperienceService.delete_experience(item_id)
                else:  # education
                    success = EducationService.delete_education(item_id)

                if success:
                    st.success(f"{item_type.title()} deleted successfully!")
                    st.session_state[f"confirm_delete_{item_type}_{item_id}"] = False
                    st.rerun()
                else:
                    st.error(f"Failed to delete {item_type}.")
            except Exception as e:
                st.error(f"Error deleting {item_type}: {str(e)}")
                logger.error(f"Error deleting {item_type}: {e}")

    with col2:
        if st.button("❌ Cancel"):
            st.session_state[f"confirm_delete_{item_type}_{item_id}"] = False
            st.rerun()


display_user_profile()
