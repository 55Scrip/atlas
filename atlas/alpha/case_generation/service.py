"""`CaseGenerationService` -- the one canonical owner of automatic
Investment Case existence (ATLAS-027, Phase 4/5/20). See this package's
own `__init__.py` for the full ownership/boundary rationale.
"""
from __future__ import annotations

from dataclasses import replace

from atlas.alpha.portfolio.models import AlphaHolding
from atlas.core.application.case.create_case import CaseService

__all__ = ["CaseGenerationService"]


class CaseGenerationService:
    def __init__(self, case_service: CaseService) -> None:
        self._case_service = case_service

    def ensure_cases(self, holdings: tuple[AlphaHolding, ...]) -> tuple[AlphaHolding, ...]:
        """Return `holdings` with a `case_id` on every element.

        Idempotent: a holding whose `case_id` is already set is returned
        by identity-preserving `replace`-free passthrough -- unchanged,
        untouched, its existing Case reused. A holding with `case_id is
        None` gets exactly one brand-new Case (`CaseService.create()`,
        the same call the manual "Open Investment Case" flow already
        makes) linked to it. Deterministic in the sense that matters for
        a holdings list: running this twice on an already-ensured list
        creates zero additional Cases, since every holding already
        carries a `case_id` the second time.

        Never guesses, never fabricates, never merges: each holding
        lacking a `case_id` gets its own new Case, one-to-one, in the
        order given. If `CaseService.create()` raises, that failure
        propagates -- an unresolved/failed Case creation must surface
        as a real error to the caller, never be silently swallowed into
        a holding left without a Case.
        """
        return tuple(
            holding if holding.case_id is not None else replace(holding, case_id=str(self._case_service.create().id))
            for holding in holdings
        )
