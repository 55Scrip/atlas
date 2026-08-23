"""Orchestration for Monitoring & Change Detection (Deliverable 4, 20,
21). The only part of this package that performs I/O.

**"Recompute vs. Ingestion" (Deliverable 19), and why `run()` exists at
all.** Auditing this codebase fresh from disk found that new
`BusinessRecord`/`BusinessFact` ingestion never itself triggers
recomputation -- Coverage, Confidence, Stance, and Evidence Timeline's
own snapshot capture all happen lazily, only as a side effect of
`InvestmentCaseCompositionService.build(case_id)` being called from an
HTTP read path (`GET /cases/{id}/analysis` and eight other independent
callers). Critically, `capture_evidence_snapshot` itself has exactly
one call site in the entire codebase today: inside that one analysis
endpoint. A Watchlist company nobody has individually opened therefore
has no Evidence Timeline history at all, no matter how much new data
has been ingested for it. `MonitoringService.run()` is Atlas's answer:
one explicit operation that performs, for every company in scope, the
identical recompute-and-capture sequence that endpoint already performs
for one Case at a time -- so continuous monitoring does not depend on
an investor happening to open every page. This mirrors, rather than
replaces, that endpoint's own logic (same pure functions, same
repositories) -- see this module's own `_evaluate_case` for the exact
parallel. No scheduler is introduced; `run()` must still be invoked
(Deliverable 20's own "not a scheduler, an explicit deterministic run").

**Known, disclosed cost, identical in kind to `daily_brief_agenda
.service`'s own documented tradeoff:** `run()` calls
`InvestmentCaseCompositionService.build(case_id)` once per monitored
Case, independently of every other reader of that same service. This is
an accepted, existing pattern in this codebase (see that module's own
docstring), not a new one introduced here.

**No new comparison state.** Every change Monitoring detects is read
from Evidence Timeline's and Change Intelligence's own snapshot
repositories, both idempotent-by-content-hash already. Monitoring's own
`SqlAlchemyMonitoringResultRepository` is a read-model cache only (see
`table.py`'s own docstring) -- it is never consulted to decide whether
something changed.

**Atlas Intelligence Sprint 8 (Automated Monitoring Operations) --
incremental recomputation, Deliverable 3/4.** `run()` no longer
evaluates every known company unconditionally. Before the expensive
per-Case sequence above, it runs one cheap pre-pass: for each known
Case, compare its last successful checkpoint
(`MonitoringResultRepository.get(case_id).generated_at`, or `None` if
never monitored) against the newest `recorded_at`/`updated_at` among
that Case's own `Decision`/`Observation`/`CaseCondition` rows -- three
plain, indexed reads (`list_all()` fetched once per run, not once per
Case), never a second `InvestmentCaseCompositionService.build()`. Only
a Case that is genuinely dirty (or has never been monitored) proceeds
to the expensive sequence; everything else is skipped and its prior
cached result carried forward unchanged (Deliverable 5's own
idempotence: no new snapshot, no new change, nothing rewritten for an
unchanged Case).

**Deliberately not detected: new `BusinessRecord`/`BusinessFact`
ingestion.** `BusinessRecord` carries no "ingested at" wall-clock field
(`published_at` is the *document's own* date, which can legitimately be
old data backfilled today) and `business_data_refresh` persists no
refresh timestamp of its own -- there is no cheap signal to read here
without doing the very rebuild this pre-pass exists to avoid. This is a
disclosed, real limitation (see this package's own `__init__.py`), not
silently ignored: `run(force=True)` is the documented escape hatch --
it evaluates every known company regardless of the cheap check,
exactly like calling this endpoint always did before this sprint.

**No new job framework, no queue.** The pre-pass is plain, synchronous
Python executed inline inside `run()` -- the same "orchestrate
existing outputs" discipline Sprint 7 already established, extended to
decide *whether* to orchestrate them, not just *how*.

**Atlas Intelligence Sprint 9 (Data Ingestion & Automatic Refresh) --
Deliverable 5.** The one gap Sprint 8's own docstring above disclosed
("deliberately not detected: new BusinessRecord ingestion") is now
closed: `_latest_signal_at` additionally reads `atlas.alpha.ingestion
.IngestionService`'s own read-model cache (`IngestionResult.ran_at`,
only when `has_new_data` is `True`) as one more real, already-computed
signal -- Monitoring never re-derives "did new data arrive" itself; it
only reads what `atlas.alpha.ingestion.engine.classify_refresh` already
decided, exactly the "Monitoring shall never itself guess" boundary
that sprint's own brief states. This is additive, not a replacement --
the Decision/Observation/CaseCondition checks above remain exactly as
they were, since those were never "guessing" either (each is a real,
dated fact from its own source); Ingestion fills the one dimension
none of them ever covered.

**Internal Alpha Fix Sprint 1 -- Automatic Monitoring & Continuous
Refresh, Deliverable 3.** Before this sprint, `run()` -- however cheap
its own dirty pre-pass made it -- was invoked by nothing (Deliverable
1's own audit finding: no scheduler, no frontend caller, manual `POST
/monitoring/run` only). This sprint does not add a scheduler, a polling
loop, or a background worker -- all three are explicitly forbidden by
its own brief. It adds exactly one thing: real product events that
already create genuinely new dirty state (Watchlist add, a new-position
trade, bulk Portfolio enrichment -- see each call site's own comment)
now call this exact, unmodified `run()` themselves, synchronously,
inline, as part of already-happening request handling. Nothing here
invents a second "when to run" concept -- `needs_recompute`'s own
pre-pass is still the only thing that decides whether any given Case
is actually re-evaluated; calling `run()` more often than before simply
means that decision gets re-checked sooner, not that it is made
differently.

**No overlapping runs (Deliverable 3/9).** `run()` now serializes
through one process-wide `threading.Lock` -- two real `run()` calls
(manual and/or automatic, from any thread) can no longer execute their
per-Case evaluation concurrently, which matters now that more than one
call site can trigger a run. The manual `POST /monitoring/run` path
still always executes, waiting for its turn if another run is already
in progress, since an operator explicitly asking for a run expects it
to actually happen. The new automatic call sites instead use
`trigger_automatic_run` (below), a best-effort, non-blocking sibling
that skips entirely -- never queues, never waits -- if a run is already
in progress. Skipping loses nothing: the event that triggered it left
real, dated rows behind (a `Decision`, an `IngestionResult`, a brand
new never-monitored Case), so the in-flight run's own pre-pass, or the
very next trigger, still finds that Case genuinely dirty and evaluates
it then. This is the same "no event, no timestamp, nothing silently
dropped" discipline this package already applies everywhere else,
applied to the act of triggering a run rather than to one Case's own
result.
"""
from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone

from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.case_membership import known_cases
from atlas.alpha.coverage import assess_coverage
from atlas.alpha.evidence_quality import assess_evidence_quality
from atlas.alpha.evidence_timeline import capture_evidence_snapshot, compare_evidence_snapshots
from atlas.alpha.evidence_timeline.repository import SqlAlchemyEvidenceSnapshotRepository
from atlas.alpha.ingestion.engine import DataFreshnessStatus, derive_data_freshness_status
from atlas.alpha.ingestion.models import IngestionResult
from atlas.alpha.ingestion.repository import SqlAlchemyIngestionResultRepository
from atlas.alpha.investment_case.service import InvestmentCaseCompositionService
from atlas.alpha.monitoring.engine import CaseConditionSignal, build_monitoring_result, derive_operational_status, needs_recompute
from atlas.alpha.monitoring.models import (
    CaseOperationalFreshness,
    MonitoringFailure,
    MonitoringOperationalStatus,
    MonitoringResult,
    MonitoringRun,
    MonitoringScope,
    MonitoringStatus,
    ScopeFreshnessSummary,
)
from atlas.alpha.monitoring.repository import SqlAlchemyMonitoringResultRepository, SqlAlchemyMonitoringRunRecordRepository
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.stance.service import StanceService
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.analysis_engine.business_data.versioning import latest_versions
from atlas.core.application.case_condition.case_condition_service import CaseConditionService
from atlas.core.application.reasoning_workspace.read_models import list_active_case_conditions
from atlas.core.domain.case.value_objects import CaseId
from atlas.core.domain.decision.repository import DecisionRepository
from atlas.core.domain.observation.repository import ObservationRepository

__all__ = ["MonitoringService"]

_RUN_LOCK = threading.Lock()
"""Process-wide, deliberately module-level rather than per-instance:
`MonitoringService` is reconstructed fresh per request (see `api
.dependencies.get_monitoring_service`/`build_monitoring_service`), so an
instance-level lock would not actually serialize two different request
threads' calls against each other. One lock, one process, matches "no
overlapping runs" literally."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _freshness_bucket(status: DataFreshnessStatus) -> str:
    """Sprint 9, Deliverable 8/9 -- the single place the three-bucket
    aggregate is defined (see `ScopeFreshnessSummary`'s own docstring
    for why these three and not a raw five-way breakdown)."""
    if status is DataFreshnessStatus.WAITING_FOR_ANALYSIS:
        return "waiting_for_analysis"
    if status is DataFreshnessStatus.WAITING_FOR_NEW_DATA:
        return "no_new_data"
    return "needs_attention"


def _latest_by_case(items, case_id_of, timestamp_of) -> dict[str, datetime]:
    """One pass, `O(len(items))` -- shared by `run()`/`operational_status()`/
    `freshness_for_case()` so the "which timestamp counts as dirty"
    rule lives in exactly one place (`needs_recompute`'s own caller
    contract), not reimplemented per method."""
    latest: dict[str, datetime] = {}
    for item in items:
        case_id = str(case_id_of(item).value)
        timestamp = timestamp_of(item)
        if case_id not in latest or timestamp > latest[case_id]:
            latest[case_id] = timestamp
    return latest


class MonitoringService:
    def __init__(
        self,
        portfolio_store: AlphaPortfolioStore,
        watchlist_store: AlphaWatchlistStore,
        composition_service: InvestmentCaseCompositionService,
        stance_service: StanceService,
        business_record_repository: SqlAlchemyBusinessRecordRepository,
        evidence_snapshot_repository: SqlAlchemyEvidenceSnapshotRepository,
        case_condition_service: CaseConditionService,
        monitoring_result_repository: SqlAlchemyMonitoringResultRepository,
        decision_repository: DecisionRepository,
        observation_repository: ObservationRepository,
        monitoring_run_record_repository: SqlAlchemyMonitoringRunRecordRepository,
        ingestion_result_repository: SqlAlchemyIngestionResultRepository,
    ) -> None:
        self._portfolio_store = portfolio_store
        self._watchlist_store = watchlist_store
        self._composition_service = composition_service
        self._stance_service = stance_service
        self._business_record_repository = business_record_repository
        self._evidence_snapshot_repository = evidence_snapshot_repository
        self._case_condition_service = case_condition_service
        self._monitoring_result_repository = monitoring_result_repository
        self._decision_repository = decision_repository
        self._observation_repository = observation_repository
        self._monitoring_run_record_repository = monitoring_run_record_repository
        self._ingestion_result_repository = ingestion_result_repository

    def _signal_maps(self) -> tuple[dict[str, datetime], dict[str, datetime]]:
        """Deliverable 4 -- one `list_all()` read each for Decision and
        Observation, grouped by Case, reused across every Case in the
        current call rather than re-queried per Case."""
        decision_latest = _latest_by_case(self._decision_repository.list_all(), lambda d: d.case_id, lambda d: d.recorded_at)
        observation_latest = _latest_by_case(
            self._observation_repository.list_all(), lambda o: o.case_id, lambda o: o.recorded_at
        )
        return decision_latest, observation_latest

    def _latest_case_condition_update(self, case_id: str) -> datetime | None:
        views = self._case_condition_service.list_for_case(CaseId(value=uuid.UUID(case_id)), include_terminal=True)
        return max((v.updated_at for v in views), default=None)

    def _latest_ingestion_signal(self, case_id: str, ingestion_result: IngestionResult | None = None) -> datetime | None:
        """Sprint 9, Deliverable 5 -- reads, never re-derives. `None`
        unless Ingestion's own last recorded result for this Case
        found genuinely new/replaced data (`has_new_data`); an
        Ingestion run that found nothing new contributes no signal
        here, the same "no event, no timestamp" discipline every other
        signal in this method already follows. `ingestion_result` may
        be passed in already-fetched (Deliverable 12's own scale audit
        -- `operational_status()` needs the same row for its freshness
        bucket and must not fetch it twice per Case)."""
        result = ingestion_result if ingestion_result is not None else self._ingestion_result_repository.get(case_id)
        if result is None or not result.has_new_data:
            return None
        return result.ran_at

    def _latest_signal_at(
        self,
        case_id: str,
        decision_latest: dict[str, datetime],
        observation_latest: dict[str, datetime],
        ingestion_result: IngestionResult | None = None,
    ) -> datetime | None:
        """The newest of Decision/Observation/CaseCondition/Ingestion
        activity for this Case -- Deliverable 4's own "when must a
        company be recomputed" answer, restricted to what is cheaply,
        honestly detectable (see this module's own docstring for what
        is deliberately excluded)."""
        candidates = [
            t
            for t in (
                decision_latest.get(case_id),
                observation_latest.get(case_id),
                self._latest_case_condition_update(case_id),
                self._latest_ingestion_signal(case_id, ingestion_result),
            )
            if t is not None
        ]
        return max(candidates) if candidates else None

    def _evaluate_case(self, case_id: str, ticker: str | None, *, is_holding: bool, now: datetime) -> MonitoringResult | None:
        composition = self._composition_service.build(case_id)
        if composition is None:
            # Deliverable 18's own `UNAVAILABLE` status -- a real
            # Portfolio/Watchlist entry whose Case could not be
            # resolved at all (should not happen in practice, but never
            # silently dropped from the read model either).
            result = MonitoringResult(
                case_id=case_id,
                ticker=ticker,
                scope=MonitoringScope.PORTFOLIO if is_holding else MonitoringScope.WATCHLIST,
                status=MonitoringStatus.UNAVAILABLE,
                changes=(),
                stance_level=None,
                confidence_level=None,
                coverage_level=None,
                latest_meaningful_evidence_at=None,
                recommended_action=None,
                generated_at=now,
            )
            self._monitoring_result_repository.upsert(result)
            return result

        stance = self._stance_service.assess_for_case(case_id)
        coverage = assess_coverage(composition.canonical_analysis, is_thesis_stale=composition.is_thesis_stale)

        records = latest_versions(self._business_record_repository.get_by_company(ticker)) if ticker is not None else ()
        evidence_quality = assess_evidence_quality(
            records,
            composition.business_facts,
            composition.market_facts,
            composition.canonical_analysis,
            evaluated_at=composition.generated_at,
        )

        evidence_snapshot = capture_evidence_snapshot(
            coverage,
            evidence_quality,
            stance,
            composition.business_facts,
            composition.market_facts,
            captured_at=composition.generated_at,
        )
        previous_evidence_snapshot = self._evidence_snapshot_repository.get_latest(case_id)
        evidence_history = compare_evidence_snapshots(previous_evidence_snapshot, evidence_snapshot)
        self._evidence_snapshot_repository.add(case_id, evidence_snapshot, evidence_history)

        case_condition_rows = tuple(
            CaseConditionSignal(
                condition_id=str(row.condition_id.value),
                role=row.role,
                status=row.status,
                predicate_text=row.predicate_text,
            )
            for row in list_active_case_conditions(self._case_condition_service, CaseId(value=uuid.UUID(case_id)))
        )

        result = build_monitoring_result(
            case_id=case_id,
            ticker=ticker,
            scope=MonitoringScope.PORTFOLIO if is_holding else MonitoringScope.WATCHLIST,
            is_holding=is_holding,
            evidence_history=evidence_history,
            change_intelligence=composition.change_intelligence,
            case_condition_rows=case_condition_rows,
            stance_level=stance.level.value if stance is not None else None,
            confidence_level=coverage.overall_confidence,
            coverage_level=coverage.overall_coverage.value,
            latest_evidence_captured_at=evidence_snapshot.captured_at,
            generated_at=now,
        )
        self._monitoring_result_repository.upsert(result)
        return result

    def run(self, *, force: bool = False) -> MonitoringRun:
        """Deliverable 20/12 -- the one, canonical, explicit monitoring
        operation; Sprint 8 adds incrementality (Deliverable 4) and
        operational tracking (Deliverable 3/6/7) around it without
        duplicating its own evaluation logic. Loads Portfolio +
        Watchlist scope, evaluates only the Cases a cheap pre-pass
        finds genuinely dirty (every Case, if `force=True`), and always
        returns one `MonitoringResult` per known Case -- a skipped or
        failed Case falls back to its last cached result rather than
        vanishing from the output (Deliverable 6: a failure degrades
        gracefully, it never blanks out what Atlas already knew).

        Internal Alpha Fix Sprint 1, Deliverable 3/9: blocks on
        `_RUN_LOCK` -- this is the one call path (manual `POST
        /monitoring/run`, and any caller that explicitly wants a run to
        happen) guaranteed to actually execute, waiting its turn if
        another run is already in progress rather than skipping. See
        `trigger_automatic_run` for the non-blocking sibling automatic
        call sites use instead."""
        with _RUN_LOCK:
            return self._run_locked(force=force)

    def trigger_automatic_run(self) -> MonitoringRun | None:
        """Internal Alpha Fix Sprint 1, Deliverable 3 -- the one new
        entrypoint this sprint adds. Best-effort and non-blocking:
        returns `None` immediately, without running anything, if a run
        (manual or automatic) is already in progress anywhere in this
        process, rather than queuing behind it or blocking the caller's
        own request. Real product events call this after they create
        genuinely new dirty state (see `watchlist`/`portfolio`'s own API
        routers) -- skipping here never loses that state: the Case is
        still genuinely dirty per `needs_recompute`, so either the
        in-flight run's own pre-pass already covers it, or the very next
        call to this method (or to `run()`) picks it up. This is what
        keeps automatic triggering from ever turning into a monitoring
        storm or a blocked user-facing request: at most one real
        evaluation sweep runs at a time, and a burst of triggering
        events collapses into that one sweep rather than queuing more
        work than the event stream actually produced."""
        if not _RUN_LOCK.acquire(blocking=False):
            return None
        try:
            return self._run_locked(force=False)
        finally:
            _RUN_LOCK.release()

    def _run_locked(self, *, force: bool) -> MonitoringRun:
        """The actual evaluation sweep, always called with `_RUN_LOCK`
        already held by the caller (`run()`/`trigger_automatic_run()`)
        -- unchanged from this method's own pre-Sprint-1 body other than
        the rename, so every existing guarantee (per-Case failure
        isolation, incremental pre-pass, graceful degradation) is
        exactly as it was."""
        now = _utc_now()
        run_record = self._monitoring_run_record_repository.start(forced=force)
        portfolio_state = self._portfolio_store.get()
        held_tickers = {h.ticker for h in portfolio_state.holdings} if portfolio_state is not None else set()
        decision_latest, observation_latest = self._signal_maps()

        results: list[MonitoringResult] = []
        failures: list[MonitoringFailure] = []
        evaluated_count = 0
        skipped_count = 0

        for case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            is_holding = ticker in held_tickers if ticker else False
            cached = self._monitoring_result_repository.get(case_id)
            checkpoint_at = cached.generated_at if cached is not None else None
            signal_at = self._latest_signal_at(case_id, decision_latest, observation_latest)

            if not force and not needs_recompute(checkpoint_at, signal_at):
                skipped_count += 1
                if cached is not None:
                    results.append(cached)
                continue

            try:
                result = self._evaluate_case(case_id, ticker, is_holding=is_holding, now=now)
            except Exception as exc:  # noqa: BLE001 -- one Case's failure must never abort the run (Deliverable 6).
                failures.append(MonitoringFailure(case_id=case_id, ticker=ticker, error=f"{type(exc).__name__}: {exc}"))
                if cached is not None:
                    results.append(cached)
                continue

            evaluated_count += 1
            if result is not None:
                results.append(result)

        self._monitoring_run_record_repository.complete(
            run_record.run_id, evaluated_count=evaluated_count, skipped_count=skipped_count, failures=tuple(failures)
        )
        return MonitoringRun(generated_at=now, results=tuple(results))

    def operational_status(self) -> MonitoringOperationalStatus:
        """Deliverable 7/14 -- `GET /monitoring/status`'s own read
        model. `pending_cases` is computed fresh (the same cheap
        pre-pass `run()` itself uses), never stored -- there is no
        separate dirty-state table to fall out of sync with reality."""
        latest_run = self._monitoring_run_record_repository.get_latest()
        decision_latest, observation_latest = self._signal_maps()
        failed_case_ids = {f.case_id for f in latest_run.failures} if latest_run is not None else set()
        portfolio_state = self._portfolio_store.get()
        held_tickers = {h.ticker for h in portfolio_state.holdings} if portfolio_state is not None else set()

        pending: list[tuple[str, str | None]] = []
        portfolio_counts = {"waiting_for_analysis": 0, "no_new_data": 0, "needs_attention": 0}
        watchlist_counts = {"waiting_for_analysis": 0, "no_new_data": 0, "needs_attention": 0}
        for case_id, ticker in known_cases(self._portfolio_store, self._watchlist_store):
            cached = self._monitoring_result_repository.get(case_id)
            checkpoint_at = cached.generated_at if cached is not None else None
            ingestion_result = self._ingestion_result_repository.get(case_id)
            signal_at = self._latest_signal_at(case_id, decision_latest, observation_latest, ingestion_result)
            if needs_recompute(checkpoint_at, signal_at):
                pending.append((case_id, ticker))

            freshness_status = derive_data_freshness_status(
                ingestion_result, checkpoint_at, last_run_failed_for_case=case_id in failed_case_ids
            )
            bucket = _freshness_bucket(freshness_status)
            counts = portfolio_counts if (ticker in held_tickers if ticker else False) else watchlist_counts
            counts[bucket] += 1

        failed_cases = latest_run.failures if latest_run is not None else ()
        return MonitoringOperationalStatus(
            status=derive_operational_status(latest_run, len(pending)),
            last_run_started_at=latest_run.started_at if latest_run is not None else None,
            last_run_completed_at=latest_run.completed_at if latest_run is not None else None,
            pending_cases=tuple(pending),
            failed_cases=failed_cases,
            portfolio_freshness=ScopeFreshnessSummary(**portfolio_counts),
            watchlist_freshness=ScopeFreshnessSummary(**watchlist_counts),
        )

    def freshness_for_case(self, case_id: str) -> CaseOperationalFreshness:
        """Deliverable 15 (Sprint 8) / Deliverable 6-7 (Sprint 9) -- the
        Investment Case page's own operational (not investment)
        freshness fact, now including the Ingestion-grounded granular
        status."""
        cached = self._monitoring_result_repository.get(case_id)
        checkpoint_at = cached.generated_at if cached is not None else None
        decision_latest, observation_latest = self._signal_maps()
        signal_at = self._latest_signal_at(case_id, decision_latest, observation_latest)
        latest_run = self._monitoring_run_record_repository.get_latest()
        last_run_failed_for_case = latest_run is not None and any(f.case_id == case_id for f in latest_run.failures)
        ingestion_result = self._ingestion_result_repository.get(case_id)
        return CaseOperationalFreshness(
            is_pending=needs_recompute(checkpoint_at, signal_at),
            last_monitored_at=checkpoint_at,
            last_run_failed_for_case=last_run_failed_for_case,
            data_freshness_status=derive_data_freshness_status(
                ingestion_result, checkpoint_at, last_run_failed_for_case=last_run_failed_for_case
            ),
        )

    def read_model(self) -> MonitoringRun:
        """Deliverable 21 -- the last run's own output, read straight
        from the cache, never recomputed. `generated_at` is the newest
        `MonitoringResult.generated_at` found, or the current time if
        nothing has ever run (an honest "no run has happened yet" is
        distinguished by an empty `results` tuple, not a fabricated
        timestamp)."""
        results = self._monitoring_result_repository.list_all()
        generated_at = max((r.generated_at for r in results), default=_utc_now())
        return MonitoringRun(generated_at=generated_at, results=results)
