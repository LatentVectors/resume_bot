"""User profile page for managing single user in the Resume Bot application."""

import streamlit as st

from app.components.confirm_delete import confirm_delete
from app.dialog.certificate_dialog import show_add_certificate_dialog, show_edit_certificate_dialog
from app.dialog.education_dialog import show_add_education_dialog, show_edit_education_dialog
from app.dialog.experience_dialog import show_add_experience_dialog, show_edit_experience_dialog
from app.services.certificate_service import CertificateService
from app.services.education_service import EducationService
from app.services.experience_service import ExperienceService
from app.services.user_service import UserService
from src.logging_config import logger


def display_user_profile():
    """Display the user profile page."""
    st.title("User Profile")

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

    st.markdown("---")

    # Certificates Management Section
    display_certificates_section(user.id)


def display_user_info(user):
    """Display user information in read-only mode."""
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Personal Information")
    with col2:
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("", icon=":material/edit:", help="Edit"):
                st.session_state.edit_mode = True
                st.rerun()

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
        st.write("**LinkedIn:** N/A")

    if user.github_url:
        st.write(f"**GitHub:** [{user.github_url}]({user.github_url})")
    else:
        st.write("**GitHub:** N/A")

    if user.website_url:
        st.write(f"**Website:** [{user.website_url}]({user.website_url})")
    else:
        st.write("**Website:** N/A")


def display_edit_form(user):
    """Display user information in edit mode."""
    with st.form("edit_user_form"):
        # Reserve a header area to render top-aligned controls after computing state
        header_container = st.container()

        # Section: Personal Information (match read-only layout)
        st.subheader("Personal Information")
        name_col1, name_col2 = st.columns(2)
        with name_col1:
            first_name = st.text_input(
                "First Name *", value=st.session_state.user_data["first_name"], help="Required field"
            )
        with name_col2:
            last_name = st.text_input(
                "Last Name *", value=st.session_state.user_data["last_name"], help="Required field"
            )

        contact_col1, contact_col2 = st.columns(2)
        with contact_col1:
            email = st.text_input(
                "Email", value=st.session_state.user_data["email"], help="Optional - must be valid email format"
            )
        with contact_col2:
            phone_number = st.text_input(
                "Phone Number", value=st.session_state.user_data["phone_number"], help="Optional"
            )

        # Section: Address (match read-only layout)
        st.subheader("Address")
        addr_row1_col1, addr_row1_col2 = st.columns(2)
        with addr_row1_col1:
            address = st.text_input("Street", value=st.session_state.user_data["address"], help="Optional")
        with addr_row1_col2:
            city = st.text_input("City", value=st.session_state.user_data["city"], help="Optional")

        addr_row2_col1, addr_row2_col2 = st.columns(2)
        with addr_row2_col1:
            state = st.text_input("State", value=st.session_state.user_data["state"], help="Optional")
        with addr_row2_col2:
            zip_code = st.text_input("ZIP Code", value=st.session_state.user_data["zip_code"], help="Optional")

        # Section: Online Presence (match read-only layout)
        st.subheader("Online Presence")
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

        # Render the header (buttons at the top) now that we have has_changes
        with header_container:
            header_left, header_right = st.columns(2)
            with header_left:
                st.subheader("Personal Information")
            with header_right:
                with st.container(horizontal=True, horizontal_alignment="right"):
                    cancel_clicked = st.form_submit_button("Cancel")
                    save_clicked = st.form_submit_button("Save", type="primary")

        if cancel_clicked:
            st.session_state.edit_mode = False
            st.rerun()

        if save_clicked:
            if not has_changes:
                st.info("No changes to save.")
            elif not first_name.strip() or not last_name.strip():
                st.error("First name and last name are required.")
            else:
                try:
                    # Update user data
                    UserService.update_user(user.id, **current_data)
                    # Keep session state in sync so future edits reflect saved values
                    st.session_state.user_data = current_data
                    st.success("Profile updated successfully!")
                    st.session_state.edit_mode = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating profile: {str(e)}")
                    logger.error(f"Error updating user profile: {e}")


def display_experience_section(user_id):
    """Display and manage work experience section."""
    st.subheader("Work Experience")

    # Add new experience button
    if st.button("Add Experience", type="primary"):
        show_add_experience_dialog(user_id)

    # Display existing experiences
    try:
        experiences = ExperienceService.list_user_experiences(user_id)

        if experiences:
            for exp in experiences:
                with st.container(border=True):
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.write(f"**{exp.job_title}**")
                    with col2:
                        with st.container(horizontal=True, horizontal_alignment="right"):
                            if st.button("", key=f"edit_exp_{exp.id}", icon=":material/edit:", help="Edit"):
                                show_edit_experience_dialog(exp, user_id)
                            if st.button("", key=f"delete_exp_{exp.id}", icon=":material/delete:", help="Delete"):
                                st.session_state[f"confirm_delete_exp_{exp.id}"] = True
                                st.rerun()

                    # Subheader: Company | Location | Mon YYYY - Mon YYYY
                    start_str = exp.start_date.strftime("%b %Y")
                    end_str = exp.end_date.strftime("%b %Y") if getattr(exp, "end_date", None) else "Present"
                    parts = [exp.company_name]
                    location_val = getattr(exp, "location", None)
                    if location_val:
                        parts.append(location_val)
                    parts.append(f"{start_str} - {end_str}")
                    st.caption(" | ".join(parts))

                    with st.expander("Details", expanded=False):
                        st.write(getattr(exp, "content", ""))

                    # Delete confirmation
                    if st.session_state.get(f"confirm_delete_exp_{exp.id}", False):

                        def _on_confirm(exp_id: int = exp.id):
                            try:
                                success = ExperienceService.delete_experience(exp_id)
                                if success:
                                    st.session_state[f"confirm_delete_exp_{exp_id}"] = False
                                    st.success("Experience deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete experience.")
                            except Exception as e:
                                st.error(f"Error deleting experience: {e}")
                                logger.error(f"Error deleting experience {exp_id}: {e}")

                        def _on_cancel(exp_id: int = exp.id):
                            st.session_state[f"confirm_delete_exp_{exp_id}"] = False
                            st.rerun()

                        confirm_delete("experience", _on_confirm, _on_cancel)
        else:
            st.info("No work experience added yet. Click 'Add Experience' to add your first experience.")

    except Exception as e:
        st.error(f"Error loading experiences: {str(e)}")
        logger.error(f"Error loading experiences: {e}")


def display_education_section(user_id):
    """Display and manage education section."""
    st.subheader("Education")

    # Add new education button
    if st.button("Add Education", type="primary"):
        show_add_education_dialog(user_id)

    # Display existing educations
    try:
        educations = EducationService.list_user_educations(user_id)

        if educations:
            for edu in educations:
                with st.container(border=True):
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.write(f"**{edu.institution}**")
                        subline = f"{edu.degree} | {edu.major} | {edu.grad_date.strftime('%b %Y')}"
                        st.caption(subline)
                    with col2:
                        with st.container(horizontal=True, horizontal_alignment="right"):
                            if st.button("", key=f"edit_edu_{edu.id}", icon=":material/edit:", help="Edit education"):
                                show_edit_education_dialog(edu, user_id)
                            if st.button(
                                "", key=f"delete_edu_{edu.id}", icon=":material/delete:", help="Delete education"
                            ):
                                st.session_state[f"confirm_delete_edu_{edu.id}"] = True
                                st.rerun()

                    # Delete confirmation using shared component
                    if st.session_state.get(f"confirm_delete_edu_{edu.id}", False):

                        def _on_confirm(edu_id: int = edu.id) -> None:
                            try:
                                success = EducationService.delete_education(edu_id)
                                if success:
                                    st.success("Education deleted successfully!")
                                else:
                                    st.error("Failed to delete education.")
                            finally:
                                st.session_state[f"confirm_delete_edu_{edu_id}"] = False
                                st.rerun()

                        def _on_cancel(edu_id: int = edu.id) -> None:
                            st.session_state[f"confirm_delete_edu_{edu_id}"] = False
                            st.rerun()

                        confirm_delete("education", _on_confirm, _on_cancel)
        else:
            st.info("No education added yet. Click 'Add Education' to add your first education.")

    except Exception as e:
        st.error(f"Error loading educations: {str(e)}")
        logger.error(f"Error loading educations: {e}")


def display_delete_confirmation(item_type: str, item_id: int, item_name: str) -> None:
    """Display delete confirmation dialog using shared component."""
    entity_label = f"{item_type}: {item_name}"

    def _on_confirm(it: str = item_type, iid: int = item_id) -> None:
        try:
            if it == "experience":
                success = ExperienceService.delete_experience(iid)
            elif it == "education":
                success = EducationService.delete_education(iid)
            elif it == "certificate":
                success = CertificateService.delete_certification(iid)
            else:
                success = False
                st.error(f"Unsupported item type: {it}")

            if success:
                st.success(f"{it.title()} deleted successfully!")
            else:
                st.error(f"Failed to delete {it}.")
        except Exception as e:
            st.error(f"Error deleting {it}: {str(e)}")
            logger.error(f"Error deleting {it}: {e}")
        finally:
            st.session_state[f"confirm_delete_{it}_{iid}"] = False
            st.rerun()

    def _on_cancel(it: str = item_type, iid: int = item_id) -> None:
        st.session_state[f"confirm_delete_{it}_{iid}"] = False
        st.rerun()

    confirm_delete(entity_label, _on_confirm, _on_cancel)


def display_certificates_section(user_id):
    """Display and manage certificates section."""
    st.subheader("Certificates")

    if st.button("Add Certificate", type="primary"):
        show_add_certificate_dialog(user_id)

    try:
        certifications = CertificateService.list_user_certifications(user_id)

        if certifications:
            for cert in certifications:
                with st.container(border=True):
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.write(f"**{cert.title}**")
                    with col2:
                        with st.container(horizontal=True, horizontal_alignment="right"):
                            if st.button(
                                "", key=f"edit_cert_{cert.id}", icon=":material/edit:", help="Edit certificate"
                            ):
                                show_edit_certificate_dialog(cert, user_id)
                            if st.button(
                                "", key=f"delete_cert_{cert.id}", icon=":material/delete:", help="Delete certificate"
                            ):
                                st.session_state[f"confirm_delete_cert_{cert.id}"] = True
                                st.rerun()

                    # Subheader line with Institution and Date
                    institution_text = cert.institution if cert.institution else ""
                    date_text = cert.date.strftime("%b %Y")
                    if institution_text:
                        st.caption(f"{institution_text} | {date_text}")
                    else:
                        st.caption(f"{date_text}")

                # Delete confirmation using shared component
                if st.session_state.get(f"confirm_delete_cert_{cert.id}", False):
                    cert_id = cert.id

                    def _on_confirm(cert_id: int = cert_id) -> None:  # bind current id
                        success = CertificateService.delete_certification(cert_id)
                        if success:
                            st.success("Certificate deleted successfully!")
                        else:
                            st.error("Failed to delete certificate.")
                        st.session_state[f"confirm_delete_cert_{cert_id}"] = False
                        st.rerun()

                    def _on_cancel(cert_id: int = cert_id) -> None:  # bind current id
                        st.session_state[f"confirm_delete_cert_{cert_id}"] = False
                        st.rerun()

                    confirm_delete("certificate", _on_confirm, _on_cancel)
        else:
            st.info("No certificates added yet. Click 'Add Certificate' to add your first one.")

    except Exception as e:
        st.error(f"Error loading certificates: {str(e)}")
        logger.error(f"Error loading certificates: {e}")


display_user_profile()
