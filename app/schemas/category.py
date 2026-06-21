"""Pydantic schemas for Category serialization."""

from pydantic import BaseModel, ConfigDict


class CategoryResponse(BaseModel):
    """Public-facing representation of a category."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    prompt_template: str
    is_active: bool


class CategoryCreate(BaseModel):
    """Schema for creating a new category."""

    name: str
    slug: str
    description: str | None = None
    topic: str