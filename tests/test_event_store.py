"""Tests for in-memory EventStore."""

from __future__ import annotations

import pytest

from cognitive_twin.hashing import compute_content_hash
from cognitive_twin.store import (
    DuplicateEventError,
    EventStore,
    UnknownEventReferenceError,
)
from conftest import make_episode, make_event


def test_append_and_get_event() -> None:
    store = EventStore()
    event = make_event("evt_a")
    store.append_event(event)
    assert store.get_event("evt_a") == event


def test_list_events() -> None:
    store = EventStore()
    store.append_event(make_event("evt_a"))
    store.append_event(make_event("evt_b"))
    ids = {e.event_id for e in store.list_events()}
    assert ids == {"evt_a", "evt_b"}


def test_duplicate_event_id_raises() -> None:
    store = EventStore()
    store.append_event(make_event("evt_dup"))
    with pytest.raises(DuplicateEventError, match="evt_dup"):
        store.append_event(make_event("evt_dup"))


def test_append_episode_with_known_events() -> None:
    store = EventStore()
    store.append_event(make_event("evt_1"))
    episode = make_episode(["evt_1"], "ep_1")
    store.append_episode(episode)
    assert store.get_episode("ep_1") == episode


def test_episode_unknown_event_ids_raises() -> None:
    store = EventStore()
    episode = make_episode(["evt_missing"], "ep_bad")
    with pytest.raises(UnknownEventReferenceError, match="evt_missing"):
        store.append_episode(episode)


def test_list_episodes() -> None:
    store = EventStore()
    store.append_event(make_event("evt_1"))
    store.append_episode(make_episode(["evt_1"], "ep_1"))
    assert len(store.list_episodes()) == 1


def test_content_hash_deterministic() -> None:
    payload = {"text": "hello"}
    metadata = {"channel": "test"}
    h1 = compute_content_hash(payload, metadata)
    h2 = compute_content_hash(payload, metadata)
    assert h1 == h2


def test_content_hash_changes_on_payload_change() -> None:
    metadata = {"channel": "test"}
    h1 = compute_content_hash({"text": "hello"}, metadata)
    h2 = compute_content_hash({"text": "world"}, metadata)
    assert h1 != h2
