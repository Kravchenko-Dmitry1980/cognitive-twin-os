"""Contract tests: JSON Schema validation against event/episode contracts."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from conftest import make_event

ROOT = Path(__file__).resolve().parent.parent
EVENT_SCHEMA_PATH = ROOT / "contracts" / "events" / "event.schema.json"


def _load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _event_validator() -> Draft202012Validator:
    schema = _load_schema(EVENT_SCHEMA_PATH)
    return Draft202012Validator(schema)


def _valid_event_dict() -> dict:
    return make_event().model_dump(mode="json")


def test_valid_event_passes_schema() -> None:
    validator = _event_validator()
    errors = list(validator.iter_errors(_valid_event_dict()))
    assert errors == []


def test_event_without_source_fails_schema() -> None:
    data = _valid_event_dict()
    del data["source"]
    errors = list(_event_validator().iter_errors(data))
    assert any("source" in str(e.message) for e in errors)


def test_event_without_actor_fails_schema() -> None:
    data = _valid_event_dict()
    del data["actor"]
    errors = list(_event_validator().iter_errors(data))
    assert any("actor" in str(e.message) for e in errors)


def test_event_without_provenance_fails_schema() -> None:
    data = _valid_event_dict()
    del data["provenance"]
    errors = list(_event_validator().iter_errors(data))
    assert any("provenance" in str(e.message) for e in errors)


def test_event_without_governance_fails_schema() -> None:
    data = _valid_event_dict()
    del data["governance"]
    errors = list(_event_validator().iter_errors(data))
    assert any("governance" in str(e.message) for e in errors)


def test_invalid_sensitivity_fails_schema() -> None:
    data = _valid_event_dict()
    data["governance"]["sensitivity"] = "top_secret"
    errors = list(_event_validator().iter_errors(data))
    assert errors


def test_invalid_consent_basis_fails_schema() -> None:
    data = _valid_event_dict()
    data["governance"]["consent_basis"] = "stolen"
    errors = list(_event_validator().iter_errors(data))
    assert errors
