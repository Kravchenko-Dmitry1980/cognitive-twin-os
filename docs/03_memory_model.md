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

## Store snapshot semantics (release 0.1.2)

After persistence, events and episodes are treated as immutable snapshots:

- Stores deep-copy on write and on read
- Mutating a model returned by `get_event` / `list_events` does not affect stored state
- Mutating the original model after `append_event` does not affect stored state
- Same rules apply to episodes and to both `InMemoryEventStore` and `JsonlEventStore`

## What memory is not

- Not a chat transcript blob
- Not an LLM system prompt
- Not an ungoverned vector index

## Phase 1.1 local durability

**FACT:** Events and episodes can now be persisted to JSONL through
`JsonlEventStore` and imported/exported through `cognitive_twin.io`.

**FACT:** Operation traces can be appended to JSONL through `JsonlTraceStore`.

The lifecycle remains:

```text
raw event -> episode -> trace record -> future consolidation
```

## ROOT CAUSE

The in-memory scaffold preserved domain invariants during one process lifetime,
but could not support local replay or durable audit after restart.

## DESIGN DECISION

Phase 1.1 adds append-oriented JSONL files:

- events stay immutable facts
- episodes reference existing `event_ids`
- traces record operations but do not update memory state
- consolidation and identity updates remain unimplemented

## TRADE-OFFS

JSONL supports transparent inspection and deterministic tests. It does not
support ranked retrieval, identity consolidation, concurrent writers, or policy
enforcement beyond explicit model fields.

## RISKS

- A future builder must avoid treating raw event frequency as preference or
  identity.
- A future retrieval layer must not read ignored runtime files as trusted
  committed fixtures.

## TEST RESULTS

Storage tests cover persistence, reload, duplicates, unknown event references,
corrupted JSONL, and deterministic list order.

## Phase 1.2 ingest and episode build

**FACT:** `ManualJsonlIngestAdapter` validates JSONL lines as events and appends
accepted records. Rejected lines are reported with line number and reason.

**FACT:** `DeterministicEpisodeBuilder` requires caller-supplied `summary`,
`episode_type`, and `salience`. It sorts `event_ids` by event timestamp and does
not modify source events.

**DESIGN DECISION:** Raw events do not directly become identity. Ingest validates;
the builder groups; consolidation and identity updates remain future phases.

## Phase 1.2 internal candidate selection

**FACT:** `filter_episodes` selects candidates by explicit fields only. It is
not a release-facing retrieval API. No embeddings, ranking models, or LLM.

## Phase 1.3 policy-gated retrieval

**FACT:** `PolicyAwareEpisodeRetriever` applies structured filters, evaluates
each candidate against event governance via `PolicyGate`, then paginates allowed
episodes only.

**DESIGN DECISION:** Policy filtering precedes pagination so denied episodes do
not occupy result slots.

**FACT:** Default policy denies `private`/`sensitive` and `imported` consent.
Denied episode content is not returned in `items`. External policy decisions
expose generic `reason_code` only (`access_denied`, `consent_not_allowed`, etc.).

## Release scope (0.1.4)

- Local policy gate before retrieval
- Pagination after policy filter
- No identity update
- No consolidation
- No LLM interpretation
- No vector search
- No production IAM, retention jobs, or deletion workflows

## NEXT ACTIONS

Phase 2 should add retention enforcement and richer governance audit trails.
