"""Confidence Engine -- Sprint N Phase 7.

Deterministic, rule-based, first-matching-rule-wins. No score, no
weighting, no randomness -- the same `(candidate, agreement, existing)`
triple always produces the same `IdentityConfidence` (Sprint M's own
four-level vocabulary: `HIGH`/`MEDIUM`/`LOW`/`REJECTED`, reused
unchanged rather than inventing a fifth scale).

**The one rule every other rule is subordinate to (Sprint N Phase 7's
own explicit requirement): ticker equality alone may never produce
`HIGH`.** Rule 3 below enforces this directly -- a candidate with zero
corroborating fields beyond its symbol is capped at `LOW` regardless of
what any other rule would otherwise conclude, and this cap is applied
*last*, after every other rule, so nothing upstream can accidentally
promote a ticker-only candidate past it.

Rules, in evaluation order (first match wins, except the ticker-alone
cap which is applied as a final clamp):

1. **Positive contradiction against an existing identity.** If an
   `existing` `CanonicalSecurity` was supplied and the candidate's
   `company_name` explicitly disagrees with it (a real `agrees=False`,
   not merely missing data) -> `REJECTED`, unconditionally. This is the
   SEC-EDGAR-collision rule: a candidate that positively contradicts an
   already-established company identity is never merely "low
   confidence," it is rejected outright.

   `exchange_mic`/`country` disagreement is *also* treated as a
   contradiction (the "wrong exchange"/"wrong country" cases) -- **but
   only when the candidate does not explicitly declare itself an
   alternate listing** (`listing_relationship` is `None` or `"NATIVE"`).
   A candidate that *does* declare `"ADR"`/`"GDR"`/`"OTC"` is expected to
   disagree with the native listing's exchange (and sometimes trading
   country) -- that disagreement is exactly what Sprint J Phase 10's
   native/ADR linking exists to accommodate, not a collision to reject.
   An undeclared candidate disagreeing on exchange or country, by
   contrast, gives no reason to believe it's a legitimate alternate
   listing rather than a genuinely wrong match.
2. **Provider disagreement.** If `agreement.has_conflict` (candidates
   split across more than one canonicalized company-name group) ->
   `MEDIUM` for a candidate in the uniquely-largest group, `LOW`
   otherwise. Never `HIGH`: conflicting providers must never be
   silently merged into full confidence (Sprint N Phase 8's own
   requirement), even when one side is a clear majority.
3. **Sufficient corroboration.** With no contradiction and no conflict:
   a candidate carrying `exchange_mic`, `country`, and `security_type`
   all present -> `HIGH`. A candidate carrying at least one
   corroborating field but not all three of those -> `MEDIUM`.
4. **Provider-agreement boost.** If the candidate's own agreement group
   (Phase 8) contains more than one independent provider corroborating
   the same company identity, the tier from rule 3 is raised by one
   step (`MEDIUM` -> `HIGH`, `LOW` -> `MEDIUM`) -- multiple providers
   agreeing increases confidence, per Phase 8's own requirement. This
   boost is applied *before* the ticker-alone clamp, so it can never
   produce a `HIGH` for a candidate with zero corroborating fields.
5. **Ticker-alone clamp (final step, always applied).** If
   `candidate.corroborating_field_count() == 0`, the result from every
   rule above is overridden to `LOW` -- unless a contradiction already
   produced `REJECTED` in rule 1, which stands (a ticker-only candidate
   can still be positively wrong if it was the *only* thing supplied
   and it disagrees with known identity).
"""
from __future__ import annotations

from atlas.alpha.canonical_security.models import CanonicalSecurity
from atlas.alpha.canonical_security.value_objects import IdentityConfidence
from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.alpha.canonical_security_resolution.comparison import compare_candidate_to_existing
from atlas.alpha.canonical_security_resolution.provider_agreement import ProviderAgreementResult

_ALWAYS_CONTRADICTION_FIELDS = frozenset({"company_name"})
_NATIVE_ONLY_CONTRADICTION_FIELDS = frozenset({"exchange_mic", "country"})
_TIER_ORDER: tuple[IdentityConfidence, ...] = ("LOW", "MEDIUM", "HIGH")


def calculate_confidence(
    candidate: ProviderCandidate,
    *,
    agreement: ProviderAgreementResult,
    existing: CanonicalSecurity | None = None,
) -> IdentityConfidence:
    # Rule 1 -- positive contradiction against an existing identity.
    if existing is not None:
        comparisons = compare_candidate_to_existing(candidate, existing)
        if any(c.agrees is False and c.field_name in _ALWAYS_CONTRADICTION_FIELDS for c in comparisons):
            return "REJECTED"
        declares_alternate_listing = candidate.listing_relationship not in (None, "NATIVE")
        if not declares_alternate_listing:
            if any(c.agrees is False and c.field_name in _NATIVE_ONLY_CONTRADICTION_FIELDS for c in comparisons):
                return "REJECTED"

    # Rule 2 -- provider disagreement caps below HIGH.
    if agreement.has_conflict:
        in_dominant = agreement.dominant_group is not None and candidate in agreement.dominant_group
        tier: IdentityConfidence = "MEDIUM" if in_dominant else "LOW"
        return _apply_ticker_alone_clamp(candidate, tier)

    # Rule 3 -- sufficient corroboration.
    strong_fields = (candidate.exchange_mic, candidate.country, candidate.security_type)
    if all(field is not None for field in strong_fields):
        tier = "HIGH"
    elif candidate.corroborating_field_count() > 0:
        tier = "MEDIUM"
    else:
        tier = "LOW"

    # Rule 4 -- provider-agreement boost (more than one corroborating provider).
    own_group = next((group for group in agreement.groups if candidate in group), (candidate,))
    if len(own_group) > 1:
        tier = _promote(tier)

    return _apply_ticker_alone_clamp(candidate, tier)


def _promote(tier: IdentityConfidence) -> IdentityConfidence:
    if tier not in _TIER_ORDER:
        return tier
    index = _TIER_ORDER.index(tier)
    return _TIER_ORDER[min(index + 1, len(_TIER_ORDER) - 1)]


def _apply_ticker_alone_clamp(candidate: ProviderCandidate, tier: IdentityConfidence) -> IdentityConfidence:
    if tier == "REJECTED":
        return tier
    if candidate.corroborating_field_count() == 0:
        return "LOW"
    return tier
