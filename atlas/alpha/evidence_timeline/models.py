"""Result shapes for the Evidence Timeline (Atlas Intelligence -- Evidence
Timeline & Historical Understanding). Mirrors `atlas.analysis_engine
.investment_case_change`'s own `AnalyticalSnapshot`/`ChangeFinding`/
`ChangeIntelligence` shapes exactly -- the same "structural columns
only, direction is a separate field, no numeric score" discipline --
applied one layer up, to Coverage/Stance/Evidence Quality's own signals
that `AnalyticalSnapshot` itself never captured (it predates all
three; see `engine.py`'s own module docstring for the full audit).
`ChangeDirection` is reused verbatim from that module rather than a
third "positive/negative/neutral" enum invented here.

**Deliverable 2's own "do not mix these concepts" instruction, made
structural.** `EvidenceTransition` (Atlas's own analytical state
changing -- a *conclusion*) and `SourceEvidenceEvent` (a new fact/
period becoming known -- a *fact about the world*) are deliberately
two distinct dataclasses, not two variants of one shape. A caller can
never accidentally render a source-evidence arrival as if it were an
Atlas conclusion, or vice versa, because the type system itself keeps
them apart -- see `EvidenceHistory`'s own two separate fields below.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Mapping

from atlas.analysis_engine.investment_case_change import ChangeDirection

__all__ = [
    "EvidenceTransitionCategory",
    "EvidenceTransition",
    "SourceEvidenceEvent",
    "EvidenceSnapshot",
    "EvidenceHistory",
]


class EvidenceTransitionCategory(str, Enum):
    """A small, closed set -- one member per *kind* of evidence-signal
    change, direction kept as a separate field (`EvidenceTransition
    .direction`), the same economy `investment_case_change
    .ChangeCategory`'s own docstring documents for itself."""

    COVERAGE_CHANGED = "coverage_changed"
    CONFIDENCE_CHANGED = "confidence_changed"
    STANCE_CHANGED = "stance_changed"
    FRESHNESS_CHANGED = "freshness_changed"
    CONFLICT_STATUS_CHANGED = "conflict_status_changed"
    EVIDENCE_QUALITY_CHANGED = "evidence_quality_changed"


@dataclass(frozen=True)
class EvidenceTransition:
    """One meaningful, traceable change between two `EvidenceSnapshot`s.
    Mirrors `investment_case_change.ChangeFinding`'s exact shape."""

    id: str
    category: EvidenceTransitionCategory
    direction: ChangeDirection
    previous_state: str
    current_state: str
    details: Mapping[str, str]


@dataclass(frozen=True)
class SourceEvidenceEvent:
    """Deliverable 2/3 -- **Source Evidence History**: a real
    `(fact_kind, period)` combination that was not present in the
    previous snapshot's own `EvidenceSnapshot.known_periods` and now
    is. A fact about the world Atlas now has -- "Atlas received a
    newer revenue observation" -- never an Atlas conclusion about what
    that fact means. Deliberately carries no `direction` (a new period
    becoming available is neither positive nor negative in itself;
    what it implies, if anything, is `EvidenceTransition`'s own job)."""

    fact_kind: str
    period: str


@dataclass(frozen=True)
class EvidenceSnapshot:
    """"What did Atlas believe this Case's evidence-signal state was at
    time T" -- never rendered prose. `content_hash` is computed over
    every field below except `captured_at`, the same "compare content,
    not time" discipline `AnalyticalSnapshot.content_hash` already
    establishes."""

    overall_coverage: str
    overall_confidence: str
    stance_level: str | None
    """`None` only when no `StanceService` was wired for the call that
    captured this snapshot -- mirrors `InvestmentCaseAnalysisView
    .stance`'s own `None` precedent; every real API call site wires
    one, so this is populated in practice."""
    evidence_quality: str
    conflict_status: str
    freshness: str
    missing_dimensions: tuple[str, ...]
    known_periods: tuple[str, ...]
    """Deliverable 2/3 -- **Source Evidence History**'s own structural
    basis: every real `f"{fact_kind}:{period}"` combination
    `InvestmentCaseComposition.business_facts`/`.market_facts` (the
    same post-conflict-drop facts Evidence Quality itself already
    reads) named at capture time, sorted. Comparing two snapshots'
    own `known_periods` is how `SourceEvidenceEvent`s are found --
    never a raw `BusinessRecord` re-fetch, never a second ingestion
    read. A period genuinely new to Atlas can only be named once a
    real prior snapshot recorded a different set to compare against."""
    content_hash: str
    captured_at: datetime


@dataclass(frozen=True)
class EvidenceHistory:
    """The full Evidence Timeline result for one comparison -- either
    "this is the first snapshot, there is nothing to compare against
    yet" (`is_baseline=True`, `transitions=()`, `new_source_evidence=()`),
    or a real comparison against a genuinely different previous state.
    Mirrors `investment_case_change.ChangeIntelligence`'s exact shape
    (minus `summary_narrative`/`thesis_impact` -- this package's own
    scope is evidence-signal history, not a second company-thesis
    narrative; that concept already belongs to `ChangeIntelligence` and
    is not duplicated here).

    `transitions` (**Atlas Analysis History** -- Atlas's own conclusions
    changing) and `new_source_evidence` (**Source Evidence History** --
    new facts becoming known) are deliberately two separate fields,
    never merged into one list -- Deliverable 2's own "do not mix these
    concepts" instruction, structural, not just documented."""

    is_baseline: bool
    transitions: tuple[EvidenceTransition, ...]
    new_source_evidence: tuple[SourceEvidenceEvent, ...]
    previous_captured_at: datetime | None
    current_captured_at: datetime
