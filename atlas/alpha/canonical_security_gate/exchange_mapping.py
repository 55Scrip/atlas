"""Exchange display-name -> MIC mapping -- Sprint O.

Deterministic, closed-list, non-fuzzy -- the same discipline
`canonical_security_resolution.normalization.canonicalize_company_text`
already establishes: a raw provider display string (Alpha Vantage's
`Exchange` field, e.g. `"NASDAQ"`) maps to a real ISO 10383 Market
Identifier Code only when the exact display string is already known.
An unrecognized string yields `None` -- never a guess, never a
fabricated MIC -- consistent with this codebase's "no AI, no
heuristics, no fabrication" rule for identity-bearing data. Growing
this table (a new exchange string a provider starts reporting) is a
deliberate, reviewable addition, the same "closed allow-list, grows
only when a real capability is confirmed" discipline
`canonical_security.value_objects` already establishes for
`ProviderName`/`SecurityType`.
"""
from __future__ import annotations

from atlas.alpha.canonical_security.value_objects import MicCode

#: Confirmed real MICs for the exchange display strings Alpha Vantage's
#: OVERVIEW endpoint is known to report for US-listed equities. Not
#: exhaustive of every exchange in the world -- only what this
#: provider's current field (`_IDENTITY_FIELD_MAP["Exchange"]`) has
#: actually been observed to contain.
_EXCHANGE_DISPLAY_NAME_TO_MIC: dict[str, str] = {
    "NASDAQ": "XNAS",
    "NYSE": "XNYS",
    "NYSE ARCA": "ARCX",
    "NYSE MKT": "XASE",
    "AMEX": "XASE",
    "BATS": "BATS",
    "OTC": "OTCM",
}


def map_exchange_display_name_to_mic(raw: str | None) -> MicCode | None:
    if raw is None:
        return None
    mic = _EXCHANGE_DISPLAY_NAME_TO_MIC.get(raw.strip().upper())
    return MicCode(mic) if mic is not None else None
