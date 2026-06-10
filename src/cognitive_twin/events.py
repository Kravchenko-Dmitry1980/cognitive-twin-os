"""Event domain models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EventType(StrEnum):
    MESSAGE = "message"
    DECISION = "decision"
    TASK = "task"
    DOCUMENT_ADDED = "document_added"
    FEEDBACK = "feedback"
    OUTCOME = "outcome"
    CORRECTION = "correction"
    SYSTEM_EVENT = "system_event"


class Sensitivity(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"
    SENSITIVE = "sensitive"


class ConsentBasis(StrEnum):
    EXPLICIT = "explicit"
    IMPORTED = "imported"
    SYSTEM_GENERATED = "system_generated"


class RetentionPolicy(StrEnum):
    DEFAULT = "default"
    SHORT = "short"
    ARCHIVE = "archive"
    DELETE_ON_REQUEST = "delete_on_request"


class EventSource(BaseModel):
    type: str
    source_id: str
    uri: str | None = None


class Actor(BaseModel):
    actor_id: str
    role: str


class Provenance(BaseModel):
    captured_by: str
    confidence: float = Field(ge=0.0, le=1.0)
    content_hash: str
    schema_version: str


class Governance(BaseModel):
    sensitivity: Sensitivity
    consent_basis: ConsentBasis
    retention_policy: RetentionPolicy


class Event(BaseModel):
    event_id: str
    source: EventSource
    actor: Actor
    timestamp: datetime
    event_type: EventType
    payload: dict[str, Any]
    provenance: Provenance
    governance: Governance
