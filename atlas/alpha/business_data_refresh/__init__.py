"""Explicit, operator-triggered real-provider refresh (ATLAS-031, Phase
17/40) -- the one write path that ever calls a real
`BusinessDataProvider`. `service.refresh_company_data` is invoked only
from `cli.py`, one ticker at a time, never from a request handler,
never on a schedule, never from `InvestmentCaseCompositionService`'s
own read paths (`build`/`build_many` stay pure reads, same discipline
`atlas.alpha.portfolio.backfill` already established for the legacy
Case backfill)."""
from __future__ import annotations
