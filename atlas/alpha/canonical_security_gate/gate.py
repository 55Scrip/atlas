"""`CanonicalSecurityIdentityGate` -- Sprint O Phase 3/4.

The one mandatory checkpoint between "a provider returned data for a
ticker" and "a `BusinessRecord` gets created for it." Implements
exactly Sprint N's Resolution Service outcome table, unmodified:

    AUTO_ACCEPT          -> proceed (BusinessRecord creation allowed)
    MANUAL_CONFIRMATION  -> stop
    LOW_CONFIDENCE       -> stop
    AMBIGUOUS            -> stop
    NO_MATCH             -> stop
    REJECT               -> stop

No fallback, no provider retry, no automatic ADR substitution --
`evaluate()` makes exactly one resolution attempt per call and returns
a `GateDecision` the caller (`business_data_refresh.service
.refresh_company_data`) acts on deterministically.

**Every attempt is persisted, allowed or not** (Phase 7's "no silent
failures"): `evaluate()` always calls `SqlAlchemyResolutionRepository
.save()`, even for the zero-candidate case, which is handled here
without ever calling `CanonicalSecurityResolutionService.resolve()`
(that method raises `NoCandidatesToResolveError` for an empty candidate
tuple -- a real, expected, common case this gate must not treat as a
crash) by constructing the equivalent `NO_MATCH` `ResolutionResult`
directly, using the exact same normalization functions `resolve()`
itself would have called.

**Existing-identity lookup is best-effort and conservative.** If at
least one candidate carries an `exchange_mic`, this gate looks up
`CanonicalSecurityRepository.find_by_ticker_and_exchange` for that
exact (ticker, exchange) pair before resolving -- giving
`CanonicalSecurityResolutionService` a real `existing` to compare
against (Phase 5's "if a CanonicalSecurity already exists, reuse it;
never create duplicates"). No candidate carrying an exchange means no
lookup is attempted; `existing=None` is always the safe default, never
a guess.

This is the one package in this codebase explicitly allowed to import
*both* `atlas.alpha.canonical_security`/`canonical_security_resolution`
*and* `atlas.analysis_engine.business_data` -- see the updated
integration-safety guards in both canonical-security test directories.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from atlas.alpha.canonical_security.models import CanonicalSecurity
from atlas.alpha.canonical_security.repository import SqlAlchemyCanonicalSecurityRepository
from atlas.alpha.canonical_security_gate.candidate_mapping import candidates_from_documents
from atlas.alpha.canonical_security_gate.provenance import BusinessRecordIdentityProvenance
from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.alpha.canonical_security_resolution.normalization import normalize_company_text, normalize_ticker
from atlas.alpha.canonical_security_resolution.outcomes import ResolutionOutcome
from atlas.alpha.canonical_security_resolution.repository import SqlAlchemyResolutionRepository
from atlas.alpha.canonical_security_resolution.service import (
    RESOLUTION_ALGORITHM_VERSION,
    CanonicalSecurityResolutionService,
    ResolutionRequest,
    ResolutionResult,
)
from atlas.analysis_engine.business_data.models import RawBusinessDocument

__all__ = ["CanonicalSecurityIdentityGate", "GateDecision"]

_REASON_BY_OUTCOME: dict[str, str] = {
    "MANUAL_CONFIRMATION": (
        "Identity resolved with only medium confidence; a human must confirm "
        "before a BusinessRecord can be created."
    ),
    "LOW_CONFIDENCE": (
        "Identity resolved with only low confidence; a human must confirm "
        "before a BusinessRecord can be created."
    ),
    "AMBIGUOUS": "Providers disagree about which company this ticker identifies; a human must resolve the conflict.",
    "NO_MATCH": "No provider returned any identity-bearing candidate for this ticker.",
    "REJECT": "The best-available candidate positively contradicts an already-established identity.",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class GateDecision:
    """`allowed=True` only for `AUTO_ACCEPT` reaching `CANONICAL` --
    every field here is also readable when `allowed=False`, since
    Phase 7 requires every blocked attempt to be just as fully
    explained as an allowed one."""

    allowed: bool
    outcome: ResolutionOutcome
    reason: str
    provenance: BusinessRecordIdentityProvenance | None
    resolution_result: ResolutionResult
    resolution_record_id: str


class CanonicalSecurityIdentityGate:
    def __init__(
        self,
        *,
        resolution_service: CanonicalSecurityResolutionService,
        canonical_security_repository: SqlAlchemyCanonicalSecurityRepository,
        resolution_repository: SqlAlchemyResolutionRepository,
    ) -> None:
        self._resolution_service = resolution_service
        self._canonical_security_repository = canonical_security_repository
        self._resolution_repository = resolution_repository

    def evaluate(
        self,
        *,
        ticker: str,
        documents: tuple[RawBusinessDocument, ...],
        clock=_utc_now,
    ) -> GateDecision:
        candidates = candidates_from_documents(documents)

        if not candidates:
            result = ResolutionResult(
                outcome="NO_MATCH",
                canonical_security=None,
                selected_candidate=None,
                evidence=(),
                normalized_company_text=normalize_company_text(None),
                normalized_ticker=normalize_ticker(ticker),
                resolved_at=clock(),
                resolution_version=RESOLUTION_ALGORITHM_VERSION,
            )
            record_id = self._resolution_repository.save(
                result,
                investor_ticker=ticker,
                investor_company_text=None,
                existing_canonical_security_id=None,
            )
            return GateDecision(
                allowed=False,
                outcome="NO_MATCH",
                reason=_REASON_BY_OUTCOME["NO_MATCH"],
                provenance=None,
                resolution_result=result,
                resolution_record_id=record_id,
            )

        existing = self._find_existing(ticker, candidates)
        request = ResolutionRequest(
            investor_ticker=ticker,
            candidates=candidates,
            existing_canonical_security=existing,
        )
        result = self._resolution_service.resolve(request, clock=clock)

        record_id = self._resolution_repository.save(
            result,
            investor_ticker=ticker,
            investor_company_text=None,
            existing_canonical_security_id=str(existing.id) if existing is not None else None,
        )

        if (
            result.outcome == "AUTO_ACCEPT"
            and result.canonical_security is not None
            and result.canonical_security.resolution_status == "CANONICAL"
        ):
            self._canonical_security_repository.save(result.canonical_security)
            provenance = BusinessRecordIdentityProvenance(
                canonical_security_id=str(result.canonical_security.id),
                resolution_version=result.resolution_version,
                resolved_at=result.resolved_at,
                provider_evidence_reference=record_id,
            )
            return GateDecision(
                allowed=True,
                outcome=result.outcome,
                reason="Resolved to a single, corroborated CanonicalSecurity.",
                provenance=provenance,
                resolution_result=result,
                resolution_record_id=record_id,
            )

        return GateDecision(
            allowed=False,
            outcome=result.outcome,
            reason=_REASON_BY_OUTCOME.get(result.outcome, "Resolution did not reach AUTO_ACCEPT."),
            provenance=None,
            resolution_result=result,
            resolution_record_id=record_id,
        )

    def _find_existing(
        self, ticker: str, candidates: tuple[ProviderCandidate, ...]
    ) -> CanonicalSecurity | None:
        normalized_ticker = ticker.strip().upper()
        for candidate in candidates:
            if candidate.exchange_mic is None:
                continue
            existing = self._canonical_security_repository.find_by_ticker_and_exchange(
                normalized_ticker, candidate.exchange_mic.value
            )
            if existing is not None:
                return existing
        return None
