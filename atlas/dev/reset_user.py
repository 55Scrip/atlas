"""Reset the fixed Atlas Alpha development user to a genuine first-time
state -- fresh user, warm Atlas.

    python -m atlas.dev.reset_user
    python -m atlas.dev.reset_user --dry-run

This clears every table this investor's own portfolio, watchlist, and
decision journal ever wrote to, and nothing else. It never touches
`business_records` (ingested filings/financials), the `canonical_security*`
tables, the Alpha Vantage quota counter, or the `investor_identity` row
itself -- see the module docstring on each `atlas/alpha/*/table.py` this
reads from for why each one is (or isn't) in scope, and
`docs/atlas_ux/` (or the sprint's own published ownership-map report)
for the full boundary writeup.

Why a wholesale `DELETE FROM <table>` is correct here, not just
convenient: this system is single-tenant per database file (exactly one
`InvestorIdentity` singleton per store, `atlas/core/domain
/investor_identity/entity.py`). Nothing in this schema supports a
second real user sharing the same `atlas.db` -- the handful of tables
that carry a `user_id` column at all (`decisions`,
`daily_brief_change_log`, `daily_brief_case_baseline`,
`daily_brief_view_state`) only ever hold the one resolved
`InvestorIdentity.user_id`. This tool still resolves and filters by
that id everywhere it's a real column, both to fail loudly if that
assumption is ever violated (an unexpected second `user_id` in one of
those tables raises rather than silently deleting it) and to keep the
scoping explicit rather than implicit. Every other table here has no
`user_id` column at all (most are keyed by `case_id`, several -- Evidence,
Interpretation, Hypothesis, the four `reasoning_link` join tables --
don't even carry `case_id`); for those, a full clear is the only
correct operation, not a shortcut.

Cases themselves (`cases` table) are cleared too, last, after Portfolio
and Watchlist -- a Case carries no ticker, no content of its own
(`atlas/core/domain/case/entity.py`); it only becomes "about AAPL"
because a Portfolio holding or Watchlist entry happens to point at its
case_id. Case creation is idempotent per ticker
(`atlas/alpha/case_generation/service.py`), so once Portfolio and
Watchlist are empty, every existing case_id is unreachable dead weight
-- clearing them is not lossy, it just avoids leaving stale rows behind
for the next `ensure_case_id` call to have to reason about.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field

from sqlalchemy import Table, delete, func, select
from sqlalchemy.engine import Connection, Engine

from atlas.core.application.investor_identity.composition import resolve_investor_identity
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.dev.guard import ensure_development_environment

# ---------------------------------------------------------------------------
# Portfolio / Watchlist / Trade Log (atlas/alpha)
# ---------------------------------------------------------------------------
from atlas.alpha.portfolio.table import alpha_portfolio_state_table, create_alpha_portfolio_state_table
from atlas.alpha.portfolio.trade_log_table import alpha_trade_log_table, create_alpha_trade_log_table
from atlas.alpha.watchlist.table import alpha_watchlist_entry_table, create_alpha_watchlist_entry_table

# ---------------------------------------------------------------------------
# Daily Brief (atlas/alpha)
# ---------------------------------------------------------------------------
from atlas.alpha.daily_brief_change_log.table import (
    create_daily_brief_change_log_table,
    daily_brief_change_log_table,
)
from atlas.alpha.daily_brief_change_log.case_baseline import (
    create_daily_brief_case_baseline_table,
    daily_brief_case_baseline_table,
)
from atlas.alpha.daily_brief_view_state.table import (
    create_daily_brief_view_state_table,
    daily_brief_view_state_table,
)

# ---------------------------------------------------------------------------
# Decision-Layer per-case caches / snapshots (atlas/alpha) -- every one of
# these is keyed by case_id only; a case_id exists only because this
# investor's own Portfolio/Watchlist named a ticker, so every row here
# belongs to the dev user being reset.
# ---------------------------------------------------------------------------
from atlas.alpha.monitoring.table import create_monitoring_result_table, monitoring_result_table
from atlas.alpha.decision_memory.table import (
    create_decision_memory_snapshot_table,
    decision_memory_snapshot_table,
)
from atlas.alpha.decision_explanation.table import (
    create_decision_explanation_result_table,
    decision_explanation_result_table,
)
from atlas.alpha.recommendation_conviction.table import (
    create_recommendation_conviction_result_table,
    recommendation_conviction_result_table,
)
from atlas.alpha.opportunity_cost.table import create_opportunity_cost_result_table, opportunity_cost_result_table
from atlas.alpha.decision_path.table import create_decision_path_result_table, decision_path_result_table
from atlas.alpha.ingestion.table import create_ingestion_result_table, ingestion_result_table
from atlas.alpha.decision_readiness.table import (
    create_decision_readiness_result_table,
    decision_readiness_result_table,
)
from atlas.alpha.decision_reliability.table import (
    create_decision_reliability_result_table,
    decision_reliability_result_table,
)
from atlas.alpha.investment_decision.table import (
    create_investment_decision_result_table,
    investment_decision_result_table,
)
from atlas.alpha.investment_case_lifecycle.table import (
    create_investment_case_lifecycle_history_table,
    investment_case_lifecycle_history_table,
)
from atlas.alpha.investment_case_change.table import (
    create_investment_case_snapshot_table,
    investment_case_snapshot_table,
)
from atlas.alpha.portfolio_decision.table import (
    create_portfolio_decision_result_table,
    portfolio_decision_result_table,
)
from atlas.alpha.evidence_timeline.table import create_evidence_snapshot_table, evidence_snapshot_table
from atlas.alpha.security_confirmation.table import (
    create_security_confirmation_table,
    security_confirmations_table,
)
from atlas.alpha.security_identity_evidence.table import (
    create_security_identity_evidence_table,
    security_identity_evidence_table,
)

# ---------------------------------------------------------------------------
# Core Decision Layer journal (atlas/core) -- this investor's own
# recorded reasoning. Cleared before `cases` itself.
# ---------------------------------------------------------------------------
from atlas.core.infrastructure.persistence.decision.table import create_decision_table, decisions_table
from atlas.core.infrastructure.persistence.outcome.table import create_outcome_table, outcomes_table
from atlas.core.infrastructure.persistence.observation.table import create_observation_table, observations_table
from atlas.core.infrastructure.persistence.judgment.table import create_judgment_table, judgments_table
from atlas.core.infrastructure.persistence.evidence.table import create_evidence_table, evidence_table
from atlas.core.infrastructure.persistence.hypothesis.table import create_hypothesis_table, hypotheses_table
from atlas.core.infrastructure.persistence.interpretation.table import (
    create_interpretation_table,
    interpretations_table,
)
from atlas.core.infrastructure.persistence.reasoning_trace.table import (
    create_reasoning_trace_tables,
    reasoning_trace_supports_table,
    reasoning_traces_table,
)
from atlas.core.infrastructure.persistence.reasoning_link.table import (
    conclusion_decision_links_table,
    create_reasoning_link_tables,
    hypothesis_evidence_links_table,
    interpretation_hypothesis_links_table,
    question_observation_links_table,
)
from atlas.core.infrastructure.persistence.case_condition.table import (
    case_condition_events_table,
    create_case_condition_events_table,
)
from atlas.core.infrastructure.persistence.assumption.table import (
    assumption_events_table,
    create_assumption_events_table,
)
from atlas.core.infrastructure.persistence.decision_draft.table import (
    create_decision_draft_events_table,
    decision_draft_events_table,
)
from atlas.core.infrastructure.persistence.knowledge_reference.table import (
    create_knowledge_reference_table,
    knowledge_references_table,
)
from atlas.core.infrastructure.persistence.case.table import cases_table, create_case_table

# ---------------------------------------------------------------------------
# Preserved, for the report only -- never written to.
# ---------------------------------------------------------------------------
from atlas.alpha.business_data_refresh.table import business_record_table, create_business_record_table
from atlas.alpha.business_data_refresh.quota_table import (
    alpha_vantage_daily_call_count_table,
    create_alpha_vantage_daily_call_count_table,
)
# Deliberately NOT importing atlas.alpha.canonical_security.table directly:
# tests/test_architecture_boundaries.py enforces that canonical_security is
# only imported by its own package/tests, the Resolution Service, and the
# Identity Gate -- a dev-reporting tool doesn't qualify, so canonical
# security tables are preserved (never written to below) but not counted
# in the printed report.


@dataclass(frozen=True)
class ClearSpec:
    label: str
    table: Table
    create: object  # Callable[[Engine], None]
    user_id_column: str | None = None


# Order matters only for readability of the report -- every delete runs
# inside one transaction, and this schema's own "no FK" convention
# (confirmed on every table.py read for this sprint) means there is no
# real constraint-ordering requirement between them.
_PORTFOLIO_WATCHLIST: tuple[ClearSpec, ...] = (
    ClearSpec("Portfolio state", alpha_portfolio_state_table, create_alpha_portfolio_state_table),
    ClearSpec("Trade log entries", alpha_trade_log_table, create_alpha_trade_log_table),
    ClearSpec("Watchlist entries", alpha_watchlist_entry_table, create_alpha_watchlist_entry_table),
)

_DAILY_BRIEF: tuple[ClearSpec, ...] = (
    ClearSpec(
        "Daily Brief change-log entries",
        daily_brief_change_log_table,
        create_daily_brief_change_log_table,
        user_id_column="user_id",
    ),
    ClearSpec(
        "Daily Brief baseline markers",
        daily_brief_case_baseline_table,
        create_daily_brief_case_baseline_table,
        user_id_column="user_id",
    ),
    ClearSpec(
        "Daily Brief read-state rows",
        daily_brief_view_state_table,
        create_daily_brief_view_state_table,
        user_id_column="user_id",
    ),
)

_DECISION_LAYER_CACHES: tuple[ClearSpec, ...] = (
    ClearSpec("Monitoring results", monitoring_result_table, create_monitoring_result_table),
    ClearSpec("Decision memory snapshots", decision_memory_snapshot_table, create_decision_memory_snapshot_table),
    ClearSpec(
        "Decision explanation results",
        decision_explanation_result_table,
        create_decision_explanation_result_table,
    ),
    ClearSpec(
        "Recommendation conviction results",
        recommendation_conviction_result_table,
        create_recommendation_conviction_result_table,
    ),
    ClearSpec("Opportunity cost results", opportunity_cost_result_table, create_opportunity_cost_result_table),
    ClearSpec("Decision path results", decision_path_result_table, create_decision_path_result_table),
    ClearSpec("Ingestion results", ingestion_result_table, create_ingestion_result_table),
    ClearSpec(
        "Decision readiness results", decision_readiness_result_table, create_decision_readiness_result_table
    ),
    ClearSpec(
        "Decision reliability results", decision_reliability_result_table, create_decision_reliability_result_table
    ),
    ClearSpec(
        "Investment decision results", investment_decision_result_table, create_investment_decision_result_table
    ),
    ClearSpec(
        "Investment case lifecycle history",
        investment_case_lifecycle_history_table,
        create_investment_case_lifecycle_history_table,
    ),
    ClearSpec(
        "Investment case snapshots", investment_case_snapshot_table, create_investment_case_snapshot_table
    ),
    ClearSpec(
        "Portfolio decision results", portfolio_decision_result_table, create_portfolio_decision_result_table
    ),
    ClearSpec("Evidence timeline snapshots", evidence_snapshot_table, create_evidence_snapshot_table),
    ClearSpec("Security confirmations", security_confirmations_table, create_security_confirmation_table),
    ClearSpec(
        "Security identity evidence", security_identity_evidence_table, create_security_identity_evidence_table
    ),
)

_DECISION_JOURNAL: tuple[ClearSpec, ...] = (
    ClearSpec("Decisions", decisions_table, create_decision_table, user_id_column="user_id"),
    ClearSpec("Outcomes", outcomes_table, create_outcome_table),
    ClearSpec("Observations", observations_table, create_observation_table),
    ClearSpec("Judgments", judgments_table, create_judgment_table),
    ClearSpec("Evidence (journal)", evidence_table, create_evidence_table),
    ClearSpec("Interpretations", interpretations_table, create_interpretation_table),
    ClearSpec("Hypotheses", hypotheses_table, create_hypothesis_table),
    ClearSpec("Reasoning traces", reasoning_traces_table, create_reasoning_trace_tables),
    ClearSpec("Reasoning trace supports", reasoning_trace_supports_table, create_reasoning_trace_tables),
    ClearSpec("Reasoning links: question→observation", question_observation_links_table, create_reasoning_link_tables),
    ClearSpec(
        "Reasoning links: interpretation→hypothesis",
        interpretation_hypothesis_links_table,
        create_reasoning_link_tables,
    ),
    ClearSpec(
        "Reasoning links: hypothesis→evidence", hypothesis_evidence_links_table, create_reasoning_link_tables
    ),
    ClearSpec(
        "Reasoning links: conclusion→decision", conclusion_decision_links_table, create_reasoning_link_tables
    ),
    ClearSpec("Case condition events", case_condition_events_table, create_case_condition_events_table),
    ClearSpec("Assumption events", assumption_events_table, create_assumption_events_table),
    ClearSpec("Decision draft events", decision_draft_events_table, create_decision_draft_events_table),
    ClearSpec("Knowledge references", knowledge_references_table, create_knowledge_reference_table),
)

_CASES: tuple[ClearSpec, ...] = (ClearSpec("Cases", cases_table, create_case_table),)

# Cleared in this order: Portfolio/Watchlist -> Daily Brief -> Decision-
# Layer caches -> Decision journal -> Cases (last, since it's the root
# every case_id-keyed table above ultimately hangs off of).
_ALL_SPECS: tuple[ClearSpec, ...] = (
    _PORTFOLIO_WATCHLIST + _DAILY_BRIEF + _DECISION_LAYER_CACHES + _DECISION_JOURNAL + _CASES
)


@dataclass
class ResetReport:
    dry_run: bool
    investor_user_id: str = ""
    portfolio_holdings_removed: int = 0
    counts: dict[str, int] = field(default_factory=dict)
    preserved: dict[str, int] = field(default_factory=dict)

    @property
    def total_removed(self) -> int:
        return sum(self.counts.values())


def _portfolio_holdings_count(connection: Connection) -> int:
    row = connection.execute(
        select(alpha_portfolio_state_table.c.holdings_json).where(alpha_portfolio_state_table.c.id == 1)
    ).first()
    if row is None or row[0] is None:
        return 0
    try:
        return len(json.loads(row[0]))
    except (TypeError, ValueError):
        return 0


def _clear(connection: Connection, spec: ClearSpec, *, dry_run: bool) -> int:
    """Wholesale clear -- correct for every table here, not just
    convenient. This system is single-tenant per database file, so
    every row in every one of these tables belongs to the one dev user
    being reset, full stop.

    Earlier revisions of this tool tried to additionally filter/verify
    against the resolved `InvestorIdentity.user_id` on the handful of
    tables that carry a `user_id` column (`decisions`,
    `daily_brief_change_log`, `daily_brief_case_baseline`,
    `daily_brief_view_state`). Live-testing against the real dev
    database (dry-run) immediately surfaced why that was the wrong
    design: Daily Brief's own `user_id` is populated from a *frontend*
    constant (`ALPHA_PLACEHOLDER_USER_ID`,
    `frontend/src/decisionWorkspace/alphaUser.ts`) that has never been
    wired to the backend's `resolve_investor_identity()` mechanism at
    all -- so real, currently-live Daily Brief rows do not carry the
    resolved investor identity's UserId, and a strict filter/refusal
    against that value would make this tool unable to reset the one
    thing it exists to reset. See this module's own docstring and the
    sprint's risk assessment for the full writeup; fixing that
    frontend/backend identity gap is explicitly out of this dev-tooling
    sprint's scope ("do not modify investment logic purely for reset
    support").
    """
    count = connection.execute(select(func.count()).select_from(spec.table)).scalar_one()
    if not dry_run and count > 0:
        connection.execute(delete(spec.table))
    return count


def _preserved_counts(connection: Connection) -> dict[str, int]:
    return {
        "Business records (ingested filings/financials)": connection.execute(
            select(func.count()).select_from(business_record_table)
        ).scalar_one(),
        "Alpha Vantage daily call-count rows": connection.execute(
            select(func.count()).select_from(alpha_vantage_daily_call_count_table)
        ).scalar_one(),
    }


def reset_development_user(engine: Engine, *, dry_run: bool = False) -> ResetReport:
    """Reset the fixed dev user to a genuine first-time state.

    Idempotent: running this against an already-reset database is safe
    and reports zero rows removed everywhere (every step is a no-op
    DELETE/no-op check on an empty table). Transactional: every delete
    runs inside one `engine.begin()` block, so a failure partway
    through rolls back everything, never leaving a half-reset database
    behind.
    """
    ensure_development_environment()

    for spec in _ALL_SPECS:
        spec.create(engine)  # type: ignore[operator]
    # Preserved tables' own create_* functions, so counting them works
    # even against a database that has never touched these paths yet.
    # (canonical_security's own tables are preserved too -- never
    # written to below -- but are not created/counted here; see the
    # import-time note above on why this module doesn't import that
    # package directly.)
    create_business_record_table(engine)
    create_alpha_vantage_daily_call_count_table(engine)

    # Resolved and preserved (never regenerated) purely for the report
    # -- see `_clear`'s own docstring for why it is deliberately NOT
    # used to filter/scope any delete below.
    investor_user_id = str(resolve_investor_identity(engine))

    report = ResetReport(dry_run=dry_run, investor_user_id=investor_user_id)
    with engine.begin() as connection:
        report.portfolio_holdings_removed = _portfolio_holdings_count(connection)
        for spec in _ALL_SPECS:
            report.counts[spec.label] = _clear(connection, spec, dry_run=dry_run)
        report.preserved = _preserved_counts(connection)
        if dry_run:
            # Nothing was deleted above (guarded by `dry_run` inside
            # `_clear`); rolling back is a no-op safety net, not a
            # correction. `engine.begin()` commits on clean exit, so
            # this makes the "no writes happened" guarantee explicit
            # rather than relying on `_clear`'s own `dry_run` check alone.
            connection.rollback()

    return report


def _format_report(report: ResetReport) -> str:
    lines: list[str] = []
    lines.append(("[DRY RUN] " if report.dry_run else "") + "Reset development user")
    lines.append(f"Investor identity preserved: {report.investor_user_id}")
    lines.append("")
    lines.append(f"Portfolio holdings removed: {report.portfolio_holdings_removed}")
    lines.append(f"Watchlist entries removed: {report.counts['Watchlist entries']}")
    lines.append(f"Trade log entries removed: {report.counts['Trade log entries']}")
    lines.append(
        "Daily Brief changes removed: "
        f"{report.counts['Daily Brief change-log entries']} "
        f"(baseline markers: {report.counts['Daily Brief baseline markers']}, "
        f"read-state: {report.counts['Daily Brief read-state rows']})"
    )
    decision_journal_total = sum(report.counts[spec.label] for spec in _DECISION_JOURNAL)
    lines.append(f"Decision-journal rows removed: {decision_journal_total} (Decisions: {report.counts['Decisions']}, Outcomes: {report.counts['Outcomes']}, Observations: {report.counts['Observations']}, Judgments: {report.counts['Judgments']}, and 12 more journal tables)")
    cache_total = sum(report.counts[spec.label] for spec in _DECISION_LAYER_CACHES)
    lines.append(f"Decision-layer cached results removed: {cache_total} (across {len(_DECISION_LAYER_CACHES)} case-scoped tables)")
    lines.append(f"Cases removed: {report.counts['Cases']}")
    lines.append("")
    for label, count in report.preserved.items():
        lines.append(f"{label} preserved: {count}")
    lines.append("")
    lines.append("Reset complete." if not report.dry_run else "Dry run complete -- nothing was changed.")
    return "\n".join(lines)


def main(argv: list[str] | None = None, *, engine: Engine | None = None) -> int:
    """`engine` defaults to the real shared `atlas.db` engine; tests
    pass an isolated in-memory engine instead, exercising this exact
    function end to end without touching real persisted state (the
    same convention `atlas/alpha/portfolio/cli.py::main` already uses).
    """
    parser = argparse.ArgumentParser(prog="python -m atlas.dev.reset_user")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be removed without deleting anything.",
    )
    args = parser.parse_args(argv)

    resolved_engine = engine if engine is not None else get_decision_engine()
    try:
        report = reset_development_user(resolved_engine, dry_run=args.dry_run)
    except Exception as exc:  # noqa: BLE001 -- top-level CLI boundary, must fail safely and print, not crash silently
        print(f"Reset failed, no changes were made: {exc}", file=sys.stderr)
        return 1

    print(_format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
