"""Business logic for job intake workflow.

This service handles the multi-step intake process including:
- Step 2: Experience & Resume Development (unified conversation)

All AI interactions and data persistence for the intake flow are centralized here.
"""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from api.services.chat_message_service import ChatMessageService
from api.services.experience_service import ExperienceService
from api.services.job_intake_service.workflows import extract_experience_updates, run_resume_chat
from api.services.job_service import JobService
from api.services.resume_service import ResumeService
from src.database import (
    AchievementAdd,
    AchievementDelete,
    AchievementUpdate,
    CompanyOverviewUpdate,
    ExperienceProposal,
    ProposalContent,
    ProposalStatus,
    ProposalType,
    RoleOverviewUpdate,
    SkillAdd,
    SkillDelete,
    db_manager,
)
from src.features.resume.types import ResumeData
from src.logging_config import logger
from src.shared.formatters import format_all_experiences


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
    def get_resume_chat_response(
        messages: list,
        job,
        selected_version,
        gap_analysis: str,
        stakeholder_analysis: str,
        user_id: int,
    ) -> tuple[AIMessage, int | None]:
        """Get AI response for Step 2 unified conversation (experience & resume).

        Args:
            messages: Chat history.
            job: Job object.
            selected_version: Selected resume version.
            gap_analysis: Gap analysis markdown from job intake session.
            stakeholder_analysis: Stakeholder analysis markdown from job intake session.
            user_id: User ID for fetching experiences.

        Returns:
            Tuple of (AIMessage response, new_version_id if tool was used, else None).

        Raises:
            ValueError: If gap_analysis or stakeholder_analysis are missing.
            OpenAIQuotaExceededError: If OpenAI API quota is exceeded.
        """
        # Validate required analyses are present
        if not gap_analysis:
            error_msg = "Gap analysis missing. Please restart the intake flow."
            logger.error(error_msg)
            return AIMessage(content=error_msg), None

        if not stakeholder_analysis:
            error_msg = "Stakeholder analysis missing. Please restart the intake flow."
            logger.error(error_msg)
            return AIMessage(content=error_msg), None

        # Get and format user's work experience
        try:
            experiences = ExperienceService.list_user_experiences(user_id)

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
            gap_analysis=gap_analysis,
            stakeholder_analysis=stakeholder_analysis,
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

    # ==================== Step 3: Experience Updates ====================

    @staticmethod
    def extract_experience_proposals(session_id: int, job_id: int, user_id: int) -> list[ExperienceProposal]:
        """Extract experience proposals from Step 2 conversation.

        Calls the extraction workflow which returns a Pydantic model with structured output,
        then creates ExperienceProposal database records from the workflow output.

        **DEVELOPMENT MODE**: Returns in-memory proposal objects only. Does NOT persist to database.

        Args:
            session_id: Intake session ID.
            job_id: Job ID (used to get experiences).
            user_id: User ID for fetching experiences.

        Returns:
            List of created proposal records (in-memory only, not persisted).

        Raises:
            ValueError: If session or job not found.
            OpenAIQuotaExceededError: If OpenAI API quota is exceeded.
        """
        try:
            # Get session and job
            session = JobService.get_intake_session(job_id)
            if not session:
                raise ValueError(f"Intake session not found for job {job_id}")

            job = JobService.get_job(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            # Get Step 2 chat messages
            messages_dict = ChatMessageService.get_messages_for_step(session_id, step=2)
            if not messages_dict:
                logger.warning("No Step 2 messages found for session %s", session_id)
                return []

            # Convert dict messages to LangChain message objects
            chat_messages: list[HumanMessage | AIMessage] = []
            for msg_dict in messages_dict:
                if msg_dict.get("type") == "human":
                    chat_messages.append(HumanMessage(content=msg_dict.get("content", "")))
                elif msg_dict.get("type") == "ai":
                    chat_messages.append(AIMessage(content=msg_dict.get("content", "")))
                # Skip tool messages for extraction

            # Get all user experiences
            experiences = ExperienceService.list_user_experiences(user_id)
            if not experiences:
                logger.info("No experiences found for user %s", user_id)
                return []

            # Call extraction workflow
            suggestions = extract_experience_updates(chat_messages, experiences)

            # Convert Pydantic model output to ExperienceProposal records
            proposals: list[ExperienceProposal] = []

            # Process role overview updates
            for role_update in suggestions.role_overviews:
                proposal = ExperienceProposal(
                    session_id=session_id,
                    proposal_type=ProposalType.role_overview_update,
                    experience_id=role_update.experience_id,
                    achievement_id=None,
                    proposed_content=ExperienceProposal.serialize_proposed_content(role_update),
                    original_proposed_content=ExperienceProposal.serialize_proposed_content(role_update),
                    status=ProposalStatus.pending,
                )
                proposals.append(proposal)

            # Process company overview updates
            for company_update in suggestions.company_overviews:
                proposal = ExperienceProposal(
                    session_id=session_id,
                    proposal_type=ProposalType.company_overview_update,
                    experience_id=company_update.experience_id,
                    achievement_id=None,
                    proposed_content=ExperienceProposal.serialize_proposed_content(company_update),
                    original_proposed_content=ExperienceProposal.serialize_proposed_content(company_update),
                    status=ProposalStatus.pending,
                )
                proposals.append(proposal)

            # Process skill additions
            for skill_add in suggestions.skills:
                proposal = ExperienceProposal(
                    session_id=session_id,
                    proposal_type=ProposalType.skill_add,
                    experience_id=skill_add.experience_id,
                    achievement_id=None,
                    proposed_content=ExperienceProposal.serialize_proposed_content(skill_add),
                    original_proposed_content=ExperienceProposal.serialize_proposed_content(skill_add),
                    status=ProposalStatus.pending,
                )
                proposals.append(proposal)

            # Process achievement additions and updates
            for achievement in suggestions.achievements:
                if isinstance(achievement, AchievementAdd):
                    proposal = ExperienceProposal(
                        session_id=session_id,
                        proposal_type=ProposalType.achievement_add,
                        experience_id=achievement.experience_id,
                        achievement_id=None,
                        proposed_content=ExperienceProposal.serialize_proposed_content(achievement),
                        original_proposed_content=ExperienceProposal.serialize_proposed_content(achievement),
                        status=ProposalStatus.pending,
                    )
                    proposals.append(proposal)
                elif isinstance(achievement, AchievementUpdate):
                    proposal = ExperienceProposal(
                        session_id=session_id,
                        proposal_type=ProposalType.achievement_update,
                        experience_id=achievement.experience_id,
                        achievement_id=achievement.achievement_id,
                        proposed_content=ExperienceProposal.serialize_proposed_content(achievement),
                        original_proposed_content=ExperienceProposal.serialize_proposed_content(achievement),
                        status=ProposalStatus.pending,
                    )
                    proposals.append(proposal)

            logger.info(
                "Extracted %d experience proposals for session %s",
                len(proposals),
                session_id,
                extra={"session_id": session_id, "proposal_count": len(proposals)},
            )

            # **DEVELOPMENT MODE**: Return in-memory objects only, do NOT persist
            return proposals

        except Exception as exc:
            logger.exception("Error extracting experience proposals: %s", exc)
            raise

    @staticmethod
    def get_pending_proposals(session_id: int) -> list[ExperienceProposal]:
        """Retrieve all pending proposals for a session.

        Args:
            session_id: Intake session ID.

        Returns:
            List of pending ExperienceProposal records.
        """
        try:
            all_proposals = db_manager.list_session_proposals(session_id)
            return [p for p in all_proposals if p.status == ProposalStatus.pending]
        except Exception as exc:
            logger.exception("Error getting pending proposals for session %s: %s", session_id, exc)
            return []

    @staticmethod
    def update_proposal_content(proposal_id: int, new_content: ProposalContent) -> ExperienceProposal:
        """Update proposal with user edits.

        **DEVELOPMENT MODE**: Validates input only, does NOT execute database updates.

        Args:
            proposal_id: ID of the proposal to update.
            new_content: New content Pydantic model to store in proposed_content field.

        Returns:
            Updated ExperienceProposal object (in-memory only, not persisted).

        Raises:
            ValueError: If proposal not found or content is invalid.
        """
        try:
            # Read-only: Get proposal to validate it exists
            proposal = db_manager.get_experience_proposal(proposal_id)
            if not proposal:
                raise ValueError(f"Proposal {proposal_id} not found")

            # Validate new_content is a ProposalContent model
            # Note: SkillDelete and AchievementDelete are valid types but typically not editable in UI
            if not isinstance(
                new_content,
                (
                    RoleOverviewUpdate,
                    CompanyOverviewUpdate,
                    SkillAdd,
                    SkillDelete,
                    AchievementAdd,
                    AchievementUpdate,
                    AchievementDelete,
                ),
            ):
                raise ValueError("new_content must be a ProposalContent Pydantic model")

            # **DEVELOPMENT MODE**: Create updated object in-memory only
            updated_proposal = ExperienceProposal(
                id=proposal.id,
                session_id=proposal.session_id,
                proposal_type=proposal.proposal_type,
                experience_id=proposal.experience_id,
                achievement_id=proposal.achievement_id,
                proposed_content=ExperienceProposal.serialize_proposed_content(new_content),
                original_proposed_content=proposal.original_proposed_content,
                status=proposal.status,
                created_at=proposal.created_at,
                updated_at=proposal.updated_at,
            )

            logger.info("Validated proposal content update for proposal %s", proposal_id)
            return updated_proposal

        except Exception as exc:
            logger.exception("Error updating proposal content for proposal %s: %s", proposal_id, exc)
            raise

    @staticmethod
    def revert_proposal_to_original(proposal_id: int) -> ExperienceProposal:
        """Revert edited proposal back to original AI-generated content.

        **DEVELOPMENT MODE**: Validates input only, does NOT execute database updates.

        Args:
            proposal_id: ID of the proposal to revert.

        Returns:
            Reverted ExperienceProposal object (in-memory only, not persisted).

        Raises:
            ValueError: If proposal not found or original content is invalid.
        """
        try:
            # Read-only: Get proposal to validate it exists
            proposal = db_manager.get_experience_proposal(proposal_id)
            if not proposal:
                raise ValueError(f"Proposal {proposal_id} not found")

            # Validate original content can be parsed (ensures it's valid)
            try:
                proposal.parse_original_proposed_content()
            except ValueError as exc:
                raise ValueError(f"Invalid original_proposed_content: {exc}") from exc

            # **DEVELOPMENT MODE**: Create reverted object in-memory only
            reverted_proposal = ExperienceProposal(
                id=proposal.id,
                session_id=proposal.session_id,
                proposal_type=proposal.proposal_type,
                experience_id=proposal.experience_id,
                achievement_id=proposal.achievement_id,
                proposed_content=proposal.original_proposed_content,  # Revert to original
                original_proposed_content=proposal.original_proposed_content,
                status=proposal.status,
                created_at=proposal.created_at,
                updated_at=proposal.updated_at,
            )

            logger.info("Validated proposal revert for proposal %s", proposal_id)
            return reverted_proposal

        except Exception as exc:
            logger.exception("Error reverting proposal %s: %s", proposal_id, exc)
            raise

    @staticmethod
    def accept_proposal(proposal_id: int) -> bool:
        """Apply proposal to actual Experience/Achievement records.

        Handles all proposal types: skills add/delete, achievement add/update/delete, overview updates.

        **DEVELOPMENT MODE**: Validates logic only, does NOT execute database modifications.

        Args:
            proposal_id: ID of the proposal to accept.

        Returns:
            True if validation succeeds, False otherwise.

        Raises:
            ValueError: If proposal not found or validation fails.
        """
        try:
            # Read-only: Get proposal to validate it exists
            proposal = db_manager.get_experience_proposal(proposal_id)
            if not proposal:
                logger.warning(
                    "Proposal not found for acceptance",
                    extra={"proposal_id": proposal_id},
                )
                raise ValueError(f"Proposal {proposal_id} not found")

            # Parse proposed content to typed model
            try:
                proposal_content = proposal.parse_proposed_content()
            except ValueError as exc:
                logger.warning(
                    "Invalid proposal content",
                    extra={"proposal_id": proposal_id, "error": str(exc)},
                )
                raise ValueError(f"Invalid proposal content: {exc}") from exc

            # Validate experience exists (read-only check)
            experience = db_manager.get_experience(proposal.experience_id)
            if not experience:
                logger.warning(
                    "Experience not found for proposal",
                    extra={"proposal_id": proposal_id, "experience_id": proposal.experience_id},
                )
                raise ValueError(f"Experience {proposal.experience_id} not found")

            # Validate proposal type and content structure using typed models
            if proposal.proposal_type == ProposalType.skill_add:
                if not isinstance(proposal_content, SkillAdd):
                    raise ValueError("Proposal content does not match skill_add type")
                if not proposal_content.skills:
                    raise ValueError("'skills' list cannot be empty")
                # Validate each skill is a non-empty string
                for skill in proposal_content.skills:
                    if not isinstance(skill, str) or not skill.strip():
                        raise ValueError("All skills must be non-empty strings")

            elif proposal.proposal_type == ProposalType.achievement_add:
                if not isinstance(proposal_content, AchievementAdd):
                    raise ValueError("Proposal content does not match achievement_add type")
                if not proposal_content.title.strip():
                    raise ValueError("Achievement title must be a non-empty string")

            elif proposal.proposal_type == ProposalType.achievement_update:
                if not isinstance(proposal_content, AchievementUpdate):
                    raise ValueError("Proposal content does not match achievement_update type")
                # Validate achievement exists (read-only check)
                achievement = db_manager.get_achievement(proposal_content.achievement_id)
                if not achievement:
                    logger.warning(
                        "Achievement not found for proposal",
                        extra={
                            "proposal_id": proposal_id,
                            "achievement_id": proposal_content.achievement_id,
                        },
                    )
                    raise ValueError(f"Achievement {proposal_content.achievement_id} not found")
                if achievement.experience_id != proposal.experience_id:
                    raise ValueError("Achievement does not belong to the proposal's experience")

            elif proposal.proposal_type in (
                ProposalType.role_overview_update,
                ProposalType.company_overview_update,
            ):
                if not isinstance(proposal_content, (RoleOverviewUpdate, CompanyOverviewUpdate)):
                    raise ValueError("Proposal content does not match overview update type")

            # **DEVELOPMENT MODE**: Log validation success, do NOT execute database modifications
            logger.info(
                "Validated proposal acceptance logic for proposal %s (type: %s)",
                proposal_id,
                proposal.proposal_type.value,
                extra={
                    "proposal_id": proposal_id,
                    "proposal_type": proposal.proposal_type.value,
                    "experience_id": proposal.experience_id,
                },
            )
            return True

        except ValueError:
            # Re-raise validation errors as-is
            raise
        except Exception as exc:
            logger.exception(
                "Unexpected error validating proposal acceptance",
                extra={
                    "proposal_id": proposal_id,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
            raise ValueError(f"Error validating proposal: {str(exc)}") from exc

    @staticmethod
    def reject_proposal(proposal_id: int) -> bool:
        """Mark proposal as rejected.

        **DEVELOPMENT MODE**: Validates input only, does NOT execute database updates.

        Args:
            proposal_id: ID of the proposal to reject.

        Returns:
            True if validation succeeds, False otherwise.

        Raises:
            ValueError: If proposal not found.
        """
        try:
            # Read-only: Get proposal to validate it exists
            proposal = db_manager.get_experience_proposal(proposal_id)
            if not proposal:
                raise ValueError(f"Proposal {proposal_id} not found")

            # **DEVELOPMENT MODE**: Log validation success, do NOT execute database updates
            logger.info("Validated proposal rejection for proposal %s", proposal_id)
            return True

        except Exception as exc:
            logger.exception("Error rejecting proposal %s: %s", proposal_id, exc)
            raise

