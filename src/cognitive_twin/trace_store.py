"""JSONL trace writer for operation traces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from cognitive_twin.errors import DuplicateTraceError, StorageError
from cognitive_twin.traces import OperationTrace


def _trace_json_line(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


class JsonlTraceStore:
    """
    Append-only JSONL trace store for Phase 1.1 operation observability.

    Traces are operation logs, not memory facts. Snapshot semantics apply:
    append deep-copies input; reads return deep copies. List order follows
    JSONL append order.
    """

    def __init__(self, traces_path: str | Path = "local_data/traces.jsonl") -> None:
        self.traces_path = Path(traces_path)
        self._traces: dict[str, OperationTrace] = {}
        self._load_traces()

    def append_trace(self, trace: OperationTrace) -> None:
        if trace.trace_id in self._traces:
            raise DuplicateTraceError(
                f"Trace with trace_id '{trace.trace_id}' already exists"
            )
        stored = trace.model_copy(deep=True)
        self.traces_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.traces_path.open("a", encoding="utf-8") as handle:
                handle.write(_trace_json_line(stored.model_dump(mode="json")))
        except OSError as exc:
            raise StorageError(f"Could not append JSONL trace to {self.traces_path}") from exc
        self._traces[stored.trace_id] = stored

    def get_trace(self, trace_id: str) -> OperationTrace | None:
        trace = self._traces.get(trace_id)
        return trace.model_copy(deep=True) if trace is not None else None

    def list_traces(self) -> list[OperationTrace]:
        return [trace.model_copy(deep=True) for trace in self._traces.values()]

    def _load_traces(self) -> None:
        if not self.traces_path.exists():
            return
        with self.traces_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    decoded = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise StorageError(
                        "Invalid JSONL trace record "
                        f"in {self.traces_path} at line {line_number}: {exc.msg}"
                    ) from exc
                if not isinstance(decoded, dict):
                    raise StorageError(
                        "Invalid JSONL trace record "
                        f"in {self.traces_path} at line {line_number}: expected object"
                    )
                try:
                    trace = OperationTrace.model_validate(decoded)
                except ValidationError as exc:
                    raise StorageError(
                        f"Invalid trace record in {self.traces_path} at line {line_number}"
                    ) from exc
                if trace.trace_id in self._traces:
                    raise DuplicateTraceError(
                        f"Trace with trace_id '{trace.trace_id}' already exists"
                    )
                self._traces[trace.trace_id] = trace.model_copy(deep=True)
