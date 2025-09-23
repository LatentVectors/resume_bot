from __future__ import annotations

import re
from pathlib import Path
from typing import cast

import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

from app.components.info_banner import top_info_banner
from app.constants import MIN_DATE
from app.dialog.resume_add_certificate_dialog import show_resume_add_certificate_dialog
from app.dialog.resume_add_education_dialog import show_resume_add_education_dialog
from app.dialog.resume_add_experience_dialog import show_resume_add_experience_dialog
from app.dialog.resume_reset_dialog import show_resume_reset_dialog
from app.services.experience_service import ExperienceService
from app.services.job_service import JobService
from app.services.resume_service import ResumeService
from app.services.user_service import UserService
from app.shared.filenames import build_resume_download_filename
from src.database import Job as DbJob
from src.features.resume.data_adapter import (
    fetch_experience_data,
    fetch_user_data,
    transform_user_to_resume_data,
)
from src.features.resume.types import (
    ResumeCertification,
    ResumeData,
    ResumeEducation,
    ResumeExperience,
)
from src.features.resume.utils import list_available_templates
from src.logging_config import logger


def _build_download_filename(job: DbJob, full_name: str) -> str:
    """Builds: "Resume - {company} - {title} - {name} - {yyyy_mm_dd}.pdf"""
    return build_resume_download_filename(job.company_name, job.job_title, full_name)


def _templates_dir() -> Path:
    # Project root from app/pages/job_tabs/resume.py → up 3 levels
    root = Path(__file__).resolve().parents[3]
    return root / "src" / "features" / "resume" / "templates"


def _load_or_seed_draft(job_id: int, job_title: str | None) -> tuple[ResumeData, str]:
    """Return current draft and template for the job, seeding from DB or profile.

    On first load for a job, prefer persisted Resume JSON; otherwise seed from user profile.
    """
    try:
        if isinstance(st.session_state.get("resume_draft"), ResumeData) and isinstance(
            st.session_state.get("resume_template"), str
        ):
            return cast(ResumeData, st.session_state["resume_draft"]), cast(str, st.session_state["resume_template"])  # type: ignore[return-value]

        # Try existing persisted resume
        row = JobService.get_resume_for_job(job_id)
        if row and (row.resume_json or "").strip():
            try:
                draft = ResumeData.model_validate_json(row.resume_json)  # type: ignore[arg-type]
                template = (row.template_name or "resume_000.html").strip() or "resume_000.html"
                st.session_state["resume_draft"] = draft
                st.session_state["resume_template"] = template
                st.session_state["resume_last_saved"] = draft
                st.session_state["resume_template_saved"] = template
                st.session_state["resume_dirty"] = False
                return draft, template
            except Exception as exc:  # noqa: BLE001
                logger.exception(exc)

        # Seed from user profile
        user = UserService.get_current_user()
        if not user or not user.id:
            # Minimal empty shell if no user yet
            draft = ResumeData(
                name="",
                title=(job_title or "")[:120],
                email="",
                phone="",
                linkedin_url="",
                professional_summary="",
                experience=[],
                education=[],
                skills=[],
                certifications=[],
            )
        else:
            user_data = fetch_user_data(user.id)
            experiences = fetch_experience_data(user.id)
            draft = transform_user_to_resume_data(
                user_data=user_data, experience_data=experiences, job_title=job_title or ""
            )

        template = "resume_000.html"
        st.session_state["resume_draft"] = draft
        st.session_state["resume_template"] = template
        st.session_state["resume_last_saved"] = draft
        st.session_state["resume_template_saved"] = template
        st.session_state["resume_dirty"] = False
        return draft, template
    except Exception as exc:  # noqa: BLE001
        logger.exception(exc)
        # Fallback safe empty draft
        empty = ResumeData(
            name="",
            title=(job_title or "")[:120],
            email="",
            phone="",
            linkedin_url="",
            professional_summary="",
            experience=[],
            education=[],
            skills=[],
            certifications=[],
        )
        st.session_state["resume_draft"] = empty
        st.session_state["resume_template"] = "resume_000.html"
        st.session_state["resume_last_saved"] = empty
        st.session_state["resume_template_saved"] = "resume_000.html"
        st.session_state["resume_dirty"] = False
        return empty, "resume_000.html"


def _missing_required_identity(draft: ResumeData) -> list[str]:
    missing: list[str] = []
    if not (draft.name or "").strip():
        missing.append("name")
    if not (draft.email or "").strip():
        missing.append("email")
    return missing


def _render_profile_section(draft: ResumeData, *, read_only: bool) -> ResumeData:
    with st.expander("Profile", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full Name", value=draft.name, key="resume_name", disabled=read_only)
        with c2:
            title = st.text_input(
                "Title :material/smart_toy:", value=draft.title, key="resume_title", disabled=read_only
            )

        c3, c4 = st.columns(2)
        with c3:
            email = st.text_input("Email", value=draft.email, key="resume_email", disabled=read_only)
        with c4:
            phone = st.text_input("Phone Number", value=draft.phone, key="resume_phone", disabled=read_only)

        linkedin = st.text_input("LinkedIn URL", value=draft.linkedin_url, key="resume_linkedin", disabled=read_only)

        summary = st.text_area(
            "Professional Summary :material/smart_toy:",
            value=draft.professional_summary,
            key="resume_summary",
            height=250,
            disabled=read_only,
        )

    return draft.model_copy(
        update={
            "name": name,
            "title": title,
            "email": email,
            "phone": phone,
            "linkedin_url": linkedin,
            "professional_summary": summary,
        }
    )


def _render_experience_section(draft: ResumeData, *, read_only: bool) -> ResumeData:
    new_experiences: list[ResumeExperience] = []
    deletion_happened = False
    with st.expander("Experience", expanded=False):
        for idx, exp in enumerate(draft.experience):
            with st.container(border=True):
                row1 = st.columns([2, 2, 0.3])
                with row1[0]:
                    etitle = st.text_input("Title", value=exp.title, key=f"exp_title_{idx}", disabled=read_only)
                with row1[1]:
                    company = st.text_input("Company", value=exp.company, key=f"exp_company_{idx}", disabled=read_only)
                with row1[2]:
                    del_exp = st.button(
                        ":material/delete:", key=f"exp_delete_{idx}", help="Delete experience", disabled=read_only
                    )

                # Row for Location (placed above dates)
                location = st.text_input(
                    "Location",
                    value=exp.location,
                    key=f"exp_location_{idx}",
                    disabled=read_only,
                )

                row2 = st.columns([2, 2])
                with row2[0]:
                    start_dt = st.date_input(
                        "Start Date",
                        value=exp.start_date,
                        min_value=MIN_DATE,
                        key=f"exp_start_{idx}",
                        disabled=read_only,
                    )
                with row2[1]:
                    end_dt = st.date_input(
                        "End Date (optional)",
                        value=exp.end_date,
                        min_value=MIN_DATE,
                        key=f"exp_end_{idx}",
                        disabled=read_only,
                    )

                # (Location already captured above)

                # Points editor (bulk via textarea; one point per line)
                points_text = st.text_area(
                    ":material/smart_toy: Points (one per line)",
                    value="\n".join(exp.points or []),
                    key=f"exp_{idx}_points_text",
                    height=350,
                    disabled=read_only,
                    help="Each non-empty line becomes a separate point.",
                )
                new_points: list[str] = [ln.strip() for ln in (points_text or "").splitlines() if ln.strip()]

                # After potential deletion, decide to keep or drop experience
                if not del_exp:
                    new_experiences.append(
                        ResumeExperience(
                            title=etitle,
                            company=company,
                            location=location,
                            start_date=start_dt,
                            end_date=end_dt,
                            points=[p for p in new_points if p.strip()],
                        )
                    )
                else:
                    deletion_happened = True

        if not read_only:
            if st.button("Add Experience", key="add_experience"):
                show_resume_add_experience_dialog()

    if deletion_happened:
        try:
            st.session_state["resume_draft"] = draft.model_copy(update={"experience": new_experiences})
            # Clear experience-related widget state to avoid index/key collisions after deletion
            for key in list(st.session_state.keys()):
                if isinstance(key, str) and key.startswith("exp_"):
                    st.session_state.pop(key, None)
        except Exception as exc:  # noqa: BLE001
            logger.exception(exc)
        st.rerun()

    return draft.model_copy(update={"experience": new_experiences})


def _render_education_section(draft: ResumeData, *, read_only: bool) -> ResumeData:
    new_education: list[ResumeEducation] = []
    deletion_happened = False
    with st.expander("Education", expanded=False):
        for idx, edu in enumerate(draft.education):
            with st.container(border=True):
                row1 = st.columns([2, 2, 0.3])
                with row1[0]:
                    inst = st.text_input(
                        "Institution", value=edu.institution, key=f"edu_inst_{idx}", disabled=read_only
                    )
                with row1[1]:
                    deg = st.text_input("Degree", value=edu.degree, key=f"edu_deg_{idx}", disabled=read_only)
                with row1[2]:
                    del_edu = st.button(
                        ":material/delete:", key=f"edu_delete_{idx}", help="Delete education", disabled=read_only
                    )

                major = st.text_input("Major", value=edu.major, key=f"edu_maj_{idx}", disabled=read_only)

                grad_dt = st.date_input(
                    "Graduation Date",
                    value=edu.grad_date,
                    min_value=MIN_DATE,
                    key=f"edu_grad_{idx}",
                    disabled=read_only,
                )

                if not del_edu:
                    new_education.append(
                        ResumeEducation(
                            degree=deg,
                            major=major,
                            institution=inst,
                            grad_date=grad_dt,
                        )
                    )
                else:
                    deletion_happened = True

        if not read_only and st.button("Add Education", key="add_education"):
            show_resume_add_education_dialog()

    if deletion_happened:
        try:
            st.session_state["resume_draft"] = draft.model_copy(update={"education": new_education})
            # Clear education-related widget state to avoid index/key collisions after deletion
            for key in list(st.session_state.keys()):
                if isinstance(key, str) and key.startswith("edu_"):
                    st.session_state.pop(key, None)
        except Exception as exc:  # noqa: BLE001
            logger.exception(exc)
        st.rerun()

    return draft.model_copy(update={"education": new_education})


def _render_certifications_section(draft: ResumeData, *, read_only: bool) -> ResumeData:
    new_certs: list[ResumeCertification] = []
    deletion_happened = False
    with st.expander("Certificates", expanded=False):
        for idx, cert in enumerate(draft.certifications):
            with st.container(border=True):
                row = st.columns([3, 2, 0.3])
                with row[0]:
                    title = st.text_input("Title", value=cert.title, key=f"cert_title_{idx}", disabled=read_only)
                with row[1]:
                    date_dt = st.date_input(
                        "Date",
                        value=cert.date,
                        min_value=MIN_DATE,
                        key=f"cert_date_{idx}",
                        disabled=read_only,
                    )
                with row[2]:
                    del_cert = st.button(
                        ":material/delete:", key=f"cert_delete_{idx}", help="Delete certification", disabled=read_only
                    )

                if not del_cert:
                    new_certs.append(ResumeCertification(title=title, date=date_dt))
                else:
                    deletion_happened = True

        if not read_only and st.button("Add Certification", key="add_cert"):
            show_resume_add_certificate_dialog()

    if deletion_happened:
        try:
            st.session_state["resume_draft"] = draft.model_copy(update={"certifications": new_certs})
            # Clear certification-related widget state to avoid index/key collisions after deletion
            for key in list(st.session_state.keys()):
                if isinstance(key, str) and key.startswith("cert_"):
                    st.session_state.pop(key, None)
        except Exception as exc:  # noqa: BLE001
            logger.exception(exc)
        st.rerun()

    return draft.model_copy(update={"certifications": new_certs})


def _render_skills_section(draft: ResumeData, *, read_only: bool) -> ResumeData:
    with st.expander("Skills :material/smart_toy:", expanded=False):
        skills_text = st.text_area(
            "Skills (accepts commas and/or newlines; formatted one per line)",
            value="\n".join(draft.skills),
            key="resume_skills_textarea",
            disabled=read_only,
            height=400,
        )
        # Accept commas, newlines, or a mix; normalize whitespace
        # Split on commas or newlines, collapse consecutive separators
        raw_parts = re.split(r"[\n,]+", skills_text or "")
        skills_list = [part.strip() for part in raw_parts if part and part.strip()]

        # Re-format textarea to one-per-line so the UI normalizes on rerun
        if not read_only:
            try:
                st.session_state["resume_skills_textarea"] = "\n".join(skills_list)
            except Exception:
                pass

    return draft.model_copy(update={"skills": (draft.skills if read_only else skills_list)})


def _embed_pdf_bytes(pdf_bytes: bytes, *, height: int = 900) -> None:
    """Embed a PDF using the custom PDF viewer component from raw bytes."""
    try:
        if not pdf_bytes:
            st.info("No preview available.")
            return
        pdf_viewer(pdf_bytes, width="100%", height=height, zoom_level="auto")
    except Exception as exc:  # noqa: BLE001
        logger.exception(exc)
        st.warning("Unable to embed PDF preview.")


def render_resume(job: DbJob) -> None:
    """Render the Resume tab with version navigation, pinning, and bytes-based preview/download."""
    # Make job id available to add-object dialogs for preview rendering
    try:
        st.session_state["current_job_id"] = job.id
    except Exception:
        pass

    is_read_only = bool(job.applied_at)

    # Fetch version history and canonical
    try:
        versions = ResumeService.list_versions(job.id)
    except Exception as exc:  # noqa: BLE001
        logger.exception(exc)
        versions = []

    try:
        canonical_row = ResumeService.get_canonical(job.id)
    except Exception as exc:  # noqa: BLE001
        logger.exception(exc)
        canonical_row = None

    id_to_version = {v.id: v for v in versions if v.id is not None}
    head_version = versions[-1] if versions else None

    # Determine which version (if any) matches canonical
    canonical_version_id: int | None = None
    if canonical_row is not None and versions:
        for v in reversed(versions):
            try:
                if v.template_name == canonical_row.template_name and v.resume_json == canonical_row.resume_json:
                    canonical_version_id = cast(int, v.id)
                    break
            except Exception:
                continue

    # Selected version logic: canonical if present, else head, else None
    selected_version_id = cast(int | None, st.session_state.get("resume_selected_version_id"))
    if selected_version_id is None or selected_version_id not in id_to_version:
        selected_version_id = (
            canonical_version_id
            if canonical_version_id is not None
            else (cast(int, head_version.id) if head_version and head_version.id is not None else None)
        )
        st.session_state["resume_selected_version_id"] = selected_version_id

    # Seed editor state: prefer in-progress draft if dirty; otherwise load from selected version
    existing_draft = cast(ResumeData | None, st.session_state.get("resume_draft"))
    existing_template = cast(str | None, st.session_state.get("resume_template"))
    loaded_from_version_id = cast(int | None, st.session_state.get("resume_loaded_from_version_id"))

    if selected_version_id is not None:
        # Reload from selected version only if version changed OR there's no working draft
        should_load_from_selected = loaded_from_version_id != selected_version_id or existing_draft is None
        if should_load_from_selected:
            sel = id_to_version[selected_version_id]
            try:
                draft = ResumeData.model_validate_json(sel.resume_json)  # type: ignore[arg-type]
            except Exception as exc:  # noqa: BLE001
                logger.exception(exc)
                draft = ResumeData(
                    name="",
                    title=(job.job_title or "")[:120],
                    email="",
                    phone="",
                    linkedin_url="",
                    professional_summary="",
                    experience=[],
                    education=[],
                    skills=[],
                    certifications=[],
                )
            template_name = (sel.template_name or "resume_000.html").strip() or "resume_000.html"
            # Baseline equals the selected version content
            st.session_state["resume_draft"] = draft
            st.session_state["resume_template"] = template_name
            st.session_state["resume_last_saved"] = draft
            st.session_state["resume_template_saved"] = template_name
            st.session_state["resume_dirty"] = False
            st.session_state["resume_loaded_from_version_id"] = selected_version_id
        else:
            # Keep working draft/template when there are unsaved edits for the same selected version
            draft = cast(ResumeData, existing_draft)
            template_name = cast(str, existing_template or "resume_000.html")
    else:
        # No selected version: use existing working draft if any; otherwise seed from DB/profile
        if isinstance(existing_draft, ResumeData) and isinstance(existing_template, str):
            draft = existing_draft
            template_name = existing_template
        else:
            draft, template_name = _load_or_seed_draft(job.id, job.job_title)

    # Experience requirement: user must have at least one profile experience
    current_user = UserService.get_current_user()
    profile_has_experience = False
    try:
        if current_user and current_user.id:
            user_experiences = ExperienceService.list_user_experiences(current_user.id)
            profile_has_experience = len(user_experiences) > 0
    except Exception as exc:  # noqa: BLE001
        logger.exception(exc)
        profile_has_experience = False

    if not profile_has_experience:
        top_info_banner(
            "You must add at least one experience to your profile before generating a resume.",
            button_label="Go to Profile",
            target_page="pages/profile.py",
            key="resume_add_experience_nav",
        )

    # Layout
    left, right = st.columns([4, 3])

    with left:
        st.subheader("Resume Content")
        # Header controls: version navigation and pin (hidden when Applied)
        if not is_read_only and versions:
            with st.container(horizontal=True, horizontal_alignment="right"):
                sel = id_to_version.get(selected_version_id) if selected_version_id is not None else None
                current_index = int(sel.version_index) if sel is not None else 1
                min_index = 1
                max_index = int(versions[-1].version_index)

                # Left arrow
                go_left = st.button(
                    ":material/chevron_left:",
                    key="resume_ver_left",
                    disabled=current_index <= min_index,
                    help="Older version",
                )

                # Dropdown of versions in descending order (vN..v1)
                try:
                    versions_desc = sorted(versions, key=lambda v: int(v.version_index), reverse=True)
                except Exception:
                    versions_desc = list(reversed(versions))
                labels = [f"v{v.version_index}" for v in versions_desc]
                indices = [int(v.version_index) for v in versions_desc]
                try:
                    dd_idx = indices.index(current_index)
                except ValueError:
                    dd_idx = 0  # default to newest (first)
                chosen_label = st.selectbox(
                    "Version",
                    options=labels,
                    index=dd_idx,
                    label_visibility="collapsed",
                    key="resume_version_select",
                )

                # Right arrow
                go_right = st.button(
                    ":material/chevron_right:",
                    key="resume_ver_right",
                    disabled=current_index >= max_index,
                    help="Newer version",
                )

                # Pin icon
                selected_is_canonical = (
                    selected_version_id is not None
                    and canonical_version_id is not None
                    and selected_version_id == canonical_version_id
                )
                pin_label = ":material/keep:" if selected_is_canonical else ":material/keep_off:"
                pin_help = "Pinned (canonical)" if selected_is_canonical else "Set selected version as canonical"
                pin_type = "primary" if selected_is_canonical else "secondary"
                pin_clicked = st.button(pin_label, help=pin_help, key="resume_pin_btn", type=pin_type)
                # Handle nav/pin events
                new_selected_id: int | None = None
                if go_left:
                    target_index = current_index - 1
                    for v in versions:
                        if int(v.version_index) == target_index:
                            new_selected_id = cast(int, v.id)
                            break
                elif go_right:
                    target_index = current_index + 1
                    for v in versions:
                        if int(v.version_index) == target_index:
                            new_selected_id = cast(int, v.id)
                            break
                else:
                    # Dropdown change
                    try:
                        chosen_index = int(chosen_label.removeprefix("v"))
                        if chosen_index != current_index:
                            for v in versions:
                                if int(v.version_index) == chosen_index:
                                    new_selected_id = cast(int, v.id)
                                    break
                    except Exception:
                        pass

                if pin_clicked and selected_version_id is not None:
                    try:
                        ResumeService.pin_canonical(job.id, selected_version_id)
                        st.toast("Pinned canonical resume.")
                    except Exception as exc:  # noqa: BLE001
                        logger.exception(exc)
                        st.error("Failed to set canonical resume.")
                    # Recompute canonical mapping
                    try:
                        canonical_row = ResumeService.get_canonical(job.id)
                    except Exception:
                        canonical_row = None
                    canonical_version_id = None
                    if canonical_row is not None:
                        for v in reversed(versions):
                            if (
                                v.template_name == canonical_row.template_name
                                and v.resume_json == canonical_row.resume_json
                            ):
                                canonical_version_id = cast(int, v.id)
                                break
                    st.rerun()

                if new_selected_id is not None and new_selected_id in id_to_version:
                    st.session_state["resume_selected_version_id"] = new_selected_id
                    # Reset dirty and baseline to selected version
                    new_v = id_to_version[new_selected_id]
                    try:
                        new_draft = ResumeData.model_validate_json(new_v.resume_json)  # type: ignore[arg-type]
                    except Exception as exc:  # noqa: BLE001
                        logger.exception(exc)
                        new_draft = draft
                    st.session_state["resume_draft"] = new_draft
                    st.session_state["resume_template"] = new_v.template_name
                    st.session_state["resume_last_saved"] = new_draft
                    st.session_state["resume_template_saved"] = new_v.template_name
                    st.session_state["resume_dirty"] = False
                    st.rerun()

        st.text_area(
            "What should the AI change?",
            key="resume_instructions",
            value=st.session_state.get("resume_instructions", ""),
            placeholder="What special instructions should the AI follow?",
            label_visibility="collapsed",
            height=300,
        )

        # Control buttons row + right-aligned Template dropdown
        cols = st.columns([1, 2, 2])
        if not is_read_only:
            try:
                templates = list_available_templates(_templates_dir())
            except Exception as exc:  # noqa: BLE001
                logger.exception(exc)
                templates = ["resume_000.html"]

            with cols[1]:
                selected_template = st.selectbox(
                    "Template",
                    options=templates,
                    index=(templates.index(template_name) if template_name in templates else 0),
                    key="resume_template_select",
                    label_visibility="collapsed",
                )
        else:
            # Keep previous template when read-only; do not render control
            selected_template = cast(str, st.session_state.get("resume_template", template_name))

        # Render sections
        updated = _render_profile_section(draft, read_only=is_read_only)
        updated = _render_experience_section(updated, read_only=is_read_only)
        updated = _render_education_section(updated, read_only=is_read_only)
        updated = _render_certifications_section(updated, read_only=is_read_only)
        updated = _render_skills_section(updated, read_only=is_read_only)

        # Compute dirty state versus baseline (selected version or last saved)
        saved_draft = cast(ResumeData, st.session_state.get("resume_last_saved", draft))
        saved_template = cast(str, st.session_state.get("resume_template_saved", template_name))
        is_dirty = updated.model_dump_json() != saved_draft.model_dump_json() or selected_template != saved_template
        st.session_state["resume_dirty"] = is_dirty

        # Persist draft and template in session for subsequent runs
        st.session_state["resume_draft"] = updated
        st.session_state["resume_template"] = selected_template

        missing = _missing_required_identity(updated)

        generate_clicked = False
        save_clicked = False
        if not is_read_only:
            with cols[0]:
                generate_clicked = st.button(
                    "Generate",
                    type="primary",
                    disabled=(bool(missing) or (not profile_has_experience)),
                    help=(
                        ("Fill required identity fields: " + ", ".join(missing))
                        if missing
                        else (
                            "Add at least one experience on your profile to enable generation"
                            if not profile_has_experience
                            else None
                        )
                    ),
                    key="resume_generate_btn",
                )
            with cols[2]:
                with st.container(horizontal=True, horizontal_alignment="right"):
                    save_clicked = st.button(
                        "Save",
                        disabled=(not is_dirty) or bool(missing),
                        key="resume_save_btn",
                        type="primary",
                    )
                    if st.button("Discard", disabled=not is_dirty, key="resume_discard_btn"):
                        saved = cast(ResumeData, st.session_state.get("resume_last_saved", draft))
                        saved_template = cast(str, st.session_state.get("resume_template_saved", template_name))
                        st.session_state["resume_draft"] = saved
                        st.session_state["resume_template"] = saved_template
                        st.session_state["resume_dirty"] = False
                        st.rerun()

        if missing:
            st.warning(
                "Required identity fields are missing: "
                + ", ".join(missing)
                + ". Update your profile or fill them here."
            )

    # Handle actions after rendering buttons to avoid layout jumps
    if generate_clicked:
        try:
            user = UserService.get_current_user()
            if not user or not user.id:
                st.error("No user found. Create a user before generating a resume.")
            else:
                prompt = cast(str, st.session_state.get("resume_instructions", ""))
                new_draft = ResumeService.generate_resume_for_job(
                    user.id, job.id, prompt, cast(ResumeData | None, st.session_state.get("resume_draft"))
                )
                st.session_state["resume_draft"] = new_draft
                st.session_state["resume_dirty"] = True
                # Clear widget keys so that the widgets re-initialize from the new draft values
                try:
                    for key in (
                        "resume_title",
                        "resume_summary",
                        "resume_skills_textarea",
                    ):
                        st.session_state.pop(key, None)
                    st.session_state["resume_instructions"] = ""
                    for key in list(st.session_state.keys()):
                        if isinstance(key, str) and key.startswith("exp_") and key.endswith("_points_text"):
                            st.session_state.pop(key, None)
                except Exception as exc:  # noqa: BLE001
                    logger.exception(exc)
                # After generate, select the new head if available
                try:
                    versions = ResumeService.list_versions(job.id)
                    if versions:
                        st.session_state["resume_selected_version_id"] = cast(int, versions[-1].id)
                except Exception as exc:  # noqa: BLE001
                    logger.exception(exc)
                st.toast("Draft updated via AI. Preview refreshed.")
                st.rerun()
        except Exception as exc:  # noqa: BLE001
            logger.exception(exc)
            st.error("Failed to generate resume draft.")

    if save_clicked:
        try:
            current_draft = cast(ResumeData, st.session_state.get("resume_draft", draft))
            saved_version = ResumeService.save_resume(
                job.id, current_draft, cast(str, st.session_state.get("resume_template", template_name))
            )
            # Clear dirty and update saved state and selection
            st.session_state["resume_last_saved"] = current_draft
            st.session_state["resume_template_saved"] = cast(
                str, st.session_state.get("resume_template", template_name)
            )
            st.session_state["resume_dirty"] = False
            try:
                st.session_state["resume_selected_version_id"] = cast(int, saved_version.id)
            except Exception:
                pass
            st.toast("Resume saved as new version.")
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            logger.exception(exc)
            st.error("Failed to save resume.")

    # Right column: preview and download (bytes only)
    with right:
        current_draft = cast(ResumeData, st.session_state.get("resume_draft", draft))
        current_template = cast(str, st.session_state.get("resume_template", template_name))
        missing = _missing_required_identity(current_draft)
        is_dirty = bool(st.session_state.get("resume_dirty", False))

        # Header row: Preview title + right-aligned Reset + Download buttons
        header_cols = st.columns([1, 1])
        with header_cols[0]:
            st.subheader("Preview")
        with header_cols[1]:
            with st.container(horizontal=True, horizontal_alignment="right"):
                if not is_read_only:
                    if st.button(
                        "Reset",
                        help=("Hard reset: clear resume and history; seed from profile."),
                        key="resume_reset_btn_header",
                    ):
                        show_resume_reset_dialog(int(job.id))

                # Render bytes only when allowed to show a preview
                pdf_bytes: bytes | None = None
                try:
                    if is_read_only:
                        # Applied: show canonical only
                        if canonical_row is not None:
                            can_draft = ResumeData.model_validate_json(canonical_row.resume_json)  # type: ignore[arg-type]
                            pdf_bytes = ResumeService.render_preview(job.id, can_draft, canonical_row.template_name)
                    else:
                        if not missing:
                            pdf_bytes = ResumeService.render_preview(job.id, current_draft, current_template)
                except Exception as exc:  # noqa: BLE001
                    logger.exception(exc)
                    pdf_bytes = None

                # Download button rules
                selected_is_canonical = (
                    selected_version_id is not None
                    and canonical_version_id is not None
                    and selected_version_id == canonical_version_id
                )
                allow_download = (is_read_only and canonical_row is not None) or (
                    (not is_read_only) and selected_is_canonical and (not is_dirty)
                )
                help_text = None
                if not allow_download:
                    if is_read_only:
                        help_text = "No canonical resume to download."
                    elif not selected_is_canonical:
                        help_text = "Download only available for pinned (canonical) version."
                    elif is_dirty:
                        help_text = "Save changes to enable download."

                st.download_button(
                    label="Download",
                    data=(pdf_bytes or b""),
                    file_name=_build_download_filename(job, current_draft.name),
                    mime="application/pdf",
                    disabled=not (allow_download and pdf_bytes),
                    type="primary",
                    help=help_text,
                    key="resume_download_btn_header",
                )

        # Body preview
        if is_read_only:
            if canonical_row is None:
                st.info("This job has no canonical resume and is locked (Applied).")
            else:
                try:
                    can_draft = ResumeData.model_validate_json(canonical_row.resume_json)  # type: ignore[arg-type]
                    can_bytes = ResumeService.render_preview(job.id, can_draft, canonical_row.template_name)
                    _embed_pdf_bytes(can_bytes)
                except Exception as exc:  # noqa: BLE001
                    logger.exception(exc)
                    st.info("Unable to render canonical preview.")
        else:
            if missing:
                st.warning("Preview disabled until required identity fields are filled")
            else:
                try:
                    preview_bytes = ResumeService.render_preview(job.id, current_draft, current_template)
                    _embed_pdf_bytes(preview_bytes)
                except Exception as exc:  # noqa: BLE001
                    logger.exception(exc)
                    st.info("No preview available.")
