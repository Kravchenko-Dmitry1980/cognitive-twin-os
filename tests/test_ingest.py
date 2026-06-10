"""Tests for ingest adapter."""

from __future__ import annotations

import json
from pathlib import Path

from cognitive_twin.ingest import IngestBatch, ManualJsonlIngestAdapter
from cognitive_twin.io import export_events_to_jsonl
from cognitive_twin.store import InMemoryEventStore
from cognitive_twin.trace_store import JsonlTraceStore
from cognitive_twin.traces import TraceStatus
from conftest import make_event


def _write_jsonl(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_valid_ingest_batch(tmp_path) -> None:
    events_path = tmp_path / "events.jsonl"
    export_events_to_jsonl(
        [make_event("evt_a"), make_event("evt_b", payload={"text": "second"})],
        events_path,
    )
    store = InMemoryEventStore()
    adapter = ManualJsonlIngestAdapter()
    result = adapter.ingest(
        IngestBatch(batch_id="batch_1", source_path=str(events_path)),
        store,
    )
    assert result.accepted_event_ids == ["evt_a", "evt_b"]
    assert result.rejected == []
    assert result.total_records == 2
    assert store.get_event("evt_a") is not None


def test_invalid_ingest_record(tmp_path) -> None:
    events_path = tmp_path / "events.jsonl"
    valid = make_event("evt_ok").model_dump(mode="json")
    _write_jsonl(
        events_path,
        [json.dumps(valid, separators=(",", ":")), '{"event_id": "bad"}'],
    )
    store = InMemoryEventStore()
    result = ManualJsonlIngestAdapter().ingest(
        IngestBatch(batch_id="batch_2", source_path=str(events_path)),
        store,
    )
    assert result.accepted_event_ids == ["evt_ok"]
    assert len(result.rejected) == 1
    assert result.rejected[0].line_number == 2
    assert result.rejected[0].event_id == "bad"


def test_partial_ingest_success_and_failure(tmp_path) -> None:
    events_path = tmp_path / "events.jsonl"
    export_events_to_jsonl([make_event("evt_dup")], events_path)
    store = InMemoryEventStore()
    store.append_event(make_event("evt_dup"))
    adapter = ManualJsonlIngestAdapter()
    result = adapter.ingest(
        IngestBatch(batch_id="batch_3", source_path=str(events_path)),
        store,
    )
    assert result.accepted_event_ids == []
    assert len(result.rejected) == 1
    assert "Duplicate" in result.rejected[0].reason


def test_ingest_writes_trace(tmp_path) -> None:
    events_path = tmp_path / "events.jsonl"
    export_events_to_jsonl([make_event("evt_trace")], events_path)
    store = InMemoryEventStore()
    trace_store = JsonlTraceStore(tmp_path / "traces.jsonl")
    ManualJsonlIngestAdapter().ingest(
        IngestBatch(batch_id="batch_4", source_path=str(events_path), actor_id="actor_1"),
        store,
        trace_store=trace_store,
    )
    traces = trace_store.list_traces()
    assert len(traces) == 1
    assert traces[0].operation == "ingest_batch"
    assert traces[0].status == TraceStatus.SUCCEEDED
    assert traces[0].output_refs == ["evt_trace"]
    assert traces[0].metadata["accepted_count"] == 1
