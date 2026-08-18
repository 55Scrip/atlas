"""Resolution Outcomes -- Sprint N Phase 6.

Exactly six outcomes, distinct from `CanonicalSecurity`'s own
`ResolutionStatus` lifecycle (Sprint M): an outcome is the answer this
one resolution *attempt* reached; `ResolutionStatus` is where the
resulting aggregate sits afterward. `AUTO_ACCEPT` is the only outcome
that produces a `CANONICAL` `CanonicalSecurity` directly within
`resolve()` itself -- every other outcome leaves aggregate creation to
a later, explicit step (`confirm_manually`, or a future sprint's own
handling of `LOW_CONFIDENCE`/`AMBIGUOUS`/`NO_MATCH`/`REJECT`).

| Outcome | Produced when |
|---|---|
| `AUTO_ACCEPT` | No provider conflict; the resolved candidate's confidence is `HIGH` |
| `MANUAL_CONFIRMATION` | No provider conflict; the resolved candidate's confidence is `MEDIUM` |
| `LOW_CONFIDENCE` | No provider conflict; the resolved candidate's confidence is `LOW` |
| `AMBIGUOUS` | The candidate set splits across more than one company identity (`ProviderAgreementResult.has_conflict`) |
| `NO_MATCH` | Zero candidates survive filtering |
| `REJECT` | No conflict, but the resolved candidate's confidence is `REJECTED` (a positive contradiction against an existing identity) |

`AMBIGUOUS` is checked before `REJECT`: a genuine multi-provider
disagreement (Sprint N Phase 8's own `MC`/`EVO` examples) is always
`AMBIGUOUS`, even if, in isolation, one of the disagreeing candidates
would individually score `REJECTED` against some other existing
identity -- conflict among the *candidates themselves* is the more
specific, more informative signal, and takes priority.
"""
from __future__ import annotations

from typing import Literal

from atlas.alpha.canonical_security.value_objects import IdentityConfidence
from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.alpha.canonical_security_resolution.exceptions import CanonicalSecurityResolutionError
from atlas.alpha.canonical_security_resolution.provider_agreement import ProviderAgreementResult

ResolutionOutcome = Literal[
    "AUTO_ACCEPT", "MANUAL_CONFIRMATION", "LOW_CONFIDENCE", "AMBIGUOUS", "NO_MATCH", "REJECT"
]
_RESOLUTION_OUTCOMES: frozenset[str] = frozenset(
    {"AUTO_ACCEPT", "MANUAL_CONFIRMATION", "LOW_CONFIDENCE", "AMBIGUOUS", "NO_MATCH", "REJECT"}
)


class UnsupportedResolutionOutcomeError(CanonicalSecurityResolutionError):
    def __init__(self, value: str) -> None:
        self.value = value
        super().__init__(f"Unsupported resolution outcome: {value!r}")


def validate_resolution_outcome(value: str) -> ResolutionOutcome:
    if value not in _RESOLUTION_OUTCOMES:
        raise UnsupportedResolutionOutcomeError(value)
    return value  # type: ignore[return-value]


def determine_outcome(
    candidates: tuple[ProviderCandidate, ...],
    confidences: tuple[IdentityConfidence, ...],
    agreement: ProviderAgreementResult,
) -> tuple[ResolutionOutcome, ProviderCandidate | None]:
    """Returns the outcome and the candidate it was decided on ( `None`
    for `NO_MATCH`/`AMBIGUOUS`, since neither has a single resolved
    candidate). `confidences` must be the same length as `candidates`,
    in the same order -- index-aligned rather than dict-keyed, since
    `ProviderCandidate` carries a plain `Mapping` field
    (`raw_metadata`) and is therefore not guaranteed hashable."""
    if not candidates:
        return "NO_MATCH", None

    if agreement.has_conflict:
        return "AMBIGUOUS", None

    if agreement.dominant_group:
        # Among agreeing candidates, prefer the most information-rich one
        # (highest `corroborating_field_count()`) as the representative --
        # e.g. if a sparse SEC EDGAR candidate and a fully-populated Twelve
        # Data candidate agree on company name, the richer one should be
        # what CanonicalSecurity construction (Phase 9's constructibility
        # check, below) actually uses. Ties keep the first occurrence,
        # preserving deterministic tuple order.
        representative = max(agreement.dominant_group, key=lambda c: c.corroborating_field_count())
        representative_index = candidates.index(representative)
    else:
        representative = candidates[0]
        representative_index = 0

    confidence = confidences[representative_index]
    if confidence == "REJECTED":
        return "REJECT", None
    if confidence == "HIGH":
        if _is_constructible(representative):
            return "AUTO_ACCEPT", representative
        # Confidence reached HIGH (possibly via the provider-agreement
        # boost, Confidence Engine rule 4) but the candidate itself
        # lacks a field CanonicalSecurity.discover() requires (company
        # name, exchange MIC, country, or currency -- see
        # `_is_constructible`). Auto-accepting here would either crash
        # constructing the aggregate or silently invent a value for a
        # required field -- neither is acceptable, so this is downgraded
        # to a human decision rather than either of those.
        return "MANUAL_CONFIRMATION", representative
    if confidence == "MEDIUM":
        return "MANUAL_CONFIRMATION", representative
    return "LOW_CONFIDENCE", representative


def _is_constructible(candidate: ProviderCandidate) -> bool:
    """Whether `candidate` alone carries every field
    `CanonicalSecurity.discover()` and `ListingRef` require. Checked
    only for `AUTO_ACCEPT` eligibility -- every other outcome leaves
    aggregate construction to a later, explicit step that can gather
    the missing information first."""
    return (
        candidate.company_name is not None
        and candidate.exchange_mic is not None
        and candidate.country is not None
        and candidate.currency is not None
    )
