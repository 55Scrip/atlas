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
from datetime import datetime, timezone

from atlas.alpha.case_instrument.models import CaseInstrumentBinding
from atlas.alpha.case_instrument.repository import CaseInstrumentBindingRepository
from atlas.alpha.portfolio.models import AlphaHolding
from atlas.core.application.case.create_case import CaseService

__all__ = ["CaseGenerationService"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CaseGenerationService:
    def __init__(
        self,
        case_service: CaseService,
        binding_repository: CaseInstrumentBindingRepository | None = None,
    ) -> None:
        self._case_service = case_service
        #: Alpha Case Instrument Binding. Optional only so the many
        #: existing construction sites keep working unchanged; every
        #: production wiring passes it. When absent this service
        #: behaves exactly as it did before the binding existed --
        #: which is the behaviour that produced identity-less Cases,
        #: so a caller that can create Cases for real tickers should
        #: always supply it.
        self._binding_repository = binding_repository

    def ensure_case_id(
        self,
        *,
        current_case_id: str | None,
        ticker: str,
        known_case_ids_by_ticker: Mapping[str, str] | None = None,
        canonical_security_id: str | None = None,
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

        `canonical_security_id` is an identity the *caller* has already
        proven about this row from Atlas's own held evidence -- never a
        value a client supplied. It is attached only on the one branch
        below that creates a Case, and that asymmetry is deliberate:
        every other branch found its Case through a ticker, and a Case
        found by ticker is not thereby proven to be that security.
        Reuse branches still pass it down so a contradiction with an
        already-established identity is raised rather than ignored.
        """
        if current_case_id is not None:
            self._check_identity(current_case_id, canonical_security_id)
            self._bind(current_case_id, ticker)
            return current_case_id
        if known_case_ids_by_ticker is not None:
            cross_context_case_id = known_case_ids_by_ticker.get(ticker)
            if cross_context_case_id is not None:
                self._check_identity(cross_context_case_id, canonical_security_id)
                self._bind(cross_context_case_id, ticker)
                return cross_context_case_id
        # (4) the binding itself is now a resolution source, and the
        # authoritative one: a Case already bound to this instrument is
        # reused even when neither membership context knows about it.
        # This is what lets a Case be opened from Discovery or search
        # without first joining the Watchlist.
        bound = self._binding_repository.get_by_instrument_key(ticker) if self._binding_repository else None
        if bound is not None:
            if self._binding_repository is not None:
                self._binding_repository.assert_identity_agrees(bound, canonical_security_id)
            return bound.case_id
        case_id = str(self._case_service.create().id)
        self._bind(case_id, ticker, canonical_security_id=canonical_security_id)
        return case_id

    def assert_no_identity_conflicts(
        self,
        holdings: tuple[AlphaHolding, ...],
        *,
        known_case_ids_by_ticker: Mapping[str, str] | None = None,
    ) -> None:
        """Raise if any holding's proven identity contradicts a Case that
        already has one, before a single binding is written.

        `ensure_cases` writes one binding per holding, so without this a
        contradiction on the fourth holding would leave the first three
        already bound and the portfolio state unwritten. Every lookup here
        is a read: no Case is created, so checking costs nothing a later
        `ensure_cases` would not have paid anyway.
        """
        if self._binding_repository is None:
            return
        for holding in holdings:
            proven = getattr(holding, "canonical_security_id", None)
            if proven is None:
                continue
            case_id = holding.case_id
            if case_id is None and known_case_ids_by_ticker is not None:
                case_id = known_case_ids_by_ticker.get(holding.ticker)
            existing = (
                self._binding_repository.get_by_case_id(case_id)
                if case_id is not None
                else self._binding_repository.get_by_instrument_key(holding.ticker)
            )
            if existing is not None:
                self._binding_repository.assert_identity_agrees(existing, proven)

    def _check_identity(self, case_id: str, proven_canonical_security_id: str | None) -> None:
        """Compare a proven identity against this Case's stored one without
        writing anything.

        Used by the reuse branches of `ensure_case_id`, which must stay able
        to *disagree* loudly while never filling in an absence: a Case whose
        binding has no canonical identity keeps none, because the Case was
        reached through its ticker.
        """
        if self._binding_repository is None or proven_canonical_security_id is None:
            return
        existing = self._binding_repository.get_by_case_id(case_id)
        if existing is not None:
            self._binding_repository.assert_identity_agrees(existing, proven_canonical_security_id)

    def _bind(
        self,
        case_id: str,
        ticker: str,
        *,
        canonical_security_id: str | None = None,
    ) -> None:
        """Record which instrument this Case is about.

        Called on every path, not only creation: a Case that predates
        the binding table, or one resolved from the other membership
        context, gets its identity written down the first time anyone
        asks. Idempotent, and raises rather than rewriting if the Case
        is already bound to a different instrument -- see
        `CaseInstrumentBindingRepository.bind`.

        `canonical_security_id` is *written*, so only the branch of
        `ensure_case_id` that creates a Case passes it. A reuse branch
        checks for contradiction through `_check_identity` and binds
        without an identity, which is what keeps a ticker-found Case from
        acquiring one.
        """
        if self._binding_repository is None:
            return
        self._binding_repository.bind(
            CaseInstrumentBinding(
                case_id=case_id, instrument_key=ticker, bound_at=_utc_now(),
                canonical_security_id=canonical_security_id,
            )
        )

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
        self.assert_no_identity_conflicts(
            holdings, known_case_ids_by_ticker=known_case_ids_by_ticker
        )
        return tuple(
            holding
            if holding.case_id is not None
            else replace(
                holding,
                case_id=self.ensure_case_id(
                    current_case_id=None,
                    ticker=holding.ticker,
                    known_case_ids_by_ticker=known_case_ids_by_ticker,
                    canonical_security_id=getattr(holding, "canonical_security_id", None),
                ),
            )
            for holding in holdings
        )
