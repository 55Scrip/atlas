"""Industry Coverage Honesty (Calibration Phase 7, Phase 14).

`industry_support_level` is **generated directly from the real rule
tables** in `valuation_context.py`/`capital_allocation_context.py`/
`moat_context.py` -- never asserted as a separate, independent claim.
This is deliberate: a support-level table maintained by hand can drift
out of sync with what the code actually does (a family could be marked
`STRONG` here while its own rule tables silently default to generic
everywhere); generating it from the same tables the interpretation
functions themselves read makes that drift structurally impossible.

- `STRONG` -- the family has at least one dedicated rule (a real,
  non-default entry) in any of the three interpretation tables.
- `PARTIAL` -- the family is classified (not `UNCLASSIFIED`/`UNKNOWN`)
  but has no dedicated rule anywhere -- the generic, non-industry-
  adjusted read applies everywhere for this family, honestly.
- `UNSUPPORTED` -- `UNCLASSIFIED` or `UNKNOWN`: no classification to
  reason from at all.
"""
from __future__ import annotations

from atlas.alpha.industry_intelligence.capital_allocation_context import (
    METRIC_NOT_APPROPRIATE_REASONING,
    STRUCTURALLY_NORMAL_REASONING,
)
from atlas.alpha.industry_intelligence.models import IndustryFamily, IndustrySupportLevel
from atlas.alpha.industry_intelligence.moat_context import RELEVANT_EVIDENCE
from atlas.alpha.industry_intelligence.valuation_context import (
    POOR_FIT_REASONING,
    USEFUL_WITH_CAVEATS_REASONING,
)

__all__ = ["industry_support_level"]

_FAMILIES_WITH_A_DEDICATED_RULE: frozenset[IndustryFamily] = frozenset(
    {
        *POOR_FIT_REASONING.keys(),
        *USEFUL_WITH_CAVEATS_REASONING.keys(),
        *STRUCTURALLY_NORMAL_REASONING.keys(),
        *METRIC_NOT_APPROPRIATE_REASONING.keys(),
        *RELEVANT_EVIDENCE.keys(),
    }
)


def industry_support_level(family: IndustryFamily) -> IndustrySupportLevel:
    """Deterministic: identical `family` always produces an identical
    `IndustrySupportLevel`."""
    if family in (IndustryFamily.UNCLASSIFIED, IndustryFamily.UNKNOWN):
        return IndustrySupportLevel.UNSUPPORTED
    if family in _FAMILIES_WITH_A_DEDICATED_RULE:
        return IndustrySupportLevel.STRONG
    return IndustrySupportLevel.PARTIAL
