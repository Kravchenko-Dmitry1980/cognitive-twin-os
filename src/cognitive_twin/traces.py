"""Operation trace domain models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TraceStatus(StrEnum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class OperationTrace(BaseModel):
    trace_id: str
    operation: str
    timestamp: datetime
    actor_id: str | None = None
    input_refs: list[str] = Field(default_factory=list)
    output_refs: list[str] = Field(default_factory=list)
    policy_result: dict[str, Any] | None = None
    status: TraceStatus
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
