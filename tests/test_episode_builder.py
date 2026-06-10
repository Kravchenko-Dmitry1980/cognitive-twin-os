"""Tests for deterministic episode builder."""

from __future__ import annotations

from datetime import UTC, datetime

from cognitive_twin.episode_builder import (
    DeterministicEpisodeBuilder,
    EpisodeBuildRequest,
    EpisodeBuildStatus,
)
from cognitive_twin.episodes import MemoryState
from cognitive_twin.store import InMemoryEventStore
from cognitive_twin.trace_store import JsonlTraceStore
from cognitive_twin.traces import TraceStatus
from conftest import make_event


def _store_with_events() -> InMemoryEventStore:
    store = InMemoryEventStore()
    store.append_event(
        make_event(
            "evt_late",
            timestamp=datetime(2026, 6, 9, 14, 0, 0, tzinfo=UTC),
        )
    )
    store.append_event(
        make_event(
            "evt_early",
            payload={"text": "first"},
            timestamp=datetime(2026, 6, 9, 10, 0, 0, tzinfo=UTC),
        )
    )
    return store


def test_deterministic_episode_build() -> None:
    store = _store_with_events()
    builder = DeterministicEpisodeBuilder()
    request = EpisodeBuildRequest(
        request_id="req_1",
        episode_id="ep_1",
        event_ids=["evt_late", "evt_early"],
        episode_type="conversation",
        summary="Caller summary",
        salience=0.8,
        entities=["user"],
        goals=["decide"],
    )
    result, episode = builder.build(request, store)
    assert result.status == EpisodeBuildStatus.SUCCEEDED
    assert episode is not None
    assert result.event_ids == ["evt_early", "evt_late"]
    assert episode.summary == "Caller summary"
    assert episode.salience == 0.8


def test_unknown_event_id_fails() -> None:
    store = InMemoryEventStore()
    store.append_event(make_event("evt_only"))
    result, episode = DeterministicEpisodeBuilder().build(
        EpisodeBuildRequest(
            request_id="req_2",
            episode_id="ep_bad",
            event_ids=["evt_only", "evt_missing"],
            episode_type="conversation",
            summary="Summary",
            salience=0.5,
        ),
        store,
    )
    assert result.status == EpisodeBuildStatus.FAILED
    assert episode is None
    assert "evt_missing" in result.error


def test_episode_build_does_not_modify_events() -> None:
    store = _store_with_events()
    before = {
        event_id: store.get_event(event_id).model_dump(mode="json")
        for event_id in ("evt_early", "evt_late")
    }
    DeterministicEpisodeBuilder().build(
        EpisodeBuildRequest(
            request_id="req_3",
            episode_id="ep_2",
            event_ids=["evt_early", "evt_late"],
            episode_type="conversation",
            summary="Summary",
            salience=0.6,
            memory_state=MemoryState.RAW,
        ),
        store,
    )
    after = {
        event_id: store.get_event(event_id).model_dump(mode="json")
        for event_id in ("evt_early", "evt_late")
    }
    assert before == after


def test_episode_build_writes_trace(tmp_path) -> None:
    store = _store_with_events()
    trace_store = JsonlTraceStore(tmp_path / "traces.jsonl")
    DeterministicEpisodeBuilder().build(
        EpisodeBuildRequest(
            request_id="req_4",
            episode_id="ep_trace",
            event_ids=["evt_early", "evt_late"],
            episode_type="conversation",
            summary="Summary",
            salience=0.5,
            actor_id="actor_builder",
        ),
        store,
        trace_store=trace_store,
    )
    traces = trace_store.list_traces()
    assert len(traces) == 1
    assert traces[0].operation == "build_episode"
    assert traces[0].status == TraceStatus.SUCCEEDED
    assert traces[0].output_refs == ["ep_trace"]
