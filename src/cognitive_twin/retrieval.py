"""Structured episode retrieval filters — no semantic search."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from cognitive_twin.episodes import Episode, MemoryState
from cognitive_twin.events import Sensitivity
from cognitive_twin.policy_engine import EpisodePolicyEvaluation, PolicyDecisionValue
from cognitive_twin.store import EpisodeRepository

DEFAULT_RETRIEVAL_LIMIT = 50
MAX_RETRIEVAL_LIMIT = 100


class RetrievalFilter(BaseModel):
    """Explicit structured filters only — no embeddings or ranking models."""

    episode_type: str | None = None
    memory_state: MemoryState | None = None
    min_salience: float | None = Field(default=None, ge=0.0, le=1.0)
    entity: str | None = None
    goal: str | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None


class RetrievalPolicyScope(BaseModel):
    """Policy constraints applied before returning retrieval results."""

    actor_id: str | None = None
    purpose: str | None = None
    allowed_sensitivities: list[Sensitivity] | None = None
    allow_imported: bool = False
    include_policy_decisions: bool = True


class RetrievalRequest(BaseModel):
    """Structured retrieval request boundary for the local runtime."""

    request_id: str = Field(min_length=1)
    filters: RetrievalFilter = Field(default_factory=RetrievalFilter)
    actor_id: str | None = None
    limit: int = DEFAULT_RETRIEVAL_LIMIT
    offset: int = 0
    policy: RetrievalPolicyScope | None = None

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, value: int) -> int:
        if value < 1:
            msg = "limit must be positive"
            raise ValueError(msg)
        if value > MAX_RETRIEVAL_LIMIT:
            msg = f"limit must not exceed {MAX_RETRIEVAL_LIMIT}"
            raise ValueError(msg)
        return value

    @field_validator("offset")
    @classmethod
    def validate_offset(cls, value: int) -> int:
        if value < 0:
            msg = "offset must be >= 0"
            raise ValueError(msg)
        return value


class RetrievalResult(BaseModel):
    """Deprecated internal shape — not a release-facing retrieval response."""

    request_id: str = Field(min_length=1)
    episode_ids: list[str] = Field(default_factory=list)
    episodes: list[Episode] = Field(default_factory=list)


class RetrievalItem(BaseModel):
    """Allowed episode returned after policy filtering."""

    episode_id: str
    episode: Episode
    policy_result: PolicyDecisionValue


class RetrievalResponse(BaseModel):
    """Policy-aware retrieval response with pagination metadata."""

    request_id: str = Field(min_length=1)
    items: list[RetrievalItem] = Field(default_factory=list)
    total_candidates: int = 0
    total_allowed: int = 0
    total_denied: int = 0
    returned_count: int = 0
    offset: int = 0
    limit: int = DEFAULT_RETRIEVAL_LIMIT
    policy_decisions: list[EpisodePolicyEvaluation] | None = None
    trace_id: str | None = None


def _matches_filter(episode: Episode, filters: RetrievalFilter) -> bool:
    if filters.episode_type is not None and episode.episode_type != filters.episode_type:
        return False
    if filters.memory_state is not None and episode.memory_state != filters.memory_state:
        return False
    if filters.min_salience is not None and episode.salience < filters.min_salience:
        return False
    if filters.entity is not None and filters.entity not in episode.entities:
        return False
    if filters.goal is not None and filters.goal not in episode.goals:
        return False
    if filters.created_after is not None and episode.created_at < filters.created_after:
        return False
    if filters.created_before is not None and episode.created_at > filters.created_before:
        return False
    return True


def filter_episodes(
    store: EpisodeRepository,
    filters: RetrievalFilter,
) -> list[Episode]:
    """
    Internal candidate selection by structured filters.

    Not a release-facing retrieval API — use PolicyAwareEpisodeRetriever.
    """
    matched = [
        episode.model_copy(deep=True)
        for episode in store.list_episodes()
        if _matches_filter(episode, filters)
    ]
    matched.sort(key=lambda item: (item.created_at, item.episode_id))
    return matched
