# Policy Model

## Purpose

Govern who can read, write, consolidate, or delete memory based on sensitivity, consent, and retention rules.

## Governance fields (on every event)

| Field | Values | Intent |
|-------|--------|--------|
| `sensitivity` | public, internal, private, sensitive | Access classification |
| `consent_basis` | explicit, imported, system_generated | Legal/ethical basis for storage |
| `retention_policy` | default, short, archive, delete_on_request | Lifecycle rule |

## Policy evaluation flow (target)

```
Request(action, resource, actor)
    → Load governance from resource/events
    → Check actor permissions
    → Apply retention constraints
    → Return PolicyResponse { allowed, reason, constraints }
```

## Policy request contract

Fields: `request_id`, `actor_id`, `action`, `resource_type`, `resource_id`, optional `proposed_sensitivity`, `context`.

Example actions (future): `read`, `share`, `consolidate`, `delete`, `export`.

## Policy response contract

Fields: `request_id`, `decision` with `allowed`, `reason`, optional `governance`, `constraints[]`.

## Phase 0/1 status

- Pydantic models: `PolicyRequest`, `PolicyResponse`, `PolicyDecision`
- JSON schemas in `contracts/policy/`
- No runtime policy engine

## Design constraints

- Deny by default for `sensitive` data without explicit consent
- `delete_on_request` must be enforceable without LLM involvement
- Policy decisions should be logged as `system_event` events (future)
