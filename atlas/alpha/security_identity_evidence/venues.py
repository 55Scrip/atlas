"""Where a holding trades, in the three vocabularies that have to agree.

A broker writes `Nasdaq Stockholm`. ISO 10383 writes `XSTO`. OpenFIGI writes
`SS`. Nothing derives one from another, so each pairing here is a measured
fact or it is not in the table, and a venue that is not in the table simply
cannot drive the creation of a security. That refusal is the point: guessing
a venue is how a Paris listing becomes a Canadian one.

Three separate jobs, deliberately not collapsed into one lookup:

* **broker text -> MIC.** Exact match only, after case and whitespace
  normalization. No prefix or fuzzy matching, for the reason
  `canonical_security_gate.exchange_mapping` already gives: a string that
  merely resembles a venue name is not evidence about a venue. Unrecognized
  text yields `None`, and the import keeps going without a venue.

* **MIC -> country.** A MIC names one exchange, and an exchange sits in one
  country; this is a property of the venue rather than a claim about the
  company. `CanonicalSecurity.country` is the listing country, which is what
  makes this the right source for it -- and why an ADR in New York is
  honestly `United States` even though the issuer is Danish.

* **MIC -> the exchange codes OpenFIGI puts in its *responses*.** Measured,
  not documented from anywhere, and different from the codes sent in a
  *request*: `master_population._MIC_TO_EXCHANGE_CODE` maps venues for the
  request side and is left alone. Two of these were surprises worth keeping
  in writing:

  - Stockholm answers on `SS`, but a request for ticker `VOLV-B` at `SS`
    returns nothing at all, because OpenFIGI spells the same share `VOLVB`.
    The broker's ticker and the provider's ticker disagree at the one venue
    where both are talking about the same listing -- so the ISIN is not
    merely the better key here, it is the only one that works.
  - Taiwan answers on the literal string `TT (Taiwan Stock Exchange)`, where
    every other venue answers with a bare two-character code. Matching `TT`
    exactly against that returns zero rows and would look exactly like "this
    security does not trade in Taiwan". Both spellings are therefore listed,
    both exact -- a prefix match would have hidden the quirk rather than
    recorded it.

A MIC with no measured response codes (the US venues, below) can still be
*matched* against the existing master and can still detect a contradiction;
it just cannot select a venue listing out of a provider response, so it
cannot create a security. Every US security Atlas holds already exists, so
nothing is lost by refusing, and a guess would be unverifiable.

All values measured against OpenFIGI on 2026-09-16.
"""
from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Venue", "mic_for_market", "venue_for_mic"]


@dataclass(frozen=True)
class Venue:
    mic: str
    #: The country the venue is in -- i.e. the listing country.
    country: str
    #: The exact `exchCode` values OpenFIGI returns for this venue. Empty
    #: means Atlas has never measured one, so a response cannot be filtered
    #: down to this venue and no security may be created for it.
    openfigi_exchange_codes: tuple[str, ...] = ()


_VENUES: dict[str, Venue] = {
    # Measured: one row each in the ISIN responses for Volvo B, Schneider
    # Electric, Atlas Copco B and Novo Nordisk B.
    "XSTO": Venue("XSTO", "Sweden", ("SS",)),
    "XPAR": Venue("XPAR", "France", ("FP",)),
    "XCSE": Venue("XCSE", "Denmark", ("DC",)),
    # `TT (Taiwan Stock Exchange)` is what the provider actually returned for
    # TSMC's ordinary share; the bare code is kept alongside it in case the
    # provider ever normalizes, and neither is a prefix rule.
    "XTAI": Venue("XTAI", "Taiwan", ("TT (Taiwan Stock Exchange)", "TT")),
    # US venues: recognized so that ticker+MIC can be checked against the
    # master and contradictions caught, but with no response code, because
    # the US rows carry both a venue code and a composite code (`UN` and
    # `US` for Suncor) and only measurement can say which is the listing.
    # Refusing to create is the safe half of that uncertainty.
    "XNYS": Venue("XNYS", "United States"),
    "XNAS": Venue("XNAS", "United States"),
}

#: Broker venue text -> MIC. A closed allow-list of exact spellings, grown
#: only when a real export shows a new one. Both the English and Swedish
#: names are present because a Swedish broker writes either depending on the
#: export format.
_MARKET_TEXT_TO_MIC: dict[str, str] = {
    "NASDAQ STOCKHOLM": "XSTO",
    "NASDAQ OMX STOCKHOLM": "XSTO",
    "STOCKHOLMSBORSEN": "XSTO",
    "STOCKHOLMSBÖRSEN": "XSTO",
    "STOCKHOLM": "XSTO",
    "EURONEXT PARIS": "XPAR",
    "PARIS": "XPAR",
    "NASDAQ COPENHAGEN": "XCSE",
    "KOPENHAMN": "XCSE",
    "KÖPENHAMN": "XCSE",
    "COPENHAGEN": "XCSE",
    "TAIWAN STOCK EXCHANGE": "XTAI",
    "TAIWAN": "XTAI",
    "NYSE": "XNYS",
    "NEW YORK STOCK EXCHANGE": "XNYS",
    "NASDAQ": "XNAS",
}


def mic_for_market(raw: str | None) -> str | None:
    """The MIC a broker's venue text names, or `None` if Atlas has never
    been taught that exact spelling. Never a guess.

    A plain string rather than a `MicCode`: this is a lookup table, and the
    canonical identity package is reachable only through the Gate (its own
    integration-safety guard enforces that). The Gate turns the string into
    a value object where one is wanted.
    """
    if raw is None:
        return None
    return _MARKET_TEXT_TO_MIC.get(" ".join(raw.split()).upper())


def venue_for_mic(mic: str | None) -> Venue | None:
    if mic is None:
        return None
    return _VENUES.get(str(mic).strip().upper())
