"""Findings architecture (ATLAS-020, Phase 4).

A `Finding` is the one shape every analysis stage in this codebase
should eventually produce, replacing ad hoc per-stage result types with
one structured, UI-agnostic conclusion. **This package never generates
UI wording.** The sprint's own field list names `summary` as a Finding
field; this module deliberately does not include a free-text `summary`
string -- `kind` (a closed enum identifying *which* finding this is)
together with `details` (structured facts: counts, ids, enum values,
never prose) already carry everything a renderer needs to produce
localized wording, exactly the same "_readable(labels, kind)" pattern
`atlas.ai.discovery_chat` and every frontend page already use for every
other enum value in this codebase. A `summary` string here would be
exactly the kind of black-box, unlocalizable, un-auditable text this
whole sprint exists to prevent.

`timestamp` (the sprint's field list) is carried on `Finding.provenance
.computed_at` rather than duplicated as a second top-level field --
"when was this computed" and "how/from what was this computed" are the
same fact, not two.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.analysis_engine.provenance import Provenance
from atlas.decision_engine.contracts import EvidenceCoverageLevel

__all__ = ["FindingKind", "FindingSeverity", "FindingProducer", "Finding"]


class FindingKind(str, Enum):
    """A closed, growing set -- every member here corresponds to a real,
    already-computed fact in this codebase today. Never a bare string;
    a future stage that needs a new kind must add a named member here,
    the same discipline `atlas.decision_engine.contracts.EvidenceGapKind`
    and `OpenQuestionKind` already established."""

    EVIDENCE_COVERAGE = "evidence_coverage"
    CONTRADICTING_EVIDENCE = "contradicting_evidence"
    MISSING_EVIDENCE = "missing_evidence"
    OPEN_QUESTION = "open_question"
    HOLDING_CONTEXT = "holding_context"
    EXECUTION_PRICE_HISTORY = "execution_price_history"
    BUSINESS_ANALYSIS_UNAVAILABLE = "business_analysis_unavailable"
    VALUATION_UNAVAILABLE = "valuation_unavailable"
    PORTFOLIO_FACTOR_UNAVAILABLE = "portfolio_factor_unavailable"
    CONVICTION_ASSESSED = "conviction_assessed"
    RECOMMENDATION_WITHHELD = "recommendation_withheld"
    VALUATION_METHOD_ASSESSED = "valuation_method_assessed"
    """ATLAS-024: one per
    `atlas.analysis_engine.valuation.contracts.ValuationMethodKind`
    member, always four per run. Mirrors `BUSINESS_CATEGORY_ASSESSED`'s
    own role exactly, for `ValuationFinding` -- `details` carries
    `method` and `status`; the full `ValuationFinding` lives on
    `CanonicalAnalysis.valuation_engine.findings`."""

    BUSINESS_CATEGORY_ASSESSED = "business_category_assessed"
    """ATLAS-021: one per `atlas.analysis_engine.business.BusinessCategory`
    member, always six per run. A flat, cross-cutting projection of the
    richer `BusinessFinding` type onto the generic `Finding` shape, for
    consumers that only want "every Finding this run produced" without
    caring about category-specific structure -- `details` carries
    `category` and `status`; the full `BusinessFinding` (with its own
    evidence/missing-evidence detail) lives on
    `CanonicalAnalysis.business_analysis.findings`, not here."""

    RISK_CATEGORY_ASSESSED = "risk_category_assessed"
    """ATLAS-025: one per category in
    `atlas.analysis_engine.risk.models.EVALUATED_RISK_CATEGORIES`
    (`BUSINESS_RISK`/`FINANCIAL_RISK`/`VALUATION_RISK`/`THESIS_RISK`),
    always four per run. Mirrors `BUSINESS_CATEGORY_ASSESSED`'s own role
    exactly, for `RiskFinding` -- `details` carries `risk_category` (the
    same key `pipeline.py::_build_findings`'s own pre-existing
    per-observation `CONTRADICTING_EVIDENCE` Findings already use, so
    `RiskSection`'s existing `"risk_category" in details` filter picks
    both up with zero changes to that filter) and `status`. The full
    `RiskFinding` (with its own missing-evidence detail) lives on
    `CanonicalAnalysis.risk_analysis.findings`, not here."""

    RECOMMENDATION_DIRECTION_SELECTED = "recommendation_direction_selected"
    """"Recommendation Backend Step 3" (`DE-008` Direction Selection):
    replaces `RECOMMENDATION_WITHHELD` as the recommendation-stage
    Finding exactly when `atlas.analysis_engine.direction_selector
    .select_direction` reaches a real direction and
    `atlas.analysis_engine.recommendation.evaluate_recommendation_gate`
    constructs a `ComputedDirectionalRecommendation` from it -- the two
    kinds are mutually exclusive per run, never both produced. `details`
    carries `direction` and `conviction_level`, never a `reason` (that
    field belongs to `RECOMMENDATION_WITHHELD` only). The full
    `ComputedDirectionalRecommendation` lives on
    `CanonicalAnalysis.recommendation.recommendation`, not here."""


class FindingSeverity(str, Enum):
    """Categorical, three-level, never numeric -- matches this
    codebase's existing refusal to score anything
    (`EvidenceCoverageLevel`, `ConcentrationLevel`). Severity describes
    how much attention a Finding deserves, never how likely a business
    outcome is -- that distinction matters: `MATERIAL` on a
    `MISSING_EVIDENCE` Finding means "this gap is worth closing," not
    "this business is risky." """

    INFO = "info"
    ATTENTION = "attention"
    MATERIAL = "material"


class FindingProducer(str, Enum):
    """Which stage produced this Finding -- a closed set mirroring the
    real module that computed it, so a Finding's origin is always a
    verifiable import path, never a guess."""

    BUSINESS_EVALUATION = "business_evaluation"
    VALUATION = "valuation"
    PORTFOLIO_INTELLIGENCE = "portfolio_intelligence"
    REASONING = "reasoning"
    CONVICTION = "conviction"
    RECOMMENDATION_GATE = "recommendation_gate"
    BUSINESS_ANALYSIS = "business_analysis"
    """ATLAS-021: `atlas.analysis_engine.business` -- distinct from
    `BUSINESS_EVALUATION` (`atlas.decision_engine`'s own stage, reused
    verbatim for Evidence Quality and, via reuse, Durability). This
    producer is analysis_engine-native: it owns the six-category
    `BusinessFinding` taxonomy Evidence Quality alone never claimed."""

    VALUATION_ENGINE = "valuation_engine"
    """ATLAS-024: `atlas.analysis_engine.valuation` -- distinct from
    `VALUATION` (`atlas.decision_engine`'s own stage, permanently
    locked to `INSUFFICIENT_INPUT`). This producer is
    analysis_engine-native: it owns the four-method `ValuationFinding`
    taxonomy the locked stage never could."""

    RISK_ANALYSIS = "risk_analysis"
    """ATLAS-025: `atlas.analysis_engine.risk` -- owns the
    `RiskFinding`/`RiskCategory` taxonomy. Distinct from `REASONING`,
    which still produces the pre-existing per-observation
    `CONTRADICTING_EVIDENCE` Findings unchanged (see
    `atlas.analysis_engine.risk.thesis_risk`'s own module docstring for
    why both coexist)."""


@dataclass(frozen=True)
class Finding:
    """One structured analytical conclusion.

    `id` is deterministic and caller-supplied (typically
    `f"{kind.value}:{reference}"` or just `kind.value` when case-wide) --
    never randomly generated, so the same input always produces the
    same `Finding.id`, matching the determinism guarantee every stage in
    `atlas.decision_engine` already provides.

    `details` holds only structured, closed-vocabulary or numeric facts
    (a count, an id, another enum's `.value`) -- never a sentence.
    `evidence_references` names the real Core record ids (Evidence,
    Observation, Decision, Outcome, or trade log entries, as plain
    strings) this Finding is grounded in; an empty tuple is valid and
    means "this Finding describes an absence," not "ungrounded."
    """

    id: str
    kind: FindingKind
    severity: FindingSeverity
    details: dict[str, str | int | float | bool | None]
    evidence_references: tuple[str, ...]
    confidence: EvidenceCoverageLevel
    producer: FindingProducer
    provenance: Provenance
