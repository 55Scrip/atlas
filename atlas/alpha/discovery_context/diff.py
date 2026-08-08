"""Deterministic comparison between two canonical intelligence snapshots
(ATLAS-018, Phase 5 -- "Conversation Continuity").

`diff_portfolio_intelligence`/`diff_case_intelligence` are pure
functions: given a `previous` and a `current`
`PortfolioIntelligenceReport`/`CaseIntelligenceReport`, they compute
what changed using nothing but `==` over already-real, already-computed
fields -- no reinterpretation, no re-running the Decision Engine, no new
conclusion. This is exactly Phase 5's own required shape: "Previous
Portfolio Intelligence -> Current Portfolio Intelligence -> Deterministic
differences -> LLM."

**Not wired into the live `/discovery/chat` flow.** Both
`PortfolioIntelligenceReport` and `CaseIntelligenceReport` are computed
fresh, from current database state, on every call -- neither this
codebase nor either sprint that introduced them (ATLAS-016, ATLAS-017)
persists a snapshot of a *previous* report anywhere. Wiring "what
changed?" into a live conversation would require a snapshot/history
store (when was each report computed, and what did it say) that does
not exist yet; building one is a real, separate persistence decision
outside this sprint's scope, and fabricating a fake "previous" value
here to make the feature appear wired would violate this sprint's own
"do not invent" principle at the data-source level, not just in
generated text. These functions exist now, real and tested, so a future
sprint that does add a snapshot store can call them directly instead of
writing this comparison logic from scratch.
"""
from __future__ import annotations

from dataclasses import dataclass

from atlas.alpha.case_intelligence.models import (
    CaseIntelligenceReport,
    DecisionHistoryEntry,
    KeyRiskItem,
    ObservationTimelineEntry,
)
from atlas.alpha.portfolio_intelligence.models import (
    ConsiderItem,
    KeyFinding,
    PortfolioIntelligenceReport,
    RiskSignal,
)
from atlas.decision_engine.contracts import EvidenceCoverageLevel, EvidenceGap

__all__ = ["PortfolioIntelligenceDiff", "diff_portfolio_intelligence", "CaseIntelligenceDiff", "diff_case_intelligence"]


@dataclass(frozen=True)
class PortfolioIntelligenceDiff:
    key_findings_added: tuple[KeyFinding, ...]
    key_findings_removed: tuple[KeyFinding, ...]
    consider_items_added: tuple[ConsiderItem, ...]
    consider_items_removed: tuple[ConsiderItem, ...]
    risk_signals_added: tuple[RiskSignal, ...]
    risk_signals_removed: tuple[RiskSignal, ...]
    holdings_count_changed: bool
    concentration_level_changed: bool

    @property
    def has_changes(self) -> bool:
        return bool(
            self.key_findings_added
            or self.key_findings_removed
            or self.consider_items_added
            or self.consider_items_removed
            or self.risk_signals_added
            or self.risk_signals_removed
            or self.holdings_count_changed
            or self.concentration_level_changed
        )


def diff_portfolio_intelligence(
    previous: PortfolioIntelligenceReport, current: PortfolioIntelligenceReport
) -> PortfolioIntelligenceDiff:
    previous_holdings_count = previous.overview.holdings_count if previous.overview else None
    current_holdings_count = current.overview.holdings_count if current.overview else None
    previous_concentration = previous.overview.concentration_level if previous.overview else None
    current_concentration = current.overview.concentration_level if current.overview else None

    return PortfolioIntelligenceDiff(
        key_findings_added=tuple(f for f in current.key_findings if f not in previous.key_findings),
        key_findings_removed=tuple(f for f in previous.key_findings if f not in current.key_findings),
        consider_items_added=tuple(c for c in current.consider_items if c not in previous.consider_items),
        consider_items_removed=tuple(c for c in previous.consider_items if c not in current.consider_items),
        risk_signals_added=tuple(s for s in current.risk_signals if s not in previous.risk_signals),
        risk_signals_removed=tuple(s for s in previous.risk_signals if s not in current.risk_signals),
        holdings_count_changed=previous_holdings_count != current_holdings_count,
        concentration_level_changed=previous_concentration != current_concentration,
    )


@dataclass(frozen=True)
class CaseIntelligenceDiff:
    confidence_changed: bool
    previous_confidence: EvidenceCoverageLevel
    current_confidence: EvidenceCoverageLevel
    missing_evidence_added: tuple[EvidenceGap, ...]
    missing_evidence_removed: tuple[EvidenceGap, ...]
    key_risks_added: tuple[KeyRiskItem, ...]
    key_risks_removed: tuple[KeyRiskItem, ...]
    consider_items_added: tuple[ConsiderItem, ...]
    consider_items_removed: tuple[ConsiderItem, ...]
    new_decisions: tuple[DecisionHistoryEntry, ...]
    new_observations: tuple[ObservationTimelineEntry, ...]

    @property
    def has_changes(self) -> bool:
        return bool(
            self.confidence_changed
            or self.missing_evidence_added
            or self.missing_evidence_removed
            or self.key_risks_added
            or self.key_risks_removed
            or self.consider_items_added
            or self.consider_items_removed
            or self.new_decisions
            or self.new_observations
        )


def diff_case_intelligence(previous: CaseIntelligenceReport, current: CaseIntelligenceReport) -> CaseIntelligenceDiff:
    previous_decision_ids = {entry.decision_id for entry in previous.decision_history}
    previous_observation_ids = {entry.observation_id for entry in previous.observation_timeline}

    return CaseIntelligenceDiff(
        confidence_changed=previous.confidence != current.confidence,
        previous_confidence=previous.confidence,
        current_confidence=current.confidence,
        missing_evidence_added=tuple(g for g in current.missing_evidence if g not in previous.missing_evidence),
        missing_evidence_removed=tuple(g for g in previous.missing_evidence if g not in current.missing_evidence),
        key_risks_added=tuple(r for r in current.key_risks if r not in previous.key_risks),
        key_risks_removed=tuple(r for r in previous.key_risks if r not in current.key_risks),
        consider_items_added=tuple(c for c in current.consider_items if c not in previous.consider_items),
        consider_items_removed=tuple(c for c in previous.consider_items if c not in current.consider_items),
        new_decisions=tuple(
            entry for entry in current.decision_history if entry.decision_id not in previous_decision_ids
        ),
        new_observations=tuple(
            entry
            for entry in current.observation_timeline
            if entry.observation_id not in previous_observation_ids
        ),
    )
