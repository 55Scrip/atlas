"""The canonical `BusinessFact` model (ATLAS-023, Phase 2).

Sits between `atlas.analysis_engine.business_data` (raw documents) and
`atlas.analysis_engine.business` (category judgments): one atomic,
normalized, structured numeric observation, extracted deterministically
from exactly one `BusinessRecord`, never interpreted or scored here.

**No `confidence` field** -- Phase 2's own suggested structure named
one, and it is deliberately not built. Every `BusinessFact` this sprint
produces is extracted by exact, deterministic key lookup (see
`extraction.py`): either the value is present, well-typed, and
uncontested, in which case the fact exists in full, or it is not, in
which case no `BusinessFact` is constructed at all. There is no partial
or uncertain extraction state for a single fact to grade -- applying
`EvidenceCoverageLevel` (a *collection*-coverage concept: "how many of
several items have evidence") to one atomic value would be exactly the
silent overload Phase 9 warns against, not a real reuse. Confidence is
computed instead where it *is* meaningful: at the `BusinessFinding`
level, from how many of a category's relevant fact kinds are actually
populated (see `atlas.analysis_engine.growth`/`capital_allocation`).

**`period` is a plain string, not a `date`.** `BusinessRecord.metadata`
values are typed `str | int | float | bool | None` with no date type
(ATLAS-022), and a fact's period is always inherited from the source
`BusinessRecord`'s own `period_end` (or `period_start` if no end is
recorded) -- never invented or parsed from free text. Periods must be
supplied in a lexicographically sortable format (e.g. `"2024"`,
`"2024-Q3"`, an ISO date) for evaluators to order them correctly; this
package never reformats or validates that convention, since doing so
would require assuming a calendar/fiscal-year convention no source data
here confirms. A real, named limitation, not a silent one.

**`published_at` (ATLAS-032) is when the source was actually made
public -- the SEC filing date, the market data fetch time -- inherited
verbatim from the source `BusinessRecord.published_at`, never derived
from `period`.** `period` and `published_at` answer different
questions and must never be confused: `period` is what the fact is
*about* (a fiscal year, a trading date), `published_at` is when Atlas
(or anyone) could first have known the value. A fiscal year's period
end is typically weeks to months before the filing that discloses it
actually publishes -- this field exists so evaluators can enforce "no
look-ahead" (never pair a fact with something published before this
fact itself was public) without conflating the two.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.provenance import Provenance

__all__ = ["BusinessFact"]


@dataclass(frozen=True)
class BusinessFact:
    """One atomic, structured business fact.

    `id` is deterministic: `f"{source_record_id}:{kind.value}:{period}"`
    -- identical inputs always produce the identical id, and two facts
    of the same kind and period from the same source record collide by
    construction (there is only ever one).
    """

    id: str
    company: str
    kind: BusinessFactKind
    value: float
    unit: str
    period: str
    source_record_id: str
    provenance: Provenance
    extracted_at: datetime
    published_at: datetime
