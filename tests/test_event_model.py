"""Tests for Event Pydantic model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from cognitive_twin.events import Event, EventType, Sensitivity
from conftest import make_event


def test_valid_event_creation() -> None:
    event = make_event()
    assert event.event_id == "evt_test001"
    assert event.event_type == EventType.MESSAGE
    assert event.governance.sensitivity == Sensitivity.INTERNAL


def test_event_requires_source() -> None:
    event = make_event()
    data = event.model_dump(mode="json")
    del data["source"]
    with pytest.raises(ValidationError):
        Event.model_validate(data)


def test_event_requires_actor() -> None:
    event = make_event()
    data = event.model_dump(mode="json")
    del data["actor"]
    with pytest.raises(ValidationError):
        Event.model_validate(data)


def test_event_requires_provenance() -> None:
    event = make_event()
    data = event.model_dump(mode="json")
    del data["provenance"]
    with pytest.raises(ValidationError):
        Event.model_validate(data)


def test_event_requires_governance() -> None:
    event = make_event()
    data = event.model_dump(mode="json")
    del data["governance"]
    with pytest.raises(ValidationError):
        Event.model_validate(data)


def test_invalid_sensitivity_rejected() -> None:
    event = make_event()
    data = event.model_dump(mode="json")
    data["governance"]["sensitivity"] = "top_secret"
    with pytest.raises(ValidationError):
        Event.model_validate(data)


def test_invalid_consent_basis_rejected() -> None:
    event = make_event()
    data = event.model_dump(mode="json")
    data["governance"]["consent_basis"] = "stolen"
    with pytest.raises(ValidationError):
        Event.model_validate(data)


def test_invalid_event_type_rejected() -> None:
    event = make_event()
    data = event.model_dump(mode="json")
    data["event_type"] = "unknown_type"
    with pytest.raises(ValidationError):
        Event.model_validate(data)
