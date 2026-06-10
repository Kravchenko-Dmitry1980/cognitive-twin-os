"""Minimal deterministic policy gate for episode retrieval."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from cognitive_twin.episodes import Episode
from cognitive_twin.errors import UnknownPolicyReferenceError
from cognitive_twin.events import ConsentBasis, Sensitivity
from cognitive_twin.store import EventRepository

DEFAULT_ALLOWED_SENSITIVITIES: tuple[Sensitivity, ...] = (
    Sensitivity.PUBLIC,
    Sensitivity.INTERNAL,
)


class PolicyDecisionValue(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REDACT = "redact"


class PolicyReasonCode(StrEnum):
    ALLOWED = "allowed"
    ACCESS_DENIED = "access_denied"
    CONSENT_NOT_ALLOWED = "consent_not_allowed"
    UNKNOWN_REFERENCE = "unknown_reference"
    POLICY_ERROR = "policy_error"


class PolicyEvaluationContext(BaseModel):
    """Input scope for evaluating episodes against event governance."""

    actor_id: str | None = None
    purpose: str | None = None
    allowed_sensitivities: list[Sensitivity] = Field(
        default_factory=lambda: list(DEFAULT_ALLOWED_SENSITIVITIES)
    )
    allow_imported: bool = False
    include_policy_decisions: bool = True


class EpisodePolicyEvaluation(BaseModel):
    """External per-episode policy outcome — reason_code only, no denial details."""

    episode_id: str
    decision: PolicyDecisionValue
    reason_code: PolicyReasonCode


class PolicyGate:
    """
    Evaluate episodes against governance of referenced events.

    Conservative by default: private/sensitive and imported consent are denied
    unless explicitly allowed in the evaluation context.
    """

    def evaluate_episode(
        self,
        episode: Episode,
        event_store: EventRepository,
        context: PolicyEvaluationContext,
    ) -> EpisodePolicyEvaluation:
        allowed_set = set(context.allowed_sensitivities)

        for event_id in episode.event_ids:
            event = event_store.get_event(event_id)
            if event is None:
                raise UnknownPolicyReferenceError(
                    f"Episode '{episode.episode_id}' references unknown event_id: "
                    f"{event_id!r}"
                )

            governance = event.governance
            if governance.sensitivity not in allowed_set:
                return EpisodePolicyEvaluation(
                    episode_id=episode.episode_id,
                    decision=PolicyDecisionValue.DENY,
                    reason_code=PolicyReasonCode.ACCESS_DENIED,
                )

            if (
                governance.consent_basis == ConsentBasis.IMPORTED
                and not context.allow_imported
            ):
                return EpisodePolicyEvaluation(
                    episode_id=episode.episode_id,
                    decision=PolicyDecisionValue.DENY,
                    reason_code=PolicyReasonCode.CONSENT_NOT_ALLOWED,
                )

        return EpisodePolicyEvaluation(
            episode_id=episode.episode_id,
            decision=PolicyDecisionValue.ALLOW,
            reason_code=PolicyReasonCode.ALLOWED,
        )

    def evaluate_episodes(
        self,
        episodes: list[Episode],
        event_store: EventRepository,
        context: PolicyEvaluationContext,
    ) -> list[EpisodePolicyEvaluation]:
        return [
            self.evaluate_episode(episode, event_store, context)
            for episode in episodes
        ]
