"""Tests for JSONL event and episode persistence."""

from __future__ import annotations

import json

import pytest

from cognitive_twin.errors import (
    DuplicateEpisodeError,
    DuplicateEventError,
    StorageError,
    UnknownEventReferenceError,
)
from cognitive_twin.jsonl_store import JsonlEventStore
from conftest import make_episode, make_event


def test_jsonl_event_store_persists_event_and_reloads(tmp_path) -> None:
    events_path = tmp_path / "events.jsonl"
    episodes_path = tmp_path / "episodes.jsonl"
    store = JsonlEventStore(events_path, episodes_path)

    event = make_event("evt_1")
    store.append_event(event)

    reloaded = JsonlEventStore(events_path, episodes_path)
    assert reloaded.get_event("evt_1") == event


def test_jsonl_event_store_persists_episode_and_reloads(tmp_path) -> None:
    events_path = tmp_path / "events.jsonl"
    episodes_path = tmp_path / "episodes.jsonl"
    store = JsonlEventStore(events_path, episodes_path)

    event = make_event("evt_1")
    episode = make_episode(["evt_1"], "ep_1")
    store.append_event(event)
    store.append_episode(episode)

    reloaded = JsonlEventStore(events_path, episodes_path)
    assert reloaded.get_episode("ep_1") == episode


def test_jsonl_duplicate_event_id_fails(tmp_path) -> None:
    store = JsonlEventStore(tmp_path / "events.jsonl", tmp_path / "episodes.jsonl")
    store.append_event(make_event("evt_dup"))

    with pytest.raises(DuplicateEventError, match="evt_dup"):
        store.append_event(make_event("evt_dup"))


def test_jsonl_duplicate_event_id_fails_on_reload(tmp_path) -> None:
    events_path = tmp_path / "events.jsonl"
    first = make_event("evt_dup").model_dump(mode="json")
    second = make_event("evt_dup", payload={"text": "duplicate"}).model_dump(mode="json")
    events_path.write_text(
        "\n".join(
            [
                json.dumps(first, separators=(",", ":")),
                json.dumps(second, separators=(",", ":")),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(DuplicateEventError, match="evt_dup"):
        JsonlEventStore(events_path, tmp_path / "episodes.jsonl")


def test_jsonl_duplicate_episode_id_fails(tmp_path) -> None:
    store = JsonlEventStore(tmp_path / "events.jsonl", tmp_path / "episodes.jsonl")
    store.append_event(make_event("evt_1"))
    store.append_episode(make_episode(["evt_1"], "ep_dup"))

    with pytest.raises(DuplicateEpisodeError, match="ep_dup"):
        store.append_episode(make_episode(["evt_1"], "ep_dup"))


def test_jsonl_duplicate_episode_id_fails_on_reload(tmp_path) -> None:
    events_path = tmp_path / "events.jsonl"
    episodes_path = tmp_path / "episodes.jsonl"
    event = make_event("evt_1")
    events_path.write_text(
        json.dumps(event.model_dump(mode="json"), separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    first = make_episode(["evt_1"], "ep_dup").model_dump(mode="json")
    second = make_episode(["evt_1"], "ep_dup").model_dump(mode="json")
    episodes_path.write_text(
        "\n".join(
            [
                json.dumps(first, separators=(",", ":")),
                json.dumps(second, separators=(",", ":")),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(DuplicateEpisodeError, match="ep_dup"):
        JsonlEventStore(events_path, episodes_path)


def test_jsonl_episode_with_unknown_event_id_fails(tmp_path) -> None:
    store = JsonlEventStore(tmp_path / "events.jsonl", tmp_path / "episodes.jsonl")

    with pytest.raises(UnknownEventReferenceError, match="evt_missing"):
        store.append_episode(make_episode(["evt_missing"], "ep_bad"))


def test_jsonl_corrupted_line_fails_clearly(tmp_path) -> None:
    events_path = tmp_path / "events.jsonl"
    events_path.write_text("{not-json}\n", encoding="utf-8")

    with pytest.raises(StorageError, match="Invalid JSONL record"):
        JsonlEventStore(events_path, tmp_path / "episodes.jsonl")


def test_jsonl_non_object_line_fails_clearly(tmp_path) -> None:
    events_path = tmp_path / "events.jsonl"
    events_path.write_text("[]\n", encoding="utf-8")

    with pytest.raises(StorageError, match="expected object"):
        JsonlEventStore(events_path, tmp_path / "episodes.jsonl")


def test_jsonl_corrupted_episode_line_fails_clearly(tmp_path) -> None:
    events_path = tmp_path / "events.jsonl"
    episodes_path = tmp_path / "episodes.jsonl"
    events_path.write_text(
        json.dumps(make_event("evt_1").model_dump(mode="json"), separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )
    episodes_path.write_text("{not-json}\n", encoding="utf-8")

    with pytest.raises(StorageError, match="Invalid JSONL record"):
        JsonlEventStore(events_path, episodes_path)


def test_jsonl_list_order_is_deterministic(tmp_path) -> None:
    store = JsonlEventStore(tmp_path / "events.jsonl", tmp_path / "episodes.jsonl")
    store.append_event(make_event("evt_a"))
    store.append_event(make_event("evt_b"))

    assert [event.event_id for event in store.list_events()] == ["evt_a", "evt_b"]


def test_jsonl_reload_preserves_file_order(tmp_path) -> None:
    events_path = tmp_path / "events.jsonl"
    episodes_path = tmp_path / "episodes.jsonl"
    store = JsonlEventStore(events_path, episodes_path)
    store.append_event(make_event("evt_b"))
    store.append_event(make_event("evt_a", payload={"text": "second"}))
    store.append_episode(make_episode(["evt_b"], "ep_b"))
    store.append_episode(make_episode(["evt_a"], "ep_a"))

    reloaded = JsonlEventStore(events_path, episodes_path)

    assert [event.event_id for event in reloaded.list_events()] == ["evt_b", "evt_a"]
    assert [episode.episode_id for episode in reloaded.list_episodes()] == ["ep_b", "ep_a"]


def test_jsonl_append_event_does_not_mutate_input(tmp_path) -> None:
    store = JsonlEventStore(tmp_path / "events.jsonl", tmp_path / "episodes.jsonl")
    event = make_event("evt_input")
    store.append_event(event)
    event.payload["text"] = "mutated"
    assert store.get_event("evt_input").payload["text"] == "hello"


def test_jsonl_append_episode_does_not_mutate_input(tmp_path) -> None:
    store = JsonlEventStore(tmp_path / "events.jsonl", tmp_path / "episodes.jsonl")
    store.append_event(make_event("evt_ep_input"))
    episode = make_episode(["evt_ep_input"], "ep_input")
    store.append_episode(episode)
    episode.summary = "mutated"
    assert store.get_episode("ep_input").summary == "Test episode"


def test_jsonl_list_episodes_order_is_deterministic(tmp_path) -> None:
    events_path = tmp_path / "events.jsonl"
    episodes_path = tmp_path / "episodes.jsonl"
    store = JsonlEventStore(events_path, episodes_path)
    store.append_event(make_event("evt_1"))
    store.append_event(make_event("evt_2"))
    store.append_episode(make_episode(["evt_1"], "ep_a"))
    store.append_episode(make_episode(["evt_2"], "ep_b"))

    assert [episode.episode_id for episode in store.list_episodes()] == ["ep_a", "ep_b"]
