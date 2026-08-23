"""Materiality Engine (Atlas Intelligence Sprint -- Materiality &
Priority Engine).

**Deliverable 1's audit, in one place.** Every evidence source
Coverage/Confidence/Stance/Explainability/Evidence Quality read was
traced back to what it actually is, before any classification was
written here:

- `Stance.supporting_signals`/`.limiting_signals` (and, one layer up,
  `Explanation.supporting_evidence`/`.contradicting_evidence`/
  `.limiting_factors`) are already **closed, deduplicated reason
  codes** -- never a raw list of observations. `StanceReasonCode` has
  seventeen members; the Stance engine can never emit the same code
  twice for the same case (each is appended at most once, by a fixed
  branch of `atlas.alpha.stance.engine.determine_stance`). This
  resolves Deliverable 1's own "can multiple observations repeat the
  same point / can one dominate many weaker ones" question directly:
  by construction, this Sprint's real inputs cannot contain duplicate
  or repeated points to begin with -- there is no "more bullets = a
  stronger case" failure mode to guard against at this layer, because
  the layer below (Stance) already collapsed every fact into at most
  one reason code per real signal. This is why Deliverable 4's "never
  count observations" rule is automatically satisfied here, not a rule
  this engine has to separately enforce.
- **Does every code always matter?** No -- and the honest answer
  differs code by code. `NO_COMPANY_DATA`/`CONTRADICTING_EVIDENCE_
  PRESENT`/`CONVICTION_INSUFFICIENT`/`HIGH_RISK_PRESENT` are read as
  `CRITICAL` unconditionally: each already represents either a
  fundamental blocker to any conclusion or a real, severe risk finding
  -- there is no context in which one of these is merely background.
  `THESIS_UNCHANGED`/`DECISION_SUPPORT_NEUTRAL` are read as
  `BACKGROUND` unconditionally for the identical reason in the other
  direction -- both name "nothing changed," which is real but never
  the thing an investor needs surfaced first. Every other code sits
  between these two poles -- see `_STANCE_REASON_MATERIALITY`'s own
  per-member comment for the specific reasoning.
- **Missing evidence** already has a real, fixed-priority "most
  valuable" pick -- `Explanation.most_valuable_missing_information`
  (Atlas Intelligence Sprint 3's own `_MISSING_INFORMATION_PRIORITY`).
  This engine reuses it verbatim as `top_missing_evidence`, never
  recomputing a second ranking over the same dimensions.
- **Evidence Quality** (Sprint 4) is deliberately *not* re-read here to
  adjust a reason's materiality. Its own `quality`/`conflict_status`/
  `warnings` already answer "how much should I trust this evidence" --
  a different, already-answered question from "how much does this
  evidence matter to the conclusion" this engine answers. Blending the
  two would let a `STALE` conflict-free case quietly inflate or deflate
  a reason's real importance for a reason Evidence Quality's own panel
  already discloses honestly on its own; kept separate, per this
  Sprint's own "do not redesign Core" discipline applied one layer up
  (never conflate two already-real, already-legitimate signals into a
  third invented one).

**No new investment analysis.** Every `MaterialEvidence` this engine
produces wraps a `StanceReason` `Explanation` (Sprint 3) already
computed; this module performs exactly one new piece of work --
classifying each already-real reason code against a fixed, declared
`MaterialityLevel`, then sorting by that fixed order (never a numeric
score, never an average, the same `risk_projection._TIE_BREAK_ORDER`/
Sprint 3's own `_MISSING_INFORMATION_PRIORITY`/Sprint 4's own
`_QUALITY_PRIORITY` discipline every prior engine in this Sprint's own
lineage already established).
"""
from __future__ import annotations

from atlas.alpha.explainability import Explanation
from atlas.alpha.stance import StanceReason, StanceReasonCode

from .models import MaterialEvidence, MaterialityAssessment, MaterialityLevel

__all__ = ["assess_materiality"]

#: Every one of `StanceReasonCode`'s seventeen members, classified once,
#: here -- the map this whole engine is grounded in. Deliberately a
#: single, shared classification (not one map per bucket): a code's own
#: real-world meaning does not change depending on which bucket
#: (`supporting_evidence`/`contradicting_evidence`/`limiting_factors`)
#: it happens to appear in, so neither should its materiality.
_STANCE_REASON_MATERIALITY: dict[StanceReasonCode, MaterialityLevel] = {
    # Fundamental blockers -- no conclusion is safely reachable without
    # addressing these first.
    StanceReasonCode.NO_COMPANY_DATA: MaterialityLevel.CRITICAL,
    StanceReasonCode.CONTRADICTING_EVIDENCE_PRESENT: MaterialityLevel.CRITICAL,
    StanceReasonCode.CONVICTION_INSUFFICIENT: MaterialityLevel.CRITICAL,
    # A real, severe risk finding -- always worth leading with.
    StanceReasonCode.HIGH_RISK_PRESENT: MaterialityLevel.CRITICAL,
    # Strong, real directional signals and significant caveats.
    StanceReasonCode.CONFIDENCE_VERY_LIMITED: MaterialityLevel.HIGH,
    StanceReasonCode.THESIS_STRENGTHENED: MaterialityLevel.HIGH,
    StanceReasonCode.THESIS_WEAKENED: MaterialityLevel.HIGH,
    StanceReasonCode.DECISION_SUPPORT_FAVORABLE: MaterialityLevel.HIGH,
    StanceReasonCode.DECISION_SUPPORT_UNFAVORABLE: MaterialityLevel.HIGH,
    StanceReasonCode.PORTFOLIO_FIT_WEAK: MaterialityLevel.HIGH,
    # Real, relevant, but not alone case-changing.
    StanceReasonCode.CONFIDENCE_LIMITED: MaterialityLevel.MEDIUM,
    StanceReasonCode.THESIS_MIXED: MaterialityLevel.MEDIUM,
    StanceReasonCode.PORTFOLIO_FIT_FAVORABLE: MaterialityLevel.MEDIUM,
    # Real but mild.
    StanceReasonCode.CONFIDENCE_MODERATE: MaterialityLevel.LOW,
    StanceReasonCode.NO_HIGH_RISK: MaterialityLevel.LOW,
    # Routine "nothing changed" facts -- true, never lead-worthy.
    StanceReasonCode.THESIS_UNCHANGED: MaterialityLevel.BACKGROUND,
    StanceReasonCode.DECISION_SUPPORT_NEUTRAL: MaterialityLevel.BACKGROUND,
}

assert set(_STANCE_REASON_MATERIALITY) == set(StanceReasonCode), (
    "Every StanceReasonCode member must be classified -- an unclassified "
    "code would silently fall through to MaterialityLevel.UNKNOWN."
)

#: Fixed declared order -- never an invented weight, the same tie-break
#: discipline `risk_projection._TIE_BREAK_ORDER` established.
_LEVEL_ORDER: tuple[MaterialityLevel, ...] = (
    MaterialityLevel.CRITICAL,
    MaterialityLevel.HIGH,
    MaterialityLevel.MEDIUM,
    MaterialityLevel.LOW,
    MaterialityLevel.BACKGROUND,
    MaterialityLevel.UNKNOWN,
)
_LEVEL_RANK: dict[MaterialityLevel, int] = {level: index for index, level in enumerate(_LEVEL_ORDER)}
#: `StanceReasonCode`'s own declared member order -- the secondary,
#: deterministic tie-break when two reasons in the same bucket share a
#: `MaterialityLevel` (never arbitrary iteration order).
_CODE_ORDER: dict[StanceReasonCode, int] = {code: index for index, code in enumerate(StanceReasonCode)}


def _classify(reasons: tuple[StanceReason, ...]) -> tuple[MaterialEvidence, ...]:
    classified = tuple(
        MaterialEvidence(reason=r, materiality=_STANCE_REASON_MATERIALITY.get(r.code, MaterialityLevel.UNKNOWN))
        for r in reasons
    )
    return tuple(sorted(classified, key=lambda m: (_LEVEL_RANK[m.materiality], _CODE_ORDER[m.reason.code])))


def assess_materiality(explanation: Explanation) -> MaterialityAssessment:
    """Deterministic: identical `explanation` always produces a deeply
    equal `MaterialityAssessment`. Reads `explanation.supporting_evidence`/
    `.contradicting_evidence`/`.limiting_factors`/
    `.most_valuable_missing_information` -- nothing else, and never
    mutates or re-evaluates any of them."""
    supporting = _classify(explanation.supporting_evidence)
    contradicting = _classify(explanation.contradicting_evidence)
    limiting = _classify(explanation.limiting_factors)
    return MaterialityAssessment(
        supporting_evidence=supporting,
        contradicting_evidence=contradicting,
        limiting_factors=limiting,
        top_supporting_evidence=supporting[0] if supporting else None,
        top_contradicting_evidence=contradicting[0] if contradicting else None,
        top_limiting_factor=limiting[0] if limiting else None,
        top_missing_evidence=explanation.most_valuable_missing_information,
    )
