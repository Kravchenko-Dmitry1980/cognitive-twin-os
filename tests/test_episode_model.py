"""Tests for Episode Pydantic model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from cognitive_twin.episodes import Episode, MemoryState
from conftest import make_episode


def test_valid_episode_creation() -> None:
    episode = make_episode(["evt_001"])
    assert episode.episode_id == "ep_test001"
    assert episode.memory_state == MemoryState.RAW
    assert episode.event_ids == ["evt_001"]


def test_episode_requires_at_least_one_event_id() -> None:
    with pytest.raises(ValidationError):
        make_episode([])


def test_invalid_memory_state_rejected() -> None:
    episode = make_episode(["evt_001"])
    data = episode.model_dump(mode="json")
    data["memory_state"] = "forgotten"
    with pytest.raises(ValidationError):
        Episode.model_validate(data)


def test_salience_bounds() -> None:
    episode = make_episode(["evt_001"])
    data = episode.model_dump(mode="json")
    data["salience"] = 1.5
    with pytest.raises(ValidationError):
        Episode.model_validate(data)
