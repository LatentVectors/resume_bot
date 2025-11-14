"""Pydantic schemas for Template models."""

from pydantic import BaseModel, Field


class TemplateListItem(BaseModel):
    """Schema for template list item."""

    name: str = Field(..., description="Template filename")
    display_name: str = Field(..., description="Human-readable template name")


class TemplateDetail(BaseModel):
    """Schema for template detail response."""

    name: str = Field(..., description="Template filename")
    display_name: str = Field(..., description="Human-readable template name")
    content: str = Field(..., description="Template HTML content")


class TemplateListResponse(BaseModel):
    """Schema for template list response."""

    templates: list[TemplateListItem] = Field(..., description="List of available templates")

