"""Alpha Case Instrument Binding -- the identity contract.

Before this table, a Case's instrument was recovered backwards from
membership: a Portfolio holding or a Watchlist entry whose `case_id`
matched. That made the investor's *relationship* to a company the
source of the Case's *identity*, and it is why a Case created outside a
membership-add path came back with no company profile, no business
facts and no coverage.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.case_instrument.backfill import backfill_case_instrument_bindings
from atlas.alpha.case_instrument.exceptions import ConflictingCaseInstrumentBindingError
from atlas.alpha.case_instrument.models import CaseInstrumentBinding
from atlas.alpha.case_instrument.repository import CaseInstrumentBindingRepository
from atlas.alpha.case_instrument.table import create_case_instrument_binding_table
from atlas.alpha.portfolio.models import AlphaHolding, AlphaPortfolioState, EntryMode
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.watchlist.models import AlphaWatchlistEntry
from atlas.alpha.watchlist.store import AlphaWatchlistStore
from atlas.alpha.watchlist.table import create_alpha_watchlist_entry_table

_NOW = datetime(2026, 9, 8, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    create_case_instrument_binding_table(engine)
    create_alpha_watchlist_entry_table(engine)
    create_alpha_portfolio_state_table(engine)
    return engine


@pytest.fixture
def repository(engine):
    return CaseInstrumentBindingRepository(engine)


def binding(case_id: str, instrument_key: str, *, at: datetime = _NOW) -> CaseInstrumentBinding:
    return CaseInstrumentBinding(case_id=case_id, instrument_key=instrument_key, bound_at=at)


class TestPersistence:
    def test_a_binding_round_trips(self, repository):
        repository.bind(binding("case-1", "MSFT"))
        stored = repository.get_by_case_id("case-1")
        assert stored is not None
        assert stored.instrument_key == "MSFT"
        assert stored.bound_at == _NOW

    def test_an_unbound_case_reads_back_as_absent_not_as_a_guess(self, repository):
        assert repository.get_by_case_id("never-bound") is None

    def test_a_case_can_be_found_by_its_instrument(self, repository):
        repository.bind(binding("case-1", "MSFT"))
        found = repository.get_by_instrument_key("MSFT")
        assert found is not None and found.case_id == "case-1"

    def test_an_unbound_instrument_reads_back_as_absent(self, repository):
        assert repository.get_by_instrument_key("MSFT") is None

    def test_canonical_security_id_is_the_migration_seam_and_is_unset_today(self, repository):
        repository.bind(binding("case-1", "MSFT"))
        assert repository.get_by_case_id("case-1").canonical_security_id is None


class TestCardinalityAndConflicts:
    def test_rebinding_the_same_instrument_is_idempotent(self, repository):
        first = repository.bind(binding("case-1", "MSFT"))
        second = repository.bind(binding("case-1", "MSFT", at=_NOW + timedelta(days=1)))
        # Identity does not get a new timestamp for being asked about twice.
        assert second.bound_at == first.bound_at
        assert len(repository.list_all()) == 1

    def test_rebinding_a_case_to_a_different_instrument_is_refused(self, repository):
        repository.bind(binding("case-1", "MSFT"))
        with pytest.raises(ConflictingCaseInstrumentBindingError):
            repository.bind(binding("case-1", "AAPL"))
        # ...and the original survives the attempt.
        assert repository.get_by_case_id("case-1").instrument_key == "MSFT"

    def test_one_case_per_instrument_is_what_lookup_returns(self, repository):
        repository.bind(binding("case-1", "MSFT"))
        assert repository.get_by_instrument_key("MSFT").case_id == "case-1"


class TestInstrumentKeysAreNotReNormalized:
    """This package records an answer; it does not compute one. Any
    normalization of its own is how two unrelated companies end up
    sharing a key."""

    def test_su_pa_never_collapses_into_su(self, repository):
        # Both exist in the real database: SU.PA is Schneider Electric
        # on Euronext Paris; SU is Suncor Energy on the NYSE.
        repository.bind(binding("case-schneider", "SU.PA"))
        repository.bind(binding("case-suncor", "SU"))
        assert repository.get_by_instrument_key("SU.PA").case_id == "case-schneider"
        assert repository.get_by_instrument_key("SU").case_id == "case-suncor"

    @pytest.mark.parametrize(
        "a,b",
        [("GOOG", "GOOGL"), ("BRK.B", "BRK.A"), ("VOLV-B", "VOLV-A"), ("ATCO-B", "ATCO-A")],
    )
    def test_share_classes_stay_distinct(self, repository, a, b):
        repository.bind(binding(f"case-{a}", a))
        repository.bind(binding(f"case-{b}", b))
        assert repository.get_by_instrument_key(a).case_id == f"case-{a}"
        assert repository.get_by_instrument_key(b).case_id == f"case-{b}"


class TestBackfill:
    def _portfolio(self, engine, holdings):
        store = AlphaPortfolioStore(engine)
        store.replace(
            AlphaPortfolioState(
                established_at=_NOW, updated_at=_NOW, entry_mode=EntryMode.FROM_SCRATCH, holdings=tuple(holdings)
            )
        )
        return store

    def test_backfills_portfolio_and_watchlist_associations(self, engine, repository):
        portfolio = self._portfolio(engine, [AlphaHolding(ticker="MSFT", weight_percent=50.0, case_id="case-msft")])
        watchlist = AlphaWatchlistStore(engine)
        watchlist.add(AlphaWatchlistEntry(ticker="MU", case_id="case-mu", added_at=_NOW))

        report = backfill_case_instrument_bindings(repository, portfolio, watchlist, bound_at=_NOW)
        assert report.is_clean
        assert set(report.bound) == {"case-msft", "case-mu"}
        assert repository.get_by_case_id("case-msft").instrument_key == "MSFT"
        assert repository.get_by_case_id("case-mu").instrument_key == "MU"

    def test_backfills_a_removed_watchlist_entry_too(self, engine, repository):
        """Removed rows are kept deliberately, and they are exactly as
        authoritative about which company a Case was about."""
        portfolio = self._portfolio(engine, [])
        watchlist = AlphaWatchlistStore(engine)
        watchlist.add(AlphaWatchlistEntry(ticker="AMD", case_id="case-amd", added_at=_NOW))
        watchlist.remove("AMD", _NOW + timedelta(days=1))

        report = backfill_case_instrument_bindings(repository, portfolio, watchlist, bound_at=_NOW)
        assert report.bound == ("case-amd",)
        assert repository.get_by_case_id("case-amd").instrument_key == "AMD"

    def test_is_idempotent(self, engine, repository):
        portfolio = self._portfolio(engine, [AlphaHolding(ticker="MSFT", weight_percent=50.0, case_id="case-msft")])
        watchlist = AlphaWatchlistStore(engine)
        first = backfill_case_instrument_bindings(repository, portfolio, watchlist, bound_at=_NOW)
        second = backfill_case_instrument_bindings(repository, portfolio, watchlist, bound_at=_NOW)
        assert first.bound == ("case-msft",)
        assert second.bound == ()
        assert second.already_bound == ("case-msft",)
        assert len(repository.list_all()) == 1

    def test_a_case_named_by_two_securities_is_reported_never_guessed(self, engine, repository):
        """The integrity defect this whole change exists to stop
        happening silently. Preferring Portfolio over Watchlist here
        would be the same backwards guess in a new place."""
        portfolio = self._portfolio(engine, [AlphaHolding(ticker="MSFT", weight_percent=50.0, case_id="shared")])
        watchlist = AlphaWatchlistStore(engine)
        watchlist.add(AlphaWatchlistEntry(ticker="AAPL", case_id="shared", added_at=_NOW))

        report = backfill_case_instrument_bindings(repository, portfolio, watchlist, bound_at=_NOW)
        assert not report.is_clean
        assert report.conflicts == (("shared", ("AAPL", "MSFT")),)
        assert report.bound == ()
        assert repository.get_by_case_id("shared") is None

    def test_one_conflict_does_not_block_the_healthy_rows(self, engine, repository):
        portfolio = self._portfolio(
            engine,
            [
                AlphaHolding(ticker="MSFT", weight_percent=50.0, case_id="shared"),
                AlphaHolding(ticker="NVDA", weight_percent=50.0, case_id="case-nvda"),
            ],
        )
        watchlist = AlphaWatchlistStore(engine)
        watchlist.add(AlphaWatchlistEntry(ticker="AAPL", case_id="shared", added_at=_NOW))

        report = backfill_case_instrument_bindings(repository, portfolio, watchlist, bound_at=_NOW)
        assert report.bound == ("case-nvda",)
        assert len(report.conflicts) == 1

    def test_a_holding_with_no_case_is_simply_not_a_binding(self, engine, repository):
        portfolio = self._portfolio(engine, [AlphaHolding(ticker="MSFT", weight_percent=50.0, case_id=None)])
        report = backfill_case_instrument_bindings(repository, portfolio, AlphaWatchlistStore(engine), bound_at=_NOW)
        assert report.bound == ()
        assert repository.list_all() == ()


class TestLifecycleIndependence:
    """Membership describes the investor's relationship to a company.
    Changing that relationship must not change what the Case is about.
    """

    def test_removing_a_watchlist_entry_leaves_the_binding_intact(self, engine, repository):
        watchlist = AlphaWatchlistStore(engine)
        watchlist.add(AlphaWatchlistEntry(ticker="MU", case_id="case-mu", added_at=_NOW))
        repository.bind(binding("case-mu", "MU"))

        watchlist.remove("MU", _NOW + timedelta(days=1))

        assert repository.get_by_case_id("case-mu").instrument_key == "MU"
        assert repository.get_by_instrument_key("MU").case_id == "case-mu"

    def test_removing_a_portfolio_holding_leaves_the_binding_intact(self, engine, repository):
        store = AlphaPortfolioStore(engine)
        store.replace(
            AlphaPortfolioState(
                established_at=_NOW, updated_at=_NOW, entry_mode=EntryMode.FROM_SCRATCH,
                holdings=(AlphaHolding(ticker="MSFT", weight_percent=100.0, case_id="case-msft"),),
            )
        )
        repository.bind(binding("case-msft", "MSFT"))

        store.replace(
            AlphaPortfolioState(
                established_at=_NOW, updated_at=_NOW, entry_mode=EntryMode.FROM_SCRATCH, holdings=()
            )
        )

        assert repository.get_by_case_id("case-msft").instrument_key == "MSFT"
