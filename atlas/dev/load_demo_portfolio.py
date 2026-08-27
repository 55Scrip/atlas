"""Restore a deterministic development portfolio and watchlist, for
testing after a `python -m atlas.dev.reset_user`.

    python -m atlas.dev.load_demo_portfolio

Deliberately separate from `reset_user`: reset never auto-loads demo
data (a "genuine first-time experience" means an empty portfolio,
per the sprint's own working principle), and this loader never resets
anything first -- it just calls the same real
`AlphaPortfolioService.import_portfolio`/`AlphaWatchlistService
.add_ticker` application code a real user-driven import/watchlist-add
goes through, so it exercises the exact same validation, Case-linking,
and cross-context reuse machinery as a live user action -- never a raw
SQL insert.

What's loaded, and why (see also the printed report at runtime):

- **Portfolio: `examples/weekly_review_realistic/portfolio.json`**, an
  existing, already-anonymized 10-holding demo dataset (this repo's
  richest one for variation) reused as-is rather than inventing a new
  one -- real spread across sector (Semiconductors, Healthcare,
  Technology, Consumer Discretionary, Industrial Technology,
  Financials, Consumer Staples, and one holding, NESTE, with no
  sector recorded at all) and country (Netherlands, Denmark, US,
  France, Sweden), plus a wide quality/risk-score range (quality 68-90,
  risk 28-58) -- enough to exercise strong cases (ASML/MSFT, high
  quality/low risk) and weaker ones (NESTE, lower quality/higher risk)
  once Atlas has real evidence for them. `CASHEUR` (the dataset's own
  cash line) becomes the imported portfolio's cash allocation, not a
  holding.
- **Watchlist: AMD, NVDA** -- the two tickers `examples
  /daily_brief_demo/` already established as this repo's own canonical
  "demo companies" (reused here rather than inventing new watchlist
  tickers), and deliberately distinct from every ticker in the
  Portfolio import above, so Portfolio and Watchlist exercise two
  genuinely separate ticker sets.

This loader never triggers a live provider/network call itself
(`_trigger_enrichment` is a guaranteed no-op here -- see
`_watchlist_service` below): whether a given demo ticker shows "strong
evidence" or "missing evidence" in the app afterward depends entirely
on whether this dev database already has cached `BusinessRecord`s for
it from earlier real usage, which is itself part of the intended
variation (some cases start warm, some start cold) rather than
something this loader should force one way or the other.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy.engine import Engine

from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.portfolio.service import AlphaPortfolioService, ImportHoldingInput, ImportPortfolioRequest
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.watchlist.service import AlphaWatchlistService
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table
from atlas.core.application.case.create_case import CaseService
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.persistence.case.sqlalchemy_repository import SqlAlchemyCaseRepository
from atlas.core.infrastructure.persistence.case.table import create_case_table
from atlas.dev.guard import ensure_development_environment

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEMO_PORTFOLIO_PATH = _REPO_ROOT / "examples" / "weekly_review_realistic" / "portfolio.json"
_CASH_TICKER = "CASHEUR"
_DEMO_WATCHLIST_TICKERS: tuple[str, ...] = ("AMD", "NVDA")


def _load_demo_holdings() -> tuple[ImportPortfolioRequest, list[dict[str, object]]]:
    data = json.loads(_DEMO_PORTFOLIO_PATH.read_text())
    raw_holdings = data["accounts"][0]["holdings"]

    cash_value = next(row["market_value"] for row in raw_holdings if row["ticker"] == _CASH_TICKER)
    equity_rows = [row for row in raw_holdings if row["ticker"] != _CASH_TICKER]
    # `ImportHoldingInput.weight_percent` is required (not nullable at
    # the `AlphaHolding` level -- `import_portfolio` has no "derive
    # weight from value" path of its own, that's a different reconcile-
    # only code path). Weights are computed here, once, from the same
    # `market_value` figures the described-holdings report below also
    # uses, against the total portfolio value (equities + cash) so they
    # sum to 100% including the cash line.
    total_value = cash_value + sum(row["market_value"] for row in equity_rows)

    holdings: list[ImportHoldingInput] = []
    described: list[dict[str, object]] = []
    for row in equity_rows:
        ticker = row["ticker"]
        value = row["market_value"]
        weight_percent = round(value / total_value * 100, 2)
        holdings.append(ImportHoldingInput(ticker=ticker, weight_percent=weight_percent, value_absolute=value))
        described.append(
            {
                "ticker": ticker,
                "name": row.get("name"),
                "sector": row.get("sector"),
                "value": value,
                "weight_percent": weight_percent,
                "quality_score": row.get("quality_score"),
                "risk_score": row.get("risk_score"),
            }
        )

    request = ImportPortfolioRequest(
        holdings=tuple(holdings),
        cash_weight_percent=round(cash_value / total_value * 100, 2),
        cash_value_absolute=cash_value,
        preferences_notes="Demo portfolio loaded via python -m atlas.dev.load_demo_portfolio",
    )
    return request, described


def _portfolio_service(engine: Engine) -> AlphaPortfolioService:
    create_alpha_portfolio_state_table(engine)
    create_alpha_watchlist_entry_table(engine)
    create_case_table(engine)
    case_generation_service = CaseGenerationService(CaseService(SqlAlchemyCaseRepository(engine)))
    return AlphaPortfolioService(
        AlphaPortfolioStore(engine),
        case_generation_service=case_generation_service,
        watchlist_store=AlphaWatchlistStore(engine),
    )


def _watchlist_service(engine: Engine) -> AlphaWatchlistService:
    """Deliberately wires only `store`/`case_generation_service`
    /`portfolio_store` -- every enrichment-related dependency
    (`business_record_repository`/`business_data_providers`
    /`identity_gate`) is left at its default `None`, which makes
    `AlphaWatchlistService._trigger_enrichment` a guaranteed no-op (see
    its own docstring: "genuinely does nothing, on purpose, if any
    dependency is absent"). This loader must stay cheap and
    deterministic -- no live provider/network calls, ever, regardless
    of whether this dev database already has cached data for a demo
    ticker or not.
    """
    create_case_table(engine)
    case_generation_service = CaseGenerationService(CaseService(SqlAlchemyCaseRepository(engine)))
    return AlphaWatchlistService(
        AlphaWatchlistStore(engine),
        case_generation_service,
        portfolio_store=AlphaPortfolioStore(engine),
    )


def load_demo_portfolio(engine: Engine) -> dict[str, object]:
    """Idempotent and deterministic: `import_portfolio` always replaces
    the whole portfolio with this exact same 10-holding set, and
    `add_ticker` is documented idempotent (returns the existing entry
    unchanged for an already-watchlisted ticker) -- running this twice
    in a row produces the identical end state both times.
    """
    ensure_development_environment()

    request, described = _load_demo_holdings()
    portfolio_state = _portfolio_service(engine).import_portfolio(request)

    watchlist_service = _watchlist_service(engine)
    watchlist_entries = [watchlist_service.add_ticker(ticker) for ticker in _DEMO_WATCHLIST_TICKERS]

    return {
        "holdings": described,
        "cash_value_absolute": portfolio_state.cash_value_absolute,
        "watchlist_tickers": [entry.ticker for entry in watchlist_entries],
    }


def _format_result(result: dict[str, object]) -> str:
    lines: list[str] = ["Demo portfolio loaded", ""]
    for holding in result["holdings"]:  # type: ignore[union-attr]
        lines.append(
            f"  {holding['ticker']:<8} {holding['name']:<24} "
            f"{str(holding['sector'] or 'no sector'):<24} "
            f"value={holding['value']:<10} weight={holding['weight_percent']}% "
            f"quality={holding['quality_score']} risk={holding['risk_score']}"
        )
    lines.append(f"  Cash: {result['cash_value_absolute']}")
    lines.append("")
    lines.append(f"Watchlist: {', '.join(result['watchlist_tickers'])}")  # type: ignore[arg-type]
    lines.append("")
    lines.append("Demo load complete.")
    return "\n".join(lines)


def main(argv: list[str] | None = None, *, engine: Engine | None = None) -> int:
    del argv  # no flags today; accepted for symmetry with reset_user.main and future use
    resolved_engine = engine if engine is not None else get_decision_engine()
    try:
        result = load_demo_portfolio(resolved_engine)
    except Exception as exc:  # noqa: BLE001 -- top-level CLI boundary, must fail safely and print, not crash silently
        print(f"Demo load failed, no changes were made: {exc}", file=sys.stderr)
        return 1

    print(_format_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
