"""Step 3: Experience Updates - Display and manage AI-generated proposals."""

from __future__ import annotations

from collections import defaultdict

import streamlit as st

from app.pages.job_tabs.utils import navigate_to_job
from app.services.job_intake_service import JobIntakeService
from app.services.job_service import JobService
from app.shared.diff_utils import generate_diff_html
from src.database import (
    AchievementAdd,
    AchievementUpdate,
    CompanyOverviewUpdate,
    Experience,
    ProposalStatus,
    ProposalType,
    RoleOverviewUpdate,
    SkillAdd,
    SkillDelete,
    db_manager,
)
from src.logging_config import logger


def render_step3_experience_proposals(job_id: int | None) -> None:
    """Render Step 3: Experience Updates with proposal display and interaction.

    Args:
        job_id: The job ID for this intake session.
    """
    if not job_id:
        st.error("No job ID provided. Cannot proceed with experience updates.")
        return

    # Inject CSS for diff styling
    st.markdown(
        """
        <style>
        .diff-added {
            color: green;
            background-color: rgba(0, 255, 0, 0.1);
        }
        .diff-deleted {
            color: red;
            text-decoration: line-through;
            background-color: rgba(255, 0, 0, 0.1);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Progress indicator
    st.caption("Step 3 of 3: Experience Updates")

    # Get job and session
    job = JobService.get_job(job_id)
    if not job:
        st.error("Job not found.")
        return

    session = JobService.get_intake_session(job_id)
    if not session:
        st.error("Intake session not found.")
        return

    # Get all proposals for this session (from session state or database)
    proposals = st.session_state.get("step3_proposals", [])

    # If no proposals in session state, try to get from database (read-only)
    if not proposals:
        try:
            proposals = JobIntakeService.get_pending_proposals(session.id)
            st.session_state.step3_proposals = proposals
            logger.info(
                "Loaded %d proposals from database for session %s",
                len(proposals),
                session.id,
                extra={"session_id": session.id, "proposal_count": len(proposals)},
            )
        except Exception as exc:
            logger.exception(
                "Error loading proposals from database",
                extra={"session_id": session.id, "error_type": type(exc).__name__, "error_message": str(exc)},
            )
            st.warning("Unable to load proposals from database. Please refresh the page.")
            proposals = []

    # Empty state: No proposals detected
    if not proposals:
        st.info("No experience updates detected from your conversation.")

        # Action buttons with two-column layout
        back_col, action_col = st.columns([1, 1])

        with back_col:
            if st.button("Back", key="step3_empty_back"):
                # Go back to Step 2 without clearing state or updating database
                st.session_state.current_step = 2
                st.rerun()

        with action_col:
            with st.container(horizontal=True, horizontal_alignment="right"):
                if st.button("Next", type="primary", key="step3_empty_next"):
                    try:
                        JobService.complete_session(session.id)
                        _clear_step3_state()
                        navigate_to_job(job_id)
                    except Exception as exc:
                        logger.exception("Error completing step 3: %s", exc)
                        st.error("Failed to complete step. Please try again.")
                    st.rerun()
        return

    # Group proposals by experience
    proposals_by_experience = _group_proposals_by_experience(proposals)

    # Display proposals grouped by experience
    for exp_id, exp_proposals in proposals_by_experience.items():
        # Get experience details
        experience = db_manager.get_experience(exp_id)
        if not experience:
            logger.warning("Experience %s not found, skipping proposals", exp_id)
            continue

        # Experience header (non-expandable)
        st.markdown(f"### {experience.job_title} at {experience.company_name}")

        # Group proposals by type for ordered display
        proposals_by_type = _group_proposals_by_type(exp_proposals)

        # Display sections in order: Company Overview, Role Overview, Skills, Achievements
        if ProposalType.company_overview_update in proposals_by_type:
            st.markdown("#### Company Overview")
            for proposal in proposals_by_type[ProposalType.company_overview_update]:
                _render_proposal_card(proposal, experience)

        if ProposalType.role_overview_update in proposals_by_type:
            st.markdown("#### Role Overview")
            for proposal in proposals_by_type[ProposalType.role_overview_update]:
                _render_proposal_card(proposal, experience)

        if ProposalType.skill_add in proposals_by_type:
            st.markdown("#### Skills")
            for proposal in proposals_by_type[ProposalType.skill_add]:
                _render_proposal_card(proposal, experience)

        if ProposalType.achievement_add in proposals_by_type:
            st.markdown("#### Achievements")
            for proposal in proposals_by_type[ProposalType.achievement_add]:
                _render_proposal_card(proposal, experience)

        if ProposalType.achievement_update in proposals_by_type:
            st.markdown("#### Achievements")
            for proposal in proposals_by_type[ProposalType.achievement_update]:
                _render_proposal_card(proposal, experience)

        if ProposalType.achievement_delete in proposals_by_type:
            st.markdown("#### Achievements")
            for proposal in proposals_by_type[ProposalType.achievement_delete]:
                _render_proposal_card(proposal, experience)

        # Divider between experiences
        st.divider()

    # Action buttons at bottom with two-column layout
    back_col, action_col = st.columns([1, 1])

    with back_col:
        if st.button("Back", key="step3_back"):
            # Go back to Step 2 without clearing state or updating database
            st.session_state.current_step = 2
            st.rerun()

    with action_col:
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("Next", type="primary", key="step3_next"):
                try:
                    JobService.complete_session(session.id)
                    _clear_step3_state()
                    navigate_to_job(job_id)
                except Exception as exc:
                    logger.exception("Error completing step 3: %s", exc)
                    st.error("Failed to complete step. Please try again.")
                st.rerun()


def _group_proposals_by_experience(proposals: list) -> dict[int, list]:
    """Group proposals by experience_id."""
    grouped = defaultdict(list)
    for proposal in proposals:
        grouped[proposal.experience_id].append(proposal)
    return dict(grouped)


def _group_proposals_by_type(proposals: list) -> dict[ProposalType, list]:
    """Group proposals by proposal_type."""
    grouped = defaultdict(list)
    for proposal in proposals:
        grouped[proposal.proposal_type].append(proposal)
    return dict(grouped)


def _render_proposal_card(proposal, experience: Experience) -> None:
    """Render a single proposal card with view/edit modes.

    Args:
        proposal: ExperienceProposal object
        experience: Experience object for context
    """
    # Check if this proposal is being edited
    editing_proposal_id = st.session_state.get("step3_editing_proposal_id")
    is_editing = editing_proposal_id == proposal.id

    # Check if proposal is rejected (grayed out)
    is_rejected = proposal.status == ProposalStatus.rejected

    # Card container with conditional styling
    card_style = "opacity: 0.5;" if is_rejected else ""
    with st.container(border=True):
        if card_style:
            st.markdown(f'<div style="{card_style}">', unsafe_allow_html=True)

        # Header row: Proposal type badge + Action buttons
        col1, col2 = st.columns([3, 1])
        with col1:
            _render_proposal_type_badge(proposal.proposal_type)
        with col2:
            if is_editing:
                # Edit mode buttons: Cancel, Save
                if st.button("Cancel", key=f"step3_cancel_{proposal.id}", use_container_width=True):
                    st.session_state.step3_editing_proposal_id = None
                    st.session_state.pop(f"step3_edit_content_{proposal.id}", None)
                    st.rerun()
                if st.button("Save", type="primary", key=f"step3_save_{proposal.id}", use_container_width=True):
                    _handle_save_proposal(proposal)
            else:
                # View mode buttons: Edit, Accept, Reject
                button_cols = st.columns(3)
                with button_cols[0]:
                    if st.button(
                        "Edit", key=f"step3_edit_{proposal.id}", use_container_width=True, disabled=is_rejected
                    ):
                        st.session_state.step3_editing_proposal_id = proposal.id
                        # Initialize edit content from current proposal (store typed model)
                        proposal_content = proposal.parse_proposed_content()
                        st.session_state[f"step3_edit_content_{proposal.id}"] = proposal_content
                        st.rerun()
                with button_cols[1]:
                    if st.button(
                        "Accept", key=f"step3_accept_{proposal.id}", use_container_width=True, disabled=is_rejected
                    ):
                        _handle_accept_proposal(proposal)
                with button_cols[2]:
                    if st.button(
                        "Reject", key=f"step3_reject_{proposal.id}", use_container_width=True, disabled=is_rejected
                    ):
                        _handle_reject_proposal(proposal)

        # Content area
        try:
            if is_editing:
                _render_proposal_edit_mode(proposal, experience)
            else:
                _render_proposal_view_mode(proposal, experience)
        except Exception as exc:
            logger.exception(
                "Error rendering proposal content",
                extra={
                    "proposal_id": proposal.id,
                    "proposal_type": proposal.proposal_type.value,
                    "is_editing": is_editing,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
            st.error("Unable to display proposal content. Please refresh the page.")

        # Revert button (if proposal has been edited)
        if not is_editing and proposal.proposed_content != proposal.original_proposed_content:
            if st.button("Revert to Original", key=f"step3_revert_{proposal.id}", use_container_width=True):
                _handle_revert_proposal(proposal)

        if card_style:
            st.markdown("</div>", unsafe_allow_html=True)


def _render_proposal_type_badge(proposal_type: ProposalType) -> None:
    """Render proposal type badge with icon and color.

    Args:
        proposal_type: The proposal type enum value
    """
    icon_map = {
        ProposalType.achievement_add: ":material/add:",
        ProposalType.skill_add: ":material/add:",
        ProposalType.achievement_update: ":material/edit:",
        ProposalType.role_overview_update: ":material/edit:",
        ProposalType.company_overview_update: ":material/edit:",
        ProposalType.achievement_delete: ":material/delete:",
        ProposalType.skill_delete: ":material/delete:",
    }

    label_map = {
        ProposalType.achievement_add: "Add Achievement",
        ProposalType.achievement_update: "Update Achievement",
        ProposalType.achievement_delete: "Delete Achievement",
        ProposalType.skill_add: "Add Skill",
        ProposalType.skill_delete: "Delete Skill",
        ProposalType.role_overview_update: "Update Role Overview",
        ProposalType.company_overview_update: "Update Company Overview",
    }

    color_map = {
        ProposalType.achievement_add: "green",
        ProposalType.skill_add: "green",
        ProposalType.achievement_update: "blue",
        ProposalType.role_overview_update: "blue",
        ProposalType.company_overview_update: "blue",
        ProposalType.achievement_delete: "red",
        ProposalType.skill_delete: "red",
    }

    icon = icon_map.get(proposal_type, ":material/info:")
    label = label_map.get(proposal_type, proposal_type.value)
    color = color_map.get(proposal_type, "gray")

    st.badge(label=label, icon=icon, color=color)


def _render_proposal_view_mode(proposal, experience: Experience) -> None:
    """Render proposal content in view mode.

    Args:
        proposal: ExperienceProposal object
        experience: Experience object for context
    """
    try:
        proposal_content = proposal.parse_proposed_content()
    except ValueError as exc:
        st.error(f"Invalid proposal data: {exc}")
        return

    if proposal.proposal_type == ProposalType.achievement_update:
        # Show separate diffs for title and content
        if isinstance(proposal_content, AchievementUpdate):
            achievement_id = proposal_content.achievement_id
            if achievement_id:
                achievement = db_manager.get_achievement(achievement_id)
                if achievement:
                    # Title diff
                    original_title = achievement.title or ""
                    proposed_title = proposal_content.title or original_title
                    if original_title != proposed_title:
                        st.markdown("**Title:**")
                        st.markdown(generate_diff_html(original_title, proposed_title), unsafe_allow_html=True)
                    else:
                        st.markdown(f"**Title:** {original_title}")

                    # Content diff
                    original_content = achievement.content or ""
                    proposed_content = proposal_content.content
                    st.markdown("**Content:**")
                    st.markdown(generate_diff_html(original_content, proposed_content), unsafe_allow_html=True)

    elif proposal.proposal_type == ProposalType.achievement_add:
        # Show new title and content directly
        if isinstance(proposal_content, AchievementAdd):
            st.markdown(f"**Title:** {proposal_content.title}")
            st.markdown(f"**Content:** {proposal_content.content}")

    elif proposal.proposal_type == ProposalType.achievement_delete:
        # Show achievement that will be deleted
        achievement_id = proposal.achievement_id
        if achievement_id:
            achievement = db_manager.get_achievement(achievement_id)
            if achievement:
                st.markdown(f"**Title:** {achievement.title or ''}")
                st.markdown(f"**Content:** {achievement.content or ''}")

    elif proposal.proposal_type in (ProposalType.role_overview_update, ProposalType.company_overview_update):
        # Show full diff for overview updates
        original_content = ""
        if proposal.proposal_type == ProposalType.role_overview_update:
            original_content = experience.role_overview or ""
        else:
            original_content = experience.company_overview or ""

        if isinstance(proposal_content, (RoleOverviewUpdate, CompanyOverviewUpdate)):
            proposed_content = proposal_content.content
            st.markdown(generate_diff_html(original_content, proposed_content), unsafe_allow_html=True)

    elif proposal.proposal_type == ProposalType.skill_add:
        # Show skills as green badges
        if isinstance(proposal_content, SkillAdd):
            existing_skills = experience.skills or []
            for skill in proposal_content.skills:
                if skill not in existing_skills:
                    st.badge(label=skill, icon=":material/add:", color="green")

    elif proposal.proposal_type == ProposalType.skill_delete:
        # Show skills as red badges with strikethrough
        if isinstance(proposal_content, SkillDelete):
            existing_skills = experience.skills or []
            for skill in proposal_content.skills:
                if skill in existing_skills:
                    st.markdown(
                        f'<span style="text-decoration: line-through; color: red;">{skill}</span>',
                        unsafe_allow_html=True,
                    )


def _render_proposal_edit_mode(proposal, experience: Experience) -> None:
    """Render proposal content in edit mode.

    Args:
        proposal: ExperienceProposal object
        experience: Experience object for context
    """
    edit_content_key = f"step3_edit_content_{proposal.id}"
    if edit_content_key not in st.session_state:
        try:
            proposal_content = proposal.parse_proposed_content()
            st.session_state[edit_content_key] = proposal_content
        except ValueError as exc:
            st.error(f"Invalid proposal data: {exc}")
            return

    proposal_content = st.session_state[edit_content_key]

    if proposal.proposal_type in (ProposalType.achievement_add, ProposalType.achievement_update):
        # Separate inputs for title and content
        title_key = f"step3_edit_title_{proposal.id}"
        content_key = f"step3_edit_content_text_{proposal.id}"

        if isinstance(proposal_content, (AchievementAdd, AchievementUpdate)):
            title = st.text_input("Title", value=proposal_content.title or "", key=title_key)
            content = st.text_area("Content", value=proposal_content.content, key=content_key, height=200)

            # Update session state with new model instance
            if isinstance(proposal_content, AchievementAdd):
                updated_content = AchievementAdd(
                    command=proposal_content.command,
                    experience_id=proposal_content.experience_id,
                    title=title,
                    content=content,
                )
            else:  # AchievementUpdate
                updated_content = AchievementUpdate(
                    command=proposal_content.command,
                    experience_id=proposal_content.experience_id,
                    achievement_id=proposal_content.achievement_id,
                    title=title if title else None,
                    content=content,
                )
            st.session_state[edit_content_key] = updated_content

    elif proposal.proposal_type == ProposalType.skill_add:
        # Individual skill inputs with add/remove buttons
        if isinstance(proposal_content, SkillAdd):
            skills = list(proposal_content.skills)
            skills_key = f"step3_edit_skills_{proposal.id}"

            # Display existing proposed skills as editable inputs
            for idx, skill in enumerate(skills):
                col1, col2 = st.columns([4, 1])
                with col1:
                    updated_skill = st.text_input(
                        f"Skill {idx + 1}", value=skill, key=f"{skills_key}_{idx}", label_visibility="collapsed"
                    )
                    if updated_skill != skill:
                        skills[idx] = updated_skill
                with col2:
                    if st.button(":material/delete:", key=f"{skills_key}_delete_{idx}", help="Remove skill"):
                        skills.pop(idx)
                        st.rerun()

            # Add new skill button
            if st.button("Add Skill", key=f"{skills_key}_add"):
                skills.append("")
                st.rerun()

            # Update session state with new model instance
            updated_content = SkillAdd(
                command=proposal_content.command,
                experience_id=proposal_content.experience_id,
                skills=skills,
            )
            st.session_state[edit_content_key] = updated_content

    elif proposal.proposal_type in (ProposalType.role_overview_update, ProposalType.company_overview_update):
        # Single textarea for overview
        content_key = f"step3_edit_overview_{proposal.id}"
        if isinstance(proposal_content, (RoleOverviewUpdate, CompanyOverviewUpdate)):
            content = st.text_area("Content", value=proposal_content.content, key=content_key, height=200)

            # Update session state with new model instance
            if isinstance(proposal_content, RoleOverviewUpdate):
                updated_content = RoleOverviewUpdate(
                    command=proposal_content.command,
                    experience_id=proposal_content.experience_id,
                    content=content,
                )
            else:  # CompanyOverviewUpdate
                updated_content = CompanyOverviewUpdate(
                    command=proposal_content.command,
                    experience_id=proposal_content.experience_id,
                    content=content,
                )
            st.session_state[edit_content_key] = updated_content


def _handle_save_proposal(proposal) -> None:
    """Handle saving edited proposal content.

    Args:
        proposal: ExperienceProposal object
    """
    try:
        edit_content_key = f"step3_edit_content_{proposal.id}"
        if edit_content_key not in st.session_state:
            logger.warning(
                "Attempted to save proposal without edit content",
                extra={"proposal_id": proposal.id, "edit_content_key": edit_content_key},
            )
            st.error("No changes to save")
            return

        proposal_content = st.session_state[edit_content_key]
        # Validate that it's a ProposalContent model
        if not isinstance(
            proposal_content, (RoleOverviewUpdate, CompanyOverviewUpdate, SkillAdd, AchievementAdd, AchievementUpdate)
        ):
            logger.warning(
                "Invalid proposal content type in session state",
                extra={"proposal_id": proposal.id, "content_type": type(proposal_content).__name__},
            )
            st.error("Invalid proposal content. Please refresh and try again.")
            return

        # Validate and update proposal content (read-only validation)
        updated_proposal = JobIntakeService.update_proposal_content(proposal.id, proposal_content)

        # Update proposal in session state list (in-memory only, no database write)
        proposals = st.session_state.get("step3_proposals", [])
        for idx, p in enumerate(proposals):
            if p.id == proposal.id:
                proposals[idx] = updated_proposal
                break
        st.session_state.step3_proposals = proposals

        # Clear edit state
        st.session_state.step3_editing_proposal_id = None
        st.session_state.pop(edit_content_key, None)
        logger.info(
            "Proposal content updated (validation only)",
            extra={
                "proposal_id": proposal.id,
                "proposal_type": proposal.proposal_type.value,
                "experience_id": proposal.experience_id,
            },
        )
        st.toast("Proposal updated")
        st.rerun()
    except ValueError as exc:
        # Handle validation errors (e.g., invalid content format, proposal not found)
        logger.warning(
            "Validation error saving proposal: %s",
            exc,
            extra={
                "proposal_id": proposal.id,
                "proposal_type": proposal.proposal_type.value,
                "error_message": str(exc),
            },
        )
        st.error(f"Unable to save proposal: {str(exc)}. Please check your edits and try again.")
    except Exception as exc:
        # Handle any other unexpected errors
        logger.exception(
            "Unexpected error saving proposal",
            extra={
                "proposal_id": proposal.id,
                "proposal_type": proposal.proposal_type.value,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        st.error("Failed to save proposal due to an unexpected error. Your edits have been preserved.")


def _handle_accept_proposal(proposal) -> None:
    """Handle accepting a proposal.

    Args:
        proposal: ExperienceProposal object
    """
    try:
        # Validate proposal before accepting (read-only validation)
        success = JobIntakeService.accept_proposal(proposal.id)
        if success:
            # Update proposal status in session state (in-memory only, no database write)
            proposals = st.session_state.get("step3_proposals", [])
            for idx, p in enumerate(proposals):
                if p.id == proposal.id:
                    updated_proposal = proposals[idx]
                    updated_proposal.status = ProposalStatus.accepted
                    proposals[idx] = updated_proposal
                    break
            st.session_state.step3_proposals = proposals
            logger.info(
                "Proposal accepted (validation only)",
                extra={
                    "proposal_id": proposal.id,
                    "proposal_type": proposal.proposal_type.value,
                    "experience_id": proposal.experience_id,
                },
            )
            st.toast("Proposal accepted")
            st.rerun()
    except ValueError as exc:
        # Handle validation errors (e.g., proposal not found, invalid data)
        logger.warning(
            "Validation error accepting proposal: %s",
            exc,
            extra={
                "proposal_id": proposal.id,
                "proposal_type": proposal.proposal_type.value,
                "error_message": str(exc),
            },
        )
        st.error(f"Unable to accept proposal: {str(exc)}. Please check the proposal data and try again.")
    except Exception as exc:
        # Handle any other unexpected errors
        logger.exception(
            "Unexpected error accepting proposal",
            extra={
                "proposal_id": proposal.id,
                "proposal_type": proposal.proposal_type.value,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        st.error("Failed to accept proposal due to an unexpected error. The proposal remains pending.")
        # Keep proposal in pending state (don't update status)


def _handle_reject_proposal(proposal) -> None:
    """Handle rejecting a proposal.

    Args:
        proposal: ExperienceProposal object
    """
    try:
        # Validate proposal before rejecting (read-only validation)
        success = JobIntakeService.reject_proposal(proposal.id)
        if success:
            # Update proposal status in session state (in-memory only, no database write)
            proposals = st.session_state.get("step3_proposals", [])
            for idx, p in enumerate(proposals):
                if p.id == proposal.id:
                    updated_proposal = proposals[idx]
                    updated_proposal.status = ProposalStatus.rejected
                    proposals[idx] = updated_proposal
                    break
            st.session_state.step3_proposals = proposals
            logger.info(
                "Proposal rejected (validation only)",
                extra={
                    "proposal_id": proposal.id,
                    "proposal_type": proposal.proposal_type.value,
                    "experience_id": proposal.experience_id,
                },
            )
            st.toast("Proposal rejected")
            st.rerun()
    except ValueError as exc:
        # Handle validation errors (e.g., proposal not found)
        logger.warning(
            "Validation error rejecting proposal: %s",
            exc,
            extra={
                "proposal_id": proposal.id,
                "proposal_type": proposal.proposal_type.value,
                "error_message": str(exc),
            },
        )
        st.error(f"Unable to reject proposal: {str(exc)}. Please try again.")
    except Exception as exc:
        # Handle any other unexpected errors
        logger.exception(
            "Unexpected error rejecting proposal",
            extra={
                "proposal_id": proposal.id,
                "proposal_type": proposal.proposal_type.value,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        st.error("Failed to reject proposal due to an unexpected error. Please try again.")


def _handle_revert_proposal(proposal) -> None:
    """Handle reverting proposal to original AI content.

    Args:
        proposal: ExperienceProposal object
    """
    try:
        # Validate and revert proposal (read-only validation)
        reverted_proposal = JobIntakeService.revert_proposal_to_original(proposal.id)

        # Update proposal in session state list (in-memory only, no database write)
        proposals = st.session_state.get("step3_proposals", [])
        for idx, p in enumerate(proposals):
            if p.id == proposal.id:
                proposals[idx] = reverted_proposal
                break
        st.session_state.step3_proposals = proposals

        logger.info(
            "Proposal reverted to original (validation only)",
            extra={
                "proposal_id": proposal.id,
                "proposal_type": proposal.proposal_type.value,
                "experience_id": proposal.experience_id,
            },
        )
        st.toast("Proposal reverted to original")
        st.rerun()
    except ValueError as exc:
        # Handle validation errors (e.g., proposal not found)
        logger.warning(
            "Validation error reverting proposal: %s",
            exc,
            extra={
                "proposal_id": proposal.id,
                "proposal_type": proposal.proposal_type.value,
                "error_message": str(exc),
            },
        )
        st.error(f"Unable to revert proposal: {str(exc)}. Please try again.")
    except Exception as exc:
        # Handle any other unexpected errors
        logger.exception(
            "Unexpected error reverting proposal",
            extra={
                "proposal_id": proposal.id,
                "proposal_type": proposal.proposal_type.value,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        st.error("Failed to revert proposal due to an unexpected error. Please try again.")


def _clear_step3_state() -> None:
    """Clear step 3 session state."""
    for key in list(st.session_state.keys()):
        if key.startswith("step3_"):
            st.session_state.pop(key, None)
