"""Service for managing chat message history in job intake flow."""

from __future__ import annotations

import json

from sqlmodel import select

from src.database import JobIntakeChatMessage as DbJobIntakeChatMessage
from src.database import db_manager
from src.logging_config import logger


class ChatMessageService:
    """Business logic for JobIntakeChatMessage persistence.

    Handles storage and retrieval of LangChain-formatted chat messages
    for the job intake flow (Steps 2 and 3).
    """

    @staticmethod
    def append_messages(session_id: int, step: int, messages_json: str) -> DbJobIntakeChatMessage:
        """Append messages to chat history for a step.

        Args:
            session_id: ID of the JobIntakeSession.
            step: Step number (2 or 3).
            messages_json: JSON-encoded string of message array.

        Returns:
            Persisted DbJobIntakeChatMessage instance.

        Raises:
            ValueError: If session_id is invalid or step is not 2 or 3.
            json.JSONDecodeError: If messages_json is not valid JSON.
        """
        if not isinstance(session_id, int) or session_id <= 0:
            raise ValueError("Invalid session_id")
        if step not in (2, 3):
            raise ValueError("step must be 2 or 3")
        if not messages_json or not messages_json.strip():
            raise ValueError("messages_json is required")

        # Validate that messages_json is valid JSON
        try:
            json.loads(messages_json)
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON in messages_json", exception=exc)
            raise

        try:
            with db_manager.get_session() as session:
                chat_message = DbJobIntakeChatMessage(
                    session_id=session_id,
                    step=step,
                    messages=messages_json,
                )
                session.add(chat_message)
                session.commit()
                session.refresh(chat_message)

                logger.info(
                    "Appended chat messages for session %s step %s (message_id: %s)",
                    session_id,
                    step,
                    chat_message.id,
                )
                return chat_message
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to append messages for session %s step %s: %s", session_id, step, exc)
            raise

    @staticmethod
    def get_messages_for_step(session_id: int, step: int) -> list[dict]:
        """Get all messages for a specific step.

        Args:
            session_id: ID of the JobIntakeSession.
            step: Step number (2 or 3).

        Returns:
            List of message dictionaries from all chat message records for this step,
            concatenated in chronological order. Returns empty list if no messages found.

        Raises:
            ValueError: If session_id is invalid or step is not 2 or 3.
        """
        if not isinstance(session_id, int) or session_id <= 0:
            raise ValueError("Invalid session_id")
        if step not in (2, 3):
            raise ValueError("step must be 2 or 3")

        try:
            with db_manager.get_session() as session:
                stmt = (
                    select(DbJobIntakeChatMessage)
                    .where(DbJobIntakeChatMessage.session_id == session_id)
                    .where(DbJobIntakeChatMessage.step == step)
                    .order_by(DbJobIntakeChatMessage.created_at.asc())
                )
                records = list(session.exec(stmt))

                # Concatenate all message arrays from records
                all_messages: list[dict] = []
                for record in records:
                    try:
                        messages = json.loads(record.messages)
                        if isinstance(messages, list):
                            all_messages.extend(messages)
                        else:
                            logger.warning(
                                "Expected list in messages JSON, got %s for record %s",
                                type(messages).__name__,
                                record.id,
                            )
                    except json.JSONDecodeError as exc:
                        logger.error(
                            "Failed to decode messages JSON for record %s: %s",
                            record.id,
                            exc,
                            exception=exc,
                        )
                        continue

                logger.info(
                    "Retrieved %d messages for session %s step %s from %d records",
                    len(all_messages),
                    session_id,
                    step,
                    len(records),
                )
                return all_messages
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to get messages for session %s step %s: %s", session_id, step, exc)
            return []

    @staticmethod
    def get_full_conversation(session_id: int) -> dict[int, list[dict]]:
        """Get complete conversation history grouped by step.

        Args:
            session_id: ID of the JobIntakeSession.

        Returns:
            Dictionary with step numbers (2 and/or 3) as keys and message lists as values.
            Returns empty dict if session has no messages.

        Raises:
            ValueError: If session_id is invalid.
        """
        if not isinstance(session_id, int) or session_id <= 0:
            raise ValueError("Invalid session_id")

        try:
            with db_manager.get_session() as session:
                stmt = (
                    select(DbJobIntakeChatMessage)
                    .where(DbJobIntakeChatMessage.session_id == session_id)
                    .order_by(DbJobIntakeChatMessage.step.asc(), DbJobIntakeChatMessage.created_at.asc())
                )
                records = list(session.exec(stmt))

                # Group messages by step
                conversation: dict[int, list[dict]] = {}
                for record in records:
                    try:
                        messages = json.loads(record.messages)
                        if isinstance(messages, list):
                            if record.step not in conversation:
                                conversation[record.step] = []
                            conversation[record.step].extend(messages)
                        else:
                            logger.warning(
                                "Expected list in messages JSON, got %s for record %s",
                                type(messages).__name__,
                                record.id,
                            )
                    except json.JSONDecodeError as exc:
                        logger.error(
                            "Failed to decode messages JSON for record %s: %s",
                            record.id,
                            exc,
                            exception=exc,
                        )
                        continue

                total_messages = sum(len(msgs) for msgs in conversation.values())
                logger.info(
                    "Retrieved full conversation for session %s: %d messages across %d steps",
                    session_id,
                    total_messages,
                    len(conversation),
                )
                return conversation
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to get full conversation for session %s: %s", session_id, exc)
            return {}

