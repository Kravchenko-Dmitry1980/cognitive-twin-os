# Cognitive Twin OS

Contract-first, event-driven, memory-centric foundation for a **cognitive/operational digital twin**.

## What this project is

A platform scaffold for decision support, memory continuity, evidence-based recommendations, and controlled learning. The core state model is **events and episodes** with provenance and governance — not an LLM chat log.

Phase 0/1 delivers:

- Product and architecture documentation
- JSON contracts and Pydantic v2 models
- In-memory event/episode store
- Contract tests and CI

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
| In-memory EventStore | Vector search |
| JSON Schema contracts | LLM providers |
| Policy/decision contract stubs | Consolidation engine |
| pytest + ruff + CI | UI |

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
DATA/          Background research only — not runtime dependency
```

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
