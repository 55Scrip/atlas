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
    """A closed, ten-member taxonomy (Phase 8's original nine, plus
    `VALUATION_RISK` added in ATLAS-025). Every member is real investing
    vocabulary, not invented; which categories this codebase can
    honestly produce a `Finding` for *today* is documented per member
    below -- Risk Findings never omit a category to make the taxonomy
    look more complete than it is; an unproducible category simply has
    zero Findings, the same "empty is a real, honest state" principle
    `atlas.decision_engine.contracts` already established for tuples
    like `evidence_gaps`.

    ATLAS-025 made `BUSINESS_RISK`, `FINANCIAL_RISK`, `VALUATION_RISK`,
    and `THESIS_RISK` real -- see `atlas.analysis_engine.risk` for the
    four evaluators. The other six stay exactly as ATLAS-020 left them:
    named, honest, zero Findings, because no canonical data source
    exists for them yet (or, for `EXECUTION_RISK`/`PORTFOLIO_RISK`, the
    ATLAS-025 audit found the underlying signal real but correctly owned
    by an Alpha composition layer, not this Core package -- see
    `atlas.analysis_engine.risk`'s own module docstring for that
    boundary decision).

    Risk never produces a recommendation (Phase 8's own instruction) --
    a `RiskCategory` Finding states a fact; only `recommendation.py`'s
    gate ever touches whether that fact permits a directional
    conclusion.
    """

    BUSINESS_RISK = "business_risk"
    """The business itself becoming less durable -- moat erosion, demand
    decline. Producible today (ATLAS-025): reuses `growth.py`'s own
    `GrowthFinding.status` verbatim, never a separate re-derivation of
    contraction. Deliberately does not also read contradicting evidence
    -- that signal belongs to `THESIS_RISK` alone."""

    EXECUTION_RISK = "execution_risk"
    """Atlas's own bookkeeping of a position is incomplete or
    unreconciled -- a workflow-state fact, not an analytical-risk fact
    (ATLAS-025 Phase 2's own distinction). Reuses the Alpha-side
    `AWAITING_RECONCILIATION` fact a composition layer already computes;
    this package only defines the category, it does not read Alpha
    state itself and does not build an evaluator for it in v1."""

    FINANCIAL_RISK = "financial_risk"
    """Balance-sheet or leverage risk. Producible today (ATLAS-025):
    reuses `capital_allocation.py`'s own `CapitalAllocationFinding.status`
    plus a direct check of the most recent known `FREE_CASH_FLOW`
    fact's sign -- no leverage ratio is invented, since no
    balance-sheet/total-debt data exists in this codebase."""

    INDUSTRY_RISK = "industry_risk"
    """Sector-wide structural risk. Requires sector-classification data
    Atlas does not have on any holding today; not producible."""

    MACRO_RISK = "macro_risk"
    """Interest rates, currency, macro cycle. Requires a macro data
    feed; not producible today."""

    PORTFOLIO_RISK = "portfolio_risk"
    """Concentration, allocation, correlation at the portfolio level.
    The ATLAS-025 audit confirmed real, deterministic concentration/
    allocation logic already exists (`atlas.alpha.portfolio_intelligence`,
    reusing `atlas.domains.portfolio.calculations.concentration_level`)
    -- but it depends on Alpha-side holding-weight data this package's
    architectural boundary must never read. Correct design: this stays
    a company-level-only package; a future Alpha composition layer adds
    Portfolio Risk on top, the same way it already adds concentration
    findings today. Not producible *by this package* in v1, by
    deliberate boundary, not by data absence."""

    BEHAVIORAL_RISK = "behavioral_risk"
    """The investor's own decision pattern -- already partially modeled
    outside this package, as `UX-008` §15's "Decision Memory" (behavioral
    patterns across decisions). Not yet connected to this taxonomy;
    flagged as a future integration point, not producible today."""

    REGULATORY_RISK = "regulatory_risk"
    """Legal or regulatory exposure. Requires a reports/news data
    source; not producible today."""

    THESIS_RISK = "thesis_risk"
    """Unresolved contradicting evidence against the investor's own
    recorded thesis, reusing `atlas.decision_engine.stages.reasoning`'s
    own `ContradictionSummary` verbatim. Not one of Phase 8's originally
    suggested categories -- added in ATLAS-020 because it was the one
    real, Core-scoped risk fact producible at the time; ATLAS-025 gave
    it a proper categorical `RiskFinding` alongside its pre-existing
    per-observation Findings (see `atlas.analysis_engine.risk`)."""

    VALUATION_RISK = "valuation_risk"
    """The risk of having overpaid, from a purely price-relative-to-
    history perspective. Producible today (ATLAS-025): reuses
    `valuation.cash_flow.evaluate_fcf_yield_relative`'s own
    `ValuationFinding.status` verbatim -- this category never
    recomputes FCF yield or historical valuation ranges itself, one
    source of valuation truth. `LOW` Valuation Risk describes only this
    one narrow dimension (not overpaying); it is never a claim about
    overall investment safety and must never be read as, or feed,
    Business Risk, Financial Risk, Thesis Risk, or Recommendation."""


class CapabilityStatus(str, Enum):
    """Why a `CanonicalAnalysis` section that is not `EvaluationState`-shaped
    (Catalysts, Scenario Analysis -- entirely new concepts, not existing
    Decision Engine findings with their own state) is currently absent."""

    NOT_YET_IMPLEMENTED = "not_yet_implemented"
