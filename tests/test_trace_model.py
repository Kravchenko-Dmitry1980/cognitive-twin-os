"""Tests for operation trace model."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

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


def test_valid_trace_passes_pydantic_validation() -> None:
    trace = make_trace()
    assert trace.trace_id == "trace_1"
    assert trace.status == TraceStatus.SUCCEEDED


def test_invalid_trace_status_fails() -> None:
    data = make_trace().model_dump(mode="json")
    data["status"] = "done"

    with pytest.raises(ValidationError):
        OperationTrace.model_validate(data)
