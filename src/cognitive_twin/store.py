"""Storage interfaces and in-memory event/episode store."""

from __future__ import annotations

from typing import Protocol

from cognitive_twin.episodes import Episode
from cognitive_twin.errors import (
    DuplicateEpisodeError,
    DuplicateEventError,
    UnknownEventReferenceError,
)
from cognitive_twin.events import Event


class EventRepository(Protocol):
    """Contract for event persistence implementations."""

    def append_event(self, event: Event) -> None: ...

    def get_event(self, event_id: str) -> Event | None: ...

    def list_events(self) -> list[Event]: ...


class EpisodeRepository(Protocol):
    """Contract for episode persistence implementations."""

    def append_episode(self, episode: Episode) -> None: ...

    def get_episode(self, episode_id: str) -> Episode | None: ...

    def list_episodes(self) -> list[Episode]: ...


class EventEpisodeRepository(EventRepository, EpisodeRepository, Protocol):
    """Combined contract for stores that persist events and episodes."""


class InMemoryEventStore:
    """
    Local in-memory store for events and episodes.

    Store-level snapshot semantics: persisted models are deep-copied on write
    and on every read. Callers never receive mutable internal references.

    No external services, no LLM calls, no persistence of secrets.
    """

    def __init__(self) -> None:
        self._events: dict[str, Event] = {}
        self._episodes: dict[str, Episode] = {}

    def append_event(self, event: Event) -> None:
        if event.event_id in self._events:
            raise DuplicateEventError(
                f"Event with event_id '{event.event_id}' already exists"
            )
        stored = event.model_copy(deep=True)
        self._events[stored.event_id] = stored

    def get_event(self, event_id: str) -> Event | None:
        event = self._events.get(event_id)
        return event.model_copy(deep=True) if event is not None else None

    def list_events(self) -> list[Event]:
        return [event.model_copy(deep=True) for event in self._events.values()]

    def append_episode(self, episode: Episode) -> None:
        missing = [eid for eid in episode.event_ids if eid not in self._events]
        if missing:
            raise UnknownEventReferenceError(
                f"Episode references unknown event_ids: {missing}"
            )
        if episode.episode_id in self._episodes:
            raise DuplicateEpisodeError(
                f"Episode with episode_id '{episode.episode_id}' already exists"
            )
        stored = episode.model_copy(deep=True)
        self._episodes[stored.episode_id] = stored

    def get_episode(self, episode_id: str) -> Episode | None:
        episode = self._episodes.get(episode_id)
        return episode.model_copy(deep=True) if episode is not None else None

    def list_episodes(self) -> list[Episode]:
        return [episode.model_copy(deep=True) for episode in self._episodes.values()]


EventStore = InMemoryEventStore
