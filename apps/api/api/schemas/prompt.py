"""Pydantic schemas for Prompt request/response models."""

from pydantic import BaseModel, Field


class PromptResponse(BaseModel):
    """Schema for prompt response."""

    prompt: str = Field(..., description="The system prompt text")

