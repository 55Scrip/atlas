"""Result shapes for the Evidence Quality Engine (Atlas Intelligence
Sprint 4 -- Evidence Quality & Conflict Resolution). See `engine.py`'s
own module docstring for the full derivation rules and the real,
audited Core behavior this package classifies -- never re-derives.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

__all__ = [
    "EvidenceFreshness",
    "EvidenceDominance",
    "EvidenceConflictStatus",
    "EvidenceQualityLevel",
    "EvidenceWarningCode",
    "EvidenceConflict",
    "FactQuality",
    "UnsupportedFinding",
    "EvidenceQualityReport",
]


class EvidenceFreshness(str, Enum):
    """How recently the underlying source document was published,
    bucketed as multiples of the one existing, real staleness
    threshold this codebase already has --
    `atlas.alpha.portfolio_status.service.VERY_OLD_CASE_THRESHOLD_DAYS`
    (90 days) -- rather than inventing a second, unrelated number.
    FRESH < 90 days, RECENT < 180, OLD < 360, STALE >= 360."""

    FRESH = "fresh"
    RECENT = "recent"
    OLD = "old"
    STALE = "stale"
    NOT_APPLICABLE = "not_applicable"
    """No timestamped fact exists to grade -- honest absence, never a
    worst-case default."""


class EvidenceDominance(str, Enum):
    """Whether a fact kind's entire history traces back to one single
    `BusinessRecord`, or is corroborated by multiple independent
    records -- a real, derivable fragility signal (`source_record_id`
    is already a real field on every `BusinessFact`/`ValuationFact`;
    this never invents a new one)."""

    SINGLE_SOURCE = "single_source"
    CORROBORATED = "corroborated"
    NOT_APPLICABLE = "not_applicable"


class EvidenceConflictStatus(str, Enum):
    CONSISTENT = "consistent"
    CONFLICTING = "conflicting"
    NOT_APPLICABLE = "not_applicable"


class EvidenceQualityLevel(str, Enum):
    """The one overall label per Deliverable 2's own list. Derived by a
    fixed priority order (`engine.py`'s own `_QUALITY_PRIORITY`),
    never a score -- the same "declared order, never invented"
    discipline `atlas.analysis_engine.risk.projection.risk_projection`
    already established."""

    FRESH = "fresh"
    RECENT = "recent"
    OLD = "old"
    STALE = "stale"
    SUPERSEDED = "superseded"
    """Reserved, like `Provenance.SourceKind.EXTERNAL_DATA_SOURCE` and
    `BusinessCategoryStatus.NOT_EVALUATED` before it -- never
    constructed today. Every real caller of this engine already passes
    `business_data.versioning.latest_versions`-filtered records (the
    same precondition `InvestmentCaseCompositionService.build` already
    enforces), so a genuinely superseded document version never reaches
    this classification. Named now so a future caller that *doesn't*
    pre-filter does not require a shape change."""
    CONFLICTING = "conflicting"
    INCOMPLETE = "incomplete"
    UNSUPPORTED = "unsupported"
    NOT_APPLICABLE = "not_applicable"


class EvidenceWarningCode(str, Enum):
    """A closed reason-code vocabulary -- the presentation layer owns
    every sentence, the same `StanceReasonCode`/`ConfidenceReasonCode`
    convention. Presence-only (no count), since each of these already
    has its own detail object (`conflicts`, `unsupported_findings`)
    a caller can enumerate for specifics."""

    CONFLICTING_SOURCE_VALUES = "conflicting_source_values"
    EVIDENCE_STALE = "evidence_stale"
    SINGLE_SOURCE_DEPENDENCY = "single_source_dependency"
    CONCLUSION_WITHOUT_SUPPORT = "conclusion_without_support"
    PARTIAL_COVERAGE = "partial_coverage"
    NO_EVIDENCE = "no_evidence"


@dataclass(frozen=True)
class EvidenceConflict:
    """One real, detected disagreement: two or more source records
    reported a different value for the same `(fact_kind, period)`.
    Mirrors exactly what `atlas.analysis_engine.business_facts
    .extraction.extract_facts_from_records` (and its `ValuationFact`
    sibling) already silently drops -- this dataclass is the first
    place in the whole codebase that surfaces what that drop discarded,
    rather than re-deciding it. `source_record_ids` names every record
    that contributed a value to the disagreement; per the Core
    function's own "drop the whole group" behavior (never picks a
    winner), every one of them is currently ignored by every downstream
    analysis, not just the minority."""

    fact_kind: str
    period: str
    unit: str
    values: tuple[float, ...]
    source_record_ids: tuple[str, ...]


@dataclass(frozen=True)
class FactQuality:
    """Freshness and dominance for one `BusinessFactKind`/
    `ValuationFactKind`, computed only from facts that actually survive
    Core's own conflict-drop (i.e. the facts real analysis is currently
    using), never from a conflicting group in isolation."""

    fact_kind: str
    freshness: EvidenceFreshness
    dominance: EvidenceDominance
    latest_period: str | None
    latest_published_at: datetime | None
    source_record_count: int


@dataclass(frozen=True)
class UnsupportedFinding:
    """A real `BusinessFinding`/`RiskFinding`/`ValuationFinding` that
    reached a genuine conclusion (not `NOT_EVALUATED`/
    `INSUFFICIENT_INPUT`) while its own `supporting_evidence`/
    `supporting_facts` tuple is empty -- a conclusion the case
    currently cannot point to any real backing evidence for."""

    category: str
    status: str


@dataclass(frozen=True)
class EvidenceQualityReport:
    """The one whole-case answer to Deliverable 3's four questions
    (Evidence Quality, Conflict Status, Freshness, Dominance) plus
    Evidence Warnings -- every field a real, already-computed
    classification, never a new investment conclusion."""

    quality: EvidenceQualityLevel
    conflict_status: EvidenceConflictStatus
    freshness: EvidenceFreshness
    dominance: EvidenceDominance
    warnings: tuple[EvidenceWarningCode, ...]
    facts: tuple[FactQuality, ...]
    conflicts: tuple[EvidenceConflict, ...]
    unsupported_findings: tuple[UnsupportedFinding, ...]
