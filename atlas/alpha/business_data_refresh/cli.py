"""CLI entry point for the real business-data refresh (ATLAS-031, Phase
40). A thin wrapper only -- all logic lives in
`refresh_company_data` (`atlas/alpha/business_data_refresh/service.py`).

Explicit and single-ticker by design (Phase 46: "do not refresh all 25
live internal holdings automatically. Start with one or two explicitly
selected internal Cases."). Never wired into application startup, a
FastAPI route, or any other automatic trigger -- an operator runs it
deliberately, once per company, when needed::

    python -m atlas.alpha.business_data_refresh.cli AAPL

`ALPHA_VANTAGE_API_KEY` missing is not fatal to the whole run -- SEC
EDGAR fundamentals still refresh; the market-data leg reports its own
`provider_errors` entry explaining exactly what's missing, per
`AlphaVantageMarketDataProvider`'s own "fail clearly when missing"
contract.
"""
from __future__ import annotations

import sys

from sqlalchemy.engine import Engine

from atlas.alpha.business_data_refresh.models import RefreshSummary
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.service import refresh_company_data
from atlas.alpha.business_data_refresh.table import create_business_record_table
from atlas.analysis_engine.business_data.providers import BusinessDataProvider
from atlas.business_data_providers.alpha_vantage import AlphaVantageMarketDataProvider
from atlas.business_data_providers.sec_edgar import SecEdgarFundamentalsProvider
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine

__all__ = ["main"]


def _print_summary(summary: RefreshSummary) -> None:
    print(f"Business data refresh -- {summary.ticker}")
    print(f"  Providers attempted:  {', '.join(summary.providers_attempted)}")
    print(f"  Documents fetched:    {summary.fetched_documents}")
    print(f"  New records:          {summary.new_records}")
    print(f"  New versions:         {summary.new_versions}")
    print(f"  Duplicates skipped:   {summary.duplicates_skipped}")
    print(f"  Documents rejected:   {summary.rejected_documents}")
    print(f"  Provider errors:      {len(summary.provider_errors)}")
    for failure in summary.provider_errors:
        print(f"    - {failure.provider_id}: {failure.error}")


def main(
    ticker: str | None,
    engine: Engine | None = None,
    providers: tuple[BusinessDataProvider, ...] | None = None,
) -> int:
    """`ticker` is a required, explicit argument -- `sys.argv` is only
    ever read at the `if __name__ == "__main__"` entry point below,
    never inside this function. That keeps `main(ticker=None, ...)`
    unambiguous for tests (exercising the "no ticker given" branch)
    regardless of whatever `sys.argv` the test runner itself was
    invoked with.

    `engine` defaults to the real shared `atlas.db` engine (the normal
    CLI invocation); `providers` defaults to the real SEC EDGAR +
    Alpha Vantage providers -- tests pass an isolated in-memory engine
    and fake providers instead, exercising this exact function end to
    end without touching real persisted state or the network (Phase
    32).
    """
    if not ticker:
        print("Usage: python -m atlas.alpha.business_data_refresh.cli TICKER")
        return 2

    engine = engine if engine is not None else get_decision_engine()
    create_business_record_table(engine)
    repository = SqlAlchemyBusinessRecordRepository(engine)

    providers = providers if providers is not None else (SecEdgarFundamentalsProvider(), AlphaVantageMarketDataProvider())
    summary = refresh_company_data(ticker.upper(), providers, repository)
    _print_summary(summary)
    return 1 if summary.provider_errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
