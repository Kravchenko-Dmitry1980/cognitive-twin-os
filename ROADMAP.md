# Roadmap

## Phase 0/1 - Foundation

- [x] Product brief and architecture docs
- [x] JSON Schema contracts: event, episode, policy, memory, decision
- [x] Pydantic v2 domain models
- [x] In-memory `EventStore`
- [x] Contract tests and CI: `ruff check .`, `pytest -q`

## Phase 1.1 - Durable Local Memory Foundation

- [x] JSONL file-based event persistence
- [x] JSONL file-based episode persistence
- [x] Operation trace JSON Schema and Pydantic model
- [x] JSONL trace writer
- [x] Event/episode import and export utilities
- [x] Explicit domain and storage errors
- [x] Runtime `local_data/*.jsonl` ignored by git

**FACT:** Phase 1.1 intentionally remains local and library-only.

**DESIGN DECISION:** JSONL gives durable append-friendly storage without
introducing server, database, vector index, LLM provider, UI, or external
network dependency.

## Phase 1.2 - Ingest and Episode Builder

- [x] Ingest adapter interface and `ManualJsonlIngestAdapter`, no LLM
- [x] Ingest batch/result JSON Schema contracts
- [x] Deterministic episode builder from explicit `event_ids`
- [x] Episode build request/result JSON Schema contracts
- [x] Structured retrieval filters: `episode_type`, `memory_state`, `salience`, `entity`, `goal`, time range
- [x] Trace coverage for ingest, episode build, and retrieval operations
- [x] Tests use `tmp_path` fixtures, not runtime `local_data/`

**FACT:** Phase 1.2 validates and groups memory. It does not consolidate,
update identity, or call external services.

## Release 0.1.2 - Stabilization

- [x] Store-level snapshot semantics for `InMemoryEventStore`
- [x] Consistent deep-copy behavior in `JsonlEventStore` and `JsonlTraceStore`
- [x] Immutability/snapshot regression tests
- [x] Episode JSON Schema contract tests
- [x] Import/export corrupted JSONL and overwrite behavior tests
- [x] Package version bumped to `0.1.2`

**DESIGN DECISION:** Snapshots at store boundary, not frozen domain models.

**FACT:** No governed runtime claim in 0.1.2. Policy enforcement is Phase 1.3.

## Release 0.1.3 - Snapshot and contract consistency

- [x] Duplicate persisted event, episode, and trace ids fail during JSONL reload
- [x] JSONL list order follows file append order after reload
- [x] Corrupted JSONL behavior covers malformed JSON and non-object records
- [x] All `contracts/**/*.schema.json` files have schema coverage
- [x] Runtime-aligned contracts for structured retrieval request/response
- [x] Dependency boundary tests reject forbidden Phase 1 dependencies
- [x] Package version bumped to `0.1.3`

**FACT:** Release 0.1.3 is a consistency and test-coverage hardening release.
It does not add transactions, concurrent writer coordination, policy
enforcement, governed runtime, identity updates, consolidation, or
semantic/vector retrieval.

## Phase 1.3 - Policy gate before retrieval

- [x] Retrieval request/response runtime aligned with structured filters
- [x] `PolicyGate` evaluates sensitivity and consent_basis from referenced events
- [x] `PolicyAwareEpisodeRetriever`: filter → policy → pagination
- [x] Conservative defaults: private/sensitive denied; imported consent denied
- [x] Pagination (`limit` default 50, max 100; `offset` >= 0) after policy filter
- [x] `policy_retrieve_episodes` operation traces without sensitive payload
- [x] Package version bumped to `0.1.4`

**FACT:** Phase 1.3 is local policy enforcement only. No production IAM,
relationship-based access control, retention jobs, or deletion workflows.

**DESIGN DECISION:** Policy filtering runs before pagination so denied episodes
do not consume result slots.

## Phase 2 - Governance hardening

- [ ] Retention policy enforcement jobs
- [ ] Deletion and archive workflows
- [ ] Relationship-based access control
- [ ] Audit log enrichment beyond operation traces

## Phase 3 - Consolidation

- [ ] Consolidation engine: raw -> curated -> consolidated
- [ ] Salience scoring pipeline
- [ ] Invalidation and archive workflows

## Phase 4 - Semantic layer

- [ ] Optional pluggable embedding index
- [ ] Hybrid retrieval: structured + semantic
- [ ] Entity linking

## Phase 5 - Decision API

- [ ] FastAPI decision support endpoints
- [ ] Evidence-linked recommendations
- [ ] Human-in-the-loop feedback loop

## Phase 6 - Evaluation and learning

- [ ] Memory recall benchmarks
- [ ] Decision quality metrics
- [ ] Controlled learning from outcomes, no unbounded self-modification

## Explicitly deferred

- LLM provider integrations: OpenAI, Anthropic, etc.
- Agent frameworks: LangChain, CrewAI, AutoGen
- Vector databases as required dependency
- Production UI
- Multi-tenant cloud deployment
