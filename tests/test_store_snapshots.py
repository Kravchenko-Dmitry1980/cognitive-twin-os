"""Tests for store-level snapshot semantics."""

from __future__ import annotations

from cognitive_twin.jsonl_store import JsonlEventStore
from cognitive_twin.store import InMemoryEventStore
from cognitive_twin.trace_store import JsonlTraceStore
from cognitive_twin.traces import OperationTrace, TraceStatus
from conftest import make_episode, make_event


def test_inmemory_mutating_original_event_after_append() -> None:
    store = InMemoryEventStore()
    event = make_event("evt_snap")
    store.append_event(event)
    event.payload["text"] = "mutated"
    assert store.get_event("evt_snap").payload["text"] == "hello"


def test_inmemory_mutating_event_from_get_event() -> None:
    store = InMemoryEventStore()
    store.append_event(make_event("evt_get"))
    retrieved = store.get_event("evt_get")
    assert retrieved is not None
    retrieved.payload["text"] = "mutated"
    assert store.get_event("evt_get").payload["text"] == "hello"


def test_inmemory_mutating_event_from_list_events() -> None:
    store = InMemoryEventStore()
    store.append_event(make_event("evt_list"))
    listed = store.list_events()
    listed[0].payload["text"] = "mutated"
    assert store.get_event("evt_list").payload["text"] == "hello"


def test_inmemory_mutating_original_episode_after_append() -> None:
    store = InMemoryEventStore()
    store.append_event(make_event("evt_ep"))
    episode = make_episode(["evt_ep"], "ep_snap")
    store.append_episode(episode)
    episode.summary = "mutated"
    assert store.get_episode("ep_snap").summary == "Test episode"


def test_inmemory_mutating_episode_from_get_episode() -> None:
    store = InMemoryEventStore()
    store.append_event(make_event("evt_ep2"))
    store.append_episode(make_episode(["evt_ep2"], "ep_get"))
    retrieved = store.get_episode("ep_get")
    assert retrieved is not None
    retrieved.summary = "mutated"
    assert store.get_episode("ep_get").summary == "Test episode"


def test_inmemory_mutating_episode_from_list_episodes() -> None:
    store = InMemoryEventStore()
    store.append_event(make_event("evt_ep3"))
    store.append_episode(make_episode(["evt_ep3"], "ep_list"))
    listed = store.list_episodes()
    listed[0].summary = "mutated"
    assert store.get_episode("ep_list").summary == "Test episode"


def test_jsonl_append_event_does_not_mutate_input(tmp_path) -> None:
    store = JsonlEventStore(tmp_path / "events.jsonl", tmp_path / "episodes.jsonl")
    event = make_event("evt_jsonl")
    store.append_event(event)
    event.payload["text"] = "mutated"
    assert store.get_event("evt_jsonl").payload["text"] == "hello"


def test_jsonl_mutating_event_from_get_event_does_not_mutate_store(tmp_path) -> None:
    store = JsonlEventStore(tmp_path / "events.jsonl", tmp_path / "episodes.jsonl")
    store.append_event(make_event("evt_jsonl_get"))
    retrieved = store.get_event("evt_jsonl_get")
    assert retrieved is not None
    retrieved.payload["text"] = "mutated"
    assert store.get_event("evt_jsonl_get").payload["text"] == "hello"


def test_jsonl_mutating_event_from_list_events_does_not_mutate_store(tmp_path) -> None:
    store = JsonlEventStore(tmp_path / "events.jsonl", tmp_path / "episodes.jsonl")
    store.append_event(make_event("evt_jsonl_list"))
    listed = store.list_events()
    listed[0].payload["text"] = "mutated"
    assert store.get_event("evt_jsonl_list").payload["text"] == "hello"


def test_jsonl_append_episode_does_not_mutate_input(tmp_path) -> None:
    store = JsonlEventStore(tmp_path / "events.jsonl", tmp_path / "episodes.jsonl")
    store.append_event(make_event("evt_jsonl_ep"))
    episode = make_episode(["evt_jsonl_ep"], "ep_jsonl")
    store.append_episode(episode)
    episode.summary = "mutated"
    assert store.get_episode("ep_jsonl").summary == "Test episode"


def test_jsonl_mutating_episode_from_get_episode_does_not_mutate_store(tmp_path) -> None:
    store = JsonlEventStore(tmp_path / "events.jsonl", tmp_path / "episodes.jsonl")
    store.append_event(make_event("evt_jsonl_ep_get"))
    store.append_episode(make_episode(["evt_jsonl_ep_get"], "ep_jsonl_get"))
    retrieved = store.get_episode("ep_jsonl_get")
    assert retrieved is not None
    retrieved.summary = "mutated"
    assert store.get_episode("ep_jsonl_get").summary == "Test episode"


def test_jsonl_mutating_episode_from_list_episodes_does_not_mutate_store(tmp_path) -> None:
    store = JsonlEventStore(tmp_path / "events.jsonl", tmp_path / "episodes.jsonl")
    store.append_event(make_event("evt_jsonl_ep_list"))
    store.append_episode(make_episode(["evt_jsonl_ep_list"], "ep_jsonl_list"))
    listed = store.list_episodes()
    listed[0].summary = "mutated"
    assert store.get_episode("ep_jsonl_list").summary == "Test episode"


def test_jsonl_list_episodes_order_is_deterministic(tmp_path) -> None:
    store = JsonlEventStore(tmp_path / "events.jsonl", tmp_path / "episodes.jsonl")
    store.append_event(make_event("evt_a"))
    store.append_event(make_event("evt_b", payload={"text": "two"}))
    store.append_episode(make_episode(["evt_a"], "ep_a"))
    store.append_episode(make_episode(["evt_b"], "ep_b"))

    assert [episode.episode_id for episode in store.list_episodes()] == ["ep_a", "ep_b"]


def test_trace_list_order_is_deterministic(tmp_path) -> None:
    from datetime import UTC, datetime

    store = JsonlTraceStore(tmp_path / "traces.jsonl")
    base = datetime(2026, 6, 10, 12, 0, 0, tzinfo=UTC)
    for trace_id in ("trace_a", "trace_b", "trace_c"):
        store.append_trace(
            OperationTrace(
                trace_id=trace_id,
                operation="ingest_batch",
                timestamp=base,
                status=TraceStatus.SUCCEEDED,
            )
        )
    reloaded = JsonlTraceStore(tmp_path / "traces.jsonl")
    assert [trace.trace_id for trace in reloaded.list_traces()] == [
        "trace_a",
        "trace_b",
        "trace_c",
    ]
