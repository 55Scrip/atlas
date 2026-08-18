"""Resolution algorithm steps 3-10 (Sprint N Phase 5): filter impossible
candidates, then compare surviving candidates field-by-field against
each other and against an existing `CanonicalSecurity`, if one was
supplied.

Every comparison here is a plain equality check on already-normalized
values -- no fuzzy matching, no scoring, no randomness. `agrees=None`
(rather than `True`/`False`) is the honest representation of "this
field is absent on one or both sides, so nothing can be concluded" --
distinct from `agrees=False` ("both sides have a value, and they
disagree"). `confidence.py` treats these very differently: a `None`
never lowers confidence on its own (missing data is not evidence of a
problem), while a `False` (Sprint N Phase 7's own conflict-lowers-
confidence requirement) always does.
"""
from __future__ import annotations

from dataclasses import dataclass

from atlas.alpha.canonical_security.models import CanonicalSecurity
from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.alpha.canonical_security_resolution.normalization import normalize_company_text


@dataclass(frozen=True)
class FieldComparison:
    field_name: str
    agrees: bool | None  # None = not comparable (a value is missing on one or both sides)
    left_value: str | None
    right_value: str | None


def filter_impossible_candidates(
    candidates: tuple[ProviderCandidate, ...],
) -> tuple[ProviderCandidate, ...]:
    """Resolution algorithm step 3. Every `ProviderCandidate` already
    guarantees a non-blank `symbol` (`candidates.py`'s own `__post_init__`)
    -- what remains here is deduplication: two candidates from the same
    provider naming the exact same symbol are the same claim reported
    twice (e.g. a provider's own API returning a duplicate row), not two
    independent pieces of corroborating evidence, and counting them
    twice would silently inflate provider-agreement confidence
    (Phase 8) without any real second source. Order is preserved for
    the first occurrence of each `(provider_name, symbol)` pair."""
    seen: set[tuple[str, str]] = set()
    survivors: list[ProviderCandidate] = []
    for candidate in candidates:
        key = (candidate.provider_name, candidate.symbol)
        if key in seen:
            continue
        seen.add(key)
        survivors.append(candidate)
    return tuple(survivors)


def _compare(field_name: str, left: str | None, right: str | None) -> FieldComparison:
    if left is None or right is None:
        return FieldComparison(field_name, None, left, right)
    return FieldComparison(field_name, left == right, left, right)


def compare_candidates(a: ProviderCandidate, b: ProviderCandidate) -> tuple[FieldComparison, ...]:
    """Resolution algorithm steps 4-10, candidate-to-candidate. Company
    name is compared via `normalize_company_text` (step 4); every other
    field is compared as already-normalized value objects (`MicCode`
    already uppercases itself, `TradingCurrency` already validates and
    uppercases -- see `atlas.alpha.canonical_security.value_objects`),
    so no further normalization is needed here."""
    return (
        _compare(
            "company_name",
            normalize_company_text(a.company_name) or None,
            normalize_company_text(b.company_name) or None,
        ),
        _compare("exchange_mic", a.exchange_mic.value if a.exchange_mic else None, b.exchange_mic.value if b.exchange_mic else None),
        _compare("country", a.country, b.country),
        _compare("currency", a.currency.value if a.currency else None, b.currency.value if b.currency else None),
        _compare("security_type", a.security_type, b.security_type),
        _compare("listing_relationship", a.listing_relationship, b.listing_relationship),
        _compare("isin", a.isin, b.isin),
        _compare("figi", a.figi, b.figi),
        _compare("cusip", a.cusip, b.cusip),
        _compare("sedol", a.sedol, b.sedol),
    )


def compare_candidate_to_existing(
    candidate: ProviderCandidate, existing: CanonicalSecurity
) -> tuple[FieldComparison, ...]:
    """Resolution algorithm steps 4-10, candidate-to-existing-identity.
    Used when a `ResolutionRequest` supplies an already-`CANONICAL`
    security (e.g. re-resolving a ticker to add a second provider's
    corroboration) -- a disagreement here is exactly the SEC-EDGAR-style
    "this ticker used to mean company X, this new evidence says
    something else" case Sprint N Phase 7's REJECTED rule exists for."""
    existing_primary = existing.primary_listing
    return (
        _compare(
            "company_name",
            normalize_company_text(candidate.company_name) or None,
            normalize_company_text(existing.canonical_company_name) or None,
        ),
        _compare(
            "exchange_mic",
            candidate.exchange_mic.value if candidate.exchange_mic else None,
            existing.primary_exchange_mic.value,
        ),
        _compare("country", candidate.country, existing.country),
        _compare(
            "currency",
            candidate.currency.value if candidate.currency else None,
            existing.trading_currency.value,
        ),
        _compare(
            "security_type",
            candidate.security_type,
            existing_primary.security_type if existing_primary else None,
        ),
    )
