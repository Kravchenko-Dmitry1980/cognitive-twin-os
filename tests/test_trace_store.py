"""Tests for JSONL trace store."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from cognitive_twin.errors import DuplicateTraceError, StorageError
from cognitive_twin.trace_store import JsonlTraceStore
from cognitive_twin.traces import OperationTrace, TraceStatus


def make_trace(trace_id: str = "trace_1") -> OperationTrace:
    return OperationTrace(
        trace_id=trace_id,
        operation="append_event",
        timestamp=datetime(2026, 6, 10, 12, 0, 0, tzinfo=UTC),
        actor_id="actor_user01",
        input_refs=["evt_1"],
        output_refs=["ep_1"],
        policy_result={"allowed": True},
        status=TraceStatus.SUCCEEDED,
        metadata={"store": "jsonl"},
    )


def test_trace_writer_appends_and_reloads_traces(tmp_path) -> None:
    traces_path = tmp_path / "traces.jsonl"
    store = JsonlTraceStore(traces_path)
    trace = make_trace("trace_1")

    store.append_trace(trace)

    reloaded = JsonlTraceStore(traces_path)
    assert reloaded.get_trace("trace_1") == trace
    assert [item.trace_id for item in reloaded.list_traces()] == ["trace_1"]


def test_trace_writer_duplicate_trace_id_fails(tmp_path) -> None:
    store = JsonlTraceStore(tmp_path / "traces.jsonl")
    store.append_trace(make_trace("trace_dup"))

    with pytest.raises(DuplicateTraceError, match="trace_dup"):
        store.append_trace(make_trace("trace_dup"))


def test_trace_writer_duplicate_trace_id_fails_on_reload(tmp_path) -> None:
    traces_path = tmp_path / "traces.jsonl"
    first = make_trace("trace_dup").model_dump_json()
    second = make_trace("trace_dup").model_dump_json()
    traces_path.write_text(f"{first}\n{second}\n", encoding="utf-8")

    with pytest.raises(DuplicateTraceError, match="trace_dup"):
        JsonlTraceStore(traces_path)


def test_trace_writer_corrupted_jsonl_fails_clearly(tmp_path) -> None:
    traces_path = tmp_path / "traces.jsonl"
    traces_path.write_text("{not-json}\n", encoding="utf-8")

    with pytest.raises(StorageError, match="Invalid JSONL trace record"):
        JsonlTraceStore(traces_path)


def test_trace_writer_non_object_jsonl_fails_clearly(tmp_path) -> None:
    traces_path = tmp_path / "traces.jsonl"
    traces_path.write_text("[]\n", encoding="utf-8")

    with pytest.raises(StorageError, match="expected object"):
        JsonlTraceStore(traces_path)


def test_trace_writer_snapshot_semantics(tmp_path) -> None:
    store = JsonlTraceStore(tmp_path / "traces.jsonl")
    trace = make_trace("trace_snapshot")
    store.append_trace(trace)

    trace.metadata["store"] = "mutated"
    from_get = store.get_trace("trace_snapshot")
    assert from_get is not None
    from_get.metadata["store"] = "mutated_again"
    from_list = store.list_traces()
    from_list[0].metadata["store"] = "mutated_third"

    assert store.get_trace("trace_snapshot").metadata["store"] == "jsonl"
