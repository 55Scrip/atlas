"""Cross-cutting contracts shared across `atlas.analysis_engine` modules
(ATLAS-020, Phase 8's Risk taxonomy design).

Kept separate from `models.py` (which defines `CanonicalAnalysis`
itself) so a stage module (`conviction.py`, `recommendation.py`, a
future `risk.py`) can import a shared vocabulary without importing the
top-level assembled object.
"""
from __future__ import annotations

from enum import Enum

__all__ = ["RiskCategory", "CapabilityStatus"]


class RiskCategory(str, Enum):
    """A closed, eight-member taxonomy (Phase 8: "design a closed
    taxonomy," not "implement every category"). Every member is real
    investing vocabulary, not invented; which categories this codebase
    can honestly produce a `Finding` for *today* is documented per
    member below -- Risk Findings never omit a category to make the
    taxonomy look more complete than it is; an unproducible category
    simply has zero Findings, the same "empty is a real, honest state"
    principle `atlas.decision_engine.contracts` already established for
    tuples like `evidence_gaps`.

    Risk never produces a recommendation (Phase 8's own instruction) --
    a `RiskCategory` Finding states a fact; only `recommendation.py`'s
    gate ever touches whether that fact permits a directional
    conclusion.
    """

    BUSINESS_RISK = "business_risk"
    """The business itself becoming less durable -- moat erosion,
    demand decline. Requires business-fact data ingestion; not
    producible today."""

    EXECUTION_RISK = "execution_risk"
    """Atlas's own bookkeeping of a position is incomplete or
    unreconciled. Producible today -- reuses the Alpha-side
    `AWAITING_RECONCILIATION` fact a composition layer already computes;
    this package only defines the category and receives the fact, it
    does not read Alpha state itself."""

    FINANCIAL_RISK = "financial_risk"
    """Balance-sheet or leverage risk. Requires financial-statement
    ingestion; not producible today."""

    INDUSTRY_RISK = "industry_risk"
    """Sector-wide structural risk. Requires sector-classification data
    Atlas does not have on any holding today; not producible."""

    MACRO_RISK = "macro_risk"
    """Interest rates, currency, macro cycle. Requires a macro data
    feed; not producible today."""

    PORTFOLIO_RISK = "portfolio_risk"
    """Concentration, allocation, correlation at the portfolio level.
    Partially producible today (concentration, allocation) by a
    composition layer that supplies the real weight data this package
    does not read directly -- see `atlas.alpha.portfolio_intelligence`."""

    BEHAVIORAL_RISK = "behavioral_risk"
    """The investor's own decision pattern -- already partially modeled
    outside this package, as `UX-008` §15's "Decision Memory" (behavioral
    patterns across decisions). Not yet connected to this taxonomy;
    flagged as a future integration point, not producible today."""

    REGULATORY_RISK = "regulatory_risk"
    """Legal or regulatory exposure. Requires a reports/news data
    source; not producible today."""

    THESIS_RISK = "thesis_risk"
    """The one category this package **can** produce today, from Core
    data alone: unresolved contradicting evidence against the
    investor's own recorded thesis, reusing
    `atlas.decision_engine.stages.reasoning`'s own
    `ContradictionSummary` verbatim. Not one of the sprint's eight
    suggested categories -- added because it is the one real,
    Core-scoped risk fact this codebase can honestly compute right now,
    and a taxonomy with zero producible members would not prove the
    architecture works.
    """


class CapabilityStatus(str, Enum):
    """Why a `CanonicalAnalysis` section that is not `EvaluationState`-shaped
    (Catalysts, Scenario Analysis -- entirely new concepts, not existing
    Decision Engine findings with their own state) is currently absent."""

    NOT_YET_IMPLEMENTED = "not_yet_implemented"
