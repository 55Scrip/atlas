"""Constructing a security Atlas has never seen, from strong identity.

Until now Atlas could not record that a Stockholm security exists. Not
because it could not identify one -- OpenFIGI names Volvo B precisely, and
its share-class FIGI is the same from any venue in the world -- but because
the aggregate demanded a quoting currency, and no identity provider supplies
one. A fact about market data was blocking a fact about identity, and eleven
holdings (about 42% of the portfolio) stayed unidentifiable as a result.

Currency is now absence-tolerant. These tests hold the line that this did
not quietly become permission to guess one.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from atlas.alpha.canonical_security.models import CanonicalSecurity, ListingRef
from atlas.alpha.canonical_security.repository import SqlAlchemyCanonicalSecurityRepository
from atlas.alpha.canonical_security.serialization import from_json_dict, to_json_dict
from atlas.alpha.canonical_security.table import create_canonical_security_tables
from atlas.alpha.canonical_security.value_objects import MicCode, TradingCurrency


@pytest.fixture
def repository():
    engine = create_engine("sqlite:///:memory:", future=True, poolclass=StaticPool,
                           connect_args={"check_same_thread": False})
    create_canonical_security_tables(engine)
    return SqlAlchemyCanonicalSecurityRepository(engine)


def _volvo_b(currency: TradingCurrency | None = None) -> CanonicalSecurity:
    return CanonicalSecurity.discover(
        canonical_company_name="VOLVO AB-B SHS",
        native_ticker="VOLV-B",
        primary_exchange_mic=MicCode("XSTO"),
        country="Sweden",
        trading_currency=currency,
    )


def test_a_stockholm_security_can_exist_without_a_proven_currency() -> None:
    security = _volvo_b()
    assert security.canonical_company_name == "VOLVO AB-B SHS"
    assert security.primary_exchange_mic.value == "XSTO"
    assert security.trading_currency is None


def test_an_unproven_currency_is_absence_not_a_placeholder() -> None:
    """`None`, never a string. A sentinel like "UNKNOWN" or "XXX" would be
    a currency-shaped value that arithmetic and formatting would happily
    accept."""
    assert _volvo_b().trading_currency is None


def test_a_proven_currency_is_still_recorded() -> None:
    security = _volvo_b(TradingCurrency("SEK"))
    assert security.trading_currency is not None
    assert security.trading_currency.value == "SEK"


def test_it_round_trips_through_storage(repository) -> None:
    security = _volvo_b().add_listing(
        ListingRef(ticker="VOLV-B", exchange_mic=MicCode("XSTO"), currency=None,
                   relationship="NATIVE", security_type="COMMON_STOCK")
    )
    repository.save(security)
    loaded = repository.load(str(security.id))
    assert loaded is not None
    assert loaded.trading_currency is None
    assert loaded.primary_exchange_mic.value == "XSTO"
    assert loaded.canonical_company_name == "VOLVO AB-B SHS"


def test_a_stored_currency_survives_the_round_trip(repository) -> None:
    """The 36 securities that already have currencies must keep them."""
    security = _volvo_b(TradingCurrency("SEK")).add_listing(
        ListingRef(ticker="VOLV-B", exchange_mic=MicCode("XSTO"), currency=None,
                   relationship="NATIVE", security_type="COMMON_STOCK")
    )
    repository.save(security)
    loaded = repository.load(str(security.id))
    assert loaded.trading_currency is not None
    assert loaded.trading_currency.value == "SEK"


def test_it_round_trips_through_serialization() -> None:
    security = _volvo_b()
    restored = from_json_dict(to_json_dict(security))
    assert restored.trading_currency is None
    assert restored.native_ticker == "VOLV-B"


def test_serialization_of_a_proven_currency_is_unchanged() -> None:
    security = _volvo_b(TradingCurrency("SEK"))
    payload = to_json_dict(security)
    assert payload["tradingCurrency"] == "SEK"
    assert from_json_dict(payload).trading_currency.value == "SEK"


# --- Currency safety ---------------------------------------------------


def test_an_unproven_currency_never_becomes_the_account_currency() -> None:
    """The live import recorded SEK against all 25 holdings because that is
    the account's reporting currency. A US security held in a Swedish
    account does not quote in SEK, and nothing here may borrow it."""
    security = _volvo_b()
    assert security.trading_currency is None
    assert security.trading_currency != TradingCurrency("SEK")


def test_an_unproven_currency_never_defaults_to_usd() -> None:
    security = _volvo_b()
    assert security.trading_currency is None


def test_a_currency_code_still_has_to_be_a_currency_code() -> None:
    """Tolerating absence must not tolerate nonsense in its place."""
    for rubbish in ["", "  ", "US", "USDD", "12A", "UNKNOWN"]:
        with pytest.raises(Exception):
            TradingCurrency(rubbish)


def test_the_aggregate_carries_no_currency_defaulting_logic() -> None:
    import inspect

    from atlas.alpha.canonical_security import models

    source = inspect.getsource(models)
    for forbidden in ('"USD"', "'USD'", '"SEK"', "'SEK'", "or TradingCurrency("):
        assert forbidden not in source, f"{forbidden} suggests a default currency"


@pytest.mark.parametrize("mic,country", [("XSTO", "Sweden"), ("XPAR", "France"), ("XTAI", "Taiwan")])
def test_venues_atlas_has_never_held_are_now_constructible(mic, country) -> None:
    """Stockholm, Paris and Taiwan -- the three markets behind the eleven
    unresolved holdings."""
    security = CanonicalSecurity.discover(
        canonical_company_name="EXAMPLE AB",
        native_ticker="EXMPL",
        primary_exchange_mic=MicCode(mic),
        country=country,
        trading_currency=None,
    )
    assert security.primary_exchange_mic.value == mic
    assert security.country == country
    assert security.trading_currency is None
