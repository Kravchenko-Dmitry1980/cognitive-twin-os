"""Policy-aware episode retrieval — gate before returning results."""

from __future__ import annotations

from typing import Any

from cognitive_twin.episodes import Episode
from cognitive_twin.errors import InvalidRetrievalRequestError
from cognitive_twin.operation_trace import TraceWriter, record_operation
from cognitive_twin.policy_engine import (
    DEFAULT_ALLOWED_SENSITIVITIES,
    EpisodePolicyEvaluation,
    PolicyDecisionValue,
    PolicyEvaluationContext,
    PolicyGate,
    PolicyReasonCode,
)
from cognitive_twin.retrieval import (
    MAX_RETRIEVAL_LIMIT,
    RetrievalFilter,
    RetrievalItem,
    RetrievalRequest,
    RetrievalResponse,
    filter_episodes,
)
from cognitive_twin.store import EventEpisodeRepository
from cognitive_twin.traces import TraceStatus

OPERATION_VERSION = "0.1.4"


def _filter_keys(filters: RetrievalFilter) -> list[str]:
    return sorted(filters.model_dump(mode="json", exclude_none=True).keys())


def _policy_decision_counts(
    evaluations: list[EpisodePolicyEvaluation],
) -> dict[str, int]:
    counts = {code.value: 0 for code in PolicyReasonCode}
    for evaluation in evaluations:
        counts[evaluation.reason_code.value] += 1
    return {key: value for key, value in counts.items() if value > 0}


def _safe_trace_metadata(
    request: RetrievalRequest,
    *,
    total_candidates: int,
    total_allowed: int,
    total_denied: int,
    returned_count: int,
    evaluations: list[EpisodePolicyEvaluation],
) -> dict[str, Any]:
    return {
        "request_id": request.request_id,
        "total_candidates": total_candidates,
        "total_allowed": total_allowed,
        "total_denied": total_denied,
        "returned_count": returned_count,
        "offset": request.offset,
        "limit": request.limit,
        "filter_keys": _filter_keys(request.filters),
        "has_policy_scope": request.policy is not None,
        "policy_decision_counts": _policy_decision_counts(evaluations),
        "operation_version": OPERATION_VERSION,
    }


def _build_policy_context(request: RetrievalRequest) -> PolicyEvaluationContext:
    policy_scope = request.policy
    allowed = (
        list(policy_scope.allowed_sensitivities)
        if policy_scope is not None and policy_scope.allowed_sensitivities is not None
        else list(DEFAULT_ALLOWED_SENSITIVITIES)
    )
    return PolicyEvaluationContext(
        actor_id=(
            policy_scope.actor_id
            if policy_scope is not None and policy_scope.actor_id is not None
            else request.actor_id
        ),
        purpose=policy_scope.purpose if policy_scope is not None else None,
        allowed_sensitivities=allowed,
        allow_imported=policy_scope.allow_imported if policy_scope is not None else False,
        include_policy_decisions=(
            policy_scope.include_policy_decisions if policy_scope is not None else True
        ),
    )


class PolicyAwareEpisodeRetriever:
    """
    Release-facing retrieval API: structured filter → policy gate → pagination.

    Denied episodes are excluded from items. External policy decisions expose
    episode_id, decision, and reason_code only.
    """

    def __init__(
        self,
        event_store: EventEpisodeRepository,
        *,
        episode_store: EventEpisodeRepository | None = None,
        policy_gate: PolicyGate | None = None,
        trace_store: TraceWriter | None = None,
    ) -> None:
        self._event_store = event_store
        self._episode_store = episode_store or event_store
        self._policy_gate = policy_gate or PolicyGate()
        self._trace_store = trace_store

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        self._validate_request(request)

        try:
            return self._retrieve_internal(request)
        except Exception as exc:
            record_operation(
                self._trace_store,
                operation="policy_retrieve_episodes",
                status=TraceStatus.FAILED,
                input_refs=[request.request_id],
                actor_id=request.actor_id,
                error=str(exc),
                metadata=_safe_trace_metadata(
                    request,
                    total_candidates=0,
                    total_allowed=0,
                    total_denied=0,
                    returned_count=0,
                    evaluations=[],
                ),
            )
            raise

    def _validate_request(self, request: RetrievalRequest) -> None:
        if request.limit < 1 or request.limit > MAX_RETRIEVAL_LIMIT:
            raise InvalidRetrievalRequestError(
                f"limit must be between 1 and {MAX_RETRIEVAL_LIMIT}, got {request.limit}"
            )
        if request.offset < 0:
            raise InvalidRetrievalRequestError(
                f"offset must be >= 0, got {request.offset}"
            )

    def _retrieve_internal(self, request: RetrievalRequest) -> RetrievalResponse:
        candidates = filter_episodes(self._episode_store, request.filters)
        context = _build_policy_context(request)

        evaluations = self._policy_gate.evaluate_episodes(
            candidates,
            self._event_store,
            context,
        )

        allowed_pairs: list[tuple[Episode, EpisodePolicyEvaluation]] = []
        denied_evaluations: list[EpisodePolicyEvaluation] = []

        for episode, evaluation in zip(candidates, evaluations, strict=True):
            if evaluation.decision == PolicyDecisionValue.ALLOW:
                allowed_pairs.append((episode, evaluation))
            else:
                denied_evaluations.append(evaluation)

        total_candidates = len(candidates)
        total_allowed = len(allowed_pairs)
        total_denied = len(denied_evaluations)

        page = allowed_pairs[request.offset : request.offset + request.limit]

        items = [
            RetrievalItem(
                episode_id=episode.episode_id,
                episode=episode,
                policy_result=evaluation.decision,
            )
            for episode, evaluation in page
        ]

        policy_decisions: list[EpisodePolicyEvaluation] | None = None
        if context.include_policy_decisions:
            policy_decisions = [
                evaluation for _, evaluation in allowed_pairs
            ] + denied_evaluations

        trace = record_operation(
            self._trace_store,
            operation="policy_retrieve_episodes",
            status=TraceStatus.SUCCEEDED,
            input_refs=[request.request_id],
            output_refs=[item.episode_id for item in items],
            actor_id=request.actor_id,
            policy_result={
                "total_candidates": total_candidates,
                "total_allowed": total_allowed,
                "total_denied": total_denied,
            },
            metadata=_safe_trace_metadata(
                request,
                total_candidates=total_candidates,
                total_allowed=total_allowed,
                total_denied=total_denied,
                returned_count=len(items),
                evaluations=evaluations,
            ),
        )

        return RetrievalResponse(
            request_id=request.request_id,
            items=items,
            total_candidates=total_candidates,
            total_allowed=total_allowed,
            total_denied=total_denied,
            returned_count=len(items),
            offset=request.offset,
            limit=request.limit,
            policy_decisions=policy_decisions,
            trace_id=trace.trace_id,
        )
