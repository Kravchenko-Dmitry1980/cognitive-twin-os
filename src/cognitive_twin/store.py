"""In-memory event and episode store."""

from __future__ import annotations

from cognitive_twin.episodes import Episode
from cognitive_twin.events import Event


class DuplicateEventError(ValueError):
    """Raised when appending an event with an existing event_id."""


class UnknownEventReferenceError(ValueError):
    """Raised when an episode references event_ids not present in the store."""


class EventStore:
    """
    Local in-memory store for events and episodes.

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
        self._events[event.event_id] = event

    def get_event(self, event_id: str) -> Event | None:
        return self._events.get(event_id)

    def list_events(self) -> list[Event]:
        return list(self._events.values())

    def append_episode(self, episode: Episode) -> None:
        missing = [eid for eid in episode.event_ids if eid not in self._events]
        if missing:
            raise UnknownEventReferenceError(
                f"Episode references unknown event_ids: {missing}"
            )
        if episode.episode_id in self._episodes:
            raise ValueError(
                f"Episode with episode_id '{episode.episode_id}' already exists"
            )
        self._episodes[episode.episode_id] = episode

    def get_episode(self, episode_id: str) -> Episode | None:
        return self._episodes.get(episode_id)

    def list_episodes(self) -> list[Episode]:
        return list(self._episodes.values())
