"""`CanonicalSecurityResolutionService` -- Sprint N Phase 3, the
orchestration layer over Sprint M's `CanonicalSecurity` foundation.

Accepts investor input plus every `ProviderCandidate` gathered for that
input (candidate *search* itself -- calling real providers -- is
explicitly out of scope this sprint, per the brief's own "not a
provider-integration sprint"; candidates arrive already assembled).
Produces a `ResolutionResult` carrying the outcome, the accepted
`CanonicalSecurity` (only for `AUTO_ACCEPT`), and the complete evidence
trail (Phase 10) needed to answer "why was this security selected" for
every candidate considered, accepted or not.

**What this service never does, structurally, not just by convention:**
- Never creates a `BusinessRecord` -- no import of
  `atlas.analysis_engine.business_data` or
  `atlas.alpha.business_data_refresh` anywhere in this package.
- Never creates a `Case` -- no import of `atlas.core.domain.case` or
  `atlas.alpha.case_generation`.
- Never calls a provider or modifies a `ProviderCandidate` -- every
  candidate is a frozen dataclass (`candidates.py`), and `resolve()`
  only ever reads from the candidates it is given.
- Never mutates a supplied `existing` `CanonicalSecurity` -- Sprint M's
  own aggregate methods (`add_listing`, `add_provider_mapping`,
  `transition_to`) are pure functions returning new instances; this
  service calls them exactly the way any other caller would.

Deterministic by construction: `resolve()` calls only pure functions
(`normalization.py`, `comparison.py`, `provider_agreement.py`,
`confidence.py`, `outcomes.py`) plus one injectable `clock` for
timestamps -- the same `ResolutionRequest` (and the same `clock`
override) always produces the same `ResolutionResult`, which is exactly
what `replay.py`'s guarantee depends on.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from atlas.alpha.canonical_security.models import CanonicalSecurity, ListingRef, ProviderMapping
from atlas.alpha.canonical_security.value_objects import IdentityConfidence
from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.alpha.canonical_security_resolution.comparison import (
    FieldComparison,
    compare_candidate_to_existing,
    filter_impossible_candidates,
)
from atlas.alpha.canonical_security_resolution.confidence import calculate_confidence
from atlas.alpha.canonical_security_resolution.exceptions import (
    CandidateNotInEvidenceError,
    ManualConfirmationNotApplicableError,
    NoCandidatesToResolveError,
)
from atlas.alpha.canonical_security_resolution.normalization import normalize_company_text, normalize_ticker
from atlas.alpha.canonical_security_resolution.outcomes import ResolutionOutcome, determine_outcome
from atlas.alpha.canonical_security_resolution.provider_agreement import evaluate_provider_agreement

#: Bumped whenever any pure function this service calls changes in a way
#: that could alter its output for the same input -- the Replay Engine
#: (Phase 12) uses this to distinguish "the algorithm genuinely isn't
#: deterministic" (a real bug) from "this was recorded under an older
#: version" (expected, and not a determinism failure at all).
RESOLUTION_ALGORITHM_VERSION = "1.0.0"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ResolutionRequest:
    investor_ticker: str
    candidates: tuple[ProviderCandidate, ...]
    investor_company_text: str | None = None
    existing_canonical_security: CanonicalSecurity | None = None


@dataclass(frozen=True)
class ResolutionEvidence:
    """One entry per candidate considered, whether or not it was
    selected -- Sprint N Phase 10: "Atlas must always be able to answer
    'why was this Canonical Security selected?'", which requires
    retaining every rejected candidate's own confidence and comparisons,
    not only the winner's."""

    candidate: ProviderCandidate
    confidence: IdentityConfidence
    comparisons_against_existing: tuple[FieldComparison, ...]
    accepted: bool


@dataclass(frozen=True)
class ResolutionResult:
    outcome: ResolutionOutcome
    canonical_security: CanonicalSecurity | None
    selected_candidate: ProviderCandidate | None
    evidence: tuple[ResolutionEvidence, ...]
    normalized_company_text: str
    normalized_ticker: str
    resolved_at: datetime
    resolution_version: str


class CanonicalSecurityResolutionService:
    def resolve(self, request: ResolutionRequest, *, clock=_utc_now) -> ResolutionResult:
        if not request.candidates:
            raise NoCandidatesToResolveError()

        # Steps 1-2: normalize.
        normalized_company_text = normalize_company_text(request.investor_company_text)
        normalized_ticker = normalize_ticker(request.investor_ticker)

        # Step 3: remove impossible (duplicate) candidates.
        surviving = filter_impossible_candidates(request.candidates)

        # Steps 4-10: compare, both cross-candidate (provider agreement)
        # and against any existing identity.
        agreement = evaluate_provider_agreement(surviving)

        confidences: list[IdentityConfidence] = []
        evidence: list[ResolutionEvidence] = []
        comparisons_by_candidate: list[tuple[FieldComparison, ...]] = []
        for candidate in surviving:
            comparisons = (
                compare_candidate_to_existing(candidate, request.existing_canonical_security)
                if request.existing_canonical_security is not None
                else ()
            )
            comparisons_by_candidate.append(comparisons)
            # Step 11: calculate confidence.
            confidence = calculate_confidence(
                candidate, agreement=agreement, existing=request.existing_canonical_security
            )
            confidences.append(confidence)

        # Step 12: determine resolution outcome.
        outcome, selected = determine_outcome(surviving, tuple(confidences), agreement)

        for index, candidate in enumerate(surviving):
            evidence.append(
                ResolutionEvidence(
                    candidate=candidate,
                    confidence=confidences[index],
                    comparisons_against_existing=comparisons_by_candidate[index],
                    accepted=(candidate is selected and outcome == "AUTO_ACCEPT"),
                )
            )

        resolved_at = clock()
        canonical_security: CanonicalSecurity | None = None
        if outcome == "AUTO_ACCEPT" and selected is not None:
            canonical_security = _build_or_extend(
                selected, existing=request.existing_canonical_security, clock=lambda: resolved_at
            )

        return ResolutionResult(
            outcome=outcome,
            canonical_security=canonical_security,
            selected_candidate=selected,
            evidence=tuple(evidence),
            normalized_company_text=normalized_company_text,
            normalized_ticker=normalized_ticker,
            resolved_at=resolved_at,
            resolution_version=RESOLUTION_ALGORITHM_VERSION,
        )

    def confirm_manually(
        self, result: ResolutionResult, *, chosen_candidate: ProviderCandidate, clock=_utc_now
    ) -> CanonicalSecurity:
        """Sprint N Phase 11 -- service-layer-only manual confirmation,
        no UI. Valid only for `MANUAL_CONFIRMATION`, `LOW_CONFIDENCE`, or
        `AMBIGUOUS` outcomes (the outcomes that leave a human choice
        genuinely open); `chosen_candidate` must be one Atlas actually
        considered (present in `result.evidence`), never an arbitrary
        new candidate that bypassed the resolution algorithm entirely.
        Produces a `CANONICAL` `CanonicalSecurity`, preserving the full
        evidence history on `result` itself -- nothing about the
        rejected candidates or the original automatic confidence
        computation is discarded by confirming manually."""
        if result.outcome not in ("MANUAL_CONFIRMATION", "LOW_CONFIDENCE", "AMBIGUOUS"):
            raise ManualConfirmationNotApplicableError(result.outcome)
        if not any(item.candidate == chosen_candidate for item in result.evidence):
            raise CandidateNotInEvidenceError(chosen_candidate.symbol)

        resolved_at = clock()
        return _build_or_extend(chosen_candidate, existing=None, clock=lambda: resolved_at)


def _build_or_extend(
    candidate: ProviderCandidate, *, existing: CanonicalSecurity | None, clock
) -> CanonicalSecurity:
    """Builds a fresh `CANONICAL` `CanonicalSecurity` from `candidate`,
    or -- if `existing` was supplied -- extends it with a corroborating
    `ProviderMapping` (and a new `ListingRef` if the candidate names a
    listing `existing` doesn't already have) rather than creating a
    duplicate aggregate for the same real-world company. Stops at
    `CANONICAL`, never `ACTIVE` -- per Sprint L's own definition,
    `ACTIVE` means a `BusinessRecord` has actually been created
    referencing this security, which this service never does (Sprint N
    Phase 16's shadow-mode boundary)."""
    mapping = ProviderMapping(
        provider_name=candidate.provider_name,
        provider_ticker=candidate.symbol,
        confidence="HIGH",
        verification_status="CORROBORATED" if existing is not None else "UNVERIFIED",
        mapped_at=clock(),
        provider_security_id=candidate.provider_security_id,
        provider_exchange_code=candidate.exchange_display_name,
    )

    if existing is not None:
        security = existing
        if not any(
            m.provider_name == mapping.provider_name and m.provider_ticker == mapping.provider_ticker
            for m in security.provider_mappings
        ):
            security = security.add_provider_mapping(mapping, clock=clock)
        listing = _listing_from_candidate(candidate)
        if listing is not None and not any(
            listing.exchange_mic == existing_listing.exchange_mic and listing.ticker == existing_listing.ticker
            for existing_listing in security.listings
        ):
            security = security.add_listing(listing, clock=clock)
        return security

    assert candidate.company_name is not None
    assert candidate.exchange_mic is not None
    assert candidate.country is not None
    assert candidate.currency is not None

    security = CanonicalSecurity.discover(
        canonical_company_name=candidate.company_name,
        native_ticker=candidate.symbol,
        primary_exchange_mic=candidate.exchange_mic,
        country=candidate.country,
        trading_currency=candidate.currency,
        clock=clock,
    )
    listing = _listing_from_candidate(candidate)
    if listing is not None:
        security = security.add_listing(listing, clock=clock)
    security = security.add_provider_mapping(mapping, clock=clock)
    security = security.transition_to("CANDIDATES_FOUND", clock=clock)
    security = security.transition_to("IDENTITY_VERIFIED", clock=clock)
    security = security.transition_to("CONFIRMED", clock=clock)
    security = security.transition_to("CANONICAL", clock=clock)
    return security


def _listing_from_candidate(candidate: ProviderCandidate) -> ListingRef | None:
    if candidate.exchange_mic is None or candidate.currency is None:
        return None
    return ListingRef(
        ticker=candidate.symbol,
        exchange_mic=candidate.exchange_mic,
        currency=candidate.currency,
        relationship=candidate.listing_relationship or "NATIVE",
        security_type=candidate.security_type or "COMMON_STOCK",
        provider_symbol=candidate.symbol,
    )
