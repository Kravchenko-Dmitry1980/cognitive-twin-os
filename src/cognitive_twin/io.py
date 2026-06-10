"""JSONL import/export utilities without CLI dependencies."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from cognitive_twin.episodes import Episode
from cognitive_twin.errors import StorageError
from cognitive_twin.events import Event


def export_events_to_jsonl(events: Iterable[Event], path: str | Path) -> None:
    _export_models_to_jsonl(events, Path(path))


def import_events_from_jsonl(path: str | Path) -> list[Event]:
    return _import_models_from_jsonl(Path(path), Event)


def export_episodes_to_jsonl(episodes: Iterable[Episode], path: str | Path) -> None:
    _export_models_to_jsonl(episodes, Path(path))


def import_episodes_from_jsonl(path: str | Path) -> list[Episode]:
    return _import_models_from_jsonl(Path(path), Episode)


def _json_line(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def _export_models_to_jsonl(models: Iterable[BaseModel], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", encoding="utf-8") as handle:
            for model in models:
                handle.write(_json_line(model.model_dump(mode="json")))
    except OSError as exc:
        raise StorageError(f"Could not export JSONL records to {path}") from exc


def _import_models_from_jsonl[ModelT: BaseModel](
    path: Path, model_type: type[ModelT]
) -> list[ModelT]:
    if not path.exists():
        raise StorageError(f"JSONL file does not exist: {path}")

    imported: list[ModelT] = []
    try:
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
                try:
                    imported.append(model_type.model_validate(decoded))
                except ValidationError as exc:
                    raise StorageError(
                        f"Invalid {model_type.__name__} record in {path} at line {line_number}"
                    ) from exc
    except OSError as exc:
        raise StorageError(f"Could not import JSONL records from {path}") from exc
    return imported
