"""Step 2: Experience gap filling and chat."""

from __future__ import annotations

import json

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from app.constants import LLMTag
from app.dialog.job_intake.helpers import (
    EXPERIENCE_SYSTEM_PROMPT,
    EXPERIENCE_TOOLS,
    SUMMARIZATION_SYSTEM_PROMPT,
    format_gap_analysis_message,
)
from app.services.chat_message_service import ChatMessageService
from app.services.experience_service import ExperienceService
from app.services.job_service import JobService
from app.services.user_service import UserService
from app.shared.formatters import format_experience_with_achievements
from src.core.models import OpenAIModels, get_model
from src.database import db_manager
from src.features.jobs.gap_analysis import GapAnalysisReport, analyze_job_experience_fit
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
            st.session_state.step2_gap_analysis = gap_report

            # Save gap analysis to session
            gap_json = gap_report.model_dump_json()
            JobService.save_gap_analysis(session.id, gap_json)

            # Add gap analysis as first AI message
            gap_message = format_gap_analysis_message(gap_report)
            st.session_state.step2_messages.append(AIMessage(content=gap_message))

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
                        _render_proposal_card(tool_call, job_id, experiences)
        elif isinstance(msg, ToolMessage):
            # Tool messages are internal, don't display to user
            pass

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
                ai_response = _get_ai_response_with_tools(
                    st.session_state.step2_messages,
                    job.job_description,
                    experiences,
                )
                st.session_state.step2_messages.append(ai_response)
                st.markdown(ai_response.content)

                # Render proposal cards if AI made tool calls
                if hasattr(ai_response, "tool_calls") and ai_response.tool_calls:
                    for tool_call in ai_response.tool_calls:
                        _render_proposal_card(tool_call, job_id, experiences)

        # Save messages to database
        _save_step2_messages(session.id, st.session_state.step2_messages)

        st.rerun()

    # Action buttons
    st.markdown("---")
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Skip", key="intake_step2_skip"):
            _complete_step2(session.id, job_id)
            st.rerun()

        next_enabled = st.session_state.step2_user_message_count >= 1
        if st.button("Next", type="primary", disabled=not next_enabled, key="intake_step2_next"):
            _complete_step2(session.id, job_id)
            st.rerun()


# ==================== Helper Functions ====================


def _get_ai_response_with_tools(
    messages: list,
    job_description: str,
    experiences: list,
) -> AIMessage:
    """Get AI response with tool binding.

    Args:
        messages: Chat message history.
        job_description: Job description text.
        experiences: List of user experiences.

    Returns:
        AIMessage with possible tool calls.
    """
    # Format experiences for context
    experience_summary = _format_experiences_for_context(experiences)

    # Build prompt with context
    system_msg = EXPERIENCE_SYSTEM_PROMPT.format(
        job_description=job_description,
        experience_summary=experience_summary,
    )

    # Create LLM with tool binding
    llm = get_model(OpenAIModels.gpt_4o)
    llm_with_tools = llm.bind_tools(EXPERIENCE_TOOLS)

    # Build messages for LLM
    llm_messages = [{"role": "system", "content": system_msg}]
    for msg in messages:
        if isinstance(msg, HumanMessage):
            llm_messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            llm_messages.append({"role": "assistant", "content": msg.content})
        elif isinstance(msg, ToolMessage):
            llm_messages.append({"role": "tool", "content": msg.content, "tool_call_id": msg.tool_call_id})

    config = RunnableConfig(tags=[LLMTag.INTAKE_EXPERIENCE_CHAT.value])

    try:
        response = llm_with_tools.invoke(llm_messages, config=config)
        return response
    except Exception as exc:
        logger.exception("Error getting AI response with tools: %s", exc)
        return AIMessage(content="I apologize, but I encountered an error. Please try again.")


def _format_experiences_for_context(experiences: list) -> str:
    """Format experiences for AI context.

    Args:
        experiences: List of Experience objects.

    Returns:
        Formatted string.
    """
    if not experiences:
        return "No experience records found."

    parts = []
    for exp in experiences:
        # Fetch achievements for this experience
        achievements = db_manager.list_experience_achievements(exp.id)
        # Use the standardized formatter
        formatted = format_experience_with_achievements(exp, achievements)
        parts.append(formatted)

    return "\n\n".join(parts)


def _render_proposal_card(tool_call: dict, job_id: int, experiences: list) -> None:
    """Render a proposal card for a tool call.

    Args:
        tool_call: Tool call dictionary from AIMessage.
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
            _render_experience_update_proposal(tool_args, tool_id, experiences)
        elif tool_name == "propose_achievement_update":
            _render_achievement_update_proposal(tool_args, tool_id, experiences)
        elif tool_name == "propose_new_achievement":
            _render_new_achievement_proposal(tool_args, tool_id, experiences)


def _render_experience_update_proposal(args: dict, tool_id: str, experiences: list) -> None:
    """Render experience update proposal card.

    Args:
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

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Accept", key=f"accept_{tool_id}", type="primary"):
            _handle_accept_experience_update(exp_id, company_overview, role_overview, skills, tool_id)
    with col2:
        if st.button("❌ Reject", key=f"reject_{tool_id}"):
            _handle_reject_proposal(tool_id, "experience update")


def _render_achievement_update_proposal(args: dict, tool_id: str, experiences: list) -> None:
    """Render achievement update proposal card.

    Args:
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

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Accept", key=f"accept_{tool_id}", type="primary"):
            _handle_accept_achievement_update(achievement_id, edited_title, edited_content, tool_id)
    with col2:
        if st.button("❌ Reject", key=f"reject_{tool_id}"):
            _handle_reject_proposal(tool_id, "achievement update")


def _render_new_achievement_proposal(args: dict, tool_id: str, experiences: list) -> None:
    """Render new achievement proposal card.

    Args:
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

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Accept", key=f"accept_{tool_id}", type="primary"):
            _handle_accept_new_achievement(exp_id, edited_title, edited_content, order, tool_id)
    with col2:
        if st.button("❌ Reject", key=f"reject_{tool_id}"):
            _handle_reject_proposal(tool_id, "new achievement")


def _handle_accept_experience_update(
    exp_id: int,
    company_overview: str,
    role_overview: str,
    skills_str: str,
    tool_id: str,
) -> None:
    """Handle acceptance of experience update proposal.

    Args:
        exp_id: Experience ID.
        company_overview: Company overview text.
        role_overview: Role overview text.
        skills_str: Comma-separated skills string.
        tool_id: Tool call ID.
    """
    try:
        # Parse skills
        skills = [s.strip() for s in skills_str.split(",") if s.strip()] if skills_str else None

        # Update experience
        ExperienceService.update_experience_fields(
            exp_id,
            company_overview=company_overview or None,
            role_overview=role_overview or None,
            skills=skills,
        )

        # Mark as handled
        if "step2_handled_proposals" not in st.session_state:
            st.session_state.step2_handled_proposals = set()
        st.session_state.step2_handled_proposals.add(f"proposal_{tool_id}")

        # Add tool result to messages
        tool_msg = ToolMessage(
            content="Experience updated successfully. The user accepted your proposal.",
            tool_call_id=tool_id,
        )
        st.session_state.step2_messages.append(tool_msg)

        st.success("Experience updated!")
        st.rerun()
    except Exception as exc:
        logger.exception("Error accepting experience update: %s", exc)
        st.error("Failed to update experience. Please try again.")


def _handle_accept_achievement_update(achievement_id: int, title: str, content: str, tool_id: str) -> None:
    """Handle acceptance of achievement update proposal.

    Args:
        achievement_id: Achievement ID.
        title: Updated title.
        content: Updated content.
        tool_id: Tool call ID.
    """
    try:
        ExperienceService.update_achievement(achievement_id, title, content)

        # Mark as handled
        if "step2_handled_proposals" not in st.session_state:
            st.session_state.step2_handled_proposals = set()
        st.session_state.step2_handled_proposals.add(f"proposal_{tool_id}")

        # Add tool result to messages
        tool_msg = ToolMessage(
            content="Achievement updated successfully. The user accepted your proposal.",
            tool_call_id=tool_id,
        )
        st.session_state.step2_messages.append(tool_msg)

        st.success("Achievement updated!")
        st.rerun()
    except Exception as exc:
        logger.exception("Error accepting achievement update: %s", exc)
        st.error("Failed to update achievement. Please try again.")


def _handle_accept_new_achievement(exp_id: int, title: str, content: str, order: int | None, tool_id: str) -> None:
    """Handle acceptance of new achievement proposal.

    Args:
        exp_id: Experience ID.
        title: Achievement title.
        content: Achievement content.
        order: Optional order.
        tool_id: Tool call ID.
    """
    try:
        ExperienceService.add_achievement(exp_id, title, content, order)

        # Mark as handled
        if "step2_handled_proposals" not in st.session_state:
            st.session_state.step2_handled_proposals = set()
        st.session_state.step2_handled_proposals.add(f"proposal_{tool_id}")

        # Add tool result to messages
        tool_msg = ToolMessage(
            content="New achievement added successfully. The user accepted your proposal.",
            tool_call_id=tool_id,
        )
        st.session_state.step2_messages.append(tool_msg)

        st.success("Achievement added!")
        st.rerun()
    except Exception as exc:
        logger.exception("Error accepting new achievement: %s", exc)
        st.error("Failed to add achievement. Please try again.")


def _handle_reject_proposal(tool_id: str, proposal_type: str) -> None:
    """Handle rejection of a proposal.

    Args:
        tool_id: Tool call ID.
        proposal_type: Type of proposal being rejected.
    """
    # Mark as handled
    if "step2_handled_proposals" not in st.session_state:
        st.session_state.step2_handled_proposals = set()
    st.session_state.step2_handled_proposals.add(f"proposal_{tool_id}")

    # Add tool result to messages
    tool_msg = ToolMessage(
        content=f"The user rejected the {proposal_type}. Please ask them why or suggest an alternative.",
        tool_call_id=tool_id,
    )
    st.session_state.step2_messages.append(tool_msg)

    st.info("Proposal rejected. The AI will ask for feedback.")
    st.rerun()


def _save_step2_messages(session_id: int, messages: list) -> None:
    """Save Step 2 messages to database.

    Args:
        session_id: Intake session ID.
        messages: List of LangChain messages.
    """
    try:
        # Convert LangChain messages to dict format
        messages_dict = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                messages_dict.append({"type": "human", "content": msg.content})
            elif isinstance(msg, AIMessage):
                msg_dict = {"type": "ai", "content": msg.content}
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    msg_dict["tool_calls"] = msg.tool_calls
                messages_dict.append(msg_dict)
            elif isinstance(msg, ToolMessage):
                messages_dict.append(
                    {
                        "type": "tool",
                        "content": msg.content,
                        "tool_call_id": msg.tool_call_id,
                    }
                )

        # Save to database
        messages_json = json.dumps(messages_dict)
        ChatMessageService.append_messages(session_id, step=2, messages_json=messages_json)
    except Exception as exc:
        logger.exception("Error saving step 2 messages: %s", exc)


def _complete_step2(session_id: int, job_id: int) -> None:
    """Complete Step 2 and move to Step 3.

    Runs conversation summarization and updates session state.

    Args:
        session_id: Intake session ID.
        job_id: Job ID.
    """
    try:
        # Run conversation summarization
        messages = st.session_state.get("step2_messages", [])
        gap_analysis = st.session_state.get("step2_gap_analysis")

        if messages:
            summary = _summarize_conversation(messages, gap_analysis)
            JobService.save_conversation_summary(session_id, summary)

        # Mark step 2 as completed and move to step 3
        JobService.update_session_step(session_id, step=3, completed=False)

        # Update session state
        st.session_state.current_step = 3

        # Clear step 2 state
        if "step2_messages" in st.session_state:
            del st.session_state.step2_messages
        if "step2_user_message_count" in st.session_state:
            del st.session_state.step2_user_message_count
        if "step2_gap_analysis" in st.session_state:
            del st.session_state.step2_gap_analysis
        if "step2_pending_proposals" in st.session_state:
            del st.session_state.step2_pending_proposals
        if "step2_handled_proposals" in st.session_state:
            del st.session_state.step2_handled_proposals

    except Exception as exc:
        logger.exception("Error completing step 2: %s", exc)
        st.error("Failed to complete step. Please try again.")


def _summarize_conversation(messages: list, gap_analysis: GapAnalysisReport | None) -> str:
    """Summarize the Step 2 conversation.

    Args:
        messages: Chat message history.
        gap_analysis: Gap analysis report.

    Returns:
        Summary string.
    """
    if not messages:
        return "No conversation to summarize."

    try:
        # Format conversation for LLM
        conversation_text = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                conversation_text.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                conversation_text.append(f"Assistant: {msg.content}")

        conversation_str = "\n".join(conversation_text)

        # Add gap analysis context
        gap_context = ""
        if gap_analysis:
            gap_context = f"\n\nGap Analysis:\n{format_gap_analysis_message(gap_analysis)}"

        prompt = f"{conversation_str}{gap_context}\n\nProvide a concise summary of key insights from this conversation:"

        # Use LLM to summarize
        llm = get_model(OpenAIModels.gpt_4o)
        messages_for_llm = [
            {"role": "system", "content": SUMMARIZATION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        config = RunnableConfig(tags=[LLMTag.INTAKE_CONVERSATION_SUMMARY.value])
        response = llm.invoke(messages_for_llm, config=config)

        return response.content if hasattr(response, "content") else str(response)

    except Exception as exc:
        logger.exception("Error summarizing conversation: %s", exc)
        return "Unable to generate conversation summary."
