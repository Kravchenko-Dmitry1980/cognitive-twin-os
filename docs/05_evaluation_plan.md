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
