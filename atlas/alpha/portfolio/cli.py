"""CLI entry point for the legacy Case backfill (ATLAS-029, Phase 5).

A thin wrapper only -- all migration logic lives in
`backfill_missing_portfolio_cases` (`atlas/alpha/portfolio/backfill.py`).
This module's own job is limited to wiring the real dependencies (the
same composition FastAPI's `Depends` providers already assemble, called
directly since there is no request here) and printing the deterministic
summary.

Deliberately not part of the legacy `atlas/cli/main.py` Typer app: that
app is a separate, pre-Alpha surface (weekly-review/company-analysis/etc.
engines) with its own large, already-fragile test suite. This is its own
small, explicit maintenance entry point, invoked as::

    python -m atlas.alpha.portfolio.cli

Never wired into application startup, a FastAPI route, or any other
automatic trigger -- an operator runs it deliberately, once, when needed.
"""
from __future__ import annotations

from sqlalchemy.engine import Engine

from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.portfolio.backfill import BackfillResult, backfill_missing_portfolio_cases
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.core.application.case.create_case import CaseService
from atlas.core.infrastructure.api.case.dependencies import get_case_repository
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine

__all__ = ["main"]


def _print_summary(result: BackfillResult) -> None:
    print("Legacy Case backfill -- execution summary")
    print(f"  Holdings scanned:    {result.holdings_scanned}")
    print(f"  Cases preserved:     {result.cases_preserved}")
    print(f"  Cases created:       {result.cases_created}")
    print(f"  Failures:            {len(result.failures)}")
    for failure in result.failures:
        print(f"    - {failure.ticker}: {failure.error}")


def main(engine: Engine | None = None) -> int:
    """`engine` defaults to the real shared `atlas.db` engine (the
    normal CLI invocation); tests pass an isolated in-memory engine
    instead, exercising this exact function end to end without touching
    real persisted state."""
    engine = engine if engine is not None else get_decision_engine()
    create_alpha_portfolio_state_table(engine)
    portfolio_store = AlphaPortfolioStore(engine)
    case_service = CaseService(get_case_repository(engine))
    case_generation_service = CaseGenerationService(case_service)

    result = backfill_missing_portfolio_cases(portfolio_store, case_generation_service)
    _print_summary(result)
    return 1 if result.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
