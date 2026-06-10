"""Deterministic episode builder from validated events."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from cognitive_twin.episodes import Episode, MemoryState
from cognitive_twin.errors import UnknownEventReferenceError
from cognitive_twin.operation_trace import TraceWriter, record_operation
from cognitive_twin.store import EventEpisodeRepository
from cognitive_twin.traces import TraceStatus


class EpisodeBuildStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class EpisodeBuildRequest(BaseModel):
    """Caller-supplied episode fields — no generated interpretation."""

    request_id: str = Field(min_length=1)
    episode_id: str = Field(min_length=1)
    event_ids: list[str] = Field(min_length=1)
    episode_type: str = Field(min_length=1)
    summary: str
    salience: float = Field(ge=0.0, le=1.0)
    entities: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    outcome: str | None = None
    memory_state: MemoryState = MemoryState.RAW
    actor_id: str | None = None


class EpisodeBuildResult(BaseModel):
    request_id: str = Field(min_length=1)
    episode_id: str = Field(min_length=1)
    event_ids: list[str] = Field(min_length=1)
    status: EpisodeBuildStatus
    error: str | None = None


def _sort_event_ids_by_timestamp(store: EventEpisodeRepository, event_ids: list[str]) -> list[str]:
    """Order event_ids deterministically by event timestamp, then event_id."""
    events = []
    for event_id in event_ids:
        event = store.get_event(event_id)
        if event is None:
            raise UnknownEventReferenceError(
                f"Episode references unknown event_ids: [{event_id}]"
            )
        events.append(event)
    events.sort(key=lambda item: (item.timestamp, item.event_id))
    return [event.event_id for event in events]


class DeterministicEpisodeBuilder:
    """
    Build episodes from explicit event_ids and caller-provided metadata.

    Does not modify events, generate summaries, update identity, or consolidate.
    """

    def build(
        self,
        request: EpisodeBuildRequest,
        store: EventEpisodeRepository,
        trace_store: TraceWriter | None = None,
    ) -> tuple[EpisodeBuildResult, Episode | None]:
        try:
            ordered_event_ids = _sort_event_ids_by_timestamp(store, request.event_ids)
        except UnknownEventReferenceError as exc:
            result = EpisodeBuildResult(
                request_id=request.request_id,
                episode_id=request.episode_id,
                event_ids=list(request.event_ids),
                status=EpisodeBuildStatus.FAILED,
                error=str(exc),
            )
            record_operation(
                trace_store,
                operation="build_episode",
                status=TraceStatus.FAILED,
                input_refs=[request.request_id, *request.event_ids],
                actor_id=request.actor_id,
                error=str(exc),
                metadata={
                    "request_id": request.request_id,
                    "episode_id": request.episode_id,
                },
            )
            return result, None

        now = datetime.now(UTC)
        episode = Episode(
            episode_id=request.episode_id,
            event_ids=ordered_event_ids,
            episode_type=request.episode_type,
            summary=request.summary,
            salience=request.salience,
            entities=list(request.entities),
            goals=list(request.goals),
            outcome=request.outcome,
            memory_state=request.memory_state,
            created_at=now,
            updated_at=now,
        )

        try:
            store.append_episode(episode)
        except (UnknownEventReferenceError, ValueError) as exc:
            result = EpisodeBuildResult(
                request_id=request.request_id,
                episode_id=request.episode_id,
                event_ids=ordered_event_ids,
                status=EpisodeBuildStatus.FAILED,
                error=str(exc),
            )
            record_operation(
                trace_store,
                operation="build_episode",
                status=TraceStatus.FAILED,
                input_refs=[request.request_id, *ordered_event_ids],
                actor_id=request.actor_id,
                error=str(exc),
                metadata={
                    "request_id": request.request_id,
                    "episode_id": request.episode_id,
                },
            )
            return result, None

        result = EpisodeBuildResult(
            request_id=request.request_id,
            episode_id=request.episode_id,
            event_ids=ordered_event_ids,
            status=EpisodeBuildStatus.SUCCEEDED,
        )
        record_operation(
            trace_store,
            operation="build_episode",
            status=TraceStatus.SUCCEEDED,
            input_refs=[request.request_id, *ordered_event_ids],
            output_refs=[episode.episode_id],
            actor_id=request.actor_id,
            metadata={
                "request_id": request.request_id,
                "episode_id": episode.episode_id,
                "event_count": len(ordered_event_ids),
            },
        )
        return result, episode
