"""Tests for ChatMessageService."""

from __future__ import annotations

import json
import os
import tempfile
from unittest import mock

import pytest

from app.services.chat_message_service import ChatMessageService
from src.database import DatabaseManager, Job, JobIntakeSession, User


@pytest.fixture
def test_db():
    """Create a temporary database for testing."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_url = f"sqlite:///{tmp.name}"
    tmp.close()

    db_manager = DatabaseManager(db_url)

    # Create user
    user = User(first_name="Test", last_name="User")
    user_id = db_manager.add_user(user)

    # Create job
    job = Job(
        user_id=user_id,
        job_description="Test job",
        company_name="Test Co",
        job_title="Test Role",
        status="Saved",
    )
    job_id = db_manager.add_job(job)

    # Create intake session
    with db_manager.get_session() as session:
        intake_session = JobIntakeSession(
            job_id=job_id,
            current_step=2,
            step1_completed=True,
        )
        session.add(intake_session)
        session.commit()
        session.refresh(intake_session)
        session_id = intake_session.id

    yield db_manager, session_id, tmp.name

    # Cleanup
    os.unlink(tmp.name)


class TestChatMessageService:
    """Test cases for ChatMessageService."""

    def test_append_messages_basic(self, test_db):
        """Test basic message appending."""
        db_manager, session_id, db_path = test_db

        with mock.patch("app.services.chat_message_service.db_manager", db_manager):
            # Test LangChain-style message format
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"},
                {"role": "assistant", "content": "Hi there!"},
            ]
            messages_json = json.dumps(messages)

            chat_message = ChatMessageService.append_messages(session_id, 2, messages_json)

            assert chat_message.id is not None
            assert chat_message.session_id == session_id
            assert chat_message.step == 2
            assert chat_message.messages == messages_json
            assert chat_message.created_at is not None

    def test_append_messages_various_formats(self, test_db):
        """Test message persistence with various LangChain message formats."""
        db_manager, session_id, db_path = test_db

        with mock.patch("app.services.chat_message_service.db_manager", db_manager):
            # Format 1: Simple role/content
            format1 = [{"role": "user", "content": "Test message"}]
            ChatMessageService.append_messages(session_id, 2, json.dumps(format1))

            # Format 2: With additional fields (tool calls, function calls, etc.)
            format2 = [
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "type": "function",
                            "function": {"name": "propose_experience_update", "arguments": '{"field": "value"}'},
                        }
                    ],
                }
            ]
            ChatMessageService.append_messages(session_id, 2, json.dumps(format2))

            # Format 3: With metadata
            format3 = [
                {
                    "role": "user",
                    "content": "Complex message",
                    "metadata": {"timestamp": "2024-01-01", "user_id": 123},
                }
            ]
            ChatMessageService.append_messages(session_id, 3, json.dumps(format3))

            # Verify all were saved
            messages_step2 = ChatMessageService.get_messages_for_step(session_id, 2)
            messages_step3 = ChatMessageService.get_messages_for_step(session_id, 3)

            assert len(messages_step2) == 2  # format1 + format2
            assert len(messages_step3) == 1  # format3

    def test_get_messages_for_step(self, test_db):
        """Test retrieving messages for a specific step."""
        db_manager, session_id, db_path = test_db

        with mock.patch("app.services.chat_message_service.db_manager", db_manager):
            # Add messages to step 2
            messages1 = [{"role": "user", "content": "First batch"}]
            messages2 = [{"role": "assistant", "content": "Response"}]
            messages3 = [{"role": "user", "content": "Second batch"}]

            ChatMessageService.append_messages(session_id, 2, json.dumps(messages1))
            ChatMessageService.append_messages(session_id, 2, json.dumps(messages2))
            ChatMessageService.append_messages(session_id, 2, json.dumps(messages3))

            # Add messages to step 3 (should not be retrieved)
            messages_step3 = [{"role": "user", "content": "Step 3 message"}]
            ChatMessageService.append_messages(session_id, 3, json.dumps(messages_step3))

            # Retrieve step 2 messages
            retrieved = ChatMessageService.get_messages_for_step(session_id, 2)

            assert len(retrieved) == 3
            assert retrieved[0]["content"] == "First batch"
            assert retrieved[1]["content"] == "Response"
            assert retrieved[2]["content"] == "Second batch"

            # Verify step 3 messages separate
            step3_messages = ChatMessageService.get_messages_for_step(session_id, 3)
            assert len(step3_messages) == 1
            assert step3_messages[0]["content"] == "Step 3 message"

    def test_get_full_conversation(self, test_db):
        """Test retrieving full conversation grouped by step."""
        db_manager, session_id, db_path = test_db

        with mock.patch("app.services.chat_message_service.db_manager", db_manager):
            # Add messages to step 2
            step2_msg1 = [{"role": "system", "content": "System message"}]
            step2_msg2 = [{"role": "user", "content": "User question"}]
            ChatMessageService.append_messages(session_id, 2, json.dumps(step2_msg1))
            ChatMessageService.append_messages(session_id, 2, json.dumps(step2_msg2))

            # Add messages to step 3
            step3_msg1 = [{"role": "assistant", "content": "Assistant response"}]
            step3_msg2 = [{"role": "user", "content": "Follow-up"}]
            ChatMessageService.append_messages(session_id, 3, json.dumps(step3_msg1))
            ChatMessageService.append_messages(session_id, 3, json.dumps(step3_msg2))

            # Retrieve full conversation
            conversation = ChatMessageService.get_full_conversation(session_id)

            assert len(conversation) == 2
            assert 2 in conversation
            assert 3 in conversation
            assert len(conversation[2]) == 2
            assert len(conversation[3]) == 2
            assert conversation[2][0]["content"] == "System message"
            assert conversation[3][1]["content"] == "Follow-up"

    def test_empty_results(self, test_db):
        """Test empty results when no messages exist."""
        db_manager, session_id, db_path = test_db

        with mock.patch("app.services.chat_message_service.db_manager", db_manager):
            # Get messages for step with no messages
            messages = ChatMessageService.get_messages_for_step(session_id, 2)
            assert messages == []

            # Get full conversation for session with no messages
            conversation = ChatMessageService.get_full_conversation(session_id)
            assert conversation == {}

    def test_invalid_session_id(self):
        """Test validation of session_id."""
        with pytest.raises(ValueError, match="Invalid session_id"):
            ChatMessageService.append_messages(0, 2, json.dumps([]))

        with pytest.raises(ValueError, match="Invalid session_id"):
            ChatMessageService.append_messages(-1, 2, json.dumps([]))

        with pytest.raises(ValueError, match="Invalid session_id"):
            ChatMessageService.get_messages_for_step(0, 2)

        with pytest.raises(ValueError, match="Invalid session_id"):
            ChatMessageService.get_full_conversation(-5)

    def test_invalid_step(self, test_db):
        """Test validation of step parameter."""
        db_manager, session_id, db_path = test_db

        with pytest.raises(ValueError, match="step must be 2 or 3"):
            ChatMessageService.append_messages(session_id, 1, json.dumps([]))

        with pytest.raises(ValueError, match="step must be 2 or 3"):
            ChatMessageService.append_messages(session_id, 4, json.dumps([]))

        with pytest.raises(ValueError, match="step must be 2 or 3"):
            ChatMessageService.get_messages_for_step(session_id, 0)

    def test_invalid_json(self, test_db):
        """Test handling of invalid JSON."""
        db_manager, session_id, db_path = test_db

        with pytest.raises(json.JSONDecodeError):
            ChatMessageService.append_messages(session_id, 2, "not valid json")

        with pytest.raises(json.JSONDecodeError):
            ChatMessageService.append_messages(session_id, 2, "{incomplete")

    def test_empty_messages_json(self, test_db):
        """Test validation of empty messages_json."""
        db_manager, session_id, db_path = test_db

        with pytest.raises(ValueError, match="messages_json is required"):
            ChatMessageService.append_messages(session_id, 2, "")

        with pytest.raises(ValueError, match="messages_json is required"):
            ChatMessageService.append_messages(session_id, 2, "   ")

    def test_json_round_trip(self, test_db):
        """Test JSON serialization and deserialization round-trip."""
        db_manager, session_id, db_path = test_db

        with mock.patch("app.services.chat_message_service.db_manager", db_manager):
            # Complex nested message structure
            original_messages = [
                {
                    "role": "assistant",
                    "content": "Here's a proposal",
                    "tool_calls": [
                        {
                            "id": "call_abc123",
                            "type": "function",
                            "function": {
                                "name": "propose_achievement_update",
                                "arguments": json.dumps(
                                    {
                                        "achievement_id": 42,
                                        "content": "Led team of 5 engineers to deliver project 2 weeks ahead of schedule",
                                        "metrics": ["5 engineers", "2 weeks early"],
                                    }
                                ),
                            },
                        }
                    ],
                    "metadata": {"timestamp": "2024-10-09T12:00:00Z", "confidence": 0.95},
                }
            ]

            messages_json = json.dumps(original_messages)
            ChatMessageService.append_messages(session_id, 2, messages_json)

            # Retrieve and verify
            retrieved_messages = ChatMessageService.get_messages_for_step(session_id, 2)

            assert len(retrieved_messages) == 1
            assert retrieved_messages[0] == original_messages[0]
            assert retrieved_messages[0]["tool_calls"][0]["function"]["name"] == "propose_achievement_update"

            # Verify nested JSON arguments can be parsed
            args_json = retrieved_messages[0]["tool_calls"][0]["function"]["arguments"]
            args = json.loads(args_json)
            assert args["achievement_id"] == 42
            assert len(args["metrics"]) == 2

    def test_chronological_ordering(self, test_db):
        """Test that messages are returned in chronological order."""
        db_manager, session_id, db_path = test_db

        with mock.patch("app.services.chat_message_service.db_manager", db_manager):
            # Add messages with slight delays to ensure different timestamps
            import time

            msg1 = [{"role": "user", "content": "First"}]
            ChatMessageService.append_messages(session_id, 2, json.dumps(msg1))

            time.sleep(0.01)  # Small delay to ensure different timestamp

            msg2 = [{"role": "assistant", "content": "Second"}]
            ChatMessageService.append_messages(session_id, 2, json.dumps(msg2))

            time.sleep(0.01)

            msg3 = [{"role": "user", "content": "Third"}]
            ChatMessageService.append_messages(session_id, 2, json.dumps(msg3))

            # Retrieve and verify order
            messages = ChatMessageService.get_messages_for_step(session_id, 2)

            assert len(messages) == 3
            assert messages[0]["content"] == "First"
            assert messages[1]["content"] == "Second"
            assert messages[2]["content"] == "Third"
