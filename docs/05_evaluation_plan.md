# Evaluation Plan

## Goals

Measure whether the cognitive twin improves decision quality and memory continuity — not just conversational fluency.

## Phase 0/1 metrics (automated in CI)

| Metric | Method |
|--------|--------|
| Schema compliance | `test_json_schemas.py` — valid/invalid cases |
| Model alignment | Pydantic validation mirrors JSON Schema enums |
| Store integrity | Duplicate event rejection, episode referential checks |
| Hash stability | Deterministic SHA-256 tests |
| Local durability | JSONL append/reload tests for events and episodes |
| Operation traceability | Trace Pydantic and JSON Schema validation |
| Import/export fidelity | JSONL roundtrip tests for events and episodes |
| Ingest validation | Accept valid JSONL, reject invalid/duplicate records |
| Episode build determinism | Timestamp ordering, no event mutation |
| Structured retrieval | Filters by memory_state, salience, entity, goal, time |
| Policy gate | Sensitivity/consent deny/allow; generic reason_code only externally |
| Policy-aware retrieval | Public API only; denied episodes excluded; pagination after policy |
| Release API boundary | Package root does not export policy-less retriever |
| Trace safety | filter_keys in metadata; no entity/goal/payload leak |
| Operation traces | ingest/build/retrieval/policy_retrieve emit trace records |
| Store snapshot isolation | Mutation of returned models does not affect stored state |
| Episode schema compliance | Valid episode passes; missing `event_ids` / invalid `memory_state` fail |
| Import/export safety | Corrupted JSONL raises `StorageError`; export overwrites target file |

## Phase 2+ metrics (planned)

### Memory recall

- **Episode retrieval precision@k** — relevant episodes returned for query
- **Event coverage** — fraction of ground-truth events linked in retrieved episodes
- **Salience calibration** — correlation between salience and human importance ratings

### Decision quality

- **Evidence coverage** — recommendations cite ≥1 valid evidence_event_id
- **Policy compliance rate** — no retrieval/decision bypasses governance
- **Outcome alignment** — post-hoc comparison of recommendation vs recorded outcome events

### Consolidation quality

- **Compression ratio** — events per consolidated episode without information loss (human eval sample)
- **Invalidation accuracy** — corrections properly invalidate superseded memory

## Benchmark datasets (future)

- Synthetic event/episode fixtures with known retrieval targets
- Redacted real-world decision cycles (with consent)
- No dependency on `DATA/` research files at runtime

## Human evaluation protocol (future)

1. Present decision scenario with retrieval context
2. Rater scores: relevance, provenance clarity, policy appropriateness
3. Compare against baseline (unstructured notes or raw chat)

## Reporting

Evaluation results should be emitted as `outcome` and `feedback` events for controlled learning loops.

## Phase 1.1 quality gates

```powershell
python -m pip install -e ".[dev]"
ruff check .
pytest -q
```

## ROOT CAUSE

Phase 0/1 tests proved schema and in-memory behavior, but not restart-safe local
durability or operation-level traceability.

## DESIGN DECISION

Phase 1.1 evaluates local durability through JSONL roundtrips, reload behavior,
corruption handling, duplicate detection, and trace schema validation.

## TRADE-OFFS

These checks validate local correctness and reproducibility. They do not measure
production concurrency, retrieval quality, semantic ranking, consolidation
quality, or decision usefulness.

## RISKS

- JSONL append is sufficient for single-process local use, not a concurrent
  production store.
- Trace coverage proves operation recording exists, not that every future
  operation emits traces.

## TEST RESULTS

Automated tests are expected to cover:

- existing in-memory store regressions
- existing JSON schema regressions
- existing hashing regressions
- JSONL event and episode persistence
- trace model, trace schema, and trace writer
- import/export roundtrips and explicit missing-file behavior

## Phase 1.2 test coverage

Automated tests in `tests/test_ingest.py`, `tests/test_episode_builder.py`, and
`tests/test_retrieval.py` cover:

- valid and partial ingest batches
- invalid ingest records with clear rejection reasons
- deterministic episode build and unknown `event_id` failure
- episode build does not mutate events
- internal `filter_episodes` candidate selection (not release-facing API)

## Release 0.1.2 quality gates

```powershell
python -m pip install -e ".[dev]"
ruff check .
pytest -q
```

Automated snapshot tests live in `tests/test_store_snapshots.py`.

**FACT:** Passing tests do not imply a governed production runtime.

## Phase 1.3 / Release 0.1.4 test coverage

Automated tests in `tests/test_policy_engine.py`, `tests/test_policy_retrieval.py`,
and `tests/test_release_api.py` cover:

- conservative default deny for private/sensitive/imported consent
- explicit allow when policy scope permits
- mixed-sensitivity episodes (most restrictive event wins)
- unknown `event_id` during policy evaluation fails clearly
- policy filtering before pagination
- denied episodes excluded from items; external `reason_code` only
- `include_policy_decisions=false` suppresses per-episode decisions
- package root does not export policy-less retriever
- `retrieval_response.schema.json` rejects legacy response shape
- `policy_retrieve_episodes` trace metadata: `filter_keys` without filter values
- expanded forbidden dependency denylist

Current quality gate: `138` tests, `ruff check .`, `pytest -q`.

## NEXT ACTIONS

Phase 2 should add retention enforcement, deletion/archive workflows,
relationship-based access control, and policy compliance rate metrics without
adding forbidden dependencies.
