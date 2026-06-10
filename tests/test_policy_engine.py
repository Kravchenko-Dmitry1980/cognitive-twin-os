"""Tests for deterministic policy gate."""

from __future__ import annotations

import pytest

from cognitive_twin.errors import UnknownPolicyReferenceError
from cognitive_twin.events import ConsentBasis, Sensitivity
from cognitive_twin.policy_engine import (
    PolicyDecisionValue,
    PolicyEvaluationContext,
    PolicyGate,
    PolicyReasonCode,
)
from cognitive_twin.store import InMemoryEventStore
from conftest import make_episode, make_event


def _store_with_events(*events) -> InMemoryEventStore:
    store = InMemoryEventStore()
    for event in events:
        store.append_event(event)
    return store


def test_public_episode_allowed_by_default() -> None:
    store = _store_with_events(
        make_event("evt_pub", sensitivity=Sensitivity.PUBLIC),
    )
    episode = make_episode(["evt_pub"], "ep_pub")
    result = PolicyGate().evaluate_episode(
        episode, store, PolicyEvaluationContext()
    )
    assert result.decision == PolicyDecisionValue.ALLOW
    assert result.reason_code == PolicyReasonCode.ALLOWED
    assert "denied_reason" not in result.model_dump()


def test_internal_episode_allowed_by_default() -> None:
    store = _store_with_events(make_event("evt_int", sensitivity=Sensitivity.INTERNAL))
    episode = make_episode(["evt_int"], "ep_int")
    result = PolicyGate().evaluate_episode(
        episode, store, PolicyEvaluationContext()
    )
    assert result.decision == PolicyDecisionValue.ALLOW


def test_private_episode_denied_by_default() -> None:
    store = _store_with_events(
        make_event("evt_priv", sensitivity=Sensitivity.PRIVATE),
    )
    episode = make_episode(["evt_priv"], "ep_priv")
    result = PolicyGate().evaluate_episode(
        episode, store, PolicyEvaluationContext()
    )
    assert result.decision == PolicyDecisionValue.DENY
    assert result.reason_code == PolicyReasonCode.ACCESS_DENIED


def test_sensitive_episode_denied_by_default() -> None:
    store = _store_with_events(
        make_event("evt_sens", sensitivity=Sensitivity.SENSITIVE),
    )
    episode = make_episode(["evt_sens"], "ep_sens")
    result = PolicyGate().evaluate_episode(
        episode, store, PolicyEvaluationContext()
    )
    assert result.decision == PolicyDecisionValue.DENY
    assert result.reason_code == PolicyReasonCode.ACCESS_DENIED


def test_private_allowed_when_in_allowed_sensitivities() -> None:
    store = _store_with_events(
        make_event("evt_priv", sensitivity=Sensitivity.PRIVATE),
    )
    episode = make_episode(["evt_priv"], "ep_priv")
    context = PolicyEvaluationContext(
        allowed_sensitivities=[
            Sensitivity.PUBLIC,
            Sensitivity.INTERNAL,
            Sensitivity.PRIVATE,
        ]
    )
    result = PolicyGate().evaluate_episode(episode, store, context)
    assert result.decision == PolicyDecisionValue.ALLOW


def test_sensitive_allowed_when_in_allowed_sensitivities() -> None:
    store = _store_with_events(
        make_event("evt_sens", sensitivity=Sensitivity.SENSITIVE),
    )
    episode = make_episode(["evt_sens"], "ep_sens")
    context = PolicyEvaluationContext(
        allowed_sensitivities=list(Sensitivity),
    )
    result = PolicyGate().evaluate_episode(episode, store, context)
    assert result.decision == PolicyDecisionValue.ALLOW


def test_imported_consent_denied_by_default() -> None:
    store = _store_with_events(
        make_event(
            "evt_imp",
            sensitivity=Sensitivity.PUBLIC,
            consent_basis=ConsentBasis.IMPORTED,
        ),
    )
    episode = make_episode(["evt_imp"], "ep_imp")
    result = PolicyGate().evaluate_episode(
        episode, store, PolicyEvaluationContext()
    )
    assert result.decision == PolicyDecisionValue.DENY
    assert result.reason_code == PolicyReasonCode.CONSENT_NOT_ALLOWED


def test_imported_consent_allowed_when_allow_imported_true() -> None:
    store = _store_with_events(
        make_event(
            "evt_imp",
            sensitivity=Sensitivity.PUBLIC,
            consent_basis=ConsentBasis.IMPORTED,
        ),
    )
    episode = make_episode(["evt_imp"], "ep_imp")
    context = PolicyEvaluationContext(allow_imported=True)
    result = PolicyGate().evaluate_episode(episode, store, context)
    assert result.decision == PolicyDecisionValue.ALLOW


def test_mixed_sensitivity_episode_uses_most_restrictive_event() -> None:
    store = _store_with_events(
        make_event("evt_pub", sensitivity=Sensitivity.PUBLIC),
        make_event("evt_priv", sensitivity=Sensitivity.PRIVATE),
    )
    episode = make_episode(["evt_pub", "evt_priv"], "ep_mixed")
    result = PolicyGate().evaluate_episode(
        episode, store, PolicyEvaluationContext()
    )
    assert result.decision == PolicyDecisionValue.DENY
    assert result.reason_code == PolicyReasonCode.ACCESS_DENIED


def test_unknown_event_id_fails_clearly() -> None:
    store = _store_with_events(make_event("evt_known"))
    episode = make_episode(["evt_known", "evt_missing"], "ep_bad")
    with pytest.raises(UnknownPolicyReferenceError, match="evt_missing"):
        PolicyGate().evaluate_episode(
            episode, store, PolicyEvaluationContext()
        )


def test_policy_decision_is_deterministic() -> None:
    store = _store_with_events(
        make_event("evt_a", sensitivity=Sensitivity.PRIVATE),
    )
    episode = make_episode(["evt_a"], "ep_a")
    gate = PolicyGate()
    context = PolicyEvaluationContext()
    first = gate.evaluate_episode(episode, store, context)
    second = gate.evaluate_episode(episode, store, context)
    assert first == second


def test_external_policy_decision_exposes_reason_code_only() -> None:
    store = _store_with_events(
        make_event("evt_priv", sensitivity=Sensitivity.PRIVATE),
    )
    episode = make_episode(["evt_priv"], "ep_priv")
    result = PolicyGate().evaluate_episode(
        episode, store, PolicyEvaluationContext()
    )
    dumped = result.model_dump(mode="json")
    assert set(dumped.keys()) == {"episode_id", "decision", "reason_code"}
    assert "private" not in str(dumped).lower()
    assert "evt_priv" not in dumped.get("reason_code", "")
