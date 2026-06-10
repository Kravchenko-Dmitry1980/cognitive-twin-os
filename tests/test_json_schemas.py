"""Contract tests: JSON Schema validation against event/episode contracts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import Draft202012Validator

from cognitive_twin.episode_builder import (
    EpisodeBuildRequest,
    EpisodeBuildResult,
    EpisodeBuildStatus,
)
from cognitive_twin.ingest import IngestBatch, IngestError, IngestResult
from cognitive_twin.policy import PolicyRequest, PolicyResponse
from cognitive_twin.retrieval import RetrievalFilter, RetrievalRequest, RetrievalResult
from cognitive_twin.traces import OperationTrace, TraceStatus
from conftest import make_episode, make_event

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_ROOT = ROOT / "contracts"
SCHEMA_PATHS = {
    path.relative_to(CONTRACTS_ROOT).as_posix(): path
    for path in sorted(CONTRACTS_ROOT.rglob("*.schema.json"))
}


def _load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator(schema_name: str) -> Draft202012Validator:
    schema = _load_schema(SCHEMA_PATHS[schema_name])
    return Draft202012Validator(schema)


def _assert_valid(schema_name: str, data: dict) -> None:
    errors = list(_validator(schema_name).iter_errors(data))
    assert errors == []


def _valid_event_dict() -> dict:
    return make_event().model_dump(mode="json")


def _valid_trace_dict() -> dict:
    return OperationTrace(
        trace_id="trace_1",
        operation="append_event",
        timestamp=datetime(2026, 6, 10, 12, 0, 0, tzinfo=UTC),
        actor_id="actor_user01",
        input_refs=["evt_1"],
        output_refs=["ep_1"],
        policy_result={"allowed": True},
        status=TraceStatus.SUCCEEDED,
        metadata={"store": "jsonl"},
    ).model_dump(mode="json")


def test_all_contract_schemas_are_covered_and_valid() -> None:
    expected = {
        "decision/decision_request.schema.json",
        "decision/decision_response.schema.json",
        "events/episode.schema.json",
        "events/event.schema.json",
        "ingest/ingest_batch.schema.json",
        "ingest/ingest_result.schema.json",
        "memory/episode_build_request.schema.json",
        "memory/episode_build_result.schema.json",
        "memory/retrieval_request.schema.json",
        "memory/retrieval_response.schema.json",
        "policy/policy_request.schema.json",
        "policy/policy_response.schema.json",
        "traces/operation_trace.schema.json",
    }
    assert set(SCHEMA_PATHS) == expected
    for path in SCHEMA_PATHS.values():
        Draft202012Validator.check_schema(_load_schema(path))


def test_valid_event_passes_schema() -> None:
    _assert_valid("events/event.schema.json", _valid_event_dict())


def test_event_without_source_fails_schema() -> None:
    data = _valid_event_dict()
    del data["source"]
    errors = list(_validator("events/event.schema.json").iter_errors(data))
    assert any("source" in str(e.message) for e in errors)


def test_event_without_actor_fails_schema() -> None:
    data = _valid_event_dict()
    del data["actor"]
    errors = list(_validator("events/event.schema.json").iter_errors(data))
    assert any("actor" in str(e.message) for e in errors)


def test_event_without_provenance_fails_schema() -> None:
    data = _valid_event_dict()
    del data["provenance"]
    errors = list(_validator("events/event.schema.json").iter_errors(data))
    assert any("provenance" in str(e.message) for e in errors)


def test_event_without_governance_fails_schema() -> None:
    data = _valid_event_dict()
    del data["governance"]
    errors = list(_validator("events/event.schema.json").iter_errors(data))
    assert any("governance" in str(e.message) for e in errors)


def test_invalid_sensitivity_fails_schema() -> None:
    data = _valid_event_dict()
    data["governance"]["sensitivity"] = "top_secret"
    errors = list(_validator("events/event.schema.json").iter_errors(data))
    assert errors


def test_invalid_consent_basis_fails_schema() -> None:
    data = _valid_event_dict()
    data["governance"]["consent_basis"] = "stolen"
    errors = list(_validator("events/event.schema.json").iter_errors(data))
    assert errors


def _valid_episode_dict() -> dict:
    return make_episode(["evt_1"]).model_dump(mode="json")


def test_valid_episode_passes_schema() -> None:
    _assert_valid("events/episode.schema.json", _valid_episode_dict())


def test_episode_without_event_ids_fails_schema() -> None:
    data = _valid_episode_dict()
    del data["event_ids"]
    errors = list(_validator("events/episode.schema.json").iter_errors(data))
    assert any("event_ids" in str(e.message) for e in errors)


def test_episode_invalid_memory_state_fails_schema() -> None:
    data = _valid_episode_dict()
    data["memory_state"] = "forgotten"
    errors = list(_validator("events/episode.schema.json").iter_errors(data))
    assert errors


def test_valid_trace_passes_schema() -> None:
    _assert_valid("traces/operation_trace.schema.json", _valid_trace_dict())


def test_invalid_trace_status_fails_schema() -> None:
    data = _valid_trace_dict()
    data["status"] = "done"
    errors = list(_validator("traces/operation_trace.schema.json").iter_errors(data))
    assert errors


def test_valid_ingest_contracts_pass_schema() -> None:
    batch = IngestBatch(
        batch_id="batch_1",
        source_path="fixtures/events.jsonl",
        actor_id="actor_user01",
    )
    result = IngestResult(
        batch_id="batch_1",
        accepted_event_ids=["evt_1"],
        rejected=[
            IngestError(
                line_number=2,
                reason="Event validation failed",
                event_id="evt_bad",
            )
        ],
        total_records=2,
    )
    _assert_valid("ingest/ingest_batch.schema.json", batch.model_dump(mode="json"))
    _assert_valid("ingest/ingest_result.schema.json", result.model_dump(mode="json"))


def test_valid_episode_build_contracts_pass_schema() -> None:
    request = EpisodeBuildRequest(
        request_id="req_1",
        episode_id="ep_1",
        event_ids=["evt_1"],
        episode_type="conversation",
        summary="Caller supplied summary",
        salience=0.8,
    )
    result = EpisodeBuildResult(
        request_id="req_1",
        episode_id="ep_1",
        event_ids=["evt_1"],
        status=EpisodeBuildStatus.SUCCEEDED,
    )
    _assert_valid(
        "memory/episode_build_request.schema.json",
        request.model_dump(mode="json"),
    )
    _assert_valid(
        "memory/episode_build_result.schema.json",
        result.model_dump(mode="json"),
    )


def test_valid_retrieval_contracts_pass_schema() -> None:
    request = RetrievalRequest(
        request_id="req_1",
        filters=RetrievalFilter(memory_state="raw", min_salience=0.5),
        actor_id="actor_user01",
    )
    result = RetrievalResult(
        request_id="req_1",
        episode_ids=["ep_1"],
        episodes=[],
    )
    _assert_valid(
        "memory/retrieval_request.schema.json",
        request.model_dump(mode="json"),
    )
    _assert_valid(
        "memory/retrieval_response.schema.json",
        result.model_dump(mode="json"),
    )


def test_valid_policy_contracts_pass_schema() -> None:
    request = PolicyRequest(
        request_id="req_1",
        actor_id="actor_user01",
        action="read",
        resource_type="episode",
        resource_id="ep_1",
    )
    response = PolicyResponse(
        request_id="req_1",
        decision={"allowed": True, "reason": "structural check only"},
    )
    _assert_valid("policy/policy_request.schema.json", request.model_dump(mode="json"))
    _assert_valid("policy/policy_response.schema.json", response.model_dump(mode="json"))


def test_valid_decision_stub_contracts_pass_schema() -> None:
    _assert_valid(
        "decision/decision_request.schema.json",
        {
            "request_id": "req_1",
            "actor_id": "actor_user01",
            "decision_type": "prioritize",
            "context_event_ids": ["evt_1"],
            "options": ["option_a", "option_b"],
            "constraints": {"deadline": "soon"},
        },
    )
    _assert_valid(
        "decision/decision_response.schema.json",
        {
            "request_id": "req_1",
            "recommendation": "option_a",
            "evidence_event_ids": ["evt_1"],
            "confidence": 0.75,
            "rationale": "Evidence-linked placeholder response.",
            "alternatives": ["option_b"],
        },
    )
