"""Tests for structured episode retrieval."""

from __future__ import annotations

from datetime import UTC, datetime

from cognitive_twin.episodes import MemoryState
from cognitive_twin.retrieval import RetrievalFilter, StructuredEpisodeRetriever
from cognitive_twin.store import InMemoryEventStore
from cognitive_twin.trace_store import JsonlTraceStore
from cognitive_twin.traces import TraceStatus
from conftest import make_episode, make_event


def _populated_store() -> InMemoryEventStore:
    store = InMemoryEventStore()
    store.append_event(make_event("evt_1"))
    store.append_event(make_event("evt_2", payload={"text": "two"}))
    base = datetime(2026, 6, 9, 12, 0, 0, tzinfo=UTC)
    store.append_episode(
        make_episode(["evt_1"], "ep_raw").model_copy(
            update={
                "episode_type": "conversation",
                "salience": 0.4,
                "entities": ["alice"],
                "goals": ["plan"],
                "memory_state": MemoryState.RAW,
                "created_at": base,
                "updated_at": base,
            }
        )
    )
    store.append_episode(
        make_episode(["evt_2"], "ep_curated").model_copy(
            update={
                "episode_type": "decision",
                "salience": 0.9,
                "entities": ["bob"],
                "goals": ["review"],
                "memory_state": MemoryState.CURATED,
                "created_at": base.replace(hour=14),
                "updated_at": base.replace(hour=14),
            }
        )
    )
    return store


def test_retrieval_by_memory_state() -> None:
    store = _populated_store()
    result = StructuredEpisodeRetriever().retrieve(
        "req_ms",
        store,
        RetrievalFilter(memory_state=MemoryState.CURATED),
    )
    assert result.episode_ids == ["ep_curated"]


def test_retrieval_by_salience() -> None:
    store = _populated_store()
    result = StructuredEpisodeRetriever().retrieve(
        "req_sal",
        store,
        RetrievalFilter(min_salience=0.8),
    )
    assert result.episode_ids == ["ep_curated"]


def test_retrieval_by_entity() -> None:
    store = _populated_store()
    result = StructuredEpisodeRetriever().retrieve(
        "req_ent",
        store,
        RetrievalFilter(entity="alice"),
    )
    assert result.episode_ids == ["ep_raw"]


def test_retrieval_by_goal() -> None:
    store = _populated_store()
    result = StructuredEpisodeRetriever().retrieve(
        "req_goal",
        store,
        RetrievalFilter(goal="review"),
    )
    assert result.episode_ids == ["ep_curated"]


def test_retrieval_by_time_range() -> None:
    store = _populated_store()
    result = StructuredEpisodeRetriever().retrieve(
        "req_time",
        store,
        RetrievalFilter(
            created_after=datetime(2026, 6, 9, 13, 0, 0, tzinfo=UTC),
        ),
    )
    assert result.episode_ids == ["ep_curated"]


def test_retrieval_writes_trace(tmp_path) -> None:
    store = _populated_store()
    trace_store = JsonlTraceStore(tmp_path / "traces.jsonl")
    StructuredEpisodeRetriever().retrieve(
        "req_trace",
        store,
        RetrievalFilter(episode_type="conversation"),
        trace_store=trace_store,
        actor_id="actor_retriever",
    )
    traces = trace_store.list_traces()
    assert len(traces) == 1
    assert traces[0].operation == "retrieve_episodes"
    assert traces[0].status == TraceStatus.SUCCEEDED
    assert traces[0].metadata["match_count"] == 1
