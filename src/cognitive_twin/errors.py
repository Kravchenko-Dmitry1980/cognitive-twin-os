"""Shared domain and storage errors."""

from __future__ import annotations


class CognitiveTwinError(Exception):
    """Base error for Cognitive Twin OS failures."""


class DomainError(CognitiveTwinError, ValueError):
    """Raised when domain invariants are violated."""


class DuplicateEventError(DomainError):
    """Raised when appending an event with an existing event_id."""


class DuplicateEpisodeError(DomainError):
    """Raised when appending an episode with an existing episode_id."""


class DuplicateTraceError(DomainError):
    """Raised when appending a trace with an existing trace_id."""


class UnknownEventReferenceError(DomainError):
    """Raised when an episode references event_ids not present in the store."""


class StorageError(CognitiveTwinError):
    """Raised when durable storage cannot be read or written safely."""


class PolicyError(DomainError):
    """Raised when policy evaluation cannot complete."""


class UnknownPolicyReferenceError(PolicyError):
    """Raised when policy evaluation references an unknown event_id."""


class InvalidRetrievalRequestError(DomainError):
    """Raised when a retrieval request violates runtime constraints."""
