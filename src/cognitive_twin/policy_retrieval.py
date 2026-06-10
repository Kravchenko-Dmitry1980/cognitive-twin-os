"""Policy-aware episode retrieval — gate before returning results."""

from __future__ import annotations

from cognitive_twin.episodes import Episode
from cognitive_twin.errors import InvalidRetrievalRequestError
from cognitive_twin.operation_trace import TraceWriter, record_operation
from cognitive_twin.policy_engine import (
    DEFAULT_ALLOWED_SENSITIVITIES,
    EpisodePolicyEvaluation,
    PolicyDecisionValue,
    PolicyEvaluationContext,
    PolicyGate,
)
from cognitive_twin.retrieval import (
    MAX_RETRIEVAL_LIMIT,
    RetrievalItem,
    RetrievalRequest,
    RetrievalResponse,
    StructuredEpisodeRetriever,
    filter_episodes,
)
from cognitive_twin.store import EventEpisodeRepository
from cognitive_twin.traces import TraceStatus


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
    Structured filter → policy gate → pagination.

    Denied episodes are excluded from items. Policy decision metadata for denied
    episodes contains ids and reason codes only — no episode payload.
    """

    def __init__(
        self,
        event_store: EventEpisodeRepository,
        *,
        episode_store: EventEpisodeRepository | None = None,
        policy_gate: PolicyGate | None = None,
        trace_store: TraceWriter | None = None,
        structured_retriever: StructuredEpisodeRetriever | None = None,
    ) -> None:
        self._event_store = event_store
        self._episode_store = episode_store or event_store
        self._policy_gate = policy_gate or PolicyGate()
        self._structured_retriever = structured_retriever or StructuredEpisodeRetriever()
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
                metadata={
                    "request_id": request.request_id,
                    "filters": request.filters.model_dump(
                        mode="json", exclude_none=True
                    ),
                    "limit": request.limit,
                    "offset": request.offset,
                },
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
                denied_reason=evaluation.denied_reason,
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
            metadata={
                "request_id": request.request_id,
                "total_candidates": total_candidates,
                "total_allowed": total_allowed,
                "total_denied": total_denied,
                "offset": request.offset,
                "limit": request.limit,
                "filters": request.filters.model_dump(mode="json", exclude_none=True),
            },
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
