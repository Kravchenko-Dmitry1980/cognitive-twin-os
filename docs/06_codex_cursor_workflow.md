# Cursor & Codex Workflow

## Roles

| Tool | Responsibility |
|------|----------------|
| **Cursor** | Implementation, scaffolding, local edits, test runs |
| **Codex** | Architecture review, contract review, test-gap detection, patch critique |

## Principles

1. **No uncontrolled code generation** — every implementation task must reference a contract or doc section
2. **Contracts before code** — JSON Schema changes precede Pydantic model updates
3. **Tests as acceptance** — new behavior requires pytest coverage before merge
4. **Minimal scope** — Phase boundaries in ROADMAP.md are hard limits unless explicitly expanded

## Typical workflow

```
1. Define or update contract (docs/02_contracts.md + contracts/*.json)
2. Codex reviews contract for completeness and enum consistency
3. Cursor implements Pydantic models + store logic + tests
4. Codex reviews diff for test gaps and boundary violations
5. CI (ruff + pytest) must pass
```

## Task contract template

Before Cursor implements a feature:

```markdown
## Task
<one-line goal>

## Contracts affected
- contracts/...

## Acceptance
- [ ] pytest tests added/updated
- [ ] ruff clean
- [ ] docs updated if public interface changed

## Out of scope
- <explicit exclusions>
```

## Review checklist (Codex)

- [ ] No LLM provider imports in core package
- [ ] No network calls in store/ingest paths
- [ ] Episode references validated against known events
- [ ] Governance enums match JSON Schema
- [ ] No secrets in tests or fixtures
- [ ] DATA/ folder not imported at runtime

## Anti-patterns

- Generating FastAPI routes before store persistence is defined
- Adding vector DB because "agents need RAG"
- Using LLM to compute content_hash or policy decisions in Phase 0/1
- Copying research prose from DATA/ into runtime code
