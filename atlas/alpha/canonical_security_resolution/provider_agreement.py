"""Provider Agreement Engine -- Sprint N Phase 8.

Groups a candidate set by canonicalized company name and reports
whether they agree. This is the direct implementation of the brief's
own two worked examples:

    SEC -> Moelis, Twelve Data -> LVMH -> AMBIGUOUS
    SEC -> Evotec, OpenFIGI -> Evolution -> AMBIGUOUS

Grouping by canonicalized name (rather than by ticker, which every
candidate already shares by construction of a single resolution
request) is deliberate: two candidates sharing a ticker are exactly the
case that might be the *same* security reported twice, or might be two
completely different companies that happen to reuse a ticker on
different exchanges -- the two Sprint H/I collisions are both the
latter. Grouping by what each provider actually claims the company
*is* (not just which symbol it used) is what correctly separates them.

Multiple candidates landing in the *same* group is corroboration and
raises confidence (Phase 7); candidates split across more than one
group is `has_conflict=True` and must never be resolved by any
counting/majority rule -- see `confidence.py`'s own comment on why a
strict majority is capped at `MEDIUM`, never promoted to `HIGH`.
"""
from __future__ import annotations

from dataclasses import dataclass

from atlas.alpha.canonical_security_resolution.candidates import ProviderCandidate
from atlas.alpha.canonical_security_resolution.normalization import normalize_company_text


@dataclass(frozen=True)
class ProviderAgreementResult:
    groups: tuple[tuple[ProviderCandidate, ...], ...]
    has_conflict: bool
    dominant_group: tuple[ProviderCandidate, ...] | None


def evaluate_provider_agreement(candidates: tuple[ProviderCandidate, ...]) -> ProviderAgreementResult:
    """Group `candidates` by canonicalized company name. Candidates with
    no `company_name` at all form their own singleton group each (there
    is nothing to agree or disagree about -- see `comparison.py`'s
    `agrees=None` philosophy, applied here at the group level: absence
    of data is never treated as either agreement or conflict)."""
    groups_by_key: dict[str, list[ProviderCandidate]] = {}
    order: list[str] = []
    for index, candidate in enumerate(candidates):
        normalized = normalize_company_text(candidate.company_name)
        key = normalized if normalized else f"__no_name_{index}__"
        if key not in groups_by_key:
            groups_by_key[key] = []
            order.append(key)
        groups_by_key[key].append(candidate)

    groups = tuple(tuple(groups_by_key[key]) for key in order)
    named_groups = tuple(group for group in groups if not group[0].company_name in (None, ""))

    has_conflict = len(named_groups) > 1
    dominant_group: tuple[ProviderCandidate, ...] | None = None
    if named_groups:
        sizes = [len(group) for group in named_groups]
        max_size = max(sizes)
        if sizes.count(max_size) == 1:
            dominant_group = next(group for group in named_groups if len(group) == max_size)

    return ProviderAgreementResult(groups=groups, has_conflict=has_conflict, dominant_group=dominant_group)
