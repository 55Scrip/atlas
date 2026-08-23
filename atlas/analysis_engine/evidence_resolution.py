"""Product Sprint 14 (Evidence & Explanation Quality) -- resolves the
opaque evidence-reference strings `BusinessFinding`/`ValuationFinding`/
`RiskFinding` carry (see each dataclass's own docstring in
`business_contracts.py`/`valuation/models.py`/`risk/models.py`) into
real, human-readable sentences.

Product Sprint 13 discovered this live: the frontend was receiving
strings like `21ea5c5cd63a91e1eebaea01df3a9645:v1:free_cash_flow:2017-06-30`
and `business_finding:growth` instead of prose, and added a defensive
filter (`isReadableFact`) to hide them. Sprint 14's own investigation
traced why: `supporting_evidence`/`contradicting_evidence`/
`supporting_facts`/`contradicting_facts` were designed, from the start,
to carry opaque reference strings -- `BusinessFact`/`ValuationFact` ids,
a Finding's own self-reference id, or (Thesis Risk only) an
`Observation` id -- on the documented assumption that a resolver would
exist before display. No such resolver was ever built. This module is
that resolver.

Every sentence this module produces is built only from fields the
referenced object's own producer already computed:
- A `BusinessFact`/`ValuationFact` reference resolves to a sentence
  built from that fact's own real `kind`/`value`/`unit`/`period`.
- A Finding self-reference (another `BusinessFinding`/`ValuationFinding`/
  `RiskFinding`'s own `id`) resolves to that finding's own real
  category/kind and status.
- An `Observation` reference resolves to that Observation's own real,
  investor-recorded `statement`.

No new fact is computed and no new conclusion is drawn -- this module
only chooses which already-real field to present as a sentence. A
reference it cannot resolve (a stale id from data since superseded, or
a shape it doesn't recognize) falls back to the original reference
string, unchanged -- an honest "could not resolve" is always safer
than an invented sentence. This is why Sprint 13's `isReadableFact`
frontend filter is kept as a defensive backstop, not removed: it
should simply stop triggering once every reference resolves.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Union

from atlas.analysis_engine.business_contracts import BusinessFinding
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.risk.models import RiskFinding
from atlas.analysis_engine.valuation.facts import ValuationFact
from atlas.analysis_engine.valuation.models import ValuationFinding
from atlas.core.domain.observation.entity import Observation

__all__ = ["resolve_evidence_references"]

AnyFact = Union[BusinessFact, ValuationFact]
AnyFinding = Union[BusinessFinding, ValuationFinding, RiskFinding]


def _label(value: object) -> str:
    """`value` is always a closed enum's own `.value` (a lowercase,
    underscore-separated string, e.g. `"free_cash_flow"`) -- this only
    reformats it for prose, never chooses or invents the word itself."""
    return str(value).replace("_", " ").capitalize()


def _describe_fact(fact: AnyFact) -> str:
    kind_label = _label(fact.kind.value)
    value_label = f"{fact.value:,.0f}" if abs(fact.value) >= 1 else f"{fact.value:,.4f}"
    return f"{kind_label} was {value_label} {fact.unit} for the period ending {fact.period}."


def _describe_finding(finding: AnyFinding) -> str:
    if isinstance(finding, RiskFinding):
        kind_label = _label(finding.category.value)
    else:
        kind_label = _label(finding.kind.value)
    return f"{kind_label}: {_label(finding.status.value)}."


def resolve_evidence_references(
    references: tuple[str, ...],
    *,
    facts_by_id: Mapping[str, AnyFact],
    findings_by_id: Mapping[str, AnyFinding],
    observations_by_id: Mapping[str, Observation],
) -> tuple[str, ...]:
    """Resolves each reference independently; order and count are
    preserved (never deduplicated, never dropped) so a caller comparing
    resolved-length to the original tuple sees no surprise."""
    resolved: list[str] = []
    for reference in references:
        if reference in findings_by_id:
            resolved.append(_describe_finding(findings_by_id[reference]))
        elif reference in facts_by_id:
            resolved.append(_describe_fact(facts_by_id[reference]))
        elif reference in observations_by_id:
            resolved.append(str(observations_by_id[reference].statement))
        else:
            resolved.append(reference)
    return tuple(resolved)
