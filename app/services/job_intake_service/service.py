"""Business logic for job intake workflow.

This service handles the multi-step intake process including:
- Step 2: Experience gap filling with AI-assisted chat
- Step 3: Resume generation and refinement

All AI interactions and data persistence for the intake flow are centralized here.
"""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.services.chat_message_service import ChatMessageService
from app.services.job_intake_service.workflows import (
    accept_achievement_update,
    accept_experience_update,
    accept_new_achievement,
    format_experiences_for_context,
    generate_resume_from_conversation,
    run_experience_chat,
    run_resume_chat,
    summarize_conversation,
)
from app.services.job_service import JobService
from app.services.resume_service import ResumeService
from src.features.resume.types import ResumeData
from src.logging_config import logger


class JobIntakeService:
    """Business logic for job intake workflow."""

    # ==================== Step 2: Experience Enhancement ====================

    @staticmethod
    def get_experience_chat_response(
        messages: list,
        job_description: str,
        experiences: list,
    ) -> AIMessage:
        """Get AI response with tool binding for experience enhancement.

        Args:
            messages: Chat message history.
            job_description: Job description text.
            experiences: List of user experiences.

        Returns:
            AIMessage with possible tool calls.
        """
        return run_experience_chat(messages, job_description, experiences)

    @staticmethod
    def format_experiences_for_context(experiences: list) -> str:
        """Format experiences for AI context.

        Args:
            experiences: List of Experience objects.

        Returns:
            Formatted string.
        """
        return format_experiences_for_context(experiences)

    @staticmethod
    def accept_experience_update(
        exp_id: int,
        company_overview: str | None,
        role_overview: str | None,
        skills: list[str] | None,
    ) -> tuple[bool, str]:
        """Accept and apply experience update proposal.

        Args:
            exp_id: Experience ID.
            company_overview: Company overview text.
            role_overview: Role overview text.
            skills: List of skills.

        Returns:
            Tuple of (success: bool, message: str).
        """
        return accept_experience_update(exp_id, company_overview, role_overview, skills)

    @staticmethod
    def accept_achievement_update(
        achievement_id: int,
        title: str,
        content: str,
    ) -> tuple[bool, str]:
        """Accept and apply achievement update proposal.

        Args:
            achievement_id: Achievement ID.
            title: Updated title.
            content: Updated content.

        Returns:
            Tuple of (success: bool, message: str).
        """
        return accept_achievement_update(achievement_id, title, content)

    @staticmethod
    def accept_new_achievement(
        exp_id: int,
        title: str,
        content: str,
        order: int | None,
    ) -> tuple[bool, str]:
        """Accept and apply new achievement proposal.

        Args:
            exp_id: Experience ID.
            title: Achievement title.
            content: Achievement content.
            order: Optional order.

        Returns:
            Tuple of (success: bool, message: str).
        """
        return accept_new_achievement(exp_id, title, content, order)

    @staticmethod
    def save_step2_messages(session_id: int, messages: list) -> None:
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

    @staticmethod
    def summarize_conversation(messages: list) -> str:
        """Summarize the Step 2 conversation.

        Args:
            messages: Chat message history.

        Returns:
            Summary string.
        """
        return summarize_conversation(messages)

    @staticmethod
    def complete_step2(
        session_id: int,
        job_id: int,
        messages: list,
    ) -> None:
        """Complete Step 2 and move to Step 3.

        Runs conversation summarization and updates session state.

        Args:
            session_id: Intake session ID.
            job_id: Job ID.
            messages: Chat message history.
        """
        try:
            # Run conversation summarization
            if messages:
                summary = JobIntakeService.summarize_conversation(messages)
                JobService.save_conversation_summary(session_id, summary)

            # Mark step 2 as completed and move to step 3
            JobService.update_session_step(session_id, step=3, completed=False)

        except Exception as exc:
            logger.exception("Error completing step 2: %s", exc)
            raise

    # ==================== Step 3: Resume Refinement ====================

    @staticmethod
    def generate_initial_resume(
        job_id: int,
        user_id: int,
        session_id: int,
    ) -> tuple[ResumeData, int]:
        """Generate initial resume from conversation context.

        Args:
            job_id: Job ID.
            user_id: User ID.
            session_id: Intake session ID.

        Returns:
            Tuple of (resume_data, version_id).

        Raises:
            Exception: If resume generation fails.
        """
        try:
            # Get session data
            session = JobService.get_intake_session(job_id)
            if not session:
                raise ValueError("Intake session not found")

            # Get chat messages from database and convert to LangChain messages
            messages_dict = ChatMessageService.get_messages_for_step(session.id, step=2)
            messages = _convert_dict_to_langchain_messages(messages_dict)

            # Generate resume using conversation context
            resume_data = generate_resume_from_conversation(
                job_id=job_id,
                user_id=user_id,
                messages=messages,
            )

            # Create first version
            version = ResumeService.create_version(
                job_id=job_id,
                resume_data=resume_data,
                template_name="resume_000.html",
                event_type="generate",
            )

            if not version.id:
                raise ValueError("Failed to create resume version")

            logger.info("Generated initial resume for intake", extra={"job_id": job_id, "version_id": version.id})
            return resume_data, version.id

        except Exception as exc:
            logger.exception("Failed to generate initial resume: %s", exc)
            raise

    @staticmethod
    def get_resume_chat_response(
        messages: list,
        job,
        selected_version,
    ) -> tuple[AIMessage, int | None]:
        """Get AI response for Step 3 resume refinement.

        Args:
            messages: Chat history.
            job: Job object.
            selected_version: Selected resume version.

        Returns:
            Tuple of (AIMessage response, new_version_id if tool was used, else None).
        """
        return run_resume_chat(messages, job, selected_version)

    @staticmethod
    def save_manual_resume_edit(
        job_id: int,
        current_version,
        updated_data: ResumeData,
    ) -> int:
        """Save manual edits from preview section as new resume version.

        Args:
            job_id: Job ID.
            current_version: Current resume version.
            updated_data: Updated resume data.

        Returns:
            New version ID.

        Raises:
            Exception: If save fails.
        """
        try:
            # Create new version
            new_version = ResumeService.create_version(
                job_id=job_id,
                resume_data=updated_data,
                template_name=current_version.template_name,
                event_type="save",
                parent_version_id=current_version.id,
            )

            if not new_version.id:
                raise ValueError("Failed to create new version")

            logger.info("Saved manual resume edit", extra={"job_id": job_id, "version_id": new_version.id})
            return new_version.id

        except Exception as exc:
            logger.exception("Failed to save changes: %s", exc)
            raise

    @staticmethod
    def complete_step3(
        session_id: int,
        job_id: int,
        pin_version_id: int | None,
    ) -> None:
        """Complete Step 3 and finalize intake session.

        Args:
            session_id: Intake session ID.
            job_id: Job ID.
            pin_version_id: Version ID to pin as canonical (None for skip).

        Raises:
            Exception: If completion fails.
        """
        try:
            if pin_version_id:
                # Pin the selected version
                ResumeService.pin_canonical(job_id, pin_version_id)

            # Mark session as completed
            JobService.complete_session(session_id)

            logger.info("Completed intake step 3", extra={"job_id": job_id, "pinned": pin_version_id is not None})

        except Exception as exc:
            logger.exception("Error completing step 3: %s", exc)
            raise


# ==================== Helper Functions ====================


def _convert_dict_to_langchain_messages(messages_dict: list[dict]) -> list:
    """Convert dict messages from database to LangChain message objects.

    Args:
        messages_dict: List of message dictionaries with 'type' and 'content'.

    Returns:
        List of LangChain BaseMessage objects.
    """
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    langchain_messages = []
    for msg in messages_dict:
        msg_type = msg.get("type")
        content = msg.get("content", "")

        if msg_type == "human":
            langchain_messages.append(HumanMessage(content=content))
        elif msg_type == "ai":
            ai_msg = AIMessage(content=content)
            # Restore tool_calls if present
            if "tool_calls" in msg:
                ai_msg.tool_calls = msg["tool_calls"]
            langchain_messages.append(ai_msg)
        elif msg_type == "tool":
            tool_call_id = msg.get("tool_call_id", "")
            langchain_messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))

    return langchain_messages
