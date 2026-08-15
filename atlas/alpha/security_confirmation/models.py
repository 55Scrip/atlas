"""`ConfirmedSecuritySelection` -- an investor-authored assertion about
one Decision, never a claim about objective security identity. See
this package's own `__init__.py` for the full ontology.

Field-naming discipline (Sprint 20 ground rule 32): every name here
reads as "what the investor confirmed," never as "what Atlas resolved
or verified." `confirmed_cik`/`discovery_method`/`discovery_source`
are carried through from whatever `SecurityCandidate` (Sprint 19) the
caller supplies -- provenance of what the investor was shown, not an
independent fact Atlas re-derives.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ConfirmedSecuritySelection:
    """`decision_id` is the entire scope of this record -- there is no
    `case_id`, no subject-string key, and no investor-global alias
    field, precisely because Sprint 20's own scope investigation found
    none of those broader scopes provably safe (see `__init__.py`).
    `confirmed_cik` is optional: SEC's own data always supplies one
    today, but a future discovery source might not, and this model
    must not require a fact it cannot always honestly carry."""

    id: str
    decision_id: str
    confirmed_ticker: str
    confirmed_display_name: str
    confirmed_cik: int | None
    discovery_method: str
    discovery_source: str
    confirmed_at: datetime
