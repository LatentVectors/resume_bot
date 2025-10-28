"""Step 2: Experience gap filling and chat."""

from __future__ import annotations

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.services.experience_service import ExperienceService
from app.services.job_intake_service import JobIntakeService, analyze_job_experience_fit
from app.services.job_intake_service.workflows.experience_enhancement import TOOLS
from app.services.job_service import JobService
from app.services.user_service import UserService
from src.logging_config import logger


def render_step2_experience(job_id: int | None) -> None:
    """Render Step 2: Experience gap filling chat.

    Args:
        job_id: The job ID for this intake session.
    """
    if not job_id:
        st.error("No job ID provided. Cannot proceed with experience review.")
        return

    # Progress indicator
    st.caption("Step 2 of 3: Experience Review")
    st.markdown("---")

    # Get job and session
    job = JobService.get_job(job_id)
    if not job:
        st.error("Job not found.")
        return

    session = JobService.get_intake_session(job_id)
    if not session:
        st.error("Intake session not found.")
        return

    # Get user and experiences
    user = UserService.get_current_user()
    if not user or not user.id:
        st.error("User not found.")
        return

    experiences = ExperienceService.list_user_experiences(user.id)

    # Initialize chat history in session state
    if "step2_messages" not in st.session_state:
        st.session_state.step2_messages = []
        st.session_state.step2_user_message_count = 0
        st.session_state.step2_gap_analysis = None
        st.session_state.step2_pending_proposals = {}

    # Run gap analysis if not already done
    if st.session_state.step2_gap_analysis is None:
        with st.spinner("Analyzing job requirements against your experience..."):
            gap_report = analyze_job_experience_fit(job.job_description, experiences)

            # Check if gap analysis was successful
            if not gap_report or not gap_report.strip():
                logger.error(
                    "Gap analysis returned empty result for job_id=%s. "
                    "This may indicate an LLM API error or configuration issue.",
                    job_id,
                )
                st.error(
                    "Unable to analyze job fit at this time. "
                    "Please try again or skip to continue with the intake process."
                )
                # Keep step2_gap_analysis as None to allow retry on rerun
            else:
                st.session_state.step2_gap_analysis = gap_report

                # Save gap analysis to session
                JobService.save_gap_analysis(session.id, gap_report)

                # Add gap analysis as first AI message
                st.session_state.step2_messages.append(AIMessage(content=gap_report))

    # Display chat messages
    for msg in st.session_state.step2_messages:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user"):
                st.markdown(msg.content)
        elif isinstance(msg, AIMessage):
            with st.chat_message("assistant"):
                st.markdown(msg.content)
                # Render proposal cards if AI made tool calls
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        _render_proposal_card(tool_call, session.id, job_id, experiences)
        elif isinstance(msg, ToolMessage):
            # Display tool execution confirmation
            with st.chat_message("assistant"):
                st.caption("🔧 Tool executed")
                st.text(msg.content)

    # Chat input
    if user_input := st.chat_input("Ask questions or provide additional context about your experience..."):
        # Add user message
        st.session_state.step2_messages.append(HumanMessage(content=user_input))
        st.session_state.step2_user_message_count += 1

        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(user_input)

        # Get AI response with tool binding
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                ai_response = JobIntakeService.get_experience_chat_response(
                    st.session_state.step2_messages,
                    job.job_description,
                    experiences,
                )
                st.session_state.step2_messages.append(ai_response)
                st.markdown(ai_response.content)

                # Execute tools immediately when AI calls them
                if hasattr(ai_response, "tool_calls") and ai_response.tool_calls:
                    for tool_call in ai_response.tool_calls:
                        # Execute the actual tool function to get its return value
                        tool_result = _invoke_tool(tool_call)

                        # Add ToolMessage with actual tool result
                        tool_msg = ToolMessage(content=tool_result, tool_call_id=tool_call.get("id"))
                        st.session_state.step2_messages.append(tool_msg)

                        # Render proposal card for user interaction
                        _render_proposal_card(tool_call, session.id, job_id, experiences)

        # Save messages to database
        JobIntakeService.save_step2_messages(session.id, st.session_state.step2_messages)

        st.rerun()

    # Action buttons
    st.markdown("---")
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Skip", key="intake_step2_skip"):
            try:
                JobIntakeService.complete_step2(
                    session.id,
                    job_id,
                    st.session_state.get("step2_messages", []),
                )
                # Clear step 2 state
                _clear_step2_state()
                # Update current step
                st.session_state.current_step = 3
                st.rerun()
            except Exception as exc:
                logger.exception("Error completing step 2: %s", exc)
                st.error("Failed to complete step. Please try again.")

        next_enabled = st.session_state.step2_user_message_count >= 1
        if st.button("Next", type="primary", disabled=not next_enabled, key="intake_step2_next"):
            try:
                JobIntakeService.complete_step2(
                    session.id,
                    job_id,
                    st.session_state.get("step2_messages", []),
                )
                # Clear step 2 state
                _clear_step2_state()
                # Update current step
                st.session_state.current_step = 3
                st.rerun()
            except Exception as exc:
                logger.exception("Error completing step 2: %s", exc)
                st.error("Failed to complete step. Please try again.")


# ==================== Helper Functions ====================


def _clear_step2_state() -> None:
    """Clear step 2 session state.

    Note: This does NOT clear intake flow state (intake_job_id, current_step, etc.)
    because step 2 is transitioning to step 3. The intake flow state is cleared
    only when the entire flow completes in step 3.
    """
    keys_to_clear = [
        "step2_messages",
        "step2_user_message_count",
        "step2_gap_analysis",
        "step2_pending_proposals",
        "step2_handled_proposals",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)


def _invoke_tool(tool_call: dict) -> str:
    """Invoke the actual tool function and return its result.

    Args:
        tool_call: Tool call dict with 'name', 'args', and 'id'.

    Returns:
        Tool result message from the actual tool function.
    """
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    # Find the matching tool by name
    for tool in TOOLS:
        if tool.name == tool_name:
            # Invoke the actual tool function with the args
            try:
                result = tool.invoke(args)
                return result
            except Exception as exc:
                logger.exception("Error invoking tool %s: %s", tool_name, exc)
                return f"Error executing tool: {str(exc)}"

    # If tool not found, return error
    return f"Unknown tool: {tool_name}"


def _render_proposal_card(tool_call: dict, session_id: int, job_id: int, experiences: list) -> None:
    """Render a proposal card for a tool call.

    Args:
        tool_call: Tool call dictionary from AIMessage.
        session_id: Intake session ID.
        job_id: Current job ID.
        experiences: List of experiences for validation.
    """
    tool_name = tool_call.get("name", "")
    tool_args = tool_call.get("args", {})
    tool_id = tool_call.get("id", "")

    # Create unique key for this proposal
    proposal_key = f"proposal_{tool_id}"

    # Check if already handled
    if proposal_key in st.session_state.get("step2_handled_proposals", set()):
        return

    with st.container(border=True):
        st.caption("🤖 Proposed Update")

        if tool_name == "propose_experience_update":
            _render_experience_update_proposal(session_id, tool_args, tool_id, experiences)
        elif tool_name == "propose_achievement_update":
            _render_achievement_update_proposal(session_id, tool_args, tool_id, experiences)
        elif tool_name == "propose_new_achievement":
            _render_new_achievement_proposal(session_id, tool_args, tool_id, experiences)


def _render_experience_update_proposal(session_id: int, args: dict, tool_id: str, experiences: list) -> None:
    """Render experience update proposal card.

    Args:
        session_id: Intake session ID.
        args: Tool arguments.
        tool_id: Tool call ID.
        experiences: List of experiences.
    """
    exp_id = args.get("experience_id")
    exp = next((e for e in experiences if e.id == exp_id), None)

    if not exp:
        st.warning(f"Experience {exp_id} not found.")
        return

    st.markdown(f"**Update Experience:** {exp.job_title} at {exp.company_name}")

    # Editable fields with proposed values
    company_overview = st.text_area(
        "Company Overview",
        value=args.get("company_overview", "") or exp.company_overview or "",
        key=f"co_{tool_id}",
    )
    role_overview = st.text_area(
        "Role Overview",
        value=args.get("role_overview", "") or exp.role_overview or "",
        key=f"ro_{tool_id}",
    )
    skills_value = args.get("skills") or exp.skills or []
    skills = st.text_input(
        "Skills (comma-separated)",
        value=", ".join(skills_value) if skills_value else "",
        key=f"sk_{tool_id}",
    )

    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Reject", key=f"reject_{tool_id}"):
            _handle_reject_proposal(session_id, tool_id, "experience update")
        if st.button("Accept", key=f"accept_{tool_id}", type="primary"):
            _handle_accept_experience_update(session_id, exp_id, company_overview, role_overview, skills, tool_id)


def _render_achievement_update_proposal(session_id: int, args: dict, tool_id: str, experiences: list) -> None:
    """Render achievement update proposal card.

    Args:
        session_id: Intake session ID.
        args: Tool arguments.
        tool_id: Tool call ID.
        experiences: List of experiences (for context).
    """
    achievement_id = args.get("achievement_id")
    title = args.get("title", "")
    content = args.get("content", "")

    st.markdown(f"**Update Achievement** (ID: {achievement_id})")

    edited_title = st.text_input(
        "Achievement Title",
        value=title,
        key=f"ach_title_{tool_id}",
    )

    edited_content = st.text_area(
        "Achievement Content",
        value=content,
        key=f"ach_{tool_id}",
    )

    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Reject", key=f"reject_{tool_id}"):
            _handle_reject_proposal(session_id, tool_id, "achievement update")
        if st.button("Accept", key=f"accept_{tool_id}", type="primary"):
            _handle_accept_achievement_update(session_id, achievement_id, edited_title, edited_content, tool_id)


def _render_new_achievement_proposal(session_id: int, args: dict, tool_id: str, experiences: list) -> None:
    """Render new achievement proposal card.

    Args:
        session_id: Intake session ID.
        args: Tool arguments.
        tool_id: Tool call ID.
        experiences: List of experiences.
    """
    exp_id = args.get("experience_id")
    title = args.get("title", "")
    content = args.get("content", "")
    order = args.get("order")

    exp = next((e for e in experiences if e.id == exp_id), None)
    if not exp:
        st.warning(f"Experience {exp_id} not found.")
        return

    st.markdown(f"**Add Achievement to:** {exp.job_title} at {exp.company_name}")

    edited_title = st.text_input(
        "Achievement Title",
        value=title,
        key=f"new_ach_title_{tool_id}",
    )

    edited_content = st.text_area(
        "Achievement Content",
        value=content,
        key=f"new_ach_{tool_id}",
    )

    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Reject", key=f"reject_{tool_id}"):
            _handle_reject_proposal(session_id, tool_id, "new achievement")
        if st.button("Accept", key=f"accept_{tool_id}", type="primary"):
            _handle_accept_new_achievement(session_id, exp_id, edited_title, edited_content, order, tool_id)


def _handle_accept_experience_update(
    session_id: int,
    exp_id: int,
    company_overview: str,
    role_overview: str,
    skills_str: str,
    tool_id: str,
) -> None:
    """Handle acceptance of experience update proposal.

    Args:
        session_id: Intake session ID.
        exp_id: Experience ID.
        company_overview: Company overview text.
        role_overview: Role overview text.
        skills_str: Comma-separated skills string.
        tool_id: Tool call ID.
    """
    # Parse skills
    skills = [s.strip() for s in skills_str.split(",") if s.strip()] if skills_str else None

    # Update experience via service
    success, message = JobIntakeService.accept_experience_update(
        exp_id,
        company_overview or None,
        role_overview or None,
        skills,
    )

    if success:
        # Mark as handled
        if "step2_handled_proposals" not in st.session_state:
            st.session_state.step2_handled_proposals = set()
        st.session_state.step2_handled_proposals.add(f"proposal_{tool_id}")

        # Add human message indicating acceptance
        human_msg = HumanMessage(content=f"I accept proposal {tool_id}. The update has been saved to my profile.")
        st.session_state.step2_messages.append(human_msg)

        # Save messages to database
        JobIntakeService.save_step2_messages(session_id, st.session_state.step2_messages)

        st.success("Experience updated!")
        st.rerun()
    else:
        st.error(message)


def _handle_accept_achievement_update(
    session_id: int, achievement_id: int, title: str, content: str, tool_id: str
) -> None:
    """Handle acceptance of achievement update proposal.

    Args:
        session_id: Intake session ID.
        achievement_id: Achievement ID.
        title: Updated title.
        content: Updated content.
        tool_id: Tool call ID.
    """
    # Update achievement via service
    success, message = JobIntakeService.accept_achievement_update(achievement_id, title, content)

    if success:
        # Mark as handled
        if "step2_handled_proposals" not in st.session_state:
            st.session_state.step2_handled_proposals = set()
        st.session_state.step2_handled_proposals.add(f"proposal_{tool_id}")

        # Add human message indicating acceptance
        human_msg = HumanMessage(content=f"I accept proposal {tool_id}. The update has been saved to my profile.")
        st.session_state.step2_messages.append(human_msg)

        # Save messages to database
        JobIntakeService.save_step2_messages(session_id, st.session_state.step2_messages)

        st.success("Achievement updated!")
        st.rerun()
    else:
        st.error(message)


def _handle_accept_new_achievement(
    session_id: int, exp_id: int, title: str, content: str, order: int | None, tool_id: str
) -> None:
    """Handle acceptance of new achievement proposal.

    Args:
        session_id: Intake session ID.
        exp_id: Experience ID.
        title: Achievement title.
        content: Achievement content.
        order: Optional order.
        tool_id: Tool call ID.
    """
    # Add new achievement via service
    success, message = JobIntakeService.accept_new_achievement(exp_id, title, content, order)

    if success:
        # Mark as handled
        if "step2_handled_proposals" not in st.session_state:
            st.session_state.step2_handled_proposals = set()
        st.session_state.step2_handled_proposals.add(f"proposal_{tool_id}")

        # Add human message indicating acceptance
        human_msg = HumanMessage(content=f"I accept proposal {tool_id}. The update has been saved to my profile.")
        st.session_state.step2_messages.append(human_msg)

        # Save messages to database
        JobIntakeService.save_step2_messages(session_id, st.session_state.step2_messages)

        st.success("Achievement added!")
        st.rerun()
    else:
        st.error(message)


def _handle_reject_proposal(session_id: int, tool_id: str, proposal_type: str) -> None:
    """Handle rejection of a proposal.

    Args:
        session_id: Intake session ID.
        tool_id: Tool call ID.
        proposal_type: Type of proposal being rejected.
    """
    # Mark as handled
    if "step2_handled_proposals" not in st.session_state:
        st.session_state.step2_handled_proposals = set()
    st.session_state.step2_handled_proposals.add(f"proposal_{tool_id}")

    # Add human message indicating rejection
    human_msg = HumanMessage(content=f"I reject proposal {tool_id}. Please suggest an alternative approach.")
    st.session_state.step2_messages.append(human_msg)

    # Save messages to database
    JobIntakeService.save_step2_messages(session_id, st.session_state.step2_messages)

    st.info("Proposal rejected. The AI will ask for feedback.")
    st.rerun()
