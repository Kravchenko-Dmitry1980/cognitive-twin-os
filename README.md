# Cognitive Twin OS

Contract-first, event-driven, memory-centric foundation for a **cognitive/operational digital twin**.

## What this project is

A platform scaffold for decision support, memory continuity, evidence-based recommendations, and controlled learning. The core state model is **events and episodes** with provenance and governance — not an LLM chat log.

Phase 0/1 delivers:

- Product and architecture documentation
- JSON contracts and Pydantic v2 models
- In-memory event/episode store
- JSONL event/episode persistence for local durable runtime state
- JSONL operation traces for audit-oriented observability
- Import/export utilities for events and episodes
- Contract tests and CI
- Full JSON Schema coverage for every contract file

Phase 1.2 adds:

- JSONL ingest adapter (validation only, no interpretation)
- Deterministic episode builder from explicit event_ids
- Structured retrieval filters (no vector search, no LLM)
- Operation traces for ingest, build, and retrieval

Phase 1.3 adds:

- Deterministic policy gate before retrieval (`PolicyGate`, `PolicyAwareEpisodeRetriever`)
- Conservative default policy: `private`/`sensitive` denied; `imported` consent denied
- Policy filtering before pagination (`limit`/`offset`, max 100)
- Policy-aware retrieval response with decision metadata (no denied episode payload)
- Operation traces for `policy_retrieve_episodes` without sensitive payloads

## What this project is not

- Not an LLM assistant or chatbot product
- Not a UI or frontend application
- Not a vector database or RAG pipeline
- Not an autonomous agent swarm
- Not a production deployment stack (yet)

## Why LLM is not the core state model

LLMs are useful for interpretation and generation, but they are **not** a durable memory substrate:

- Context windows are volatile working memory, not long-term identity
- Raw chat logs lack provenance, governance, and structured retrieval
- Parametric knowledge cannot be audited or deleted on request
- Recommendations without evidence links are not decision-grade

Cognitive Twin OS treats **events** (atomic facts with provenance) and **episodes** (curated memory units) as the source of truth. LLM layers may be added later as *consumers* of this memory — not as the memory itself.

## Phase 1 scope

| Included | Not included |
|----------|--------------|
| Event & episode schemas | FastAPI / HTTP API |
| Pydantic models | PostgreSQL / SQLAlchemy |
| In-memory and JSONL EventStore | Vector search |
| JSONL ingest adapter | LLM providers |
| Deterministic episode builder | Consolidation engine |
| Structured retrieval filters | Identity updates |
| Policy gate before retrieval | FastAPI / HTTP API |
| Pagination after policy filter | PostgreSQL / SQLAlchemy |
| JSON Schema contracts | UI |
| Policy/decision contracts | Production IAM |
| pytest + ruff + CI | PostgreSQL / SQLAlchemy |

See [ROADMAP.md](ROADMAP.md) for future phases.

## Quick start

Requires **Python 3.12+**.

```powershell
cd C:\Dima\Projects\CURSOR\cognitive-twin-os
python -m pip install -e ".[dev]"
ruff check .
pytest -q
```

Copy `.env.example` to `.env` for local configuration (optional in Phase 1).

## Project layout

```
contracts/     JSON Schema contracts (source of truth for interchange)
docs/          Architecture, memory model, evaluation plan
src/           cognitive_twin Python package
tests/         Model, store, and schema contract tests
local_data/    Local runtime JSONL files, ignored by git
DATA/          Background research only — not runtime dependency
```

## Phase 1.1 Durable Local Memory Foundation

**FACT:** Phase 1.1 adds local reproducible durability without introducing a
server, database, vector index, LLM provider, or UI.

**DESIGN DECISION:** JSONL is used because each record remains human-readable,
append-only, fixture-friendly, and easy to validate through Pydantic models and
JSON Schema contracts.

Runtime data belongs under `local_data/*.jsonl` and is ignored by git. Committed
examples should live only under explicit fixtures or examples paths.

Memory lifecycle remains controlled:

```text
Event -> Episode -> OperationTrace -> future consolidation
```

Traces record operations and outcomes. They do not automatically become memory,
beliefs, preferences, skills, or identity signals.

## Phase 1.2 Ingest, Episode Builder, Retrieval

**FACT:** Ingest validates events from JSONL and appends accepted records to a
repository. It does not interpret content or update identity.

**FACT:** The episode builder groups validated events into episodes using
caller-supplied `summary`, `episode_type`, and `salience`. Event order is
deterministic (sorted by timestamp). No semantic generation or consolidation.

**FACT:** Retrieval applies explicit filters (`episode_type`, `memory_state`,
`min_salience`, `entity`, `goal`, time range). No embeddings, ranking models,
or LLM.

```text
JSONL -> IngestAdapter -> EventStore -> EpisodeBuilder -> EpisodeStore
                                              |
                                    StructuredEpisodeRetriever
```

## Release 0.1.2 — Store snapshot semantics

**DESIGN DECISION:** Domain models are treated as immutable snapshots after
persistence. Stores use `model_copy(deep=True)` on write and on read — not
global frozen Pydantic models.

`InMemoryEventStore` and `JsonlEventStore` behave consistently: callers never
receive mutable internal references.

**FACT:** `export_events_to_jsonl` and `export_episodes_to_jsonl` open the
target file in write mode (`"w"`) and overwrite existing content.

**FACT:** Policy fields (`sensitivity`, `consent_basis`, `retention_policy`) are
structurally validated on events. Policy **enforcement** is Phase 1.3.

**FACT:** This release does not claim a governed production runtime. No identity
update, no consolidation, no LLM, no vector search.

## Release 0.1.3 - Snapshot and contract consistency

**ROOT CAUSE:** Phase 1.2 had runtime behavior for JSONL stores, traces, and
structured retrieval, but tests and docs did not fully prove every persisted
contract boundary.

**DESIGN DECISION:** Release 0.1.3 keeps the local library architecture and
adds coverage instead of introducing a database, API framework, LLM provider,
or vector retrieval stack.

**FACT:** JSONL event, episode, and trace reload paths reject duplicate
persisted ids.

**FACT:** JSONL stores preserve file append order when listing records after
reload.

**FACT:** Corrupted JSONL behavior is explicit: malformed JSON and non-object
records raise `StorageError` with file and line context.

**FACT:** Tests cover every `contracts/**/*.schema.json` file and verify that
Phase 1 runtime payloads serialize into matching schemas.

**FACT:** Dependency boundary tests reject forbidden runtime dependencies:
LLM SDKs, agent frameworks, vector DB clients, web/API frameworks, database
ORMs, and network HTTP clients.

**FACT:** This release still does not implement transactions, concurrent
writer coordination, policy enforcement, governed runtime, identity update,
consolidation, or semantic/vector retrieval.

## Release 0.1.4 — Policy gate before retrieval

**FACT:** `PolicyAwareEpisodeRetriever` applies structured filters, evaluates
each candidate episode against governance of referenced events, then paginates
allowed results only.

**DESIGN DECISION:** Default policy is conservative: `allowed_sensitivities` is
`["public", "internal"]`, `allow_imported` is `false`. Denied episodes are
excluded from `items`; `policy_decisions` may include episode id and reason code
only.

**FACT:** Policy enforcement is local and minimal — not a production governed
runtime. No relationship-based access control, retention jobs, or deletion
workflows yet.

**FACT:** Traces for policy retrieval record counts and ids only — no event
payloads or sensitive content in metadata.

Current package version: **0.1.4** (Phase 1.3 policy gate).

## Documentation

- [Product brief](docs/00_product_brief.md)
- [Architecture](docs/01_architecture.md)
- [Contracts](docs/02_contracts.md)
- [Memory model](docs/03_memory_model.md)
- [Policy model](docs/04_policy_model.md)
- [Evaluation plan](docs/05_evaluation_plan.md)
- [Cursor/Codex workflow](docs/06_codex_cursor_workflow.md)

## License

MIT
