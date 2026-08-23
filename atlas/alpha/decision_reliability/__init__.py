"""Decision Reliability (Atlas Decision Layer Sprint 7).

DELIVERABLE 1 -- RELIABILITY AUDIT
====================================

Every existing reliability-related concept in this codebase, audited
before any new code was written.

**Coverage & Confidence** (`atlas.alpha.coverage`, Atlas Intelligence
Sprint 1) -- `CoverageAssessment.overall_confidence` (`ConfidenceLevel`:
HIGH/MODERATE/LIMITED/VERY_LIMITED) is already the closest existing
thing to a whole-Case reliability judgment: "how much an investor
should trust Atlas's own understanding," derived from real dimension-
coverage counts, contradiction presence, and thesis staleness. **This
already genuinely affects reliability** -- it is this package's own
primary input, reused via `assess_coverage` (the same pure function
`explainability`/`stance` already call), never recomputed.

**Evidence Quality** (`atlas.alpha.evidence_quality`, Atlas
Intelligence Sprint 4) -- `EvidenceQualityReport.quality`/`.warnings`
answer a different, complementary question: not "how complete is
Atlas's analysis" but "how trustworthy is the investor's own recorded
evidence" (freshness, single-source dependency, conflicting values,
unsupported conclusions). **Genuinely belongs** -- reused directly as
this package's second primary input, never recomputed.

**Decision Readiness** (`atlas.alpha.decision_readiness`, Atlas
Intelligence Sprint 11) -- `DecisionReadiness.status`/`.blockers`/
`.supporting_reasons` already answer "has Atlas earned the right to
state a view at all," including every real operational fact
(`MONITORING_PENDING`/`MONITORING_FAILED`/`OPERATIONAL_FRESHNESS_OUTDATED`
-- Monitoring's own contribution, already folded in one layer down).
**Genuinely belongs, and already subsumes Monitoring** -- composing
`MonitoringService` directly here would duplicate a fact Decision
Readiness already carries; this package reads Decision Readiness only.

**Monitoring** (`atlas.alpha.monitoring`) -- audited and found
**already fully represented via Decision Readiness** (see above); not
composed as a separate input, to avoid exactly the duplication the
brief warns against.

**Evidence Graph** (`atlas.alpha.evidence_graph`, Atlas Intelligence
Sprint 10) -- audited and found **presentation-only for this
package's purpose**: its own weak-dependency detection already feeds
Recommendation Conviction (Sprint 2) and, transitively, Decision
Explanation (Sprint 6); Reliability's own inputs (Coverage, Evidence
Quality, Decision Readiness) do not need a second, independent read of
the same graph. `ReliabilityReference` still reuses the Evidence
Graph's own traceable node-kind vocabulary (via `ExplanationReference`,
see below) for any future caller that resolves a code further, but
this package does not compose `EvidenceGraphService` itself.

**Decision Explanation** (`atlas.alpha.decision_explanation`, Sprint
6) -- audited and found **a peer, not an input**: it already answers
"why did Atlas reach this decision," a different question from "how
reliable is that reasoning." Cross-layer consistency between the two
(Deliverable 12) is achieved by construction: Reliability's own three
inputs are the same real, already-validated objects Decision
Explanation's own upstream services (Decision Readiness) already
compose, so the two can never disagree about the underlying facts,
only present a different lens on them. `ReliabilityReference` is
literally `atlas.alpha.decision_explanation.models.ExplanationReference`
reused verbatim (never redeclared) -- see `models.py`'s own docstring.

**Decision Memory** (`atlas.alpha.decision_memory`, Sprint 5) --
audited and found **not composed directly**: Decision Memory already
owns durable, append-only decision history; duplicating a second
historical ledger here for Reliability would be exactly the "redesign
an earlier layer" the brief forbids. This package follows the same
"live cache, not a second ledger" discipline `decision_explanation`
already established (see `table.py`'s own docstring) -- change
detection reads back only the *previous live computation*, never a
durable history of its own.

**Duplication found and avoided**: Monitoring (already inside Decision
Readiness) and a second Evidence Graph traversal (already unnecessary
given Coverage/Evidence Quality/Decision Readiness cover the same
ground for this purpose) were both found and deliberately NOT composed
a second time.

**Presentation-only found**: every input's own reason vocabulary
(`ConfidenceReasonCode`/`EvidenceWarningCode`/`DecisionBlockerKind`/
`DecisionReadinessReasonKind`) is already closed and structured -- no
free text exists anywhere in the three input layers to reclassify.

This package computes no new analysis. It is a pure reclassification
and composition layer over three already-real, already-validated
judgments, exactly as the brief's own opening states.
"""
from atlas.alpha.decision_reliability.models import (
    DecisionReliability,
    DecisionReliabilitySummary,
    PortfolioReliabilityBreakdown,
    ReliabilityChange,
    ReliabilityComparison,
    ReliabilityLevel,
    ReliabilityReason,
    ReliabilityReference,
    ReliabilitySource,
)
from atlas.alpha.decision_reliability.service import DecisionReliabilityService

__all__ = [
    "ReliabilityLevel",
    "ReliabilitySource",
    "ReliabilityReference",
    "ReliabilityReason",
    "DecisionReliability",
    "DecisionReliabilitySummary",
    "ReliabilityComparison",
    "ReliabilityChange",
    "PortfolioReliabilityBreakdown",
    "DecisionReliabilityService",
]
