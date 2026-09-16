"""OpenFIGI responses as the provider actually returned them, 2026-09-16.

Measured, not composed. That distinction is the point of this file: a
fixture invented to match the resolver's expectations proves only that the
resolver agrees with itself, and two of the facts below were surprises that
an invented fixture would never have contained --

* Volvo B's ISIN returns 209 listings of which **7 carry no share class at
  all**, so "ignore rows with no share class" is a rule about real data
  rather than a defensive nicety;
* the Taiwan Stock Exchange answers with the literal `exchCode`
  `"TT (Taiwan Stock Exchange)"` where every other venue answers with a bare
  two-character code.

Each fixture keeps the rows that carry meaning -- the venue listing, a
sample of the foreign ones, and the real null-share-class rows -- rather
than all several hundred, whose only other contribution is bulk.
"""
from __future__ import annotations

from atlas.alpha.security_identity_evidence.openfigi_adapter import (
    OpenFigiMappingResult,
    OpenFigiMatch,
)

# --- Identifiers, each confirmed against the provider ------------------
# ATCO_B_ISIN is worth a note: `SE0017486889` was the obvious guess and it
# is Atlas Copco's **A** share -- the provider named it `ATLAS COPCO AB-A
# SHS`. The B share is `...897`. Two ISINs differing in one character are
# two different securities, which is the whole reason a ticker like
# `ATCO-B` cannot be the key.
VOLVO_B_ISIN = "SE0000115446"
ASSA_B_ISIN = "SE0007100581"
ATCO_B_ISIN = "SE0017486897"
INVE_B_ISIN = "SE0015811963"
SCHNEIDER_ISIN = "FR0000121972"
SUNCOR_ISIN = "CA8672241079"
NOVO_B_ORDINARY_ISIN = "DK0062498333"
TSMC_ORDINARY_ISIN = "TW0002330008"

# --- Share classes -----------------------------------------------------
# The pairs below are the ones this whole design exists to keep apart. Note
# that each pair is the *same issuer* and a *different security*.
VOLVO_B_SHARE_CLASS = "BBG001S69SV8"
ASSA_B_SHARE_CLASS = "BBG001S66J50"
ATCO_B_SHARE_CLASS = "BBG001S61XR0"
INVE_B_SHARE_CLASS = "BBG001S723X6"
SCHNEIDER_SHARE_CLASS = "BBG001S67MN2"
SUNCOR_SHARE_CLASS = "BBG001S5YSF0"
TSMC_ORDINARY_SHARE_CLASS = "BBG001S6Q004"
TSM_ADR_SHARE_CLASS = "BBG001S5WWW4"
NOVO_ORDINARY_SHARE_CLASS = "BBG001S6RN12"
NVO_ADR_SHARE_CLASS = "BBG001S5TSK0"
GOOG_SHARE_CLASS = "BBG009S3NB21"
GOOGL_SHARE_CLASS = "BBG009S39JY5"
MSFT_SHARE_CLASS = "BBG001S5TD05"


def match(
    figi: str,
    ticker: str,
    exch_code: str,
    share_class: str | None,
    name: str,
    composite: str | None = None,
    security_type: str = "Common Stock",
) -> OpenFigiMatch:
    return OpenFigiMatch(
        figi=figi, ticker=ticker, name=name, exch_code=exch_code,
        security_type=security_type, market_sector="Equity",
        composite_figi=composite, share_class_figi=share_class,
    )


def _result(*matches: OpenFigiMatch) -> OpenFigiMappingResult:
    return OpenFigiMappingResult(matches=tuple(matches))


VOLVO_B = _result(
    match("BBG000BCH2F1", "VOLVB", "SS", VOLVO_B_SHARE_CLASS, "VOLVO AB-B SHS", "BBG000BCH216"),
    match("BBG000BY18V9", "VOLVF", "US", VOLVO_B_SHARE_CLASS, "VOLVO AB-B SHS", "BBG000BY18V9"),
    match("BBG000J5QGF7", "VOLVB", "EO", VOLVO_B_SHARE_CLASS, "VOLVO AB-B SHS", "BBG000J5QGF7"),
    match("BBG006TLX4J3", "VOLVB", "SW", VOLVO_B_SHARE_CLASS, "VOLVO AB-B SHS", "BBG006TLX4J3"),
    # Real rows with no share class -- 7 of the live 209, all at exchange X1.
    match("BBG00QFY3C83", "VOLVBUSD", "X1", None, "VOLVO AB-B SHS", "BBG000GK07C8"),
    match("BBG00QFYCJJ6", "VOLVBEUR", "X1", None, "VOLVO AB-B SHS", "BBG000JHKZ83"),
    match("BBG00QFYCK58", "VOLVBGBP", "X1", None, "VOLVO AB-B SHS", "BBG000JHP1R2"),
)

# For the four below only the home-venue row was individually recorded, so
# only it appears. A plausible-looking foreign listing added here to make a
# fixture "realistic" would be an invented FIGI wearing the same clothes as
# a measured one.
ASSA_B = _result(
    match("BBG000BGRY70", "ASSAB", "SS", ASSA_B_SHARE_CLASS, "ASSA ABLOY AB-B", "BBG000BGRXM5"),
)

ATCO_B = _result(
    match("BBG000BBM5J6", "ATCOB", "SS", ATCO_B_SHARE_CLASS, "ATLAS COPCO AB-B SHS", "BBG000BBM533"),
)

INVE_B = _result(
    match("BBG000BG97S6", "INVEB", "SS", INVE_B_SHARE_CLASS, "INVESTOR AB-B SHS", "BBG000BG97J6"),
)

SCHNEIDER = _result(
    match("BBG000BBWCH2", "SU", "FP", SCHNEIDER_SHARE_CLASS, "SCHNEIDER ELECTRIC SE", "BBG000BBWBV8"),
)

# Suncor trades as `SU` too -- in Canada, and in New York. Same ticker as
# Schneider, different company, and the share classes never collide.
SUNCOR = _result(
    match("BBG000BC1LY5", "SU", "CN", SUNCOR_SHARE_CLASS, "SUNCOR ENERGY INC", "BBG000BC1LY5"),
    match("BBG000BRK9W0", "SU", "UN", SUNCOR_SHARE_CLASS, "SUNCOR ENERGY INC", "BBG000BRK7L6"),
    match("BBG000BRK7L6", "SU", "US", SUNCOR_SHARE_CLASS, "SUNCOR ENERGY INC", "BBG000BRK7L6"),
)

NOVO_B_ORDINARY = _result(
    match("BBG000F8TZ33", "NOVOB", "DC", NOVO_ORDINARY_SHARE_CLASS, "NOVO NORDISK A/S-B", "BBG000F8TYC6"),
)

TSMC_ORDINARY = _result(
    # The parenthesised exchange code is verbatim from the provider.
    match("BBG000BN2JD8", "2330", "TT (Taiwan Stock Exchange)", TSMC_ORDINARY_SHARE_CLASS,
          "TAIWAN SEMICONDUCTOR MANUFAC", "BBG000BN2HR7"),
    match("BBG000M4F3B1", "TSMWF", "US", TSMC_ORDINARY_SHARE_CLASS,
          "TAIWAN SEMICONDUCTOR MANUFAC", "BBG000M4F3B1"),
)

NO_MATCH = _result()

BY_ISIN = {
    VOLVO_B_ISIN: VOLVO_B,
    ASSA_B_ISIN: ASSA_B,
    ATCO_B_ISIN: ATCO_B,
    INVE_B_ISIN: INVE_B,
    SCHNEIDER_ISIN: SCHNEIDER,
    SUNCOR_ISIN: SUNCOR,
    NOVO_B_ORDINARY_ISIN: NOVO_B_ORDINARY,
    TSMC_ORDINARY_ISIN: TSMC_ORDINARY,
}
