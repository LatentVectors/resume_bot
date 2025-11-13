from __future__ import annotations

import asyncio

import streamlit as st

from app.api_client.endpoints.messages import MessagesAPI
from api.schemas.job import JobResponse
from api.schemas.message import MessageResponse
from src.logging_config import logger


def render_messages(job: JobResponse) -> None:
    """Render the Messages tab with messages for the job."""
    st.subheader("Messages")

    try:
        messages: list[MessageResponse] = asyncio.run(MessagesAPI.list_messages(job.id))
    except Exception as e:  # noqa: BLE001
        st.error("Failed to load messages. Please try again later.")
        logger.error(f"Error listing messages: {e}")
        return

    if not messages:
        st.info("No messages yet for this job.")
        return

    # Display messages
    for msg in messages:
        with st.container(border=True):
            col1, col2 = st.columns([1, 4])
            with col1:
                st.write(f"**{msg.channel.value if hasattr(msg.channel, 'value') else str(msg.channel)}**")
                if msg.created_at:
                    st.caption(msg.created_at.strftime("%Y-%m-%d %H:%M:%S"))
            with col2:
                st.write(msg.body)
