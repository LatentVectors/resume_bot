"""Education dialog components for adding and editing education entries."""

from datetime import date

import streamlit as st

from app.constants import MIN_DATE
from app.services.education_service import EducationService
from src.logging_config import logger


@st.dialog("Add Education", width="large")
def show_add_education_dialog(user_id):
    """Show dialog for adding new education entry aligned to new schema."""
    st.subheader("Add New Education")

    with st.form("add_education_dialog_form"):
        institution = st.text_input("Institution *", help="Required")
        col_deg, col_major = st.columns(2)
        with col_deg:
            degree = st.text_input("Degree *", help="Required")
        with col_major:
            major = st.text_input("Major *", help="Required")

        grad_date = st.date_input(
            "Graduation Date *",
            value=date.today(),
            min_value=MIN_DATE,
            help="Required",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Add", type="primary"):
                if not institution.strip() or not degree.strip() or not major.strip():
                    st.error("Institution, degree, and major are required.")
                else:
                    try:
                        education_data = {
                            "institution": institution.strip(),
                            "degree": degree.strip(),
                            "major": major.strip(),
                            "grad_date": grad_date.isoformat(),
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
    """Show dialog for editing existing education entry aligned to new schema."""
    st.subheader("Edit Education")

    with st.form(f"edit_education_dialog_form_{education.id}"):
        institution = st.text_input("Institution *", value=education.institution, help="Required")
        col_deg, col_major = st.columns(2)
        with col_deg:
            degree = st.text_input("Degree *", value=education.degree, help="Required")
        with col_major:
            major = st.text_input("Major *", value=education.major, help="Required")

        grad_date = st.date_input(
            "Graduation Date *",
            value=education.grad_date,
            min_value=MIN_DATE,
            help="Required",
        )

        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.form_submit_button("Cancel"):
                st.rerun()

            if st.form_submit_button("Save", type="primary"):
                if not institution.strip() or not degree.strip() or not major.strip():
                    st.error("Institution, degree, and major are required.")
                else:
                    try:
                        update_data = {
                            "institution": institution.strip(),
                            "degree": degree.strip(),
                            "major": major.strip(),
                            "grad_date": grad_date.isoformat(),
                        }

                        EducationService.update_education(education.id, **update_data)
                        st.success("Education updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating education: {str(e)}")
                        logger.error(f"Error updating education: {e}")
