"""`InvestmentCaseComposition` (ATLAS-027, Phase 9) -- see this
package's own `__init__.py` for the full ownership rationale.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.alpha.portfolio.models import AlphaHolding, AlphaTradeLogEntry
from atlas.analysis_engine.models import CanonicalAnalysis
from atlas.core.domain.decision.entity import Decision
from atlas.core.domain.observation.entity import Observation

__all__ = ["CurrentThesis", "InvestmentCaseComposition"]


@dataclass(frozen=True)
class CurrentThesis:
    """The investor's own most recent words, verbatim -- never
    interpreted, scored, or reworded. Mirrors
    `atlas.alpha.case_intelligence`'s own `CurrentThesis` shape (an
    independent, non-analytical derivation each Alpha service is
    expected to make for itself, not a canonical value with one owner
    the way Business/Valuation/Risk/Conviction are)."""

    latest_decision_reason: str | None
    latest_decision_type: str | None
    latest_observation_statement: str | None


@dataclass(frozen=True)
class InvestmentCaseComposition:
    """The canonical Investment Case view: one Case's own identity and
    record history, plus the exact `CanonicalAnalysis` object
    `atlas.analysis_engine.pipeline.assemble_analysis` produced for it.

    `canonical_analysis` already carries Business Analysis, Valuation,
    Risk, Confidence, Conviction, Recommendation, supporting/
    contradicting evidence, missing evidence, and open questions --
    none of those are duplicated as separate fields here. Only what
    `CanonicalAnalysis` does not and should not know about (the linked
    holding, the investor's own recorded history) is added.

    `outcome_history` is deliberately untyped (not `tuple[Outcome,
    ...]`): `atlas.alpha` is forbidden from importing
    `atlas.core.domain.outcome.entity` at all, the same restriction
    `pipeline_bridge.py`'s own `outcomes` parameter documents.
    """

    case_id: str
    holding_context: AlphaHolding | None
    canonical_analysis: CanonicalAnalysis
    current_thesis: CurrentThesis
    decision_history: tuple[Decision, ...]
    observation_history: tuple[Observation, ...]
    outcome_history: tuple
    trade_log: tuple[AlphaTradeLogEntry, ...]
    generated_at: datetime
