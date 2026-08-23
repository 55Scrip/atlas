"""Evidence Timeline Engine (Atlas Intelligence -- Evidence Timeline &
Historical Understanding).

**Deliverable 1's audit, in one place.** `atlas.analysis_engine
.investment_case_change` already gives this codebase a complete, real,
persisted point-in-time comparison mechanism (`AnalyticalSnapshot`,
`capture_snapshot`, `compare_snapshots`) plus a durable, per-Case
snapshot store (`atlas.alpha.investment_case_change.repository
.SqlAlchemyInvestmentCaseSnapshotRepository`, "History v1") and a
read-only cross-Case timeline reader (`atlas.alpha
.investment_case_history`) -- already wired into `InvestmentCase
CompositionService.build()` and already exposed at `GET /history
/analysis`. That mechanism captures the *company's* analytical state
(business/risk/valuation category conclusions, strengths, risks, open
questions, the Atlas Thesis narrative) -- real timestamps
(`AnalyticalSnapshot.captured_at` is `CanonicalAnalysis.generated_at`),
a real event shape (a new row only when content genuinely changes,
content-hash-deduplicated), and a real, already-legitimate place on a
timeline.

**What that mechanism does not, and cannot, cover**: it predates Sprint
1 (Coverage & Confidence), Sprint 2 (Stance), and Sprint 4 (Evidence
Quality) -- `AnalyticalSnapshot` has no field for any of their signals.
No snapshot of "what was Coverage/Confidence/Stance/Evidence Quality at
time T" has ever been captured, for any Case, at any point before this
Sprint. Per this Sprint's own "never fabricate missing events"
instruction, that history genuinely does not exist and is not invented
retroactively -- every Case in this codebase starts Sprint 5 with a
real, honest, empty Evidence Timeline (a baseline), and real transitions
only begin accumulating from the first real call after this Sprint
ships. This is documented, not hidden.

**This module is the new capture mechanism for exactly those four
signals**, deliberately mirroring `investment_case_change.py`'s own
`capture_snapshot`/`compare_snapshots` pair -- same shape, same
determinism, same "content hash decides whether anything changed"
discipline -- one layer up, fed by `CoverageAssessment`/`Stance`/
`EvidenceQualityReport` instead of a raw `CanonicalAnalysis`. It
performs no new analysis: every field on `EvidenceSnapshot` is read
verbatim from an already-computed object; every `EvidenceTransition` is
a deterministic before/after comparison over already-ranked closed
enums, never a numeric score.

**Deliverable 2 -- Source Evidence History.** `capture_evidence_snapshot`
also records `known_periods`, a real `(fact_kind, period)` set read
straight off `InvestmentCaseComposition.business_facts`/`.market_facts`
(already-computed, post-conflict-drop facts -- see
`atlas.alpha.evidence_quality`'s own audit for why these, not a raw
`BusinessRecord` re-read, are the correct "facts Atlas is actually
using" source). `compare_evidence_snapshots` finds `SourceEvidenceEvent`s
by set-differencing two real, persisted `known_periods` tuples -- never
by re-deriving "new" from a single snapshot alone, and never when no
real prior snapshot exists (a baseline has no `known_periods` to diff
against; see that function's own `is_baseline` branch).

**Deliverable 7 -- Materiality Integration.** `is_material_transition`
is a fixed, declared filter -- never a second priority engine (Sprint
5's own Materiality Engine already owns "what matters"; this reuses its
core discipline -- gates/conflicts/severe-negative signals are always
material -- applied to the `(category, direction, state)` triples this
package's own closed vocabulary produces, since a raw `EvidenceTransition`
carries no `StanceReasonCode` for Materiality's own map to classify
directly).

**Deliverable 14 -- Evidence Freshness Transitions.** `derive_staleness_date`
is a pure calculation from a fact's own real `latest_published_at` plus
the *same* freshness threshold `atlas.alpha.evidence_quality.engine`'s
own (private) `_STALE_THRESHOLD_DAYS` already uses -- re-derived here
from the one public constant both ultimately depend on
(`atlas.alpha.portfolio_status.service.VERY_OLD_CASE_THRESHOLD_DAYS`),
never a second, independently-invented number. This is explicitly a
**derived** date, not an **observed** one: no row is ever written
recording "this fact became stale on this date" -- the date is
recomputed fresh, every time, from data already on hand. See that
function's own docstring for why this distinction is load-bearing.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta

from atlas.alpha.coverage import ConfidenceLevel, CoverageAssessment
from atlas.alpha.evidence_quality import EvidenceConflictStatus, EvidenceFreshness, EvidenceQualityLevel, EvidenceQualityReport
from atlas.alpha.evidence_quality.models import FactQuality
from atlas.alpha.portfolio_status.service import VERY_OLD_CASE_THRESHOLD_DAYS
from atlas.alpha.stance import Stance, StanceLevel
from atlas.analysis_engine.analysis_coverage import AnalysisCoverageLevel
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.investment_case_change import ChangeDirection
from atlas.analysis_engine.valuation.facts import ValuationFact

from .models import EvidenceHistory, EvidenceSnapshot, EvidenceTransition, EvidenceTransitionCategory, SourceEvidenceEvent

__all__ = [
    "capture_evidence_snapshot",
    "compare_evidence_snapshots",
    "is_material_transition",
    "material_transitions",
    "derive_staleness_date",
]

#: Must stay in lockstep with `atlas.alpha.evidence_quality.engine`'s
#: own private `_STALE_THRESHOLD_DAYS` -- both are re-derived from the
#: identical public constant rather than one importing the other's
#: private name, the same "reuse the one real threshold, never a second
#: invented number" discipline that module's own docstring establishes.
_STALE_THRESHOLD_DAYS = VERY_OLD_CASE_THRESHOLD_DAYS * 4

#: Fixed, declared rank orders -- never an invented numeric score, the
#: same "fixed dependency/priority order" discipline `risk_projection`'s
#: own `_TIE_BREAK_ORDER` and Sprint 4's own `_QUALITY_PRIORITY`
#: establish. Each maps a closed enum's own member to its position on a
#: worse-to-better scale, used only to decide a transition's
#: `ChangeDirection`, never rendered.
_COVERAGE_RANK = {
    AnalysisCoverageLevel.NO_COVERAGE: 0,
    AnalysisCoverageLevel.PARTIAL_COVERAGE: 1,
    AnalysisCoverageLevel.SUBSTANTIAL_COVERAGE: 2,
}
_CONFIDENCE_RANK = {
    ConfidenceLevel.VERY_LIMITED: 0,
    ConfidenceLevel.LIMITED: 1,
    ConfidenceLevel.MODERATE: 2,
    ConfidenceLevel.HIGH: 3,
}
_FRESHNESS_RANK = {
    EvidenceFreshness.STALE: 0,
    EvidenceFreshness.OLD: 1,
    EvidenceFreshness.RECENT: 2,
    EvidenceFreshness.FRESH: 3,
}
_QUALITY_RANK = {
    EvidenceQualityLevel.CONFLICTING: 0,
    EvidenceQualityLevel.UNSUPPORTED: 1,
    EvidenceQualityLevel.STALE: 2,
    EvidenceQualityLevel.INCOMPLETE: 3,
    EvidenceQualityLevel.OLD: 4,
    EvidenceQualityLevel.RECENT: 5,
    EvidenceQualityLevel.FRESH: 6,
}
#: `StanceLevel`'s own direction reading -- mirrors the tone this
#: codebase's own `STANCE_LEVEL_TONE` frontend map already establishes
#: (`increase`="View strengthened", `reduce`="View weakened"), never a
#: trade-sizing interpretation (Atlas Intelligence Sprint 2's own
#: standing rule).
_STANCE_DIRECTION = {
    StanceLevel.INCREASE: ChangeDirection.POSITIVE,
    StanceLevel.REDUCE: ChangeDirection.NEGATIVE,
}


def capture_evidence_snapshot(
    coverage: CoverageAssessment,
    evidence_quality: EvidenceQualityReport,
    stance: Stance | None,
    business_facts: tuple[BusinessFact, ...] = (),
    market_facts: tuple[ValuationFact, ...] = (),
    *,
    captured_at: datetime,
) -> EvidenceSnapshot:
    """Pure projection of already-computed Coverage/Stance/Evidence
    Quality results, plus the same post-conflict-drop
    `business_facts`/`market_facts` `InvestmentCaseComposition` already
    exposes -- never a `BusinessRecord` or `CanonicalAnalysis` directly.
    `captured_at` is always caller-supplied (the same `CanonicalAnalysis
    .generated_at` every sibling snapshot mechanism in this codebase
    uses), never a wall-clock read. `business_facts`/`market_facts`
    default to `()` so existing callers/tests that only care about
    Coverage/Stance/Evidence Quality history are unaffected -- an empty
    tuple honestly means "no known periods," never a fabricated one."""
    known_periods = tuple(sorted({f"{f.kind.value}:{f.period}" for f in (*business_facts, *market_facts)}))

    hashed_content = {
        "overall_coverage": coverage.overall_coverage.value,
        "overall_confidence": coverage.overall_confidence.value,
        "stance_level": stance.level.value if stance is not None else None,
        "evidence_quality": evidence_quality.quality.value,
        "conflict_status": evidence_quality.conflict_status.value,
        "freshness": evidence_quality.freshness.value,
        "missing_dimensions": sorted(coverage.missing_dimensions),
        "known_periods": known_periods,
    }
    content_hash = hashlib.sha256(json.dumps(hashed_content, sort_keys=True).encode("utf-8")).hexdigest()

    return EvidenceSnapshot(
        overall_coverage=coverage.overall_coverage.value,
        overall_confidence=coverage.overall_confidence.value,
        stance_level=stance.level.value if stance is not None else None,
        evidence_quality=evidence_quality.quality.value,
        conflict_status=evidence_quality.conflict_status.value,
        freshness=evidence_quality.freshness.value,
        missing_dimensions=tuple(sorted(coverage.missing_dimensions)),
        known_periods=known_periods,
        content_hash=content_hash,
        captured_at=captured_at,
    )


def _coverage_transition(previous: EvidenceSnapshot, current: EvidenceSnapshot) -> EvidenceTransition | None:
    if previous.overall_coverage == current.overall_coverage:
        return None
    prev_rank = _COVERAGE_RANK[AnalysisCoverageLevel(previous.overall_coverage)]
    curr_rank = _COVERAGE_RANK[AnalysisCoverageLevel(current.overall_coverage)]
    direction = ChangeDirection.POSITIVE if curr_rank > prev_rank else ChangeDirection.NEGATIVE
    return EvidenceTransition(
        id="evidence_transition:coverage",
        category=EvidenceTransitionCategory.COVERAGE_CHANGED,
        direction=direction,
        previous_state=previous.overall_coverage,
        current_state=current.overall_coverage,
        details={},
    )


def _confidence_transition(previous: EvidenceSnapshot, current: EvidenceSnapshot) -> EvidenceTransition | None:
    if previous.overall_confidence == current.overall_confidence:
        return None
    prev_rank = _CONFIDENCE_RANK[ConfidenceLevel(previous.overall_confidence)]
    curr_rank = _CONFIDENCE_RANK[ConfidenceLevel(current.overall_confidence)]
    direction = ChangeDirection.POSITIVE if curr_rank > prev_rank else ChangeDirection.NEGATIVE
    return EvidenceTransition(
        id="evidence_transition:confidence",
        category=EvidenceTransitionCategory.CONFIDENCE_CHANGED,
        direction=direction,
        previous_state=previous.overall_confidence,
        current_state=current.overall_confidence,
        details={},
    )


def _stance_transition(previous: EvidenceSnapshot, current: EvidenceSnapshot) -> EvidenceTransition | None:
    if previous.stance_level == current.stance_level:
        return None
    if previous.stance_level is None or current.stance_level is None:
        return None
    direction = _STANCE_DIRECTION.get(StanceLevel(current.stance_level), ChangeDirection.NEUTRAL)
    return EvidenceTransition(
        id="evidence_transition:stance",
        category=EvidenceTransitionCategory.STANCE_CHANGED,
        direction=direction,
        previous_state=previous.stance_level,
        current_state=current.stance_level,
        details={},
    )


def _freshness_transition(previous: EvidenceSnapshot, current: EvidenceSnapshot) -> EvidenceTransition | None:
    if previous.freshness == current.freshness:
        return None
    prev_level = EvidenceFreshness(previous.freshness)
    curr_level = EvidenceFreshness(current.freshness)
    if prev_level not in _FRESHNESS_RANK or curr_level not in _FRESHNESS_RANK:
        direction = ChangeDirection.NEUTRAL
    else:
        direction = ChangeDirection.POSITIVE if _FRESHNESS_RANK[curr_level] > _FRESHNESS_RANK[prev_level] else ChangeDirection.NEGATIVE
    return EvidenceTransition(
        id="evidence_transition:freshness",
        category=EvidenceTransitionCategory.FRESHNESS_CHANGED,
        direction=direction,
        previous_state=previous.freshness,
        current_state=current.freshness,
        details={},
    )


def _conflict_status_transition(previous: EvidenceSnapshot, current: EvidenceSnapshot) -> EvidenceTransition | None:
    if previous.conflict_status == current.conflict_status:
        return None
    if current.conflict_status == EvidenceConflictStatus.CONFLICTING.value:
        direction = ChangeDirection.NEGATIVE
    elif previous.conflict_status == EvidenceConflictStatus.CONFLICTING.value:
        direction = ChangeDirection.POSITIVE
    else:
        direction = ChangeDirection.NEUTRAL
    return EvidenceTransition(
        id="evidence_transition:conflict_status",
        category=EvidenceTransitionCategory.CONFLICT_STATUS_CHANGED,
        direction=direction,
        previous_state=previous.conflict_status,
        current_state=current.conflict_status,
        details={},
    )


def _evidence_quality_transition(previous: EvidenceSnapshot, current: EvidenceSnapshot) -> EvidenceTransition | None:
    if previous.evidence_quality == current.evidence_quality:
        return None
    prev_level = EvidenceQualityLevel(previous.evidence_quality)
    curr_level = EvidenceQualityLevel(current.evidence_quality)
    if prev_level not in _QUALITY_RANK or curr_level not in _QUALITY_RANK:
        direction = ChangeDirection.NEUTRAL
    else:
        direction = ChangeDirection.POSITIVE if _QUALITY_RANK[curr_level] > _QUALITY_RANK[prev_level] else ChangeDirection.NEGATIVE
    return EvidenceTransition(
        id="evidence_transition:evidence_quality",
        category=EvidenceTransitionCategory.EVIDENCE_QUALITY_CHANGED,
        direction=direction,
        previous_state=previous.evidence_quality,
        current_state=current.evidence_quality,
        details={},
    )


_TRANSITION_BUILDERS = (
    _coverage_transition,
    _confidence_transition,
    _stance_transition,
    _freshness_transition,
    _conflict_status_transition,
    _evidence_quality_transition,
)


def _source_evidence_events(previous: EvidenceSnapshot, current: EvidenceSnapshot) -> tuple[SourceEvidenceEvent, ...]:
    """Deliverable 2 -- Source Evidence History. A genuine set
    difference over two real, persisted `known_periods` tuples -- never
    a re-derivation from `current` alone (which could not honestly
    distinguish "always known" from "newly known" without a real prior
    snapshot to compare against)."""
    new_keys = sorted(set(current.known_periods) - set(previous.known_periods))
    events: list[SourceEvidenceEvent] = []
    for key in new_keys:
        fact_kind, _, period = key.partition(":")
        events.append(SourceEvidenceEvent(fact_kind=fact_kind, period=period))
    return tuple(events)


def compare_evidence_snapshots(previous: EvidenceSnapshot | None, current: EvidenceSnapshot) -> EvidenceHistory:
    """Deterministic: identical `previous`/`current` always produce a
    deeply equal `EvidenceHistory`. `previous=None` means no prior
    snapshot exists -- a baseline, not a change (`transitions=()` *and*
    `new_source_evidence=()`; Deliverable 5's own "Historical Honesty"
    bar applies identically to both kinds of history -- a fact cannot
    honestly be called "new" without a real prior snapshot recording it
    was once absent). Mirrors `investment_case_change.compare_snapshots`'s
    own calling convention exactly: a caller (`investment_case/api
    /router.py`) may call this unconditionally on every request,
    including one where nothing changed since the last capture -- every
    comparison below naturally produces zero transitions/events in that
    case, so this stays safe either way; the repository's own `add()`,
    not this function, is what keeps a no-op from ever being persisted
    as a duplicate row."""
    if previous is None:
        return EvidenceHistory(
            is_baseline=True, transitions=(), new_source_evidence=(), previous_captured_at=None, current_captured_at=current.captured_at
        )

    transitions = tuple(t for builder in _TRANSITION_BUILDERS if (t := builder(previous, current)) is not None)
    return EvidenceHistory(
        is_baseline=False,
        transitions=transitions,
        new_source_evidence=_source_evidence_events(previous, current),
        previous_captured_at=previous.captured_at,
        current_captured_at=current.captured_at,
    )


#: Deliverable 7 -- Materiality Integration. A fixed, declared rule:
#: which `EvidenceTransitionCategory` always warrants prominence
#: regardless of direction (a real conflict or a Stance change is
#: always investor-relevant, whichever way it moved) versus only when
#: the direction is negative (a confidence/quality decline matters more
#: than a routine improvement) or the current state itself names the
#: material condition (freshly stale). Coverage changes are always
#: material -- a real change in what Atlas can evaluate at all.
_ALWAYS_MATERIAL_CATEGORIES = frozenset(
    {
        EvidenceTransitionCategory.CONFLICT_STATUS_CHANGED,
        EvidenceTransitionCategory.STANCE_CHANGED,
        EvidenceTransitionCategory.COVERAGE_CHANGED,
    }
)
_MATERIAL_WHEN_NEGATIVE_CATEGORIES = frozenset(
    {
        EvidenceTransitionCategory.CONFIDENCE_CHANGED,
        EvidenceTransitionCategory.EVIDENCE_QUALITY_CHANGED,
    }
)


def is_material_transition(transition: EvidenceTransition) -> bool:
    """Never a second priority engine -- a fixed, declared filter over
    this package's own closed `(category, direction, state)`
    vocabulary, the same "materiality explains, it does not fabricate"
    discipline `atlas.alpha.materiality`'s own module docstring
    establishes one layer over Stance's reason codes, applied here."""
    if transition.category in _ALWAYS_MATERIAL_CATEGORIES:
        return True
    if transition.category in _MATERIAL_WHEN_NEGATIVE_CATEGORIES and transition.direction is ChangeDirection.NEGATIVE:
        return True
    if transition.category is EvidenceTransitionCategory.FRESHNESS_CHANGED and transition.current_state == EvidenceFreshness.STALE.value:
        return True
    return False


def material_transitions(history: EvidenceHistory) -> tuple[EvidenceTransition, ...]:
    """The subset of `history.transitions` Deliverable 7 says should
    receive prominence -- every other real transition remains fully
    available on `history.transitions` itself (Deliverable 5's own
    "never remove information," applied to prominence the same way
    Materiality applies it to evidence buckets)."""
    return tuple(t for t in history.transitions if is_material_transition(t))


def derive_staleness_date(fact: FactQuality) -> datetime | None:
    """Deliverable 14. A **derived** calculation, not an **observed**
    event: no row anywhere records "this fact became stale on this
    date" -- this function recomputes it fresh from `fact
    .latest_published_at` (a real, already-known timestamp) plus the
    identical threshold `atlas.alpha.evidence_quality.engine` already
    uses to classify `EvidenceFreshness.STALE`. The returned date may
    be in the past (the fact is already stale) or the future (it will
    become stale later) -- both are honest, deterministic facts about
    a threshold crossing, never a claim that Atlas observed the
    crossing happen. Returns `None` only when `fact.latest_published_at`
    itself is `None` (nothing to derive from)."""
    if fact.latest_published_at is None:
        return None
    return fact.latest_published_at + timedelta(days=_STALE_THRESHOLD_DAYS)
