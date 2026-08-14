"""Internal proof representation (`DE-015` §16 Proof Standard).

**Not a public Domain Object.** `DE-015` §16 is explicit: "no new public
Domain Object is created for this -- it is a synthesis rule, not a type."
`ProofVerdict`/`PathProof` exist purely so `scenario_proof.py`/
`net_cash_proof.py`/`synthesis.py` can pass a per-path verdict around
without conflating it with the public, three-state `ValuationSupportStatus`
-- a single path's own opinion is never itself a `ValuationSupport.status`.
Nothing outside `atlas.analysis_engine.valuation`'s own implementation
modules imports this module; `support.py`'s own `__all__` does not name
it, and it is never referenced by any API schema, frontend type, or any
other domain's code (verified by
`tests/unit/analysis_engine/valuation/test_proof_boundary.py`).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = ["ProofVerdict", "PathProof"]


class ProofVerdict(str, Enum):
    """One valuation capability's own opinion about one real case --
    never itself shown to a consumer, never itself a
    `ValuationSupportStatus`."""

    ESTABLISHES_SUPPORT = "establishes_support"
    ESTABLISHES_NON_SUPPORT = "establishes_non_support"
    DOES_NOT_ESTABLISH = "does_not_establish"


@dataclass(frozen=True)
class PathProof:
    """`path_name` is a short, stable internal identifier (e.g.
    `"scenario"`, `"net_cash"`) -- never rendered to a user, only used
    for internal traceability and to build `ValuationSupport.reasoning`
    text. `evidence_summary` is plain internal diagnostic text, not
    itself the public `reasoning` string."""

    path_name: str
    verdict: ProofVerdict
    evidence_summary: str
