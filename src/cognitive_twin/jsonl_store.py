"""JSONL-backed event and episode store."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from cognitive_twin.episodes import Episode
from cognitive_twin.errors import (
    DuplicateEpisodeError,
    DuplicateEventError,
    StorageError,
    UnknownEventReferenceError,
)
from cognitive_twin.events import Event


def _json_line(model_data: dict[str, Any]) -> str:
    return json.dumps(model_data, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _read_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    if not path.exists():
        return

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                decoded = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise StorageError(
                    f"Invalid JSONL record in {path} at line {line_number}: {exc.msg}"
                ) from exc
            if not isinstance(decoded, dict):
                raise StorageError(
                    f"Invalid JSONL record in {path} at line {line_number}: expected object"
                )
            yield line_number, decoded


class JsonlEventStore:
    """
    Durable local JSONL store for Phase 1.1.

    Store-level snapshot semantics: append deep-copies input models; reads return
    deep copies. List order follows JSONL append order (insertion order).

    The store intentionally has no network, DB, vector, API, or LLM dependency.
    """

    def __init__(
        self,
        events_path: str | Path = "local_data/events.jsonl",
        episodes_path: str | Path = "local_data/episodes.jsonl",
    ) -> None:
        self.events_path = Path(events_path)
        self.episodes_path = Path(episodes_path)
        self._events: dict[str, Event] = {}
        self._episodes: dict[str, Episode] = {}
        self._load_events()
        self._load_episodes()

    def append_event(self, event: Event) -> None:
        if event.event_id in self._events:
            raise DuplicateEventError(
                f"Event with event_id '{event.event_id}' already exists"
            )
        stored = event.model_copy(deep=True)
        self._append_model(self.events_path, stored)
        self._events[stored.event_id] = stored

    def get_event(self, event_id: str) -> Event | None:
        event = self._events.get(event_id)
        return event.model_copy(deep=True) if event is not None else None

    def list_events(self) -> list[Event]:
        return [event.model_copy(deep=True) for event in self._events.values()]

    def append_episode(self, episode: Episode) -> None:
        missing = [event_id for event_id in episode.event_ids if event_id not in self._events]
        if missing:
            raise UnknownEventReferenceError(
                f"Episode references unknown event_ids: {missing}"
            )
        if episode.episode_id in self._episodes:
            raise DuplicateEpisodeError(
                f"Episode with episode_id '{episode.episode_id}' already exists"
            )
        stored = episode.model_copy(deep=True)
        self._append_model(self.episodes_path, stored)
        self._episodes[stored.episode_id] = stored

    def get_episode(self, episode_id: str) -> Episode | None:
        episode = self._episodes.get(episode_id)
        return episode.model_copy(deep=True) if episode is not None else None

    def list_episodes(self) -> list[Episode]:
        return [episode.model_copy(deep=True) for episode in self._episodes.values()]

    def _load_events(self) -> None:
        for line_number, decoded in _read_jsonl(self.events_path):
            try:
                event = Event.model_validate(decoded)
            except ValidationError as exc:
                raise StorageError(
                    f"Invalid event record in {self.events_path} at line {line_number}"
                ) from exc
            if event.event_id in self._events:
                raise DuplicateEventError(
                    f"Event with event_id '{event.event_id}' already exists"
                )
            self._events[event.event_id] = event.model_copy(deep=True)

    def _load_episodes(self) -> None:
        for line_number, decoded in _read_jsonl(self.episodes_path):
            try:
                episode = Episode.model_validate(decoded)
            except ValidationError as exc:
                raise StorageError(
                    f"Invalid episode record in {self.episodes_path} at line {line_number}"
                ) from exc
            missing = [
                event_id for event_id in episode.event_ids if event_id not in self._events
            ]
            if missing:
                raise UnknownEventReferenceError(
                    f"Episode references unknown event_ids: {missing}"
                )
            if episode.episode_id in self._episodes:
                raise DuplicateEpisodeError(
                    f"Episode with episode_id '{episode.episode_id}' already exists"
                )
            self._episodes[episode.episode_id] = episode.model_copy(deep=True)

    @staticmethod
    def _append_model(path: Path, model: Event | Episode) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = model.model_dump(mode="json")
        try:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(_json_line(data))
        except OSError as exc:
            raise StorageError(f"Could not append JSONL record to {path}") from exc
