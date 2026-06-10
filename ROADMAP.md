# Roadmap

## Phase 0 — Foundation (current)

- [x] Product brief and architecture docs
- [x] JSON Schema contracts (event, episode, policy, memory, decision)
- [x] Pydantic v2 domain models
- [x] In-memory EventStore
- [x] Contract tests and CI (ruff + pytest)

## Phase 1 — Persistence & ingest

- [ ] File-based or SQLite episode/event persistence
- [ ] Ingest adapter interface (no LLM)
- [ ] Episode builder from event batches
- [ ] Basic retrieval by episode_type, salience, memory_state

## Phase 2 — Policy & governance runtime

- [ ] Policy engine implementation (consent, sensitivity, retention)
- [ ] Audit log for policy decisions
- [ ] Retention job stubs

## Phase 3 — Consolidation

- [ ] Consolidation engine (raw → curated → consolidated)
- [ ] Salience scoring pipeline
- [ ] Invalidation and archive workflows

## Phase 4 — Semantic layer

- [ ] Embedding index (optional, pluggable)
- [ ] Hybrid retrieval (structured + semantic)
- [ ] Entity linking

## Phase 5 — Decision API

- [ ] FastAPI decision support endpoints
- [ ] Evidence-linked recommendations
- [ ] Human-in-the-loop feedback loop

## Phase 6 — Evaluation & learning

- [ ] Memory recall benchmarks
- [ ] Decision quality metrics
- [ ] Controlled learning from outcomes (no unbounded self-modification)

## Explicitly deferred

- LLM provider integrations (OpenAI, Anthropic, etc.)
- Agent frameworks (LangChain, CrewAI, AutoGen)
- Vector databases as required dependency
- Production UI
- Multi-tenant cloud deployment
