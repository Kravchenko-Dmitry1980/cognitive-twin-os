"""Tests for policy-aware episode retrieval."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from cognitive_twin.episodes import MemoryState
from cognitive_twin.errors import InvalidRetrievalRequestError, UnknownPolicyReferenceError
from cognitive_twin.events import ConsentBasis, Sensitivity
from cognitive_twin.policy_engine import PolicyDecisionValue, PolicyReasonCode
from cognitive_twin.policy_retrieval import PolicyAwareEpisodeRetriever
from cognitive_twin.retrieval import RetrievalFilter, RetrievalPolicyScope, RetrievalRequest
from cognitive_twin.store import InMemoryEventStore
from cognitive_twin.trace_store import JsonlTraceStore
from cognitive_twin.traces import TraceStatus
from conftest import make_episode, make_event


def _base_time() -> datetime:
    return datetime(2026, 6, 9, 12, 0, 0, tzinfo=UTC)


def _policy_store() -> InMemoryEventStore:
    store = InMemoryEventStore()
    base = _base_time()
    store.append_event(
        make_event("evt_pub", sensitivity=Sensitivity.PUBLIC, timestamp=base),
    )
    store.append_event(
        make_event(
            "evt_priv",
            sensitivity=Sensitivity.PRIVATE,
            timestamp=base.replace(hour=13),
        ),
    )
    store.append_event(
        make_event(
            "evt_imp",
            sensitivity=Sensitivity.PUBLIC,
            consent_basis=ConsentBasis.IMPORTED,
            timestamp=base.replace(hour=14),
        ),
    )
    store.append_episode(
        make_episode(["evt_pub"], "ep_allowed").model_copy(
            update={"created_at": base, "updated_at": base}
        )
    )
    store.append_episode(
        make_episode(["evt_priv"], "ep_denied_priv").model_copy(
            update={
                "created_at": base.replace(hour=13),
                "updated_at": base.replace(hour=13),
            }
        )
    )
    store.append_episode(
        make_episode(["evt_imp"], "ep_denied_imp").model_copy(
            update={
                "created_at": base.replace(hour=14),
                "updated_at": base.replace(hour=14),
            }
        )
    )
    return store


def test_structured_filters_still_work() -> None:
    store = _policy_store()
    store.append_episode(
        make_episode(["evt_pub"], "ep_curated").model_copy(
            update={
                "memory_state": MemoryState.CURATED,
                "created_at": _base_time().replace(hour=3),
                "updated_at": _base_time().replace(hour=3),
            }
        )
    )
    response = PolicyAwareEpisodeRetriever(store).retrieve(
        RetrievalRequest(
            request_id="req_filter",
            filters=RetrievalFilter(memory_state=MemoryState.CURATED),
        )
    )
    assert [item.episode_id for item in response.items] == ["ep_curated"]
    assert response.total_candidates == 1


def test_denied_episodes_are_not_returned() -> None:
    store = _policy_store()
    response = PolicyAwareEpisodeRetriever(store).retrieve(
        RetrievalRequest(request_id="req_deny")
    )
    assert [item.episode_id for item in response.items] == ["ep_allowed"]
    assert response.total_denied == 2
    assert response.total_allowed == 1


def test_allowed_episodes_are_returned() -> None:
    store = _policy_store()
    response = PolicyAwareEpisodeRetriever(store).retrieve(
        RetrievalRequest(
            request_id="req_allow",
            policy=RetrievalPolicyScope(
                allowed_sensitivities=list(Sensitivity),
                allow_imported=True,
            ),
        )
    )
    assert response.total_allowed == 3
    assert response.returned_count == 3


def test_policy_decisions_expose_reason_code_only() -> None:
    store = _policy_store()
    response = PolicyAwareEpisodeRetriever(store).retrieve(
        RetrievalRequest(request_id="req_decisions")
    )
    assert response.policy_decisions is not None
    denied = [
        decision
        for decision in response.policy_decisions
        if decision.decision == PolicyDecisionValue.DENY
    ]
    assert len(denied) == 2
    for decision in denied:
        dumped = decision.model_dump(mode="json")
        assert set(dumped.keys()) == {"episode_id", "decision", "reason_code"}
        assert dumped["reason_code"] in {
            PolicyReasonCode.ACCESS_DENIED.value,
            PolicyReasonCode.CONSENT_NOT_ALLOWED.value,
        }
        assert "private" not in str(dumped).lower()
        assert "sensitive" not in str(dumped).lower()
        assert "imported" not in str(dumped).lower()
        assert "evt_" not in dumped["reason_code"]


def test_include_policy_decisions_false_suppresses_decisions() -> None:
    store = _policy_store()
    response = PolicyAwareEpisodeRetriever(store).retrieve(
        RetrievalRequest(
            request_id="req_no_decisions",
            policy=RetrievalPolicyScope(include_policy_decisions=False),
        )
    )
    assert response.policy_decisions is None
    assert response.total_denied == 2
    assert [item.episode_id for item in response.items] == ["ep_allowed"]
    assert all(
        item.episode_id != "ep_denied_priv" and item.episode_id != "ep_denied_imp"
        for item in response.items
    )


def test_pagination_after_policy_filtering() -> None:
    store = InMemoryEventStore()
    base = _base_time()
    for index in range(5):
        event_id = f"evt_page_{index}"
        store.append_event(
            make_event(event_id, sensitivity=Sensitivity.PUBLIC, timestamp=base),
        )
        store.append_episode(
            make_episode([event_id], f"ep_page_{index}").model_copy(
                update={
                    "created_at": base.replace(minute=index),
                    "updated_at": base.replace(minute=index),
                }
            )
        )
    store.append_event(
        make_event("evt_denied", sensitivity=Sensitivity.PRIVATE, timestamp=base),
    )
    store.append_episode(
        make_episode(["evt_denied"], "ep_denied").model_copy(
            update={
                "created_at": base.replace(minute=10),
                "updated_at": base.replace(minute=10),
            }
        )
    )

    response = PolicyAwareEpisodeRetriever(store).retrieve(
        RetrievalRequest(request_id="req_page", limit=2, offset=1)
    )
    assert response.total_candidates == 6
    assert response.total_allowed == 5
    assert response.total_denied == 1
    assert response.returned_count == 2
    assert [item.episode_id for item in response.items] == ["ep_page_1", "ep_page_2"]


def test_limit_works() -> None:
    store = _policy_store()
    response = PolicyAwareEpisodeRetriever(store).retrieve(
        RetrievalRequest(
            request_id="req_limit",
            policy=RetrievalPolicyScope(
                allowed_sensitivities=list(Sensitivity),
                allow_imported=True,
            ),
            limit=1,
        )
    )
    assert response.returned_count == 1


def test_offset_works() -> None:
    store = InMemoryEventStore()
    base = _base_time()
    for index in range(4):
        event_id = f"evt_off_{index}"
        store.append_event(
            make_event(event_id, sensitivity=Sensitivity.PUBLIC, timestamp=base),
        )
        store.append_episode(
            make_episode([event_id], f"ep_off_{index}").model_copy(
                update={
                    "created_at": base.replace(minute=index),
                    "updated_at": base.replace(minute=index),
                }
            )
        )

    response = PolicyAwareEpisodeRetriever(store).retrieve(
        RetrievalRequest(request_id="req_offset", offset=2, limit=1)
    )
    assert response.returned_count == 1
    assert response.items[0].episode_id == "ep_off_2"


def test_invalid_limit_fails() -> None:
    with pytest.raises(ValidationError):
        RetrievalRequest(request_id="req_bad", limit=0)
    with pytest.raises(ValidationError):
        RetrievalRequest(request_id="req_bad", limit=101)

    store = _policy_store()
    with pytest.raises(InvalidRetrievalRequestError):
        PolicyAwareEpisodeRetriever(store).retrieve(
            RetrievalRequest.model_construct(request_id="req_bad", limit=0, offset=0)
        )


def test_invalid_offset_fails() -> None:
    with pytest.raises(ValidationError):
        RetrievalRequest(request_id="req_bad", offset=-1)

    store = _policy_store()
    with pytest.raises(InvalidRetrievalRequestError):
        PolicyAwareEpisodeRetriever(store).retrieve(
            RetrievalRequest.model_construct(
                request_id="req_bad",
                limit=50,
                offset=-1,
            )
        )


def test_deterministic_result_order() -> None:
    store = _policy_store()
    retriever = PolicyAwareEpisodeRetriever(store)
    first = retriever.retrieve(
        RetrievalRequest(
            request_id="req_order_1",
            policy=RetrievalPolicyScope(
                allowed_sensitivities=list(Sensitivity),
                allow_imported=True,
            ),
        )
    )
    second = retriever.retrieve(
        RetrievalRequest(
            request_id="req_order_2",
            policy=RetrievalPolicyScope(
                allowed_sensitivities=list(Sensitivity),
                allow_imported=True,
            ),
        )
    )
    assert [item.episode_id for item in first.items] == [
        item.episode_id for item in second.items
    ]


def test_trace_metadata_does_not_contain_entity_filter_value(tmp_path) -> None:
    store = _policy_store()
    trace_store = JsonlTraceStore(tmp_path / "traces.jsonl")
    PolicyAwareEpisodeRetriever(store, trace_store=trace_store).retrieve(
        RetrievalRequest(
            request_id="req_entity_trace",
            filters=RetrievalFilter(entity="secret_entity_name"),
        )
    )
    metadata = trace_store.list_traces()[0].metadata
    assert "entity" in metadata["filter_keys"]
    assert "secret_entity_name" not in str(metadata)


def test_trace_metadata_does_not_contain_goal_filter_value(tmp_path) -> None:
    store = _policy_store()
    trace_store = JsonlTraceStore(tmp_path / "traces.jsonl")
    PolicyAwareEpisodeRetriever(store, trace_store=trace_store).retrieve(
        RetrievalRequest(
            request_id="req_goal_trace",
            filters=RetrievalFilter(goal="secret_goal_name"),
        )
    )
    metadata = trace_store.list_traces()[0].metadata
    assert "goal" in metadata["filter_keys"]
    assert "secret_goal_name" not in str(metadata)


def test_trace_metadata_does_not_contain_event_payload_or_summary(tmp_path) -> None:
    store = _policy_store()
    trace_store = JsonlTraceStore(tmp_path / "traces.jsonl")
    PolicyAwareEpisodeRetriever(store, trace_store=trace_store).retrieve(
        RetrievalRequest(request_id="req_payload_trace")
    )
    metadata = trace_store.list_traces()[0].metadata
    assert "hello" not in str(metadata).lower()
    assert "test episode" not in str(metadata).lower()
    assert "filters" not in metadata


def test_trace_metadata_contains_filter_keys_not_values(tmp_path) -> None:
    store = _policy_store()
    trace_store = JsonlTraceStore(tmp_path / "traces.jsonl")
    PolicyAwareEpisodeRetriever(store, trace_store=trace_store).retrieve(
        RetrievalRequest(
            request_id="req_keys",
            filters=RetrievalFilter(entity="alice", goal="plan"),
        )
    )
    metadata = trace_store.list_traces()[0].metadata
    assert metadata["filter_keys"] == ["entity", "goal"]
    assert "alice" not in str(metadata)
    assert "plan" not in str(metadata)


def test_trace_written_for_successful_policy_retrieval(tmp_path) -> None:
    store = _policy_store()
    trace_store = JsonlTraceStore(tmp_path / "traces.jsonl")
    response = PolicyAwareEpisodeRetriever(store, trace_store=trace_store).retrieve(
        RetrievalRequest(request_id="req_trace")
    )
    traces = trace_store.list_traces()
    assert len(traces) == 1
    trace = traces[0]
    assert trace.operation == "policy_retrieve_episodes"
    assert trace.status == TraceStatus.SUCCEEDED
    assert trace.policy_result == {
        "total_candidates": 3,
        "total_allowed": 1,
        "total_denied": 2,
    }
    assert trace.metadata["offset"] == 0
    assert trace.metadata["limit"] == 50
    assert trace.metadata["operation_version"] == "0.1.4"
    assert trace.output_refs == ["ep_allowed"]
    assert "ep_denied_priv" not in trace.output_refs
    assert response.trace_id == trace.trace_id


def test_trace_written_for_failed_retrieval(tmp_path) -> None:
    episode_store = InMemoryEventStore()
    episode_store.append_event(make_event("evt_only"))
    episode_store.append_event(make_event("evt_missing"))
    episode_store.append_episode(make_episode(["evt_only", "evt_missing"], "ep_bad"))

    event_store = InMemoryEventStore()
    event_store.append_event(make_event("evt_only"))

    trace_store = JsonlTraceStore(tmp_path / "traces.jsonl")
    retriever = PolicyAwareEpisodeRetriever(
        event_store,
        episode_store=episode_store,
        trace_store=trace_store,
    )
    with pytest.raises(UnknownPolicyReferenceError):
        retriever.retrieve(RetrievalRequest(request_id="req_fail"))
    traces = trace_store.list_traces()
    assert len(traces) == 1
    assert traces[0].operation == "policy_retrieve_episodes"
    assert traces[0].status == TraceStatus.FAILED
    assert "filters" not in traces[0].metadata
    assert "evt_missing" not in str(traces[0].metadata)
