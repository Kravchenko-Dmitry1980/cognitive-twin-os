"""Structured episode retrieval filters — no semantic search."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from cognitive_twin.episodes import Episode, MemoryState
from cognitive_twin.operation_trace import TraceWriter, record_operation
from cognitive_twin.store import EpisodeRepository
from cognitive_twin.traces import TraceStatus


class RetrievalFilter(BaseModel):
    """Explicit structured filters only — no embeddings or ranking models."""

    episode_type: str | None = None
    memory_state: MemoryState | None = None
    min_salience: float | None = Field(default=None, ge=0.0, le=1.0)
    entity: str | None = None
    goal: str | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None


class RetrievalRequest(BaseModel):
    """Structured retrieval request boundary for the local runtime."""

    request_id: str = Field(min_length=1)
    filters: RetrievalFilter = Field(default_factory=RetrievalFilter)
    actor_id: str | None = None


class RetrievalResult(BaseModel):
    request_id: str = Field(min_length=1)
    episode_ids: list[str] = Field(default_factory=list)
    episodes: list[Episode] = Field(default_factory=list)


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


class StructuredEpisodeRetriever:
    """
    Filter episodes by explicit fields.

    No vector search, ranking model, LLM, or embeddings.
    """

    def retrieve(
        self,
        request_id: str,
        store: EpisodeRepository,
        filters: RetrievalFilter,
        trace_store: TraceWriter | None = None,
        actor_id: str | None = None,
    ) -> RetrievalResult:
        matched = [
            episode.model_copy(deep=True)
            for episode in store.list_episodes()
            if _matches_filter(episode, filters)
        ]
        matched.sort(key=lambda item: (item.created_at, item.episode_id))

        episode_ids = [episode.episode_id for episode in matched]
        result = RetrievalResult(
            request_id=request_id,
            episode_ids=episode_ids,
            episodes=matched,
        )

        record_operation(
            trace_store,
            operation="retrieve_episodes",
            status=TraceStatus.SUCCEEDED,
            input_refs=[request_id],
            output_refs=episode_ids,
            actor_id=actor_id,
            metadata={
                "request_id": request_id,
                "match_count": len(episode_ids),
                "filters": filters.model_dump(mode="json", exclude_none=True),
            },
        )
        return result
