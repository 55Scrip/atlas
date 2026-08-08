"""One-time legacy Case backfill (ATLAS-029, Phase 2-4).

`AlphaPortfolioService._ensure_cases` (ATLAS-027) already guarantees
every holding created through a live write path -- `import_portfolio`,
`apply_confirmed_trade`, `reconcile_replace_allocation` -- gets a
`case_id`. A holding with `case_id is None` can therefore only be
persisted state from before that guarantee existed. This module is the
one canonical, explicit repair path for exactly that state: never
triggered by a read, never triggered automatically, and reusing
`CaseGenerationService` (ATLAS-027) as its only Case-creation mechanism
-- this file creates no Case itself.

Deliberately NOT read-time self-healing (that decision was already made,
and re-affirmed for this sprint): `PortfolioCockpitService.build_report`
and `InvestmentCaseCompositionService.build`/`build_many` stay pure reads
today and after this module exists. The only caller is the CLI in
`atlas/alpha/portfolio/cli.py`.

Per-holding, not batched through `ensure_cases` as one call: `ensure_cases`
raises on the first `CaseService.create()` failure, aborting its entire
tuple with no partial progress. Calling it once per holding that actually
needs a Case means one holding's failure never blocks another's repair,
and yields the specific ticker-level failure list this module reports.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.portfolio.store import AlphaPortfolioStore

__all__ = ["BackfillFailure", "BackfillResult", "backfill_missing_portfolio_cases"]


@dataclass(frozen=True)
class BackfillFailure:
    ticker: str
    error: str


@dataclass(frozen=True)
class BackfillResult:
    """A deterministic summary of one backfill run -- the exact four
    counts the CLI must print, per Phase 5's requirement."""

    holdings_scanned: int
    cases_preserved: int
    cases_created: int
    failures: tuple[BackfillFailure, ...]


def backfill_missing_portfolio_cases(
    portfolio_store: AlphaPortfolioStore,
    case_generation_service: CaseGenerationService,
) -> BackfillResult:
    """Idempotent and safe to rerun: a holding whose `case_id` is
    already set is counted as preserved and never touched again -- a
    second run over an already-repaired portfolio always reports
    `cases_created=0` and writes nothing back.

    Never modifies an existing Case, never creates a duplicate (each
    holding gets at most one `ensure_cases` call, and only if its own
    `case_id` is `None`), never touches Decisions/Observations/Evidence
    /Outcomes, and never guesses an identity -- a holding whose repair
    fails keeps `case_id is None`, reported honestly in `failures`
    rather than papered over.
    """
    state = portfolio_store.get()
    if state is None or not state.holdings:
        return BackfillResult(holdings_scanned=0, cases_preserved=0, cases_created=0, failures=())

    holdings_scanned = len(state.holdings)
    cases_preserved = sum(1 for holding in state.holdings if holding.case_id is not None)
    cases_created = 0
    failures: list[BackfillFailure] = []
    repaired_holdings = list(state.holdings)
    any_change = False

    for index, holding in enumerate(state.holdings):
        if holding.case_id is not None:
            continue
        try:
            (repaired,) = case_generation_service.ensure_cases((holding,))
        except Exception as exc:  # noqa: BLE001 -- reported, never silently swallowed
            failures.append(BackfillFailure(ticker=holding.ticker, error=str(exc)))
            continue
        repaired_holdings[index] = repaired
        cases_created += 1
        any_change = True

    if any_change:
        portfolio_store.replace(dataclasses.replace(state, holdings=tuple(repaired_holdings)))

    return BackfillResult(
        holdings_scanned=holdings_scanned,
        cases_preserved=cases_preserved,
        cases_created=cases_created,
        failures=tuple(failures),
    )
