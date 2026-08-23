"""The Monitoring & Change Detection engine -- pure, deterministic,
orchestrates existing outputs rather than recomputing them (Deliverable
4). Every function here is a total function of already-computed
`EvidenceHistory`/`ChangeIntelligence`/`ActiveCaseConditionRow` values;
none of them read a repository, call a network, or produce a new
investment conclusion.

**Change taxonomy (Deliverable 5) -- source of each category:**

- `NEW_MATERIAL_EVIDENCE`, `MATERIAL_EVIDENCE_STRENGTHENED`/`_WEAKENED`,
  `EVIDENCE_BECAME_STALE`, `EVIDENCE_CONFLICT_APPEARED`/`_RESOLVED`,
  `COVERAGE_IMPROVED`/`_DETERIORATED`, `CONFIDENCE_IMPROVED`/
  `_DETERIORATED`, `STANCE_STRENGTHENED`/`_WEAKENED`/
  `_BECAME_UNCERTAIN` -- every one a direct, 1:1 relabeling of an
  `atlas.alpha.evidence_timeline.EvidenceTransition` already produced by
  `compare_evidence_snapshots`, keyed on `(category, direction)`.
  `NEW_MATERIAL_EVIDENCE` is the one category not keyed on a single
  transition -- it fires once per capture when `EvidenceHistory
  .new_source_evidence` is non-empty **and** at least one transition in
  the same capture is material (Deliverable 11's own "new data must
  materially change something," read literally: new evidence alone is
  never sufficient).
- `MATERIAL_RISK_APPEARED` -- a direct read of `ChangeIntelligence
  .changes` filtered to `ChangeCategory.RISK_ADDED`
  (`atlas.analysis_engine.investment_case_change`), always
  `ChangeDirection.NEGATIVE` by that category's own construction.
- `CASE_CONDITION_TRIGGERED` -- a direct read of
  `ActiveCaseConditionRow.status == "satisfied"`, the exact same
  current-state gate `atlas.alpha.daily_brief_agenda.engine
  .case_condition_signal` already applies (Deliverable 16: "a routine
  unsatisfied condition should produce no investor-facing monitoring
  event" -- already true of the reused gate, not reimplemented).

**Materiality (Deliverable 6) is reused, never reinvented.** Every
Evidence-Timeline-sourced category takes its `MonitoringMateriality`
directly from `EvidenceTransition.is_material`
(`atlas.alpha.evidence_timeline.engine.is_material_transition`).
`MATERIAL_RISK_APPEARED` is fixed `MATERIAL` (a new risk finding is, by
`ChangeCategory.RISK_ADDED`'s own construction, never a no-op).
`CASE_CONDITION_TRIGGERED` is `MATERIAL` when `role == "invalidation"`,
else `MINOR` -- the identical CRITICAL/HIGH split
`case_condition_signal` already uses, restated as Monitoring's own two-
level scale rather than the Agenda's four-level `PriorityLevel`.

**Noise suppression (Deliverable 11) is structural, not a filter bolted
on afterward.** A `MonitoringChange` can only exist here when a real
transition/finding/satisfied-condition was passed in -- there is no
code path that manufactures one from unchanged input. Running this
engine twice against the identical `EvidenceHistory`/`ChangeIntelligence`
(e.g. two `compare_*` calls against the same unchanged content hash)
produces the identical, empty change list both times, for free, because
`compare_evidence_snapshots`/`compare_snapshots` themselves already are
that idempotent (see each function's own module docstring) -- Monitoring
adds no new state to go stale.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from atlas.alpha.coverage.models import ConfidenceLevel
from atlas.alpha.daily_brief_agenda.models import AgendaItemKind
from atlas.alpha.evidence_timeline.engine import is_material_transition
from atlas.alpha.evidence_timeline.models import EvidenceHistory, EvidenceTransition, EvidenceTransitionCategory
from atlas.alpha.monitoring.models import (
    MonitoringChange,
    MonitoringChangeCategory,
    MonitoringMateriality,
    MonitoringResult,
    MonitoringRunRecord,
    MonitoringScope,
    OperationalMonitoringStatus,
    OperationalRunStatus,
    MonitoringStatus,
)
from atlas.analysis_engine.investment_case_change import ChangeCategory, ChangeDirection, ChangeIntelligence

__all__ = [
    "classify_evidence_history",
    "classify_material_risk",
    "classify_case_condition",
    "derive_status",
    "recommended_action",
    "build_monitoring_result",
    "HIGH_IMPORTANCE_CATEGORIES",
    "DAILY_BRIEF_EXCLUDED_CATEGORIES",
    "needs_recompute",
    "derive_operational_status",
]


@dataclass(frozen=True)
class CaseConditionSignal:
    """The one slice of `ActiveCaseConditionRow` this engine needs --
    kept local so this module never imports `atlas.core.domain
    .case_condition` types directly (Alpha never imports Core value
    objects it does not otherwise need; the service layer converts)."""

    condition_id: str
    role: str | None
    status: str
    predicate_text: str | None


# `(category, direction) -> MonitoringChangeCategory`. Every key here is
# a real `EvidenceTransitionCategory`/`ChangeDirection` pair
# `compare_evidence_snapshots` can actually produce -- see that
# function's own `_stance_transition`/`_coverage_transition`/etc. helpers.
_EVIDENCE_TRANSITION_MAP: dict[tuple[EvidenceTransitionCategory, ChangeDirection], MonitoringChangeCategory] = {
    (EvidenceTransitionCategory.EVIDENCE_QUALITY_CHANGED, ChangeDirection.POSITIVE): MonitoringChangeCategory.MATERIAL_EVIDENCE_STRENGTHENED,
    (EvidenceTransitionCategory.EVIDENCE_QUALITY_CHANGED, ChangeDirection.NEGATIVE): MonitoringChangeCategory.MATERIAL_EVIDENCE_WEAKENED,
    (EvidenceTransitionCategory.CONFLICT_STATUS_CHANGED, ChangeDirection.NEGATIVE): MonitoringChangeCategory.EVIDENCE_CONFLICT_APPEARED,
    (EvidenceTransitionCategory.CONFLICT_STATUS_CHANGED, ChangeDirection.POSITIVE): MonitoringChangeCategory.EVIDENCE_CONFLICT_RESOLVED,
    (EvidenceTransitionCategory.COVERAGE_CHANGED, ChangeDirection.POSITIVE): MonitoringChangeCategory.COVERAGE_IMPROVED,
    (EvidenceTransitionCategory.COVERAGE_CHANGED, ChangeDirection.NEGATIVE): MonitoringChangeCategory.COVERAGE_DETERIORATED,
    (EvidenceTransitionCategory.CONFIDENCE_CHANGED, ChangeDirection.POSITIVE): MonitoringChangeCategory.CONFIDENCE_IMPROVED,
    (EvidenceTransitionCategory.CONFIDENCE_CHANGED, ChangeDirection.NEGATIVE): MonitoringChangeCategory.CONFIDENCE_DETERIORATED,
    (EvidenceTransitionCategory.STANCE_CHANGED, ChangeDirection.POSITIVE): MonitoringChangeCategory.STANCE_STRENGTHENED,
    (EvidenceTransitionCategory.STANCE_CHANGED, ChangeDirection.NEGATIVE): MonitoringChangeCategory.STANCE_WEAKENED,
    (EvidenceTransitionCategory.STANCE_CHANGED, ChangeDirection.NEUTRAL): MonitoringChangeCategory.STANCE_BECAME_UNCERTAIN,
}

# `FRESHNESS_CHANGED` is handled separately below: only its
# `is_material_transition`-true case (current_state == stale) is ever
# reported, and it maps to one category regardless of direction --
# mirrors `is_material_transition`'s own asymmetric treatment exactly.

_REASON_TEMPLATE: dict[MonitoringChangeCategory, str] = {
    MonitoringChangeCategory.NEW_MATERIAL_EVIDENCE: "Atlas received new evidence that materially changed its reading of {ticker}.",
    MonitoringChangeCategory.MATERIAL_EVIDENCE_STRENGTHENED: "The overall quality of the evidence behind {ticker} improved.",
    MonitoringChangeCategory.MATERIAL_EVIDENCE_WEAKENED: "The overall quality of the evidence behind {ticker} declined.",
    MonitoringChangeCategory.EVIDENCE_BECAME_STALE: "The evidence behind {ticker} is now stale.",
    MonitoringChangeCategory.EVIDENCE_CONFLICT_APPEARED: "Atlas found evidence for {ticker} that disagrees with itself.",
    MonitoringChangeCategory.EVIDENCE_CONFLICT_RESOLVED: "A disagreement in the evidence for {ticker} was resolved.",
    MonitoringChangeCategory.COVERAGE_IMPROVED: "Atlas now understands more about {ticker} than before.",
    MonitoringChangeCategory.COVERAGE_DETERIORATED: "Atlas now understands less about {ticker} than before.",
    MonitoringChangeCategory.CONFIDENCE_IMPROVED: "Atlas's confidence in its analysis of {ticker} increased.",
    MonitoringChangeCategory.CONFIDENCE_DETERIORATED: "Atlas's confidence in its analysis of {ticker} decreased.",
    MonitoringChangeCategory.STANCE_STRENGTHENED: "Atlas's view on {ticker} strengthened.",
    MonitoringChangeCategory.STANCE_WEAKENED: "Atlas's view on {ticker} weakened.",
    MonitoringChangeCategory.STANCE_BECAME_UNCERTAIN: "Atlas's view on {ticker} changed, though not clearly for the better or worse.",
    MonitoringChangeCategory.MATERIAL_RISK_APPEARED: "Atlas identified a new risk for {ticker}.",
    MonitoringChangeCategory.CASE_CONDITION_TRIGGERED: "A condition you set for {ticker} was met: {predicate}.",
}


def _reason(category: MonitoringChangeCategory, *, ticker: str | None, predicate: str | None = None) -> str:
    label = ticker or "this company"
    return _REASON_TEMPLATE[category].format(ticker=label, predicate=predicate or "")


def classify_evidence_history(history: EvidenceHistory, *, ticker: str | None) -> tuple[MonitoringChange, ...]:
    """Every real `EvidenceTransition` in `history`, relabeled into
    Monitoring's own taxonomy, plus `NEW_MATERIAL_EVIDENCE` when new
    Source Evidence coincided with a material transition. Never called
    for a baseline `EvidenceHistory` by its caller (see `service.py`) --
    but safe regardless, since `history.transitions`/`new_source_evidence`
    are always `()` for a genuine baseline."""
    if history.is_baseline:
        return ()

    changes: list[MonitoringChange] = []
    for transition in history.transitions:
        change = _classify_transition(transition, ticker=ticker)
        if change is not None:
            changes.append(change)

    if history.new_source_evidence and any(is_material_transition(t) for t in history.transitions):
        changes.append(
            MonitoringChange(
                id=f"{MonitoringChangeCategory.NEW_MATERIAL_EVIDENCE.value}:{history.current_captured_at.isoformat()}",
                category=MonitoringChangeCategory.NEW_MATERIAL_EVIDENCE,
                materiality=MonitoringMateriality.MATERIAL,
                direction=ChangeDirection.NEUTRAL,
                reason=_reason(MonitoringChangeCategory.NEW_MATERIAL_EVIDENCE, ticker=ticker),
                source_capability="evidence_timeline",
                evidence_reference=None,
            )
        )
    return tuple(changes)


def _classify_transition(transition: EvidenceTransition, *, ticker: str | None) -> MonitoringChange | None:
    is_material = is_material_transition(transition)

    if transition.category is EvidenceTransitionCategory.FRESHNESS_CHANGED:
        if not is_material:
            return None
        return MonitoringChange(
            id=transition.id,
            category=MonitoringChangeCategory.EVIDENCE_BECAME_STALE,
            materiality=MonitoringMateriality.MATERIAL,
            direction=transition.direction,
            reason=_reason(MonitoringChangeCategory.EVIDENCE_BECAME_STALE, ticker=ticker),
            source_capability="evidence_timeline",
            evidence_reference=transition.id,
        )

    category = _EVIDENCE_TRANSITION_MAP.get((transition.category, transition.direction))
    if category is None:
        return None
    return MonitoringChange(
        id=transition.id,
        category=category,
        materiality=MonitoringMateriality.MATERIAL if is_material else MonitoringMateriality.MINOR,
        direction=transition.direction,
        reason=_reason(category, ticker=ticker),
        source_capability="evidence_timeline",
        evidence_reference=transition.id,
    )


def classify_material_risk(change_intelligence: ChangeIntelligence | None, *, ticker: str | None) -> tuple[MonitoringChange, ...]:
    """`ChangeIntelligence.changes` filtered to `RISK_ADDED` -- a new
    risk finding, always `NEGATIVE`, always `MATERIAL` by that
    category's own construction (`_highlight_changes` only ever adds a
    `RISK_ADDED` finding for a genuinely new risk-highlight kind)."""
    if change_intelligence is None or change_intelligence.is_baseline:
        return ()
    changes: list[MonitoringChange] = []
    for finding in change_intelligence.changes:
        if finding.category is not ChangeCategory.RISK_ADDED:
            continue
        changes.append(
            MonitoringChange(
                id=finding.id,
                category=MonitoringChangeCategory.MATERIAL_RISK_APPEARED,
                materiality=MonitoringMateriality.MATERIAL,
                direction=ChangeDirection.NEGATIVE,
                reason=_reason(MonitoringChangeCategory.MATERIAL_RISK_APPEARED, ticker=ticker),
                source_capability="change_intelligence",
                evidence_reference=finding.id,
            )
        )
    return tuple(changes)


def classify_case_condition(row: CaseConditionSignal, *, ticker: str | None) -> MonitoringChange | None:
    """`status == "satisfied"` only -- the identical current-state gate
    `atlas.alpha.daily_brief_agenda.engine.case_condition_signal`
    already applies; a routine `active`/`superseded`/`retired` condition
    produces nothing here either, by construction, not by a separate
    filter (Deliverable 16)."""
    if row.status != "satisfied":
        return None
    materiality = MonitoringMateriality.MATERIAL if row.role == "invalidation" else MonitoringMateriality.MINOR
    predicate = row.predicate_text or "a monitored condition"
    return MonitoringChange(
        id=f"{MonitoringChangeCategory.CASE_CONDITION_TRIGGERED.value}:{row.condition_id}",
        category=MonitoringChangeCategory.CASE_CONDITION_TRIGGERED,
        materiality=materiality,
        direction=ChangeDirection.NEGATIVE if row.role == "invalidation" else ChangeDirection.NEUTRAL,
        reason=_reason(MonitoringChangeCategory.CASE_CONDITION_TRIGGERED, ticker=ticker, predicate=predicate),
        source_capability="case_condition",
        evidence_reference=row.condition_id,
    )


# Deliverable 18 -- which categories, when material, mean "high
# importance" rather than merely "review suggested." A fixed, declared
# table, the same discipline `daily_brief_agenda.engine._WORKFLOW_PRIORITY`
# already uses -- never a numeric score. Exported (not private) because
# `daily_brief_agenda.engine.monitoring_signal` reuses this exact table
# for its own priority mapping, rather than maintaining a second one.
HIGH_IMPORTANCE_CATEGORIES = frozenset(
    {
        MonitoringChangeCategory.STANCE_WEAKENED,
        MonitoringChangeCategory.EVIDENCE_CONFLICT_APPEARED,
        MonitoringChangeCategory.MATERIAL_RISK_APPEARED,
        MonitoringChangeCategory.MATERIAL_EVIDENCE_WEAKENED,
        MonitoringChangeCategory.COVERAGE_DETERIORATED,
    }
)

# Deliverable 12 -- Deduplication. Both categories here already have
# their own, independent, pre-existing Daily Brief signal source that
# reads the *same underlying fact*: `MATERIAL_RISK_APPEARED` traces to
# the identical `ChangeFinding` `change_intelligence_signal` already
# turns into a Daily Brief item (via `ChangeIntelligence.thesis_impact`,
# which that finding itself drives); `CASE_CONDITION_TRIGGERED` traces
# to the identical `ActiveCaseConditionRow`
# `daily_brief_agenda.engine.case_condition_signal` already turns into
# one. Provenance is provable (same source id) in both cases, so per
# Deliverable 12's own "group related consequences... where provable"
# instruction, `daily_brief_agenda.engine.monitoring_signal` excludes
# these two categories rather than surface the same fact twice under
# two different sources. Both remain fully present on `MonitoringResult
# .changes` and drive `MonitoringStatus`/`recommended_action` normally
# -- only their *Daily Brief* signal is suppressed, not the fact itself.
DAILY_BRIEF_EXCLUDED_CATEGORIES = frozenset(
    {
        MonitoringChangeCategory.MATERIAL_RISK_APPEARED,
        MonitoringChangeCategory.CASE_CONDITION_TRIGGERED,
    }
)


def derive_status(changes: tuple[MonitoringChange, ...], confidence_level: ConfidenceLevel | None) -> MonitoringStatus:
    """Deliverable 18 -- derived, never invented. `UNAVAILABLE` is the
    caller's own responsibility (no Case/composition to evaluate at
    all); this function only ever sees a company Monitoring could
    genuinely evaluate."""
    material = [c for c in changes if c.materiality is MonitoringMateriality.MATERIAL]
    if any(c.category in HIGH_IMPORTANCE_CATEGORIES for c in material):
        return MonitoringStatus.CHANGED_HIGH_IMPORTANCE
    invalidation_triggered = any(
        c.category is MonitoringChangeCategory.CASE_CONDITION_TRIGGERED and c.direction is ChangeDirection.NEGATIVE for c in material
    )
    if invalidation_triggered:
        return MonitoringStatus.CHANGED_HIGH_IMPORTANCE
    if material:
        return MonitoringStatus.CHANGED_REVIEW_SUGGESTED
    if confidence_level is ConfidenceLevel.VERY_LIMITED:
        return MonitoringStatus.WAITING_FOR_BETTER_EVIDENCE
    return MonitoringStatus.UP_TO_DATE


# Deliverable 7 -- reuses `AgendaItemKind` verbatim; no new action
# vocabulary. `EVALUATE_CASE_CONDITION` always wins when present (the
# most specific, investor-authored destination), otherwise a plain
# review of the position/case, scoped by whether it is a real holding.
def recommended_action(changes: tuple[MonitoringChange, ...], *, is_holding: bool) -> AgendaItemKind | None:
    material = [c for c in changes if c.materiality is MonitoringMateriality.MATERIAL]
    if not material:
        return None
    if any(c.category is MonitoringChangeCategory.CASE_CONDITION_TRIGGERED for c in material):
        return AgendaItemKind.EVALUATE_CASE_CONDITION
    return AgendaItemKind.REVIEW_PORTFOLIO_POSITION if is_holding else AgendaItemKind.REVIEW_WATCHLIST_CANDIDATE


def build_monitoring_result(
    *,
    case_id: str,
    ticker: str | None,
    scope: MonitoringScope,
    is_holding: bool,
    evidence_history: EvidenceHistory | None,
    change_intelligence: ChangeIntelligence | None,
    case_condition_rows: tuple[CaseConditionSignal, ...],
    stance_level: str | None,
    confidence_level: ConfidenceLevel | None,
    coverage_level: str | None,
    latest_evidence_captured_at: datetime | None,
    generated_at: datetime,
) -> MonitoringResult:
    """Pure assembly -- every input already computed by its own
    capability; this function only classifies and rolls up. `None` for
    `evidence_history`/`change_intelligence` means that capability had
    nothing to report this run (never treated as an error, never
    fabricated into a change)."""
    changes: list[MonitoringChange] = []
    if evidence_history is not None:
        changes.extend(classify_evidence_history(evidence_history, ticker=ticker))
    changes.extend(classify_material_risk(change_intelligence, ticker=ticker))
    for row in case_condition_rows:
        change = classify_case_condition(row, ticker=ticker)
        if change is not None:
            changes.append(change)

    status = derive_status(tuple(changes), confidence_level)
    return MonitoringResult(
        case_id=case_id,
        ticker=ticker,
        scope=scope,
        status=status,
        changes=tuple(changes),
        stance_level=stance_level,
        confidence_level=confidence_level.value if confidence_level is not None else None,
        coverage_level=coverage_level,
        latest_meaningful_evidence_at=latest_evidence_captured_at,
        recommended_action=recommended_action(tuple(changes), is_holding=is_holding),
        generated_at=generated_at,
    )


# ---------------------------------------------------------------------
# Atlas Intelligence Sprint 8 -- Automated Monitoring Operations.
# Pure operational functions -- see `service.py`'s own module docstring
# for the full lifecycle (Deliverable 2) and for exactly which cheap
# signals `needs_recompute` is called with.
# ---------------------------------------------------------------------


def needs_recompute(checkpoint_at: datetime | None, latest_signal_at: datetime | None) -> bool:
    """Deliverable 4 -- the one incremental-monitoring rule. `True`
    when this Case has never been monitored (`checkpoint_at is None`),
    or when a real, dated signal (`latest_signal_at`, the newest of
    Decision/Observation/CaseCondition `recorded_at`/`updated_at` --
    see `service.py`'s own `_latest_signal_at`) is newer than the last
    successful checkpoint. Never `True` merely because time has passed
    -- there is no "N days since last run" branch here."""
    if checkpoint_at is None:
        return True
    return latest_signal_at is not None and latest_signal_at > checkpoint_at


def derive_operational_status(latest_run: MonitoringRunRecord | None, pending_count: int) -> OperationalMonitoringStatus:
    """Deliverable 7. `latest_run` is the most recent `MonitoringRunRecord`
    regardless of outcome; `pending_count` is how many known Cases
    `needs_recompute` currently returns `True` for. Order matters:
    a run actively `RUNNING` always wins (even with pending work behind
    it); a `FAILED` last run wins over mere pending work, since a
    failure is a stronger, more specific fact than "some Cases are
    due" -- see `MonitoringRunRecord.status`'s own docstring for why
    `FAILED` describes an otherwise-completed run's outcome, not a
    crash."""
    if latest_run is None:
        return OperationalMonitoringStatus.UNKNOWN
    if latest_run.status is OperationalRunStatus.RUNNING:
        return OperationalMonitoringStatus.RUNNING
    if latest_run.status is OperationalRunStatus.FAILED:
        return OperationalMonitoringStatus.FAILED
    if pending_count > 0:
        return OperationalMonitoringStatus.PENDING
    return OperationalMonitoringStatus.UP_TO_DATE
