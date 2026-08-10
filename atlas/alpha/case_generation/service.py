"""`CaseGenerationService` -- the one canonical owner of automatic
Investment Case existence (ATLAS-027, Phase 4/5/20). See this package's
own `__init__.py` for the full ownership/boundary rationale.

Investment Case Engine v1 slice: `ensure_case_id`/`ensure_cases` gained
an optional `known_case_ids_by_ticker` parameter so a ticker that
already has a Case linked in *one* membership context (Watchlist or
Portfolio) is reused, never re-created, when the same ticker is added
in the *other* context -- "Watchlist and Portfolio are membership
contexts around the same company knowledge," not two separate
analytical worlds. Omitting the parameter (every existing call site)
preserves the exact prior behavior: a `None` map is never consulted, so
no cross-context lookup happens and every case-less holding still gets
its own brand-new Case exactly as before this slice.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from atlas.alpha.portfolio.models import AlphaHolding
from atlas.core.application.case.create_case import CaseService

__all__ = ["CaseGenerationService"]


class CaseGenerationService:
    def __init__(self, case_service: CaseService) -> None:
        self._case_service = case_service

    def ensure_case_id(
        self,
        *,
        current_case_id: str | None,
        ticker: str,
        known_case_ids_by_ticker: Mapping[str, str] | None = None,
    ) -> str:
        """Return the one authoritative Case id for `ticker`.

        Get-or-set, in priority order: (1) `current_case_id`, if already
        set, is returned unchanged -- the identity-preserving idempotent
        path every caller of this service relies on; (2)
        `known_case_ids_by_ticker`, when given, is checked for a Case
        already linked to this same ticker in the *other* membership
        context -- reused, never duplicated; (3) only if neither exists
        is a brand-new Case created. `known_case_ids_by_ticker=None`
        (the default) skips step 2 entirely, matching this method's
        behavior before this slice existed.
        """
        if current_case_id is not None:
            return current_case_id
        if known_case_ids_by_ticker is not None:
            cross_context_case_id = known_case_ids_by_ticker.get(ticker)
            if cross_context_case_id is not None:
                return cross_context_case_id
        return str(self._case_service.create().id)

    def ensure_cases(
        self,
        holdings: tuple[AlphaHolding, ...],
        *,
        known_case_ids_by_ticker: Mapping[str, str] | None = None,
    ) -> tuple[AlphaHolding, ...]:
        """Return `holdings` with a `case_id` on every element.

        Idempotent: a holding whose `case_id` is already set is returned
        by identity-preserving `replace`-free passthrough -- unchanged,
        untouched, its existing Case reused. A holding with `case_id is
        None` resolves via `ensure_case_id` -- reusing a cross-context
        Case for its ticker if `known_case_ids_by_ticker` names one,
        otherwise getting exactly one brand-new Case
        (`CaseService.create()`, the same call the manual "Open
        Investment Case" flow already makes). Deterministic in the
        sense that matters for a holdings list: running this twice on
        an already-ensured list creates zero additional Cases, since
        every holding already carries a `case_id` the second time.

        Never guesses, never fabricates, never merges: each holding
        lacking a `case_id` gets its own resolved Case, one-to-one, in
        the order given. If `CaseService.create()` raises, that failure
        propagates -- an unresolved/failed Case creation must surface
        as a real error to the caller, never be silently swallowed into
        a holding left without a Case.
        """
        return tuple(
            holding
            if holding.case_id is not None
            else replace(
                holding,
                case_id=self.ensure_case_id(
                    current_case_id=None,
                    ticker=holding.ticker,
                    known_case_ids_by_ticker=known_case_ids_by_ticker,
                ),
            )
            for holding in holdings
        )
