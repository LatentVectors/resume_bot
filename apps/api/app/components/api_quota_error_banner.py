"""Reusable API quota error banner component for OpenAI rate limit errors."""

from __future__ import annotations

import streamlit as st


def show_api_quota_error_banner() -> None:
    """Display a prominent error banner for OpenAI API quota exhaustion.

    Shows a big red error message with clear instructions on how to resolve
    the quota issue by adding funds to their OpenAI account.
    """
    st.error(
        """
        **:material/warning: API Quota Exceeded**

        You've exceeded your OpenAI API quota. To continue using AI-powered features:

        1. Visit [OpenAI Billing Settings](https://platform.openai.com/account/billing)
        2. Add credits to your account or upgrade your plan
        3. Wait a few minutes for the changes to take effect
        4. Try again

        For more information, see [OpenAI's billing documentation](https://platform.openai.com/docs/guides/error-codes/api-errors).
        """
    )
