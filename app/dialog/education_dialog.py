"""Education dialog components for adding and editing education entries."""

from datetime import date

import streamlit as st
from loguru import logger

from app.services.education_service import EducationService


@st.dialog("Add Education", width="large")
def show_add_education_dialog(user_id):
    """Show dialog for adding new education entry."""
    st.subheader("Add New Education")

    with st.form("add_education_dialog_form"):
        # School and Degree in a single column
        school = st.text_input("School/Institution *", help="Required")
        degree = st.text_input("Degree *", help="Required")

        # Start and End dates inline at the bottom
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date *", value=date.today(), help="Required")
        with col2:
            end_date = st.date_input("End Date *", value=date.today(), help="Required")

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Add Education", type="primary"):
                if not school.strip() or not degree.strip():
                    st.error("School and degree are required.")
                elif start_date > end_date:
                    st.error("Start date must be before end date.")
                else:
                    try:
                        education_data = {
                            "school": school.strip(),
                            "degree": degree.strip(),
                            "start_date": start_date.isoformat(),
                            "end_date": end_date.isoformat(),
                        }

                        EducationService.create_education(user_id, **education_data)
                        st.success("Education added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding education: {str(e)}")
                        logger.error(f"Error adding education: {e}")

        with col2:
            if st.form_submit_button("Cancel"):
                st.rerun()


@st.dialog("Edit Education", width="large")
def show_edit_education_dialog(education, user_id):
    """Show dialog for editing existing education entry."""
    st.subheader("Edit Education")

    with st.form(f"edit_education_dialog_form_{education.id}"):
        # School and Degree in a single column
        school = st.text_input("School/Institution *", value=education.school, help="Required")
        degree = st.text_input("Degree *", value=education.degree, help="Required")

        # Start and End dates inline at the bottom
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date *", value=education.start_date, help="Required")
        with col2:
            end_date = st.date_input("End Date *", value=education.end_date, help="Required")

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Save Changes", type="primary"):
                if not school.strip() or not degree.strip():
                    st.error("School and degree are required.")
                elif start_date > end_date:
                    st.error("Start date must be before end date.")
                else:
                    try:
                        update_data = {
                            "school": school.strip(),
                            "degree": degree.strip(),
                            "start_date": start_date.isoformat(),
                            "end_date": end_date.isoformat(),
                        }

                        EducationService.update_education(education.id, **update_data)
                        st.success("Education updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating education: {str(e)}")
                        logger.error(f"Error updating education: {e}")

        with col2:
            if st.form_submit_button("Cancel"):
                st.rerun()
