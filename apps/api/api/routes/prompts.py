"""Prompt API routes for fetching system prompts."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from api.schemas.prompt import PromptResponse

router = APIRouter()

# Path to prompts directory
PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


def extract_system_prompt(prompt_data: dict) -> str:
    """Extract system prompt text from the prompt JSON structure.
    
    Args:
        prompt_data: The loaded JSON data from a prompt file
        
    Returns:
        The system prompt text
        
    Raises:
        ValueError: If the prompt structure is invalid
    """
    try:
        # Navigate the nested structure to find the system prompt template
        prompt_template = prompt_data["prompt_template"]
        first = prompt_template["kwargs"]["first"]
        messages = first["kwargs"]["messages"]
        system_message = messages[0]  # First message is the system message
        prompt = system_message["kwargs"]["prompt"]
        template = prompt["kwargs"]["template"]
        return template
    except (KeyError, IndexError, TypeError) as e:
        raise ValueError(f"Invalid prompt structure: {e}") from e


@router.get("/prompts/{prompt_name}", response_model=PromptResponse)
async def get_prompt(prompt_name: str) -> PromptResponse:
    """Get a system prompt by name.
    
    Args:
        prompt_name: Name of the prompt (gap_analysis, stakeholder_analysis, or resume_alignment_workflow)
        
    Returns:
        PromptResponse containing the system prompt text
        
    Raises:
        HTTPException: If prompt not found or invalid
    """
    # Validate prompt name
    valid_prompts = ["gap_analysis", "stakeholder_analysis", "resume_alignment_workflow"]
    if prompt_name not in valid_prompts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid prompt name. Must be one of: {', '.join(valid_prompts)}",
        )
    
    # Load prompt file
    prompt_file = PROMPTS_DIR / f"{prompt_name}.json"
    if not prompt_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt file not found: {prompt_name}",
        )
    
    try:
        with prompt_file.open() as f:
            prompt_data = json.load(f)
        
        # Extract the system prompt text
        system_prompt = extract_system_prompt(prompt_data)
        
        return PromptResponse(prompt=system_prompt)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load prompt: {str(e)}",
        ) from e

