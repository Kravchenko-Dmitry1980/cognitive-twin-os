"""Cognitive Twin OS: contract-first, event-driven memory foundation."""

from cognitive_twin.episode_builder import (
    DeterministicEpisodeBuilder,
    EpisodeBuildRequest,
    EpisodeBuildResult,
    EpisodeBuildStatus,
)
from cognitive_twin.episodes import Episode, MemoryState
from cognitive_twin.errors import (
    DuplicateEpisodeError,
    DuplicateEventError,
    DuplicateTraceError,
    StorageError,
    UnknownEventReferenceError,
)
from cognitive_twin.events import (
    Actor,
    ConsentBasis,
    Event,
    EventSource,
    EventType,
    Governance,
    Provenance,
    RetentionPolicy,
    Sensitivity,
)
from cognitive_twin.ingest import (
    IngestAdapter,
    IngestBatch,
    IngestError,
    IngestResult,
    ManualJsonlIngestAdapter,
)
from cognitive_twin.jsonl_store import JsonlEventStore
from cognitive_twin.retrieval import (
    RetrievalFilter,
    RetrievalRequest,
    RetrievalResult,
    StructuredEpisodeRetriever,
)
from cognitive_twin.store import EventStore, InMemoryEventStore
from cognitive_twin.trace_store import JsonlTraceStore
from cognitive_twin.traces import OperationTrace, TraceStatus

__all__ = [
    "Actor",
    "ConsentBasis",
    "DeterministicEpisodeBuilder",
    "DuplicateEpisodeError",
    "DuplicateEventError",
    "DuplicateTraceError",
    "Episode",
    "EpisodeBuildRequest",
    "EpisodeBuildResult",
    "EpisodeBuildStatus",
    "Event",
    "EventSource",
    "EventStore",
    "EventType",
    "Governance",
    "InMemoryEventStore",
    "IngestAdapter",
    "IngestBatch",
    "IngestError",
    "IngestResult",
    "JsonlEventStore",
    "JsonlTraceStore",
    "ManualJsonlIngestAdapter",
    "MemoryState",
    "OperationTrace",
    "Provenance",
    "RetentionPolicy",
    "RetrievalFilter",
    "RetrievalRequest",
    "RetrievalResult",
    "Sensitivity",
    "StorageError",
    "StructuredEpisodeRetriever",
    "TraceStatus",
    "UnknownEventReferenceError",
]

__version__ = "0.1.3"
