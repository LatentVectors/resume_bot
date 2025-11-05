"""Business logic for job intake workflow.

This service handles the multi-step intake process including:
- Step 2: Experience & Resume Development (unified conversation)

All AI interactions and data persistence for the intake flow are centralized here.
"""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.services.chat_message_service import ChatMessageService
from app.services.experience_service import ExperienceService
from app.services.job_intake_service.workflows import (
    generate_resume_from_conversation,
    run_resume_chat,
)
from app.services.job_service import JobService
from app.services.resume_service import ResumeService
from app.shared.formatters import format_all_experiences
from src.database import db_manager
from src.features.resume.types import ResumeData
from src.logging_config import logger


class JobIntakeService:
    """Business logic for job intake workflow."""

    # ==================== Step 2: Experience & Resume Development ====================

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
        """Get AI response for Step 2 unified conversation (experience & resume).

        Args:
            messages: Chat history.
            job: Job object.
            selected_version: Selected resume version.

        Returns:
            Tuple of (AIMessage response, new_version_id if tool was used, else None).

        Raises:
            ValueError: If gap_analysis or stakeholder_analysis are missing from session.
        """
        # Get intake session to retrieve analyses
        session = JobService.get_intake_session(job.id)
        if not session:
            error_msg = "Intake session not found. Cannot proceed with resume chat."
            logger.error(error_msg)
            return AIMessage(content=error_msg), None

        # Validate required analyses are present
        if not session.gap_analysis:
            error_msg = "Gap analysis missing. Please restart the intake flow."
            logger.error(error_msg)
            return AIMessage(content=error_msg), None

        if not session.stakeholder_analysis:
            error_msg = "Stakeholder analysis missing. Please restart the intake flow."
            logger.error(error_msg)
            return AIMessage(content=error_msg), None

        # Get and format user's work experience
        try:
            experiences = ExperienceService.list_user_experiences(job.user_id)

            # Build achievements dict for formatting
            achievements_by_exp: dict[int, list] = {}
            for exp in experiences:
                achievements = db_manager.list_experience_achievements(exp.id)
                achievements_by_exp[exp.id] = achievements

            # Format all experiences with their achievements
            work_experience = format_all_experiences(experiences, achievements_by_exp)

        except Exception as exc:
            logger.exception("Error formatting work experience: %s", exc)
            work_experience = "No work experience available."

        # Call resume chat with all required context
        return run_resume_chat(
            messages=messages,
            job=job,
            selected_version=selected_version,
            gap_analysis=session.gap_analysis,
            stakeholder_analysis=session.stakeholder_analysis,
            work_experience=work_experience,
        )

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
    def complete_step2_final(
        session_id: int,
        job_id: int,
        pin_version_id: int | None,
    ) -> None:
        """Complete Step 2 and finalize intake session.

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

            logger.info("Completed intake step 2", extra={"job_id": job_id, "pinned": pin_version_id is not None})

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
