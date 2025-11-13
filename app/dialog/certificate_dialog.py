"""Certificate dialog components for adding and editing certification entries."""

import asyncio
from datetime import date

import streamlit as st

from app.api_client.endpoints.certificates import CertificatesAPI
from app.components.confirm_delete import confirm_delete
from app.constants import MIN_DATE
from src.logging_config import logger


@st.dialog("Add Certificate", width="large")
def show_add_certificate_dialog(user_id):
    """Show dialog for adding a new certificate entry."""
    st.subheader("Add New Certificate")

    with st.form("add_certificate_dialog_form"):
        # Title and Institution
        title = st.text_input("Title *", help="Required")
        institution = st.text_input("Institution", help="Optional")

        # Date
        cert_date = st.date_input("Date *", value=date.today(), min_value=MIN_DATE, help="Required")

        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.form_submit_button("Cancel"):
                st.rerun()

            if st.form_submit_button("Save", type="primary"):
                if not title.strip():
                    st.error("Title is required.")
                else:
                    try:
                        data = {"title": title.strip(), "date": cert_date.isoformat()}
                        if institution.strip():
                            data["institution"] = institution.strip()
                        asyncio.run(
                            CertificatesAPI.create_certificate(
                                user_id=user_id,
                                title=data["title"],
                                date=data["date"],
                                institution=data.get("institution"),
                            )
                        )
                        st.success("Certificate added successfully!")
                        st.rerun()
                    except Exception as e:  # noqa: BLE001
                        st.error(f"Error adding certificate: {str(e)}")
                        logger.error(f"Error adding certificate: {e}")


@st.dialog("Edit Certificate", width="large")
def show_edit_certificate_dialog(certificate, user_id):
    """Show dialog for editing an existing certificate entry."""
    st.subheader("Edit Certificate")

    # Optional inline delete confirmation inside dialog
    confirm_key = f"confirm_delete_dialog_cert_{certificate.id}"
    if st.session_state.get(confirm_key, False):

        def _on_confirm() -> None:
            try:
                asyncio.run(CertificatesAPI.delete_certificate(certificate.id))
                st.session_state[confirm_key] = False
                st.success("Certificate deleted successfully!")
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(f"Error deleting certificate: {str(e)}")
                logger.error(f"Error deleting certificate: {e}")

        def _on_cancel() -> None:
            st.session_state[confirm_key] = False
            st.rerun()

        confirm_delete("certificate", _on_confirm, _on_cancel)
        return

    with st.form(f"edit_certificate_dialog_form_{certificate.id}"):
        title = st.text_input("Title *", value=certificate.title, help="Required")
        institution = st.text_input("Institution", value=certificate.institution or "", help="Optional")
        cert_date = st.date_input("Date *", value=certificate.date, min_value=MIN_DATE, help="Required")

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.form_submit_button("Save", type="primary"):
                if not title.strip():
                    st.error("Title is required.")
                else:
                    try:
                        updates = {"title": title.strip(), "date": cert_date.isoformat()}
                        updates["institution"] = institution.strip() if institution.strip() else None
                        asyncio.run(
                            CertificatesAPI.update_certificate(
                                certificate_id=certificate.id,
                                title=updates["title"],
                                date=updates["date"],
                                institution=updates.get("institution"),
                            )
                        )
                        st.success("Certificate updated successfully!")
                        st.rerun()
                    except Exception as e:  # noqa: BLE001
                        st.error(f"Error updating certificate: {str(e)}")
                        logger.error(f"Error updating certificate: {e}")

        with col2:
            if st.form_submit_button("Cancel"):
                st.rerun()

        with col3:
            if st.form_submit_button("Delete"):
                st.session_state[confirm_key] = True
                st.rerun()
