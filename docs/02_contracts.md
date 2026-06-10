# Contracts

All interchange boundaries are defined as JSON Schema in `contracts/`. Pydantic models in `src/cognitive_twin/` must stay aligned with these schemas.

## Ingest Contract

**Schema:** `contracts/events/event.schema.json`

Defines the canonical event envelope for all ingested signals.

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

**Implementations (Phase 0/1):** `cognitive_twin.events.Event`

## Memory Contract

**Schemas:**

- `contracts/events/episode.schema.json` — episode unit
- `contracts/memory/retrieval_request.schema.json`
- `contracts/memory/retrieval_response.schema.json`

Episodes group events into recallable memory units with salience, entities, goals, and `memory_state`.

Retrieval request/response define the future API for evidence-backed context fetch.

**Implementations (Phase 0/1):** `cognitive_twin.episodes.Episode`, in-memory store

## Policy Contract

**Schemas:**

- `contracts/policy/policy_request.schema.json`
- `contracts/policy/policy_response.schema.json`

Policy requests describe an action on a resource; responses return `allowed`, `reason`, optional `governance`, and `constraints`.

**Implementations (Phase 0/1):** `cognitive_twin.policy.PolicyRequest`, `PolicyResponse`

## Retrieval Contract

See Memory Contract retrieval schemas. Phase 0/1 defines shape only; no retrieval engine.

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

Contract tests assert required fields and enum constraints match runtime models.
