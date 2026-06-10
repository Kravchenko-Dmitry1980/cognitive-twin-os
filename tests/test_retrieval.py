"""Tests for internal structured candidate selection (not release-facing API)."""

from __future__ import annotations

from datetime import UTC, datetime

from cognitive_twin.episodes import MemoryState
from cognitive_twin.retrieval import RetrievalFilter, filter_episodes
from conftest import make_episode, make_event


def _populated_store():
    from cognitive_twin.store import InMemoryEventStore

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


def _episode_ids(store, filters: RetrievalFilter) -> list[str]:
    return [episode.episode_id for episode in filter_episodes(store, filters)]


def test_filter_by_memory_state() -> None:
    store = _populated_store()
    assert _episode_ids(store, RetrievalFilter(memory_state=MemoryState.CURATED)) == [
        "ep_curated"
    ]


def test_filter_by_salience() -> None:
    store = _populated_store()
    assert _episode_ids(store, RetrievalFilter(min_salience=0.8)) == ["ep_curated"]


def test_filter_by_entity() -> None:
    store = _populated_store()
    assert _episode_ids(store, RetrievalFilter(entity="alice")) == ["ep_raw"]


def test_filter_by_goal() -> None:
    store = _populated_store()
    assert _episode_ids(store, RetrievalFilter(goal="review")) == ["ep_curated"]


def test_filter_by_time_range() -> None:
    store = _populated_store()
    assert _episode_ids(
        store,
        RetrievalFilter(created_after=datetime(2026, 6, 9, 13, 0, 0, tzinfo=UTC)),
    ) == ["ep_curated"]
