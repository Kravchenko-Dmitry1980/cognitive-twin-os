"""Ingest adapter contract and JSONL implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field, ValidationError

from cognitive_twin.errors import DuplicateEventError
from cognitive_twin.events import Event
from cognitive_twin.operation_trace import TraceWriter, record_operation
from cognitive_twin.store import EventRepository
from cognitive_twin.traces import TraceStatus


class IngestError(BaseModel):
    """Rejected ingest record with a clear reason."""

    line_number: int = Field(ge=1)
    reason: str = Field(min_length=1)
    event_id: str | None = None


class IngestBatch(BaseModel):
    """Batch descriptor for a file-based ingest operation."""

    batch_id: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    actor_id: str | None = None


class IngestResult(BaseModel):
    """Outcome of an ingest batch: accepted ids and rejected records."""

    batch_id: str = Field(min_length=1)
    accepted_event_ids: list[str] = Field(default_factory=list)
    rejected: list[IngestError] = Field(default_factory=list)
    total_records: int = Field(ge=0)


class IngestAdapter(Protocol):
    """Contract for validating and persisting ingested events."""

    def ingest(
        self,
        batch: IngestBatch,
        store: EventRepository,
        trace_store: TraceWriter | None = None,
    ) -> IngestResult: ...


class ManualJsonlIngestAdapter:
    """
    Read events from JSONL, validate as Event models, append accepted records.

    Validation only — no interpretation, consolidation, identity updates,
    external services, or LLM calls.
    """

    def ingest(
        self,
        batch: IngestBatch,
        store: EventRepository,
        trace_store: TraceWriter | None = None,
    ) -> IngestResult:
        path = Path(batch.source_path)
        accepted: list[str] = []
        rejected: list[IngestError] = []
        total_records = 0

        if not path.exists():
            reason = f"Source file does not exist: {path}"
            record_operation(
                trace_store,
                operation="ingest_batch",
                status=TraceStatus.FAILED,
                input_refs=[batch.batch_id, str(path)],
                actor_id=batch.actor_id,
                error=reason,
                metadata={
                    "batch_id": batch.batch_id,
                    "accepted_count": 0,
                    "rejected_count": 0,
                },
            )
            return IngestResult(
                batch_id=batch.batch_id,
                accepted_event_ids=[],
                rejected=[],
                total_records=0,
            )

        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                total_records += 1
                try:
                    decoded = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    rejected.append(
                        IngestError(
                            line_number=line_number,
                            reason=f"Invalid JSON: {exc.msg}",
                        )
                    )
                    continue

                try:
                    event = Event.model_validate(decoded)
                except ValidationError:
                    event_id = decoded.get("event_id") if isinstance(decoded, dict) else None
                    rejected.append(
                        IngestError(
                            line_number=line_number,
                            reason="Event validation failed",
                            event_id=event_id if isinstance(event_id, str) else None,
                        )
                    )
                    continue

                try:
                    store.append_event(event)
                except DuplicateEventError:
                    rejected.append(
                        IngestError(
                            line_number=line_number,
                            reason=f"Duplicate event_id: {event.event_id}",
                            event_id=event.event_id,
                        )
                    )
                    continue

                accepted.append(event.event_id)

        if total_records == 0:
            status = TraceStatus.FAILED
        elif rejected and not accepted:
            status = TraceStatus.FAILED
        else:
            status = TraceStatus.SUCCEEDED

        record_operation(
            trace_store,
            operation="ingest_batch",
            status=status,
            input_refs=[batch.batch_id, str(path)],
            output_refs=accepted,
            actor_id=batch.actor_id,
            metadata={
                "batch_id": batch.batch_id,
                "accepted_count": len(accepted),
                "rejected_count": len(rejected),
                "total_records": total_records,
            },
        )

        return IngestResult(
            batch_id=batch.batch_id,
            accepted_event_ids=accepted,
            rejected=rejected,
            total_records=total_records,
        )
