# Contracts

All interchange boundaries are defined as JSON Schema in `contracts/`. Pydantic models in `src/cognitive_twin/` must stay aligned with these schemas.

## Store snapshot contract (release 0.1.3)

**DESIGN DECISION:** Immutability is enforced at the store boundary, not by
freezing Pydantic models globally.

| Operation | Semantics |
|-----------|-----------|
| `append_event` / `append_episode` | Store `model_copy(deep=True)`; input model is not mutated |
| `get_*` / `list_*` | Return `model_copy(deep=True)`; internal dict is never exposed |
| `JsonlEventStore` reload | Loaded models are deep-copied into internal storage |
| `JsonlTraceStore` | Traces are operation logs, not memory facts; same snapshot rules |

`InMemoryEventStore`, `JsonlEventStore`, and `JsonlTraceStore` must behave
consistently.

Release 0.1.3 also makes persisted JSONL reload behavior explicit:

- Duplicate persisted ids fail on reload
- File append order is preserved by list operations after reload
- Malformed JSON and non-object records fail with `StorageError`

## Ingest Contract

**Event envelope schema:** `contracts/events/event.schema.json`

**Batch schemas:**

- `contracts/ingest/ingest_batch.schema.json`
- `contracts/ingest/ingest_result.schema.json`

Defines the canonical event envelope for all ingested signals and the batch
operation result shape.

| Field | Purpose |
|-------|---------|
| `event_id` | Stable unique identifier |
| `source` | Origin system (type, source_id, uri) |
| `actor` | Who caused or authored the signal |
| `timestamp` | When the event occurred (ISO 8601) |
| `event_type` | Semantic category (message, decision, task, …) |
| `payload` | Type-specific content (opaque object) |
| `provenance` | Capture metadata and content hash |
| `governance` | Sensitivity, consent, retention |

**Implementations:**

- `cognitive_twin.events.Event`
- `cognitive_twin.ingest.IngestBatch`, `IngestResult`, `IngestError`
- `cognitive_twin.ingest.ManualJsonlIngestAdapter`

Ingest is validation, not interpretation. Rejected records include line number
and reason; accepted records are appended to the event repository.

## Memory Contract

**Schemas:**

- `contracts/events/episode.schema.json` — episode unit
- `contracts/memory/episode_build_request.schema.json`
- `contracts/memory/episode_build_result.schema.json`
- `contracts/memory/retrieval_request.schema.json`
- `contracts/memory/retrieval_response.schema.json`

Episodes group events into recallable memory units with salience, entities, goals, and `memory_state`.

Episode build contracts define deterministic grouping from explicit `event_ids`.
Retrieval request/response define the local structured retrieval boundary:
`request_id`, explicit filters, and matched episodes.

**Implementations:**

- `cognitive_twin.episodes.Episode`
- `cognitive_twin.episode_builder.DeterministicEpisodeBuilder`
- `cognitive_twin.retrieval.StructuredEpisodeRetriever`

## Policy Contract

**Schemas:**

- `contracts/policy/policy_request.schema.json`
- `contracts/policy/policy_response.schema.json`

Policy requests describe an action on a resource; responses return `allowed`, `reason`, optional `governance`, and `constraints`.

**Implementations (Phase 0/1):** `cognitive_twin.policy.PolicyRequest`, `PolicyResponse`

## Retrieval Contract

Structured filtering is implemented in Phase 1.2 via `RetrievalRequest`,
`RetrievalFilter`, `RetrievalResult`, and `StructuredEpisodeRetriever`.

No vector search, ranking model, or LLM in Phase 1.2.

## Decision Contract

**Schemas:**

- `contracts/decision/decision_request.schema.json`
- `contracts/decision/decision_response.schema.json`

Decision requests include `context_event_ids`; responses include `recommendation`, `evidence_event_ids`, and `confidence`.

Phase 0/1: schema only.

## Evaluation Contract

Not yet formalized as JSON Schema. Planned metrics:

- Schema compliance rate
- Episode referential integrity
- Retrieval precision@k (future)
- Evidence coverage in decisions (future)

See [05_evaluation_plan.md](05_evaluation_plan.md).

## Versioning

- `provenance.schema_version` on each event tracks event schema version
- Breaking contract changes require major version bump and migration plan

## Validation

```powershell
pytest tests/test_json_schemas.py -q
```

Contract tests validate every `contracts/**/*.schema.json` file and assert
representative runtime payloads serialize into matching schemas.

## Trace Contract

**Schema:** `contracts/traces/operation_trace.schema.json`

**Implementation:** `cognitive_twin.traces.OperationTrace`

Trace records describe operations performed by the runtime. They are audit and
observability records, not memory records.

| Field | Purpose |
|-------|---------|
| `trace_id` | Stable unique trace identifier |
| `operation` | Operation name, for example `append_event` |
| `timestamp` | Operation timestamp in ISO 8601 form |
| `actor_id` | Optional actor responsible for the operation |
| `input_refs` | Event, episode, or trace references consumed by operation |
| `output_refs` | Event, episode, or trace references produced by operation |
| `policy_result` | Optional serialized policy result |
| `status` | `started`, `succeeded`, `failed`, or `skipped` |
| `error` | Optional failure message |
| `metadata` | Additional structured operation metadata |

## ROOT CAUSE

Phase 0/1 had contracts for memory and policy shapes, but no operation-level
record that could explain how local state was produced.

## DESIGN DECISION

Trace is a separate contract so that operation history can be inspected without
promoting traces into identity, beliefs, preferences, skills, or stable memory.

## TRADE-OFFS

The trace contract is intentionally generic. It avoids premature coupling to a
future policy engine, orchestrator, API, or database schema.

## RISKS

- Trace `metadata` can become inconsistent if callers do not define local
  conventions.
- Trace append does not guarantee cross-file transactionality with event or
  episode append.

## TEST RESULTS

`tests/test_json_schemas.py` validates a trace instance and rejects invalid
trace status values.

## Phase 1.2 trace conventions

| Operation | `operation` value | Minimal `metadata` |
|-----------|-------------------|--------------------|
| Ingest | `ingest_batch` | `batch_id`, `accepted_count`, `rejected_count` |
| Episode build | `build_episode` | `request_id`, `episode_id`, `event_count` |
| Retrieval | `retrieve_episodes` | `request_id`, `match_count`, `filters` |

## Import/export contract

- `export_events_to_jsonl` / `export_episodes_to_jsonl`: overwrite target file
- `import_*_from_jsonl`: raise `StorageError` on missing file or corrupted JSONL

## Policy status (0.1.2)

Governance enums are validated structurally on events. Runtime policy
enforcement (deny/allow before retrieval) is **not** implemented — Phase 1.3.

## NEXT ACTIONS

Phase 1.3 should wire policy checks into retrieval and formalize evaluation
metrics for ingest rejection rates and filter precision.
