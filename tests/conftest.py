"""Shared test fixtures."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cognitive_twin.episodes import Episode, MemoryState
from cognitive_twin.events import (
    Actor,
    ConsentBasis,
    Event,
    EventSource,
    EventType,
    Governance,
    Provenance,
    RetentionPolicy,
    Sensitivity,
)
from cognitive_twin.hashing import compute_content_hash


def make_event(
    event_id: str = "evt_test001",
    payload: dict | None = None,
    metadata: dict | None = None,
    timestamp: datetime | None = None,
    sensitivity: Sensitivity = Sensitivity.INTERNAL,
    consent_basis: ConsentBasis = ConsentBasis.EXPLICIT,
) -> Event:
    payload = payload or {"text": "hello"}
    metadata = metadata or {"channel": "test"}
    content_hash = compute_content_hash(payload, metadata)
    now = timestamp or datetime(2026, 6, 9, 12, 0, 0, tzinfo=UTC)
    return Event(
        event_id=event_id,
        source=EventSource(type="chat", source_id="src_chat01"),
        actor=Actor(actor_id="actor_user01", role="user"),
        timestamp=now,
        event_type=EventType.MESSAGE,
        payload=payload,
        provenance=Provenance(
            captured_by="test_harness",
            confidence=0.95,
            content_hash=content_hash,
            schema_version="1.0.0",
        ),
        governance=Governance(
            sensitivity=sensitivity,
            consent_basis=consent_basis,
            retention_policy=RetentionPolicy.DEFAULT,
        ),
    )


def make_episode(event_ids: list[str], episode_id: str = "ep_test001") -> Episode:
    now = datetime(2026, 6, 9, 12, 5, 0, tzinfo=UTC)
    return Episode(
        episode_id=episode_id,
        event_ids=event_ids,
        episode_type="conversation",
        summary="Test episode",
        salience=0.7,
        entities=["user"],
        goals=["clarify intent"],
        outcome=None,
        memory_state=MemoryState.RAW,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_event() -> Event:
    return make_event()


@pytest.fixture
def event_store():
    from cognitive_twin.store import EventStore

    return EventStore()
