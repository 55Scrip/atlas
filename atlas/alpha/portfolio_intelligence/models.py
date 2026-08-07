"""Data model for the Portfolio Intelligence report (ATLAS-016).

Every field here is either read verbatim from an existing record, reused
directly from the canonical Decision Engine pipeline's own output
(`atlas.decision_engine.contracts`), or a deterministic count/threshold
comparison over those -- never a score, never AI-generated, never a new
confidence or conviction system. `EvidenceCoverageLevel` is imported and
reused as-is for every `ConsiderItem.confidence` and `RiskSignal`
evidence fact, rather than inventing a second "Atlas confidence" scale
-- see `atlas/decision_engine/contracts.py`'s own definition.

`ConsiderKind` is deliberately a small, closed set, limited to the
findings this module can actually back with real data today (see
`service.py`'s own module docstring for what was excluded and why --
"Consider Increase Conviction" and "Consider Wait" have no deterministic
data source and are not implemented, per the "nothing may be
hallucinated" rule). None of these imply a trade instruction: no kind
here is "Buy X" or "Sell Y" -- each is a review suggestion only.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.alpha.portfolio_status.models import PortfolioSummaryMetrics
from atlas.decision_engine.contracts import EvidenceCoverageLevel, EvidenceGapKind

__all__ = [
    "KeyFindingKind",
    "KeyFinding",
    "ConsiderKind",
    "ConsiderItem",
    "RiskSignalKind",
    "RiskSignal",
    "MissingEvidenceItem",
    "PortfolioFitUnavailableReason",
    "PortfolioFitStatus",
    "PortfolioIntelligenceReport",
]


class KeyFindingKind(str, Enum):
    """A portfolio-wide headline fact -- every member maps 1:1 onto a
    count or level already computed by `PortfolioStatusService` (ATLAS-015)
    or this module's own per-case pipeline runs. Never a sector/country/
    correlation finding -- Atlas has no data for those (see
    `service.py`)."""

    HIGH_CONCENTRATION = "high_concentration"
    ELEVATED_CONCENTRATION = "elevated_concentration"
    LARGE_UNALLOCATED = "large_unallocated"
    MULTIPLE_MISSING_CASES = "multiple_missing_cases"
    MULTIPLE_STALE_CASES = "multiple_stale_cases"
    MULTIPLE_EVIDENCE_GAPS = "multiple_evidence_gaps"


@dataclass(frozen=True)
class KeyFinding:
    """One headline finding. `tickers` names every holding the finding is
    actually about -- empty only for `LARGE_UNALLOCATED`, which is not
    about any single holding. `count` is `len(tickers)` for aggregate
    kinds, or `1` for a single-holding kind (e.g. the one largest
    position driving `HIGH_CONCENTRATION`)."""

    kind: KeyFindingKind
    count: int
    tickers: tuple[str, ...]


class ConsiderKind(str, Enum):
    """A structured review suggestion -- never a trade instruction. See
    module docstring for what is deliberately not implemented."""

    OPEN_INVESTMENT_CASE = "open_investment_case"
    GATHER_EVIDENCE = "gather_evidence"
    REVIEW_THESIS = "review_thesis"
    UPDATE_CASE = "update_case"
    REVIEW_CONCENTRATION = "review_concentration"


@dataclass(frozen=True)
class ConsiderItem:
    """One structured Consider object. `confidence` reuses
    `EvidenceCoverageLevel` verbatim -- see module docstring. Exactly one
    of `evidence_gap_count`/`age_days`/`weight_percent`/`pending_item_count`
    is populated, matching whichever fact backs `kind`; the rest are
    `None`. `related_holdings` is always `(ticker,)` this sprint -- every
    Consider this module produces is single-holding scoped."""

    kind: ConsiderKind
    ticker: str
    case_id: str | None
    confidence: EvidenceCoverageLevel
    related_holdings: tuple[str, ...]
    evidence_gap_count: int | None = None
    age_days: int | None = None
    weight_percent: float | None = None
    pending_item_count: int | None = None


class RiskSignalKind(str, Enum):
    """A deterministic, already-supported risk category -- every member
    maps 1:1 onto an existing `AttentionCategory` (ATLAS-015) or a
    concentration/evidence-coverage fact already computed elsewhere in
    this codebase. "Old thesis" and "No recent review" from the sprint's
    own examples share one real data source (`VERY_OLD_CASE`) and are
    represented here as the single `STALE_REVIEW` kind rather than two
    kinds backed by the same fact."""

    HIGH_CONCENTRATION = "high_concentration"
    MISSING_CASE = "missing_case"
    MISSING_EVIDENCE = "missing_evidence"
    AWAITING_RECONCILIATION = "awaiting_reconciliation"
    STALE_REVIEW = "stale_review"


@dataclass(frozen=True)
class RiskSignal:
    kind: RiskSignalKind
    ticker: str
    case_id: str | None
    age_days: int | None = None


@dataclass(frozen=True)
class MissingEvidenceItem:
    """One `EvidenceGap`, passed through verbatim from the Decision
    Engine's Business Evaluation stage -- never inferred here."""

    ticker: str
    case_id: str
    gap_kind: EvidenceGapKind
    reference: str | None


class PortfolioFitUnavailableReason(str, Enum):
    NOT_YET_IMPLEMENTED = "not_yet_implemented"


@dataclass(frozen=True)
class PortfolioFitStatus:
    """Always `available=False` this sprint -- a direct, honest reflection
    of `atlas.decision_engine.contracts.PortfolioFinding` being
    structurally locked to `INSUFFICIENT_INPUT` (see
    `atlas/decision_engine/stages/portfolio_intelligence.py`). This is a
    disclosed placeholder, not an invented status: Portfolio Fit will
    become available exactly when the canonical pipeline's own
    `PortfolioDoctrineFactor` evaluation does, and not before."""

    available: bool
    reason: PortfolioFitUnavailableReason | None = None


@dataclass(frozen=True)
class PortfolioIntelligenceReport:
    """The full report `PortfolioIntelligenceService.build_report()`
    returns. `overview` is `PortfolioStatusService`'s own
    `PortfolioSummaryMetrics`, reused verbatim -- this module never
    recomputes holdings count, largest position, concentration, or
    unallocated percent."""

    exists: bool
    overview: PortfolioSummaryMetrics | None
    cash_weight_percent: float | None
    cash_value_absolute: float | None
    key_findings: tuple[KeyFinding, ...]
    consider_items: tuple[ConsiderItem, ...]
    risk_signals: tuple[RiskSignal, ...]
    missing_evidence: tuple[MissingEvidenceItem, ...]
    portfolio_fit: PortfolioFitStatus

    @classmethod
    def empty(cls) -> "PortfolioIntelligenceReport":
        return cls(
            exists=False,
            overview=None,
            cash_weight_percent=None,
            cash_value_absolute=None,
            key_findings=(),
            consider_items=(),
            risk_signals=(),
            missing_evidence=(),
            portfolio_fit=PortfolioFitStatus(
                available=False, reason=PortfolioFitUnavailableReason.NOT_YET_IMPLEMENTED
            ),
        )
