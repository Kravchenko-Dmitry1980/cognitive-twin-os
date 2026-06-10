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

Phase 0/1: models and contracts only; no live ingest adapters.

### Episodic store

Persists events and episodes. An episode references one or more event_ids and tracks memory lifecycle (`raw` → `curated` → `consolidated` → `archived` / `invalidated`).

Phase 0/1: in-memory `EventStore` with referential integrity checks.

### Semantic layer (placeholder)

Future embedding index and entity graph for similarity search and cross-episode linking. Not implemented in Phase 0/1.

### Consolidation engine (placeholder)

Future offline process that compacts raw episodes, updates salience, extracts entities/goals, and promotes memory_state. Inspired by biological consolidation/replay — implemented as deterministic pipelines first, optional LLM enrichment later.

### Policy / governance layer

Evaluates whether an action (read, share, consolidate, delete) is allowed given sensitivity, consent_basis, and retention_policy. Contracts: `policy_request.schema.json`, `policy_response.schema.json`.

Phase 0/1: Pydantic models and JSON schemas; no runtime engine.

### Retrieval layer (placeholder)

Returns episodes and supporting events for a query, filtered by memory_state and governance. Contracts: `retrieval_request.schema.json`, `retrieval_response.schema.json`.

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
