"""Decision Explanation & Traceability (Atlas Decision Layer Sprint 6).

DELIVERABLE 1 -- EXPLANATION AUDIT
===================================

Every existing explanation source in this codebase, audited before any
new code was written.

**Investment Decision** (`atlas.alpha.investment_decision`, Sprint 1)
-- `InvestmentDecision.supporting_reasons`/`.blockers`/`.change_trigger`,
each a `DecisionReason(source, code)` tagged pointer at a real
`DecisionBlockerKind`/`DecisionReadinessReasonKind`/`StanceReasonCode`
value. Already the final synthesis; already ordered (first entry is
already "primary"). **Reused directly, not redesigned.**

**Recommendation Conviction** (`atlas.alpha.recommendation_conviction`,
Sprint 2) -- `RecommendationConviction.supporting_reasons`/
`.limiting_reasons`/`.strengthening_trigger`, the same tagged-pointer
shape (`ConvictionReason`). One genuine traceability gap found here:
its `ConvictionReasonSource.EVIDENCE_GRAPH`-sourced reasons already
exist but are pre-deduplicated down to a bare `WeaknessKind` code
(e.g. `"no_support"`) -- the specific Finding node id that weakness
was actually about is discarded before it reaches this reason.
Deliverable 4 closes this: `engine.py::_evidence_graph_findings`
re-joins that same code against the Case's own already-computed
`WeakDependency` list to recover the real Finding node id(s), without
recomputing the weakness detection itself. **Reused, gap closed by
re-joining against already-real data, nothing re-derived.**

**Decision Path** (`atlas.alpha.decision_path`, Sprint 3) --
`DecisionPath.steps`, each a `DecisionStep(dependency, progress_kind,
reachability)`, already deterministically ordered. Its own
`immediate_blocker` is frequently the *same* real fact as Decision
Readiness's own primary blocker (a `DecisionStep`'s `dependency` is
itself sourced from `DecisionBlockerKind`/`DecisionReadinessReasonKind`)
-- this is a deliberate, disclosed overlap between the Blocking and
Dependency sections below (they answer two different questions: "why
isn't Atlas more decisive" vs. "what needs to happen next"), the same
"informational overlap is expected, not redundant" precedent Sprint
5's own Daily Brief integration already established. **Reused
directly, exposed as its own Dependency section.**

**Decision Memory** (`atlas.alpha.decision_memory`, Sprint 5) -- the
Case's own most recent real `DecisionSnapshot`, when a real (non-
baseline) change has ever been recorded. This package deliberately
does not persist a second historical ledger of its own (see
`table.py`'s own docstring) -- Decision Memory already owns durable
history; this package only ever *points at* its latest real snapshot
(one `ExplanationReference(DECISION_SNAPSHOT, content_hash)`), never
duplicates it.

**Decision Readiness** (`atlas.alpha.decision_readiness`, Atlas
Intelligence Sprint 11) -- `DecisionReadiness.blockers`/
`.supporting_reasons`. Already the ultimate source every Investment
Decision/Recommendation Conviction readiness-sourced reason is itself
built from -- included directly (not only transitively via those two
layers) so `named_by` on a `SupportingFinding`/`BlockingFinding`
correctly names every layer that actually surfaced a given fact,
never just the first one encountered.

**Evidence Graph** (`atlas.alpha.evidence_graph`, Atlas Intelligence
Sprint 10) -- real `FINDING`/`OBSERVATION` nodes with real ids, and
`upstream_support`/`downstream_impact` graph traversal already built.
This is the traceability substrate itself: every `ExplanationReference`
of kind `FINDING`/`OBSERVATION` is a real `GraphNode.id`, resolvable
in this same Case's own Evidence Graph.

**A different, pre-existing feature found and deliberately NOT
touched**: `atlas.alpha.explainability` (Atlas Intelligence Sprint 3,
"Decision Explainability & Evidence Trace"). Its own `Explanation`
model (supporting/contradicting evidence, limiting factors, missing
evidence, confidence drivers) is built entirely from `Stance`/
`CoverageAssessment` and predates every Decision Layer package above
-- it answers "why does Atlas currently believe X" (a directional
read), never "why is Atlas recommending this specific action" (the
Decision Layer's own `InvestmentDecision.action`). Both questions are
real and both stay: this package is named `decision_explanation`
(never `explainability`), every model class here uses a name distinct
from that package's own `Explanation`/`ComparisonEvidence`, and its
own UI panel (`frontend/src/explainability/`, already live on
Investment Case) is left completely unmodified.

**Duplication found and resolved by construction**: the same real
code (e.g. `missing_thesis_evidence`) is very often named by three or
four upstream layers simultaneously (Investment Decision's own
blockers already forward every Decision Readiness blocker verbatim;
Recommendation Conviction's own limiting reasons very often name the
identical code again). `engine.py::_merge_supporting`/`_merge_blocking`
collapse same-code references into one `SupportingFinding`/
`BlockingFinding`, carrying every layer that named it in `named_by`
-- counted once, never once per layer.

**Presentation-only found**: every upstream reason/blocker/step is
already a closed-vocabulary code, never free text -- there is no
"AI-generated wording" anywhere in the five input layers to begin
with. This package inherits that discipline rather than introducing
any (see Deliverable 14, this package's own Language Audit).

This package computes no new analysis. It is a pure reclassification
and traceability layer over five already-real objects, exactly as the
brief's own opening states.
"""
from atlas.alpha.decision_explanation.models import (
    BlockingFinding,
    DecisionExplanation,
    DecisionExplanationChange,
    DecisionExplanationComparison,
    DecisionExplanationSummary,
    ExplanationChain,
    ExplanationLayer,
    ExplanationReference,
    ExplanationReferenceKind,
    ExplanationSection,
    ExplanationSectionKind,
    PortfolioDecisionExplanationBreakdown,
    SupportingFinding,
)
from atlas.alpha.decision_explanation.service import DecisionExplanationService

__all__ = [
    "ExplanationReferenceKind",
    "ExplanationReference",
    "ExplanationLayer",
    "SupportingFinding",
    "BlockingFinding",
    "ExplanationSectionKind",
    "ExplanationSection",
    "ExplanationChain",
    "DecisionExplanation",
    "DecisionExplanationSummary",
    "DecisionExplanationComparison",
    "DecisionExplanationChange",
    "PortfolioDecisionExplanationBreakdown",
    "DecisionExplanationService",
]
