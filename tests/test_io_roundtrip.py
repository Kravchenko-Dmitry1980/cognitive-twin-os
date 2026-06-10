"""Tests for JSONL import/export utilities."""

from __future__ import annotations

import pytest

from cognitive_twin.errors import StorageError
from cognitive_twin.io import (
    export_episodes_to_jsonl,
    export_events_to_jsonl,
    import_episodes_from_jsonl,
    import_events_from_jsonl,
)
from conftest import make_episode, make_event


def test_export_import_events_roundtrip(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    events = [make_event("evt_a"), make_event("evt_b")]

    export_events_to_jsonl(events, path)

    assert import_events_from_jsonl(path) == events


def test_export_import_episodes_roundtrip(tmp_path) -> None:
    path = tmp_path / "episodes.jsonl"
    episodes = [make_episode(["evt_a"], "ep_a"), make_episode(["evt_b"], "ep_b")]

    export_episodes_to_jsonl(episodes, path)

    assert import_episodes_from_jsonl(path) == episodes


def test_import_events_missing_file_behavior_is_explicit(tmp_path) -> None:
    with pytest.raises(StorageError, match="does not exist"):
        import_events_from_jsonl(tmp_path / "missing_events.jsonl")


def test_import_episodes_missing_file_behavior_is_explicit(tmp_path) -> None:
    with pytest.raises(StorageError, match="does not exist"):
        import_episodes_from_jsonl(tmp_path / "missing_episodes.jsonl")


def test_import_events_corrupted_jsonl_raises_storage_error(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text("{not-json}\n", encoding="utf-8")
    with pytest.raises(StorageError, match="Invalid JSONL record"):
        import_events_from_jsonl(path)


def test_import_episodes_corrupted_jsonl_raises_storage_error(tmp_path) -> None:
    path = tmp_path / "episodes.jsonl"
    path.write_text("{not-json}\n", encoding="utf-8")
    with pytest.raises(StorageError, match="Invalid JSONL record"):
        import_episodes_from_jsonl(path)


def test_export_events_overwrites_existing_file(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    export_events_to_jsonl([make_event("evt_old")], path)
    export_events_to_jsonl([make_event("evt_new")], path)
    imported = import_events_from_jsonl(path)
    assert [event.event_id for event in imported] == ["evt_new"]


def test_export_episodes_overwrites_existing_file(tmp_path) -> None:
    path = tmp_path / "episodes.jsonl"
    export_episodes_to_jsonl([make_episode(["evt_a"], "ep_old")], path)
    export_episodes_to_jsonl([make_episode(["evt_b"], "ep_new")], path)
    imported = import_episodes_from_jsonl(path)
    assert [episode.episode_id for episode in imported] == ["ep_new"]
