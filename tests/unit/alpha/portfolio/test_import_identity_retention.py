"""An earned security identity must survive the user pressing Confirm.

Sprint 67 measured the gap this file closes: `POST /import/preview` resolves a
holding's ISIN to a canonical security and returns the id on the wire, and
`POST /import` -- the request that actually persists -- carried the 2026-08-28
contract, so the identity was dropped by the frontend's own confirm mapper and
had no field to occupy anywhere after it. The binding column existed the whole
time and was NULL 48 times.

The retention is deliberately *not* a seventh field forwarded from the preview
response. The browser is not an authority on which security a holding is, so
confirm carries the row's own hard identifier and the backend resolves it again
from held state. Three consequences are the point of this file:

* a client that invents, swaps or tampers with a canonical id changes nothing,
  because no canonical id is ever read from the request;
* persisting an import never reaches a provider, so a master hit works offline
  and a master miss withholds instead of guessing;
* a Case that was only ever selected by its ticker does not acquire a canonical
  identity. Historical reconciliation is a separate question with a separate
  burden of proof, and ticker equality is not that proof.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool

from atlas.alpha.canonical_security_gate.factory import build_offline_import_identity_verifier
from atlas.alpha.case_generation.service import CaseGenerationService
from atlas.alpha.case_instrument.exceptions import ConflictingCaseInstrumentBindingError
from atlas.alpha.case_instrument.models import CaseInstrumentBinding
from atlas.alpha.case_instrument.repository import CaseInstrumentBindingRepository
from atlas.alpha.case_instrument.table import (
    case_instrument_binding_table,
    create_case_instrument_binding_table,
)
from atlas.alpha.portfolio.api.schemas import ImportHoldingRequest
from atlas.alpha.portfolio.models import AlphaHolding
from atlas.alpha.portfolio.service import (
    AlphaPortfolioService,
    ImportHoldingInput,
    ImportPortfolioRequest,
)
from atlas.alpha.portfolio.store import AlphaPortfolioStore
from atlas.alpha.portfolio.table import create_alpha_portfolio_state_table
from atlas.alpha.security_identity_evidence.openfigi_adapter import OpenFigiProviderUnavailable
from tests.unit.alpha.canonical_security_gate import figi_fixtures as fx
from tests.unit.alpha.canonical_security_gate.master_fixtures import (
    MasterSecurity,
    create_master_tables,
    seed_master,
)

_RECORDED = datetime(2026, 9, 16, tzinfo=timezone.utc)


# ---------------------------------------------------------------------
# Fixtures: a real master, a real binding repository, a real portfolio
# store, and a Case service that hands out predictable ids.
# ---------------------------------------------------------------------
class _CaseService:
    """Core `CaseService`'s one method, so these tests exercise the Alpha
    identity path without creating Core Case rows."""

    def __init__(self) -> None:
        self.created: list[str] = []

    def create(self):
        case_id = f"case-{len(self.created) + 1}"
        self.created.append(case_id)
        return type("Case", (), {"id": case_id})()


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite:///:memory:", future=True, poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    create_master_tables(engine)
    create_case_instrument_binding_table(engine)
    create_alpha_portfolio_state_table(engine)
    return engine


@pytest.fixture
def master(engine):
    """`{ISIN: canonical security id}`.

    The live master holds Suncor at NYSE and zero ISIN rows, so a recorded
    ISIN has to be seeded: it is the only correspondence a confirm can
    verify without a provider. Suncor is here because it is the doctrine's
    own worked example -- `SU` at NYSE is Suncor in this database while
    `SU.PA` in Paris is Schneider Electric, and no ticker can tell them
    apart.
    """
    return seed_master(
        engine,
        MasterSecurity(
            name="Volvo AB", ticker="VOLV-B", mic="XSTO", country="Sweden",
            currency="SEK", share_class_figi=fx.VOLVO_B_SHARE_CLASS,
            isin=fx.VOLVO_B_ISIN,
        ),
        MasterSecurity(
            name="Suncor Energy Inc.", ticker="SU", mic="XNYS",
            country="United States", share_class_figi=fx.SUNCOR_SHARE_CLASS,
            isin=fx.SUNCOR_ISIN,
        ),
    )


@pytest.fixture
def bindings(engine):
    return CaseInstrumentBindingRepository(engine)


@pytest.fixture
def case_service():
    return _CaseService()


@pytest.fixture
def service(engine, master, bindings, case_service):
    return AlphaPortfolioService(
        AlphaPortfolioStore(engine),
        case_generation_service=CaseGenerationService(case_service, binding_repository=bindings),
        verify_import_identity=build_offline_import_identity_verifier(engine),
    )


def row(ticker: str, **overrides) -> ImportHoldingInput:
    fields = dict(ticker=ticker, value_absolute=100.0, currency="SEK")
    fields.update(overrides)
    return ImportHoldingInput(**fields)


def confirm(service, *rows: ImportHoldingInput):
    return service.import_portfolio(ImportPortfolioRequest(holdings=tuple(rows)))


def canonical_ids(engine) -> dict[str, str | None]:
    with engine.connect() as connection:
        return {
            r.instrument_key: r.canonical_security_id
            for r in connection.execute(select(case_instrument_binding_table))
        }


def volvo_row(**overrides) -> ImportHoldingInput:
    return row("VOLV-B", isin=fx.VOLVO_B_ISIN, market="Nasdaq Stockholm", **overrides)


# ---------------------------------------------------------------------
# §64.1 / §64.2 -- the seam itself
# ---------------------------------------------------------------------
class TestIdentityReachesTheBinding:
    def test_a_verified_identity_survives_confirm_and_reaches_the_binding(self, service, engine, master):
        """§64.1 + §64.2 + P1-P4. Before Sprint 68 the ISIN had no field on
        the confirm request, so this could not even be expressed."""
        state = confirm(service, volvo_row())

        expected = master[fx.VOLVO_B_ISIN]
        assert state.holdings[0].canonical_security_id == expected
        assert canonical_ids(engine) == {"VOLV-B": expected}

    def test_the_identity_survives_the_portfolio_state_round_trip(self, service, engine, master):
        """P3. `holdings_json` is written by an explicit field list, so a new
        domain field reaching the database is its own assertion."""
        confirm(service, volvo_row())

        reloaded = AlphaPortfolioStore(engine).get()
        expected = master[fx.VOLVO_B_ISIN]
        assert reloaded.holdings[0].canonical_security_id == expected
        assert reloaded.holdings[0].source_isin == fx.VOLVO_B_ISIN

    def test_a_ticker_only_import_still_works_and_binds_no_identity(self, service, engine):
        """P7 + N8. The import path must not start demanding an ISIN."""
        state = confirm(service, row("MSFT"))

        assert state.holdings[0].canonical_security_id is None
        assert canonical_ids(engine) == {"MSFT": None}


# ---------------------------------------------------------------------
# §64.3 -- the browser is not an authority
# ---------------------------------------------------------------------
class TestClientSuppliedIdentityIsNotEvidence:
    def test_a_client_canonical_id_without_a_hard_identifier_binds_nothing(self, service, engine, master):
        """N1. `ImportHoldingInput` has no canonical-id field at all, so this
        asserts the absence rather than a defence against it."""
        suncor_id = master[fx.SUNCOR_ISIN]
        with pytest.raises(TypeError):
            ImportHoldingInput(ticker="VOLV-B", value_absolute=100.0,
                               canonical_security_id=suncor_id)

        assert canonical_ids(engine) == {}

    def test_a_hard_identifier_naming_another_security_binds_that_other_security(self, service, engine, master):
        """N2. The backend reads the ISIN and nothing else, so a mismatched
        pair cannot produce the identity the client asked for."""
        state = confirm(service, row("VOLV-B", isin=fx.SUNCOR_ISIN, market="NYSE"))

        suncor_id = master[fx.SUNCOR_ISIN]
        volvo_id = master[fx.VOLVO_B_ISIN]
        assert state.holdings[0].canonical_security_id != volvo_id
        assert state.holdings[0].canonical_security_id == suncor_id

    def test_a_contradictory_ticker_and_market_withholds_identity(self, service, engine):
        """N3 + §29. `SU` at NYSE is Suncor in this master; a Volvo ISIN on
        that row is two identifiers naming two securities."""
        state = confirm(service, row("SU", isin=fx.VOLVO_B_ISIN, market="NYSE"))

        assert state.holdings[0].canonical_security_id is None
        assert canonical_ids(engine) == {"SU": None}

    def test_an_unknown_isin_withholds_rather_than_inventing_a_security(self, service, engine):
        """N4 + N10 + §36. Offline, an ISIN the master has never recorded
        cannot be resolved, and persistence never reaches a provider."""
        state = confirm(service, row("ASSA-B", isin=fx.ASSA_B_ISIN, market="Nasdaq Stockholm"))

        assert state.holdings[0].canonical_security_id is None
        assert canonical_ids(engine) == {"ASSA-B": None}

    def test_a_malformed_isin_withholds(self, service, engine):
        """N9. One character off a real ISIN fails its check digit."""
        state = confirm(service, row("VOLV-B", isin="SE0000115447", market="Nasdaq Stockholm"))

        assert state.holdings[0].canonical_security_id is None

    def test_swapping_identifiers_between_rows_binds_neither_wrongly(self, service, engine, master):
        """N5. Each row is resolved from its own identifier, so a swap simply
        relabels which row is which -- never a wrong pairing."""
        state = confirm(
            service,
            row("VOLV-B", isin=fx.SUNCOR_ISIN, market="NYSE"),
            row("SU", isin=fx.VOLVO_B_ISIN, market="NYSE"),
        )

        volvo_id = master[fx.VOLVO_B_ISIN]
        suncor_id = master[fx.SUNCOR_ISIN]
        by_ticker = {h.ticker: h.canonical_security_id for h in state.holdings}
        assert by_ticker["VOLV-B"] == suncor_id      # its own ISIN, not its ticker's security
        assert by_ticker["SU"] is None               # withheld: ISIN and ticker disagree
        assert volvo_id not in canonical_ids(engine).values()


# ---------------------------------------------------------------------
# §64.4 -- the legacy boundary, the most important negative
# ---------------------------------------------------------------------
class TestLegacyTickerOnlyCasesAreNotUpgraded:
    def test_an_existing_ticker_only_case_is_not_given_a_canonical_identity(
        self, service, engine, bindings, master
    ):
        """§23 + N6. The Case is found by `instrument_key == ticker`, which is
        exactly the proof Atlas has decided is insufficient."""
        bindings.bind(CaseInstrumentBinding(
            case_id="legacy-case", instrument_key="VOLV-B", bound_at=_RECORDED,
        ))

        confirm(service, volvo_row())

        assert canonical_ids(engine) == {"VOLV-B": None}
        assert bindings.get_by_case_id("legacy-case").canonical_security_id is None

    def test_the_holding_still_records_what_was_proven(self, service, engine, bindings, master):
        """The refusal is about the *binding*, not about the evidence: a
        future reconciliation sprint needs to be able to tell the two
        apart, so the verified id stays on the holding."""
        bindings.bind(CaseInstrumentBinding(
            case_id="legacy-case", instrument_key="VOLV-B", bound_at=_RECORDED,
        ))

        state = confirm(service, volvo_row())

        expected = master[fx.VOLVO_B_ISIN]
        assert state.holdings[0].canonical_security_id == expected
        assert bindings.get_by_case_id("legacy-case").canonical_security_id is None

    def test_an_existing_binding_with_the_same_identity_is_accepted_unchanged(
        self, service, engine, bindings, master
    ):
        """§21 + P6."""
        expected = master[fx.VOLVO_B_ISIN]
        bindings.bind(CaseInstrumentBinding(
            case_id="bound-case", instrument_key="VOLV-B", bound_at=_RECORDED,
            canonical_security_id=expected,
        ))

        confirm(service, volvo_row())

        assert canonical_ids(engine) == {"VOLV-B": expected}

    def test_an_existing_binding_with_a_different_identity_fails_closed(
        self, service, engine, bindings, master
    ):
        """§22. Never overwritten, and never silently tolerated either."""
        suncor_id = master[fx.SUNCOR_ISIN]
        bindings.bind(CaseInstrumentBinding(
            case_id="bound-case", instrument_key="VOLV-B", bound_at=_RECORDED,
            canonical_security_id=suncor_id,
        ))

        with pytest.raises(ConflictingCaseInstrumentBindingError):
            confirm(service, volvo_row())

        assert canonical_ids(engine) == {"VOLV-B": suncor_id}


# ---------------------------------------------------------------------
# Provider, idempotence, share classes, venues
# ---------------------------------------------------------------------
class TestPersistingAnImportNeverFetches:
    def test_a_master_hit_costs_no_provider_call(self, engine, master, bindings, case_service):
        """§37 + §38 + §89. The verifier is handed a provider that raises if
        it is ever called, which is what makes "offline" measurable."""
        calls: list[str] = []

        def counted(isin):
            calls.append(isin)
            raise AssertionError("persisting an import must not reach a provider")

        service = AlphaPortfolioService(
            AlphaPortfolioStore(engine),
            case_generation_service=CaseGenerationService(case_service, binding_repository=bindings),
            verify_import_identity=build_offline_import_identity_verifier(engine, map_isin_fn=counted),
        )
        state = confirm(service, volvo_row())

        assert calls == []
        assert state.holdings[0].canonical_security_id is not None

    def test_a_master_miss_asks_a_provider_that_cannot_fetch_and_withholds(
        self, engine, master, bindings, case_service
    ):
        """§36 + N10, stated exactly as it behaves.

        A master miss *does* reach step 2 of the resolver -- that is how the
        withholding happens. What it reaches is a provider that reports
        itself unavailable without being able to go anywhere, so the row
        resolves to nothing rather than to a guess. The distinction worth
        keeping precise: zero network, one call into a stub that cannot
        make one. Claiming "no provider call" here would be false; claiming
        "no network" is the true and the load-bearing part.
        """
        calls: list[str] = []
        real = build_offline_import_identity_verifier(engine)

        def counted(isin):
            calls.append(isin)
            raise OpenFigiProviderUnavailable("no network while persisting an import")

        service = AlphaPortfolioService(
            AlphaPortfolioStore(engine),
            case_generation_service=CaseGenerationService(case_service, binding_repository=bindings),
            verify_import_identity=build_offline_import_identity_verifier(engine, map_isin_fn=counted),
        )
        state = confirm(service, row("ATCO-B", isin=fx.ATCO_B_ISIN, market="Nasdaq Stockholm"))

        assert calls == [fx.ATCO_B_ISIN]
        assert state.holdings[0].canonical_security_id is None
        assert state.holdings[0].source_isin == fx.ATCO_B_ISIN

    def test_the_default_verifier_cannot_reach_a_provider_at_all(self, engine, master):
        """The default `map_isin_fn` is not a network client with a short
        timeout -- it is a function that refuses, so "offline" is a property
        of the wiring rather than of the environment."""
        verify = build_offline_import_identity_verifier(engine)

        assert verify(ticker="ATCO-B", isin=fx.ATCO_B_ISIN, market="Nasdaq Stockholm") is None
        assert verify(ticker="VOLV-B", isin=fx.VOLVO_B_ISIN, market="Nasdaq Stockholm") is not None


class TestIdempotence:
    def test_importing_the_same_verified_holding_twice_changes_nothing(
        self, service, engine, master, case_service
    ):
        """§54 + P5."""
        confirm(service, volvo_row())
        first = canonical_ids(engine)

        confirm(service, volvo_row())

        assert canonical_ids(engine) == first
        assert len(case_service.created) == 1


class TestShareClassesStayDistinct:
    def test_two_share_classes_of_one_issuer_are_two_securities(self, engine, bindings, case_service):
        """§34. Novo Nordisk's Copenhagen ordinary share and its New York ADR
        share an issuer and nothing else that matters here."""
        seed_master(
            engine,
            MasterSecurity(
                name="Novo Nordisk A/S", ticker="NOVO-B", mic="XCSE", country="Denmark",
                currency="DKK", share_class_figi=fx.NOVO_ORDINARY_SHARE_CLASS,
                isin=fx.NOVO_B_ORDINARY_ISIN,
            ),
            MasterSecurity(
                name="Novo Nordisk A/S ADR", ticker="NVO", mic="XNYS",
                country="United States", share_class_figi=fx.NVO_ADR_SHARE_CLASS,
                isin="US6701002056",
            ),
        )
        service = AlphaPortfolioService(
            AlphaPortfolioStore(engine),
            case_generation_service=CaseGenerationService(case_service, binding_repository=bindings),
            verify_import_identity=build_offline_import_identity_verifier(engine),
        )

        confirm(
            service,
            row("NOVO-B", isin=fx.NOVO_B_ORDINARY_ISIN, market="Nasdaq Copenhagen"),
            row("NVO", isin="US6701002056", market="NYSE"),
        )

        ids = canonical_ids(engine)
        assert ids["NOVO-B"] is not None
        assert ids["NVO"] is not None
        assert ids["NOVO-B"] != ids["NVO"]

    def test_a_cross_listing_resolves_to_the_same_security(self, service, engine, master):
        """§35. A share class is the same share class at a second venue, so a
        venue difference is not a conflict -- but it is also not a reason to
        collapse two different share classes, which the test above covers."""
        state = confirm(service, row("VOLVB", isin=fx.VOLVO_B_ISIN, market="Stockholm"))

        expected = master[fx.VOLVO_B_ISIN]
        assert state.holdings[0].canonical_security_id == expected


class TestNonUsHoldings:
    def test_a_stockholm_holding_completes_the_whole_path(self, service, engine, master):
        """§36 (the sprint's stated future value): the eleven followed
        non-US holdings are exactly the rows a ticker cannot identify, and
        `VOLV-B` is spelled `VOLVB` by the provider at the one venue where
        both are talking about the same listing."""
        state = confirm(service, volvo_row())

        expected = master[fx.VOLVO_B_ISIN]
        assert state.holdings[0].canonical_security_id == expected
        assert canonical_ids(engine)["VOLV-B"] == expected


class TestPartialAndAtomic:
    def test_one_unresolved_row_does_not_borrow_the_other_rows_identity(self, service, engine, master):
        """§51."""
        state = confirm(service, volvo_row(), row("MSFT"))

        by_ticker = {h.ticker: h.canonical_security_id for h in state.holdings}
        assert by_ticker["VOLV-B"] is not None
        assert by_ticker["MSFT"] is None

    def test_an_identity_conflict_writes_no_binding_at_all(self, service, engine, bindings, master):
        """§52 + §53. The conflict is detected before any binding is written,
        so a rejected import leaves no half-written identity behind."""
        suncor_id = master[fx.SUNCOR_ISIN]
        bindings.bind(CaseInstrumentBinding(
            case_id="bound-case", instrument_key="VOLV-B", bound_at=_RECORDED,
            canonical_security_id=suncor_id,
        ))

        with pytest.raises(ConflictingCaseInstrumentBindingError):
            confirm(service, row("MSFT"), volvo_row())

        assert "MSFT" not in canonical_ids(engine)
        assert AlphaPortfolioStore(engine).get() is None


# ---------------------------------------------------------------------
# §13 / §48 / §49 -- the confirm request itself, and calling it directly
# ---------------------------------------------------------------------
class TestTheConfirmRequestContract:
    def test_the_request_carries_the_identifier_and_the_venue(self):
        """§13 + §46. The two fields the backend needs, and no more."""
        request = ImportHoldingRequest(
            ticker="VOLV-B", valueAbsolute=1000.0, currency="SEK",
            isin=fx.VOLVO_B_ISIN, market="Nasdaq Stockholm",
        )

        assert request.isin == fx.VOLVO_B_ISIN
        assert request.market == "Nasdaq Stockholm"

    def test_a_client_supplied_canonical_id_is_not_part_of_the_contract(self):
        """§13 + §49. A valid-looking canonical id sent by a client is not
        a field of this request, so it cannot be read, forwarded or bound.
        Asserted on `model_dump` rather than on a raised error because
        Pydantic ignores extras -- the point being that the value has
        nowhere to go, which is why nothing downstream has to defend
        against it."""
        request = ImportHoldingRequest(
            ticker="VOLV-B", valueAbsolute=1000.0,
            canonicalSecurityId="8075-0590-whatever-the-client-wants",
            securityName="Something Else Entirely",
        )

        dumped = request.model_dump()
        assert "canonical_security_id" not in dumped
        assert "8075-0590-whatever-the-client-wants" not in str(dumped)
        assert set(dumped) == {
            "ticker", "weight_percent", "value_absolute", "quantity",
            "price", "currency", "isin", "market",
        }

    def test_a_legacy_request_without_any_identity_still_validates(self):
        """§46 + §87. Nothing about this path now requires an ISIN."""
        request = ImportHoldingRequest(ticker="MSFT", weightPercent=10.0)

        assert request.isin is None
        assert request.market is None

    def test_direct_confirm_with_a_fabricated_identity_binds_nothing(
        self, service, engine, master
    ):
        """§48 + §49 + N4. Backend safety does not depend on the frontend
        having called preview first: this import never went near one, and
        the only thing that could have bound an identity -- a recorded
        ISIN correspondence -- is absent."""
        state = confirm(service, row("VOLV-B", isin="SE0000000000", market="Nasdaq Stockholm"))

        assert state.holdings[0].canonical_security_id is None
        assert canonical_ids(engine) == {"VOLV-B": None}


# ---------------------------------------------------------------------
# §17 / §45 -- backward compatibility of the persisted shape
# ---------------------------------------------------------------------
class TestPersistedShapeCompatibility:
    def test_a_payload_written_before_identity_retention_still_reads(self, engine):
        """§17 + §45 + §79. This is the live 2026-08-28 shape, verbatim:
        eight keys and no identity. It must deserialize untouched -- no
        migration, and no historical row rewritten to add the new keys."""
        import json

        from sqlalchemy import insert

        from atlas.alpha.portfolio.table import alpha_portfolio_state_table

        legacy = [{
            "ticker": "VOLV-B", "weightPercent": 4.0, "valueAbsolute": 1000.0,
            "quantity": 10.0, "price": 100.0, "currency": "SEK",
            "caseId": "legacy-case", "reconciliationStatus": "NONE",
        }]
        with engine.begin() as connection:
            connection.execute(insert(alpha_portfolio_state_table).values(
                id=1, established_at="2026-08-28T11:10:31.113319+00:00",
                updated_at="2026-08-28T11:10:31.113319+00:00", entry_mode="IMPORTED",
                holdings_json=json.dumps(legacy),
            ))

        state = AlphaPortfolioStore(engine).get()

        assert state.holdings[0].ticker == "VOLV-B"
        assert state.holdings[0].case_id == "legacy-case"
        assert state.holdings[0].source_isin is None
        assert state.holdings[0].canonical_security_id is None

    def test_a_verified_holding_round_trips_through_the_store(self, engine, master):
        """§45. Write then read, with no service in between."""
        from datetime import datetime as _dt

        from atlas.alpha.portfolio.models import AlphaPortfolioState, EntryMode

        expected = master[fx.VOLVO_B_ISIN]
        store = AlphaPortfolioStore(engine)
        store.replace(AlphaPortfolioState(
            established_at=_dt(2026, 10, 15, tzinfo=timezone.utc),
            updated_at=_dt(2026, 10, 15, tzinfo=timezone.utc),
            entry_mode=EntryMode.IMPORTED,
            holdings=(AlphaHolding(
                ticker="VOLV-B", weight_percent=100.0, value_absolute=1000.0,
                currency="SEK", source_isin=fx.VOLVO_B_ISIN,
                canonical_security_id=expected,
            ),),
        ))

        reloaded = store.get()

        assert reloaded.holdings[0].source_isin == fx.VOLVO_B_ISIN
        assert reloaded.holdings[0].canonical_security_id == expected
