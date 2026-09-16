"""Venue text, MIC, and the code the provider answers with.

Three vocabularies for one place, none derivable from another. The table
under test is closed on purpose: an unrecognised venue yields `None`, and
`None` stops a security being created rather than starting a guess.
"""
from __future__ import annotations

import pytest

from atlas.alpha.security_identity_evidence.venues import mic_for_market, venue_for_mic


@pytest.mark.parametrize(
    "market,mic",
    [
        ("Nasdaq Stockholm", "XSTO"),
        ("NASDAQ STOCKHOLM", "XSTO"),
        ("  Nasdaq   Stockholm  ", "XSTO"),
        ("Stockholmsbörsen", "XSTO"),
        ("Euronext Paris", "XPAR"),
        ("Nasdaq Copenhagen", "XCSE"),
        ("Taiwan Stock Exchange", "XTAI"),
        ("NYSE", "XNYS"),
        ("NASDAQ", "XNAS"),
    ],
)
def test_known_venue_text_maps_to_its_mic(market, mic) -> None:
    assert mic_for_market(market).value == mic


@pytest.mark.parametrize("market", [None, "", "   ", "Some Regional Exchange", "Stockh", "XSTO "])
def test_unknown_venue_text_maps_to_nothing(market) -> None:
    """Including `Stockh`, a prefix of a known name: a string that
    resembles a venue is not evidence about a venue."""
    assert mic_for_market(market) is None


def test_a_mic_carries_its_country() -> None:
    """`CanonicalSecurity.country` is the listing country, and a MIC names
    one exchange, which sits in one country."""
    assert venue_for_mic("XSTO").country == "Sweden"
    assert venue_for_mic("XPAR").country == "France"
    assert venue_for_mic("XCSE").country == "Denmark"
    assert venue_for_mic("XTAI").country == "Taiwan"


def test_stockholm_is_ss_in_the_providers_own_vocabulary() -> None:
    assert venue_for_mic("XSTO").openfigi_exchange_codes == ("SS",)


def test_taiwan_keeps_the_exact_string_the_provider_returned() -> None:
    """Measured: the Taiwan Stock Exchange answers with a parenthesised
    description where every other venue answers with a bare code. Matching
    `TT` alone against it finds nothing, which reads exactly like "this
    security does not trade in Taiwan"."""
    codes = venue_for_mic("XTAI").openfigi_exchange_codes
    assert "TT (Taiwan Stock Exchange)" in codes
    assert "TT" in codes


def test_a_venue_with_no_measured_code_cannot_select_a_listing() -> None:
    """US venues are recognised -- enough to check the master and catch a
    contradiction -- but carry no response code, because the US rows return
    both a venue code and a composite one and only measurement can say
    which is the listing. Refusing to create is the safe half."""
    assert venue_for_mic("XNYS").openfigi_exchange_codes == ()
    assert venue_for_mic("XNAS").openfigi_exchange_codes == ()


def test_an_unknown_mic_is_not_a_venue() -> None:
    assert venue_for_mic("XFRA") is None
    assert venue_for_mic(None) is None
