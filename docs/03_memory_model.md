# Memory Model

## Hierarchy

| Level | Unit | Role |
|-------|------|------|
| Atomic | Event | Immutable fact with provenance |
| Composed | Episode | Curated memory segment |
| Indexed | (future) Semantic entries | Embeddings, entities |
| Consolidated | (future) Knowledge summaries | Distilled long-term memory |

## Event

Every observation is an event. Events are append-only; corrections are new events of type `correction` referencing prior event_ids in payload.

Key enums:

- **event_type:** message, decision, task, document_added, feedback, outcome, correction, system_event
- **sensitivity:** public, internal, private, sensitive
- **consent_basis:** explicit, imported, system_generated
- **retention_policy:** default, short, archive, delete_on_request

## Episode

Episodes bundle related events into a recall unit:

```
episode_id
├── event_ids[]      → must exist in store
├── episode_type     → e.g. conversation, project, decision_cycle
├── summary          → human-readable gist
├── salience         → 0.0–1.0 importance score
├── entities[]       → named entities
├── goals[]          → associated goals
├── outcome          → optional result
└── memory_state     → lifecycle stage
```

## Memory states

| State | Meaning |
|-------|---------|
| `raw` | Just ingested, unprocessed |
| `curated` | Reviewed, summary updated |
| `consolidated` | Merged into long-term memory |
| `archived` | Retained but low-priority |
| `invalidated` | Superseded or retracted |

Transitions are driven by the consolidation engine (future), subject to policy checks.

## Content hashing

`provenance.content_hash` is SHA-256 over canonical JSON of `{payload, metadata}`. Enables integrity verification and deduplication without storing secrets in the hash input.

## Referential integrity

- Episodes cannot reference unknown `event_ids`
- Store rejects duplicate `event_id` on append

## What memory is not

- Not a chat transcript blob
- Not an LLM system prompt
- Not an ungoverned vector index
