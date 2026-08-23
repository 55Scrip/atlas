"""Result shapes for the Monitoring & Change Detection layer (Atlas
Intelligence Sprint 7). See `engine.py`'s own module docstring for the
full derivation rules, and this package's `__init__.py` for the
Monitoring Audit (Deliverable 1) and Monitoring Boundary (Deliverable 2).

**Smallest possible model (Deliverable 3).** Four concepts, no more:
`MonitoringChangeCategory` (the closed taxonomy, Deliverable 5),
`MonitoringChange` (one classified, already-detected change),
`MonitoringResult` (one company's monitoring state, the unit Daily
Brief/Investment Case/the read model all consume), `MonitoringRun` (one
explicit evaluation across every monitored company, Deliverable 20).
Nothing here recomputes an investment conclusion -- every field is a
reclassification of an output `atlas.alpha.evidence_timeline`/
`atlas.analysis_engine.investment_case_change`/`CaseCondition` already
produced.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.alpha.daily_brief_agenda.models import AgendaItemKind
from atlas.alpha.ingestion.engine import DataFreshnessStatus
from atlas.analysis_engine.investment_case_change import ChangeDirection

__all__ = [
    "MonitoringChangeCategory",
    "MonitoringMateriality",
    "MonitoringStatus",
    "MonitoringScope",
    "MonitoringChange",
    "MonitoringResult",
    "MonitoringRun",
    "OperationalRunStatus",
    "OperationalMonitoringStatus",
    "MonitoringFailure",
    "MonitoringRunRecord",
    "CaseOperationalFreshness",
    "MonitoringOperationalStatus",
]


class MonitoringChangeCategory(str, Enum):
    """Deliverable 5's closed taxonomy. Every member is directly proven
    by a real, already-computed field -- see `engine.py`'s own
    `_classify_evidence_transition`/`_classify_case_condition`/
    `_classify_material_risk` for the exact source of each. Two of the
    brief's own example members (`PORTFOLIO_FIT_IMPROVED`/
    `PORTFOLIO_FIT_DETERIORATED`) are deliberately omitted -- see this
    package's own `__init__.py`, "Deduplication" section, for why:
    `FitTrend` is itself only a relabeling of `ChangeIntelligence
    .thesis_impact` (`atlas.alpha.portfolio_fit.engine
    ._TREND_BY_THESIS_IMPACT`), so a Portfolio-Fit-sourced category
    would silently duplicate `STANCE_STRENGTHENED`/`STANCE_WEAKENED`/
    `MATERIAL_RISK_APPEARED` below rather than prove a genuinely
    independent fact."""

    NEW_MATERIAL_EVIDENCE = "new_material_evidence"
    MATERIAL_EVIDENCE_STRENGTHENED = "material_evidence_strengthened"
    MATERIAL_EVIDENCE_WEAKENED = "material_evidence_weakened"
    EVIDENCE_BECAME_STALE = "evidence_became_stale"
    EVIDENCE_CONFLICT_APPEARED = "evidence_conflict_appeared"
    EVIDENCE_CONFLICT_RESOLVED = "evidence_conflict_resolved"
    COVERAGE_IMPROVED = "coverage_improved"
    COVERAGE_DETERIORATED = "coverage_deteriorated"
    CONFIDENCE_IMPROVED = "confidence_improved"
    CONFIDENCE_DETERIORATED = "confidence_deteriorated"
    STANCE_STRENGTHENED = "stance_strengthened"
    STANCE_WEAKENED = "stance_weakened"
    STANCE_BECAME_UNCERTAIN = "stance_became_uncertain"
    MATERIAL_RISK_APPEARED = "material_risk_appeared"
    CASE_CONDITION_TRIGGERED = "case_condition_triggered"


class MonitoringMateriality(str, Enum):
    """Deliverable 6 -- reused, never a second priority scale. For every
    Evidence-Timeline-sourced category this is a direct read of
    `EvidenceTransition.is_material` (`atlas.alpha.evidence_timeline
    .engine.is_material_transition`, Sprint 6's own reuse of Sprint 5's
    Materiality judgment); for `MATERIAL_RISK_APPEARED`/
    `CASE_CONDITION_TRIGGERED` it is a small, fixed, documented rule
    (see `engine.py`), never an invented score."""

    MATERIAL = "material"
    MINOR = "minor"


class MonitoringStatus(str, Enum):
    """Deliverable 18. Derived entirely from already-computed
    materiality and Coverage/Confidence -- never a new health score."""

    UP_TO_DATE = "up_to_date"
    CHANGED_REVIEW_SUGGESTED = "changed_review_suggested"
    CHANGED_HIGH_IMPORTANCE = "changed_high_importance"
    WAITING_FOR_BETTER_EVIDENCE = "waiting_for_better_evidence"
    UNAVAILABLE = "unavailable"


class MonitoringScope(str, Enum):
    """Deliverable 17 -- the exact, already-established scope
    `atlas.alpha.case_membership.known_cases` defines (Portfolio
    holdings + Watchlist companies), reused verbatim rather than
    redefined here."""

    PORTFOLIO = "portfolio"
    WATCHLIST = "watchlist"


@dataclass(frozen=True)
class MonitoringChange:
    """One classified, already-detected change (Deliverable 3's own
    "what changed / how important / why does it matter / what
    capability detected it" questions, answered per field)."""

    id: str
    category: MonitoringChangeCategory
    materiality: MonitoringMateriality
    direction: ChangeDirection
    reason: str
    """A fixed-template sentence (Deliverable 23) -- never generated
    text."""
    source_capability: str
    """Which existing Atlas capability detected this -- one of
    `"evidence_timeline"`, `"change_intelligence"`, `"case_condition"`.
    Traceability, not a new taxonomy of its own."""
    evidence_reference: str | None
    """The real id of the underlying `EvidenceTransition`/
    `ChangeFinding`/`CaseCondition` this was classified from -- never
    fabricated, `None` only when no stable id exists on the source."""


@dataclass(frozen=True)
class MonitoringResult:
    """One company's monitoring state -- the unit Daily Brief, the
    Investment Case page, and the read model (Deliverable 21) all
    consume. `changes` holds every classified change this run found for
    this company, material and minor alike (Deliverable 12: never
    hidden, only prioritized); Daily Brief and other prominence-driven
    surfaces filter to `materiality is MATERIAL` themselves, mirroring
    exactly how `EvidenceTimelinePanel` already treats
    `EvidenceTransition.is_material`."""

    case_id: str
    ticker: str | None
    scope: MonitoringScope
    status: MonitoringStatus
    changes: tuple[MonitoringChange, ...]
    stance_level: str | None
    confidence_level: str | None
    coverage_level: str | None
    latest_meaningful_evidence_at: datetime | None
    """The most recent `captured_at` among this run's Evidence Timeline
    snapshot and any material change found -- `None` when genuinely
    unknown, never defaulted to "now"."""
    recommended_action: AgendaItemKind | None
    """Deliverable 7 -- reuses `AgendaItemKind` verbatim (the existing
    closed workflow-destination vocabulary `daily_brief_agenda` already
    established) rather than inventing a parallel action taxonomy.
    `None` only when `status is UP_TO_DATE` and there is genuinely
    nothing to route the investor toward."""
    generated_at: datetime


@dataclass(frozen=True)
class MonitoringRun:
    """Deliverable 20's own explicit run output -- every
    `MonitoringResult` this run produced, oldest-scope-first
    (Portfolio, then Watchlist), never partially applied."""

    generated_at: datetime
    results: tuple[MonitoringResult, ...]


# ---------------------------------------------------------------------
# Atlas Intelligence Sprint 8 -- Automated Monitoring Operations.
# Everything below is *operational* state (is Monitoring itself
# up to date?) -- deliberately never mixed with the *investment* state
# above (`MonitoringStatus`, `MonitoringResult`). See this package's
# own `__init__.py` for the full Deliverable 2 lifecycle and Deliverable
# 3 "why no DirtyCompany table" rationale.
# ---------------------------------------------------------------------


class OperationalRunStatus(str, Enum):
    """The lifecycle of one `MonitoringRunRecord` -- distinct from
    `OperationalMonitoringStatus` below (a run's own state vs. the
    system's overall state, which also considers pending work between
    runs)."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    """At least one company failed to evaluate during this run --
    the run itself still completed (every other company was evaluated
    and persisted); `FAILED` describes its outcome, not a crash."""


class OperationalMonitoringStatus(str, Enum):
    """Deliverable 7 -- whether Monitoring *itself* is current. Never
    conflated with `MonitoringStatus` (whether a *company's investment
    picture* changed) -- a company can be `UP_TO_DATE` on investment
    status while Monitoring overall is `PENDING` for a different
    company entirely."""

    UP_TO_DATE = "up_to_date"
    RUNNING = "running"
    PENDING = "pending"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class MonitoringFailure:
    """One company Monitoring could not evaluate during a run
    (Deliverable 6). Never silently dropped -- kept on `MonitoringRun
    Record.failures` and re-attempted (never marked clean) on the next
    run, since the failure means no new checkpoint was ever written for
    this company."""

    case_id: str
    ticker: str | None
    error: str
    """A short, safe description (`type(exc).__name__: str(exc)`) --
    never a full traceback exposed over the API."""


@dataclass(frozen=True)
class MonitoringRunRecord:
    """Deliverable 3 -- the one new persisted operational concept this
    sprint needs: a record of one `MonitoringService.run()` execution.
    Not a job queue, not a scheduler -- one row per call, written at
    start and updated at completion, so a concurrent status read can
    honestly observe `RUNNING` (Deliverable 7) and so `GET /monitoring
    /status` never has to guess whether the last run actually finished."""

    run_id: str
    status: OperationalRunStatus
    started_at: datetime
    completed_at: datetime | None
    forced: bool
    """Whether this run was invoked with `force=True` (evaluated every
    known company, not just dirty ones) -- Deliverable 13's own
    documented escape hatch for changes this sprint's cheap dirty-check
    cannot detect (see `service.py`'s own module docstring)."""
    evaluated_count: int
    skipped_count: int
    """How many known companies were skipped because they were not
    dirty -- Deliverable 4's own incremental-monitoring proof, exposed
    rather than hidden."""
    failures: tuple[MonitoringFailure, ...]


@dataclass(frozen=True)
class CaseOperationalFreshness:
    """Deliverable 15 -- what Investment Case needs to honestly
    disclose about *operational* freshness, kept fully separate from
    `MonitoringStatusView` (investment status) on the same page."""

    is_pending: bool
    """`True` when this Case has a real, detected reason to be
    recomputed that the last run has not yet picked up -- never `True`
    merely because time has passed."""
    last_monitored_at: datetime | None
    """`None` only when this Case has never been evaluated by
    Monitoring at all."""
    last_run_failed_for_case: bool
    """`True` only when the most recent attempt to evaluate this
    specific Case raised and was never superseded by a later success
    (Deliverable 6's own "never silently mark clean")."""
    data_freshness_status: DataFreshnessStatus
    """Atlas Intelligence Sprint 9 (Data Ingestion & Automatic Refresh,
    Deliverable 6/7) -- the granular, Ingestion-grounded status
    (`waiting_for_new_data`/`waiting_for_analysis`/`monitoring_failed`/
    `no_data_source`/`unknown`). `is_pending` above is kept, unchanged,
    for backward compatibility with existing readers; this field is
    the authoritative, more precise successor for anything that needs
    to distinguish *why* a Case is pending."""


@dataclass(frozen=True)
class ScopeFreshnessSummary:
    """Atlas Intelligence Sprint 9, Deliverable 8/9 -- the aggregate
    count Portfolio ("X holdings waiting for refresh...") and
    Watchlist want, computed once server-side rather than re-derived
    per row on the frontend. Deliberately three buckets, not a raw
    breakdown of all five `DataFreshnessStatus` values: the brief's own
    example language ("waiting for refresh" / "already refreshed" /
    "no new data") does not correspond to a real fourth or fifth
    distinguishable fact Atlas can honestly compute (see
    `DataFreshnessStatus`'s own docstring, which already merged the
    brief's "new data available" and "waiting for refresh" examples
    into one real state for the identical reason) -- `needs_attention`
    groups `monitoring_failed`/`no_data_source`/`unknown` because none
    of those three is "waiting on new data" in the ordinary sense, and
    splitting them further would invent a distinction the underlying
    facts don't carry."""

    waiting_for_analysis: int
    """New/replaced data has been detected but Monitoring has not yet
    recomputed this Case (`DataFreshnessStatus.WAITING_FOR_ANALYSIS`)."""
    no_new_data: int
    """Ingestion has checked and found nothing new since the last
    check (`DataFreshnessStatus.WAITING_FOR_NEW_DATA`)."""
    needs_attention: int
    """`monitoring_failed` / `no_data_source` / `unknown` combined --
    not a refresh-timing fact, a disclosure that Atlas's own read is
    incomplete for this company."""


@dataclass(frozen=True)
class MonitoringOperationalStatus:
    """Deliverable 14's own read model -- `GET /monitoring/status`.
    Deliberately narrow: counts and the pending/failed ticker lists,
    never the internal dirty-detection mechanism itself."""

    status: OperationalMonitoringStatus
    last_run_started_at: datetime | None
    last_run_completed_at: datetime | None
    pending_cases: tuple[tuple[str, str | None], ...]
    """`(case_id, ticker)` pairs currently detected as needing
    recomputation -- Deliverable 9/10's own "Portfolio/Watchlist
    monitoring pending" read directly from this."""
    failed_cases: tuple[MonitoringFailure, ...]
    portfolio_freshness: ScopeFreshnessSummary
    """Sprint 9, Deliverable 8 -- Portfolio holdings only."""
    watchlist_freshness: ScopeFreshnessSummary
    """Sprint 9, Deliverable 9 -- Watchlist entries only."""
