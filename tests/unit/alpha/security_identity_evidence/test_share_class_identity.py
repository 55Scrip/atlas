"""Share-class identity from an ISIN, and the collisions it must survive.

Every FIGI in this file was observed from the live provider on 2026-09-16.
The Schneider/Suncor pair is the reason the whole identity layer exists:
both trade under the ticker `SU`, on different exchanges, as different
companies.
"""
from __future__ import annotations

import pytest

from atlas.alpha.security_identity_evidence.openfigi_adapter import OpenFigiMatch
from atlas.alpha.security_identity_evidence.share_class_identity import share_class_identity

# Observed live.
VOLVO_B_SHARE_CLASS = "BBG001S69SV8"
SCHNEIDER_SHARE_CLASS = "BBG001S67MN2"
SUNCOR_SHARE_CLASS = "BBG001S5YSF0"


def _match(
    figi: str,
    *,
    share_class: str | None,
    ticker: str = "SU",
    exch: str = "FP",
    name: str = "SCHNEIDER ELECTRIC SE",
    composite: str | None = None,
) -> OpenFigiMatch:
    return OpenFigiMatch(
        figi=figi, ticker=ticker, name=name, exch_code=exch,
        security_type="Common Stock", market_sector="Equity",
        composite_figi=composite, share_class_figi=share_class,
    )


def test_hundreds_of_listings_still_name_one_share_class() -> None:
    """Volvo B really does return 209 listings. Unanimity, not count, is
    what makes the answer safe."""
    matches = tuple(
        _match(f"BBG{index:09d}", share_class=VOLVO_B_SHARE_CLASS, ticker="VOLVB",
               exch="SS", name="VOLVO AB-B SHS")
        for index in range(209)
    )
    identity = share_class_identity(matches)
    assert identity is not None
    assert identity.share_class_figi == VOLVO_B_SHARE_CLASS
    assert identity.listing_count == 209
    assert identity.name == "VOLVO AB-B SHS"


def test_one_listing_is_enough() -> None:
    identity = share_class_identity((_match("BBG000BBWCH2", share_class=SCHNEIDER_SHARE_CLASS),))
    assert identity is not None
    assert identity.share_class_figi == SCHNEIDER_SHARE_CLASS


def test_the_same_ticker_on_two_exchanges_is_two_share_classes() -> None:
    """The collision this exists to survive: Schneider trades as `SU` in
    Paris and Suncor trades as `SU` in Canada."""
    schneider = share_class_identity(
        (_match("BBG000BBWCH2", share_class=SCHNEIDER_SHARE_CLASS, ticker="SU", exch="FP"),)
    )
    suncor = share_class_identity(
        (_match("BBG000BC1LY5", share_class=SUNCOR_SHARE_CLASS, ticker="SU", exch="CN",
                name="SUNCOR ENERGY INC"),)
    )
    assert schneider is not None and suncor is not None
    assert schneider.share_class_figi != suncor.share_class_figi
    assert schneider.share_class_figi == SCHNEIDER_SHARE_CLASS
    assert suncor.share_class_figi == SUNCOR_SHARE_CLASS


def test_an_unknown_isin_resolves_nothing() -> None:
    assert share_class_identity(()) is None


def test_listings_without_a_share_class_resolve_nothing() -> None:
    assert share_class_identity((_match("BBG000BBWCH2", share_class=None),)) is None


def test_disagreement_resolves_nothing_rather_than_voting() -> None:
    """If the listings disagree, the ISIN is not naming one share class --
    and a majority of a disagreement is still a guess."""
    matches = (
        _match("BBG000BBWCH2", share_class=SCHNEIDER_SHARE_CLASS),
        _match("BBG000BBWCH3", share_class=SCHNEIDER_SHARE_CLASS),
        _match("BBG000BC1LY5", share_class=SUNCOR_SHARE_CLASS, name="SUNCOR ENERGY INC"),
    )
    assert share_class_identity(matches) is None


def test_a_disputed_name_is_dropped_not_chosen() -> None:
    """Names describe; they never key. A disagreement about the name must
    not become a silent pick."""
    matches = (
        _match("BBG000BBWCH2", share_class=SCHNEIDER_SHARE_CLASS, name="SCHNEIDER ELECTRIC SE"),
        _match("BBG000BKHC34", share_class=SCHNEIDER_SHARE_CLASS, name="SCHNEIDER ELECTRIC"),
    )
    identity = share_class_identity(matches)
    assert identity is not None
    assert identity.share_class_figi == SCHNEIDER_SHARE_CLASS
    assert identity.name is None


def test_the_venue_level_figi_is_never_used_as_the_identity() -> None:
    """Each listing has its own `figi`; only the share class is shared. If
    the venue FIGI were the key, the same security would look like hundreds
    of different ones."""
    matches = (
        _match("BBG000BCH2F1", share_class=VOLVO_B_SHARE_CLASS, ticker="VOLVB", exch="SS"),
        _match("BBG000BLPJ65", share_class=VOLVO_B_SHARE_CLASS, ticker="VOL1", exch="GR"),
    )
    identity = share_class_identity(matches)
    assert identity is not None
    assert identity.share_class_figi == VOLVO_B_SHARE_CLASS
    assert identity.share_class_figi not in {m.figi for m in matches}


def test_composite_figi_is_not_the_share_class() -> None:
    """Composites group listings per country, so two venues of one share
    class can carry different composites. Keying on a composite would split
    one security into several."""
    matches = (
        _match("BBG000BCH2F1", share_class=VOLVO_B_SHARE_CLASS, composite="BBG000BCH216", exch="SS"),
        _match("BBG000BLPJ65", share_class=VOLVO_B_SHARE_CLASS, composite="BBG000BLPJ65", exch="GR"),
    )
    identity = share_class_identity(matches)
    assert identity is not None
    assert len({m.composite_figi for m in matches}) == 2
    assert identity.share_class_figi == VOLVO_B_SHARE_CLASS


def test_the_module_reaches_no_provider_and_invents_no_identifier() -> None:
    import inspect

    from atlas.alpha.security_identity_evidence import share_class_identity as module

    source = inspect.getsource(module)
    for forbidden in ("httpx", "requests", "import os", "ticker_to", "TICKER_TO"):
        assert forbidden not in source


def test_the_real_response_shape_mixes_a_share_class_with_nulls() -> None:
    """Observed live: every ISIN queried returned exactly one real
    share-class FIGI *and* a number of listings carrying none at all --
    instruments in the same response that have no share class. Those nulls
    are not disagreement, and treating them as such would reject every real
    ISIN. Volvo B: 209 listings, 209 distinct venue FIGIs, 80 distinct
    composites, one share class.
    """
    matches = tuple(
        _match(f"BBG{index:09d}",
               share_class=VOLVO_B_SHARE_CLASS if index % 3 else None,
               ticker="VOLVB", exch="SS", name="VOLVO AB-B SHS")
        for index in range(209)
    )
    identity = share_class_identity(matches)
    assert identity is not None
    assert identity.share_class_figi == VOLVO_B_SHARE_CLASS
    assert identity.listing_count < 209  # the null-carrying listings are excluded


# Observed live, 2026-09-16, and the sharpest proof in this file.
NOVO_ADR_SHARE_CLASS = "BBG001S5TSK0"        # NVO on NYSE: NOVO-NORDISK A/S-SPONS ADR
NOVO_ORDINARY_SHARE_CLASS = "BBG001S6RN12"   # DK0062498333: NOVO NORDISK A/S-B
ALPHABET_C_SHARE_CLASS = "BBG009S3NB21"      # GOOG
ALPHABET_A_SHARE_CLASS = "BBG009S39JY5"      # GOOGL


def test_an_adr_is_not_its_ordinary_share() -> None:
    """One issuer, two securities. Novo Nordisk's New York ADR and its
    Copenhagen B share carry different share classes, so issuer-level
    evidence may only ever be shared after the issuer link is proven --
    never as a side effect of them looking like the same company.
    """
    adr = share_class_identity(
        (_match("BBG000BQBKR3", share_class=NOVO_ADR_SHARE_CLASS, ticker="NVO", exch="US",
                name="NOVO-NORDISK A/S-SPONS ADR"),)
    )
    ordinary = share_class_identity(
        (_match("BBG000F8V450", share_class=NOVO_ORDINARY_SHARE_CLASS, ticker="NOVOB", exch="DC",
                name="NOVO NORDISK A/S-B"),)
    )
    assert adr is not None and ordinary is not None
    assert adr.share_class_figi != ordinary.share_class_figi


def test_two_share_classes_of_one_issuer_stay_apart() -> None:
    """Alphabet A and Alphabet C differ only by a letter in the ticker, and
    by everything in the identifier."""
    c = share_class_identity((_match("BBG009S3NB30", share_class=ALPHABET_C_SHARE_CLASS,
                                     ticker="GOOG", exch="US", name="ALPHABET INC-CL C"),))
    a = share_class_identity((_match("BBG009S39JX6", share_class=ALPHABET_A_SHARE_CLASS,
                                     ticker="GOOGL", exch="US", name="ALPHABET INC-CL A"),))
    assert c is not None and a is not None
    assert c.share_class_figi != a.share_class_figi
