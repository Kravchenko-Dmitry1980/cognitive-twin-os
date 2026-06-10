"""Identifier generation utilities."""

from __future__ import annotations

import uuid
from typing import Literal

IdPrefix = Literal["evt", "ep", "actor", "src", "trace", "batch"]


def new_id(prefix: IdPrefix) -> str:
    """Generate a prefixed unique identifier."""
    return f"{prefix}_{uuid.uuid4().hex}"
