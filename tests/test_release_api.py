"""Regression tests for Phase 1.3 release-facing API boundaries."""

from __future__ import annotations

import cognitive_twin
from cognitive_twin.events import ConsentBasis, Sensitivity
from cognitive_twin.policy_engine import PolicyDecisionValue, PolicyReasonCode
from cognitive_twin.policy_retrieval import PolicyAwareEpisodeRetriever
from cognitive_twin.retrieval import RetrievalRequest
from cognitive_twin.store import InMemoryEventStore
from conftest import make_episode, make_event


def test_package_root_does_not_export_policy_less_retriever() -> None:
    assert "StructuredEpisodeRetriever" not in cognitive_twin.__all__
    assert not hasattr(cognitive_twin, "StructuredEpisodeRetriever")
    assert "RetrievalResult" not in cognitive_twin.__all__
    assert not hasattr(cognitive_twin, "RetrievalResult")


def test_package_root_exports_policy_aware_retriever() -> None:
    assert "PolicyAwareEpisodeRetriever" in cognitive_twin.__all__
    assert hasattr(cognitive_twin, "PolicyAwareEpisodeRetriever")


def test_release_retrieval_denies_private_episodes_by_default() -> None:
    store = InMemoryEventStore()
    store.append_event(make_event("evt_pub", sensitivity=Sensitivity.PUBLIC))
    store.append_event(make_event("evt_priv", sensitivity=Sensitivity.PRIVATE))
    store.append_episode(make_episode(["evt_pub"], "ep_allowed"))
    store.append_episode(make_episode(["evt_priv"], "ep_denied"))

    response = PolicyAwareEpisodeRetriever(store).retrieve(
        RetrievalRequest(request_id="req_release")
    )
    assert [item.episode_id for item in response.items] == ["ep_allowed"]
    assert response.total_denied == 1
    denied = [
        decision
        for decision in (response.policy_decisions or [])
        if decision.decision == PolicyDecisionValue.DENY
    ]
    assert len(denied) == 1
    assert denied[0].reason_code == PolicyReasonCode.ACCESS_DENIED
    assert not hasattr(denied[0], "denied_reason") or "denied_reason" not in (
        denied[0].model_fields
    )


def test_release_retrieval_denies_imported_consent_by_default() -> None:
    store = InMemoryEventStore()
    store.append_event(
        make_event(
            "evt_imp",
            sensitivity=Sensitivity.PUBLIC,
            consent_basis=ConsentBasis.IMPORTED,
        )
    )
    store.append_episode(make_episode(["evt_imp"], "ep_denied"))

    response = PolicyAwareEpisodeRetriever(store).retrieve(
        RetrievalRequest(request_id="req_imported")
    )
    assert response.items == []
    assert response.total_denied == 1
    denied = response.policy_decisions or []
    assert denied[0].reason_code == PolicyReasonCode.CONSENT_NOT_ALLOWED
