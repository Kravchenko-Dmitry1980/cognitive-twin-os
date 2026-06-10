# Architecture

## Design principles

1. **Contract-first** — interchange formats defined before implementations
2. **Event-driven** — all state changes flow through typed events
3. **Memory-centric** — episodes are the unit of recall, not raw prompts
4. **Governance by default** — sensitivity, consent, retention on every event
5. **Evidence-linked decisions** — recommendations cite event_ids

## Layer overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Decision API (placeholder)                  │
├─────────────────────────────────────────────────────────────┤
│                    Retrieval Layer (placeholder)               │
├─────────────────────────────────────────────────────────────┤
│              Policy / Governance Layer                         │
├─────────────────────────────────────────────────────────────┤
│         Consolidation Engine (placeholder)                     │
├─────────────────────────────────────────────────────────────┤
│              Semantic Layer (placeholder)                        │
├─────────────────────────────────────────────────────────────┤
│                    Episodic Store                              │
│              (EventStore — Phase 0/1)                          │
├─────────────────────────────────────────────────────────────┤
│              Ingest & Provenance Layer                         │
└─────────────────────────────────────────────────────────────┘
```

## Layers

### Ingest and provenance layer

Accepts external signals (messages, documents, outcomes) and normalizes them into `Event` records. Each event carries:

- Source identity (type, source_id, optional uri)
- Actor (actor_id, role)
- Provenance (captured_by, confidence, content_hash, schema_version)
- Governance (sensitivity, consent_basis, retention_policy)

Phase 1.2: `ManualJsonlIngestAdapter` reads JSONL, validates `Event` models,
appends accepted records, and returns rejected lines with reasons. Validation
only — no interpretation, consolidation, or identity updates.

### Episodic store

Persists events and episodes. An episode references one or more event_ids and tracks memory lifecycle (`raw` → `curated` → `consolidated` → `archived` / `invalidated`).

Phase 1.1: in-memory and JSONL `EventStore` with referential integrity checks.

**Release 0.1.2:** Both stores enforce snapshot semantics — `model_copy(deep=True)`
on append and on every read. Domain models are treated as immutable after
persistence; stores never expose internal mutable references.

Phase 1.2: `DeterministicEpisodeBuilder` groups validated events into episodes
using caller-supplied metadata. `event_ids` are ordered by timestamp before
persistence.

### Semantic layer (placeholder)

Future embedding index and entity graph for similarity search and cross-episode linking. Not implemented in Phase 0/1.

### Consolidation engine (placeholder)

Future offline process that compacts raw episodes, updates salience, extracts entities/goals, and promotes memory_state. Inspired by biological consolidation/replay — implemented as deterministic pipelines first, optional LLM enrichment later.

### Policy / governance layer

Evaluates whether an action (read, share, consolidate, delete) is allowed given sensitivity, consent_basis, and retention_policy. Contracts: `policy_request.schema.json`, `policy_response.schema.json`, `episode_policy_evaluation.schema.json`.

Phase 1.3: `PolicyGate` evaluates each candidate episode against governance of
all referenced events. Conservative defaults deny `private`/`sensitive` and
`imported` consent unless explicitly allowed in `RetrievalPolicyScope`.

**FACT:** This is local policy enforcement only — not production IAM, not
relationship-based access control, not retention job execution.

### Retrieval layer

Phase 1.2: `StructuredEpisodeRetriever` filters episodes by explicit fields
(`episode_type`, `memory_state`, `min_salience`, `entity`, `goal`, time range).
No vector search, ranking model, or LLM.

Phase 1.3: `PolicyAwareEpisodeRetriever` runs structured filter → policy gate →
pagination. Denied episodes are excluded from `items`; `policy_decisions` may
include episode id and reason code only.

### Decision API (placeholder)

Accepts a decision request with context_event_ids; returns a recommendation with evidence_event_ids and confidence. Contracts: `decision_request.schema.json`, `decision_response.schema.json`.

### Evaluation layer

Measures memory recall fidelity, policy compliance, and recommendation grounding. See [05_evaluation_plan.md](05_evaluation_plan.md).

## Data flow (target)

```
Ingest → Event → Episode (raw)
                    ↓
            Consolidation → Episode (curated/consolidated)
                    ↓
            Retrieval ← Policy check
                    ↓
            Decision API → Outcome Event → feedback loop
```

## Technology constraints (Phase 0/1)

- Python 3.12, Pydantic v2
- No database, no vector store, no LLM SDKs
- No network calls in core store

## Phase 1.1 component map

**FACT:** Durable local storage is implemented as library code, not as a
service.

| Layer | Phase 1.1 component |
|-------|---------------------|
| Domain Layer | `Event`, `Episode`, `OperationTrace`, explicit errors |
| Application Layer | Import/export functions in `cognitive_twin.io` |
| Infrastructure Layer | `InMemoryEventStore`, `JsonlEventStore`, `JsonlTraceStore` |
| Orchestration Layer | `ManualJsonlIngestAdapter`, `DeterministicEpisodeBuilder`, `StructuredEpisodeRetriever`, `PolicyAwareEpisodeRetriever` |
| Interface Layer | JSON Schema contracts under `contracts/` |

## ROOT CAUSE

Phase 0/1 had correct event and episode contracts, but runtime state existed
only in memory. That made tests deterministic, but did not provide reproducible
local persistence for future ingest, replay, or audit workflows.

## DESIGN DECISION

Phase 1.1 uses JSONL for events, episodes, and operation traces:

- `local_data/events.jsonl`
- `local_data/episodes.jsonl`
- `local_data/traces.jsonl`

Each line is a complete contract-valid record. Runtime data is ignored by git;
fixtures must be committed only under explicit fixture/example paths.

## TRADE-OFFS

JSONL keeps the foundation transparent and dependency-light. It does not provide
concurrent writes, indexes, migrations, or query planning. Those are accepted
limitations for Phase 1.1 because the current goal is durable local replay, not
production serving.

## RISKS

- Concurrent writers can interleave records; this is out of scope for Phase 1.1.
- Large files will require indexing or database-backed repositories later.
- Trace logs improve observability but are not a policy engine.

## TEST RESULTS

Quality gates are defined as:

```powershell
python -m pip install -e ".[dev]"
ruff check .
pytest -q
```

## Phase 1.2 component map

| Operation | Component | Trace `operation` |
|-----------|-----------|-------------------|
| Ingest JSONL | `ManualJsonlIngestAdapter` | `ingest_batch` |
| Build episode | `DeterministicEpisodeBuilder` | `build_episode` |
| Filter episodes | `StructuredEpisodeRetriever` | `retrieve_episodes` |
| Policy retrieval | `PolicyAwareEpisodeRetriever` | `policy_retrieve_episodes` |

Trace metadata stays minimal: batch/request ids, counts, and filter keys. Policy
retrieval traces must not include event payloads or sensitive content.

## Import/export semantics

`cognitive_twin.io.export_*_to_jsonl` overwrites the target file (`"w"` mode).
`import_*_from_jsonl` raises `StorageError` on corrupted JSONL with line number.

## Phase 1.3 component flow

```text
RetrievalRequest
  -> filter_episodes (structured)
  -> PolicyGate (per episode, all referenced events)
  -> pagination on allowed episodes only
  -> RetrievalResponse + optional policy_retrieve_episodes trace
```

## NEXT ACTIONS

Phase 2 should add retention enforcement, deletion workflows, and richer audit
without introducing FastAPI, PostgreSQL, vector search, or LLM dependencies
until explicitly scoped.
