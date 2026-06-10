"""Episode domain models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class MemoryState(StrEnum):
    RAW = "raw"
    CURATED = "curated"
    CONSOLIDATED = "consolidated"
    ARCHIVED = "archived"
    INVALIDATED = "invalidated"


class Episode(BaseModel):
    episode_id: str
    event_ids: list[str] = Field(min_length=1)
    episode_type: str
    summary: str
    salience: float = Field(ge=0.0, le=1.0)
    entities: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    outcome: str | None = None
    memory_state: MemoryState
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
