"""Shared utilities for all agents."""

from __future__ import annotations

from .formatters import format_all_experiences, format_experience_with_achievements
from .llm import get_openrouter_model
from .model_names import ModelName
from .models import (
    AchievementAdd,
    AchievementUpdate,
    CompanyOverviewUpdate,
    ProposedExperience,
    RoleOverviewUpdate,
    SkillAdd,
    TitleCompany,
    WorkExperienceEnhancementSuggestions,
)
from .prompts import PROMPTS_DIR, PromptName, load_prompt

__all__ = [
    # LLM utilities
    "get_openrouter_model",
    "ModelName",
    # Prompt utilities
    "load_prompt",
    "PromptName",
    "PROMPTS_DIR",
    # Formatting utilities
    "format_experience_with_achievements",
    "format_all_experiences",
    # Pydantic models
    "TitleCompany",
    "ProposedExperience",
    "RoleOverviewUpdate",
    "CompanyOverviewUpdate",
    "SkillAdd",
    "AchievementAdd",
    "AchievementUpdate",
    "WorkExperienceEnhancementSuggestions",
]
