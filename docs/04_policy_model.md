# Policy Model

## Purpose

Govern who can read, write, consolidate, or delete memory based on sensitivity, consent, and retention rules.

## Governance fields (on every event)

| Field | Values | Intent |
|-------|--------|--------|
| `sensitivity` | public, internal, private, sensitive | Access classification |
| `consent_basis` | explicit, imported, system_generated | Legal/ethical basis for storage |
| `retention_policy` | default, short, archive, delete_on_request | Lifecycle rule |

## Phase 1.3 policy gate (retrieval)

Before returning episodes, `PolicyGate` evaluates every `event_id` referenced by
the candidate episode:

1. Load event governance from `EventStore`
2. Deny if any event sensitivity is not in `allowed_sensitivities`
3. Deny if any event has `consent_basis = imported` and `allow_imported` is false
4. Fail clearly if any referenced `event_id` is unknown (`UnknownPolicyReferenceError`)

### Conservative defaults

| Setting | Default | Effect |
|---------|---------|--------|
| `allowed_sensitivities` | `["public", "internal"]` | `private` and `sensitive` denied |
| `allow_imported` | `false` | imported consent denied |
| `include_policy_decisions` | `true` | return decision metadata |

Mixed-sensitivity episodes use the most restrictive referenced event: if any
event denies, the episode is denied.

### Decision values

`PolicyDecisionValue`: `allow`, `deny`, `redact` (enum includes `redact` for
future use; Phase 1.3 implements allow/deny only).

Denied episodes are not returned in `RetrievalResponse.items`. When
`include_policy_decisions` is true, denied entries include `episode_id` and
`reason_code` only — no episode payload.

## Policy evaluation flow

```text
Episode + PolicyEvaluationContext
    -> for each event_id in episode.event_ids
        -> load Event.governance
        -> check sensitivity + consent_basis
    -> EpisodePolicyEvaluation { allow | deny, reason_code }
```

## Policy request contract (generic)

Fields: `request_id`, `actor_id`, `action`, `resource_type`, `resource_id`, optional `proposed_sensitivity`, `context`.

Example actions (future): `read`, `share`, `consolidate`, `delete`, `export`.

## Policy response contract

Fields: `request_id`, `decision` with `allowed`, `reason`, optional `governance`, `constraints[]`, optional `decision_value`.

## Episode policy evaluation contract

Schema: `contracts/policy/episode_policy_evaluation.schema.json`

Implementation: `cognitive_twin.policy_engine.EpisodePolicyEvaluation`

## Retrieval policy scope

`RetrievalPolicyScope` on `RetrievalRequest.policy` carries:

- `actor_id`, `purpose`
- `allowed_sensitivities`
- `allow_imported`
- `include_policy_decisions`

## Trace conventions (policy retrieval)

Operation: `policy_retrieve_episodes`

| Field | Content |
|-------|---------|
| `policy_result` | `{ total_candidates, total_allowed, total_denied }` |
| `metadata` | request id, counts, offset, limit, filter keys |
| Must not include | event payloads, sensitive text |

## Phase status

| Phase | Status |
|-------|--------|
| 0/1 | Pydantic models + JSON schemas |
| 1.3 | `PolicyGate`, `PolicyAwareEpisodeRetriever` for retrieval |
| 2+ | Retention jobs, deletion workflows, production IAM |

## Design constraints

- Deny by default for `private`/`sensitive` without explicit allowance
- `imported` consent denied unless `allow_imported = true`
- Policy gate does not modify events or episodes
- No LLM involvement in policy decisions
- No identity inference or consolidation

## Explicit limitations (0.1.4)

- No transactions across event/episode/trace stores
- No concurrent writer support
- No production IAM or relationship-based access control
- No retention job execution
- No deletion workflows yet
- Not a production-grade governed runtime
