"""Policy contract models (request/response placeholders)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from cognitive_twin.events import Governance, Sensitivity


class PolicyRequest(BaseModel):
    """Request to evaluate governance policy for an action or resource."""

    request_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    proposed_sensitivity: Sensitivity | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class PolicyDecision(BaseModel):
    allowed: bool
    reason: str
    governance: Governance | None = None
    constraints: list[str] = Field(default_factory=list)


class PolicyResponse(BaseModel):
    request_id: str
    decision: PolicyDecision
