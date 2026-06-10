"""Helpers for writing minimal operation traces."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Protocol

from cognitive_twin.ids import new_id
from cognitive_twin.traces import OperationTrace, TraceStatus

if TYPE_CHECKING:
    pass


class TraceWriter(Protocol):
    """Contract for append-only trace persistence."""

    def append_trace(self, trace: OperationTrace) -> None: ...


def record_operation(
    trace_store: TraceWriter | None,
    *,
    operation: str,
    status: TraceStatus,
    input_refs: list[str] | None = None,
    output_refs: list[str] | None = None,
    actor_id: str | None = None,
    error: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> OperationTrace:
    """
    Build and optionally persist an operation trace.

    Metadata should stay minimal: counts, ids, and filter keys only.
    """
    trace = OperationTrace(
        trace_id=new_id("trace"),
        operation=operation,
        timestamp=datetime.now(UTC),
        actor_id=actor_id,
        input_refs=input_refs or [],
        output_refs=output_refs or [],
        status=status,
        error=error,
        metadata=metadata or {},
    )
    if trace_store is not None:
        trace_store.append_trace(trace)
    return trace
