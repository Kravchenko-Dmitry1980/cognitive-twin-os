"""Deterministic content hashing for events."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _canonical_json(data: Any) -> str:
    """Serialize data to canonical JSON for stable hashing."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_content_hash(payload: dict[str, Any], metadata: dict[str, Any]) -> str:
    """
    Compute deterministic SHA-256 hash over event payload and metadata.

    Same input always produces the same hash; any change in payload or metadata
    produces a different hash.
    """
    canonical = _canonical_json({"payload": payload, "metadata": metadata})
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
