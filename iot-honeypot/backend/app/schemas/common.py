"""Common DTOs used across endpoints."""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class HealthOut(BaseModel):
    status: str = "ok"
    version: str
    components: dict[str, str] = Field(default_factory=dict)


class ErrorOut(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int