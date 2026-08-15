"""`ConfirmedSecuritySelection` -- an investor-authored assertion about
one Decision, never a claim about objective security identity. See
this package's own `__init__.py` for the full ontology.

Field-naming discipline (Sprint 20 ground rule 32): every name here
reads as "what the investor confirmed," never as "what Atlas resolved
or verified." `confirmed_cik`/`discovery_method`/`discovery_source`
are carried through from whatever `SecurityCandidate` (Sprint 19) the
caller supplies -- provenance of what the investor was shown, not an
independent fact Atlas re-derives.

`SecurityConfirmationEvent` (Sprint 22) is the append-only lifecycle
primitive underneath `ConfirmedSecuritySelection` -- see `table.py`'s
own docstring, which already anticipated this exact model when Sprint
20 first shipped. `ConfirmedSecuritySelection` remains the public
"what is currently confirmed" view, unchanged in shape, used only when
the latest event for a Decision is a `"confirmed"` one; a `"revoked"`
event has no corresponding `ConfirmedSecuritySelection` at all.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

SecurityConfirmationEventType = Literal["confirmed", "revoked"]


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


@dataclass(frozen=True)
class SecurityConfirmationEvent:
    """One append-only row in the confirmation lifecycle for a single
    Decision. A `"confirmed"` event means "as of `recorded_at`, the
    investor confirmed this ticker." A `"revoked"` event means "as of
    `recorded_at`, the investor withdrew their prior confirmation" --
    it still carries the ticker/display-name/cik/discovery fields of
    *the confirmation being revoked*, so every row remains fully
    self-describing without a join back to an earlier row (see
    `repository.py`'s own `_to_row`/`_to_event`). A revoked event never
    implies the earlier confirmation was wrong or that any other ticker
    is correct -- see this package's own `__init__.py` for the full
    ontology Sprint 22 established for this distinction.

    Events for one `decision_id` are never UPDATEd or DELETEd; "current
    state" is always derived by reading the single latest event (see
    `repository.get_latest_event`), never by mutating history."""

    id: str
    decision_id: str
    event_type: SecurityConfirmationEventType
    confirmed_ticker: str
    confirmed_display_name: str
    confirmed_cik: int | None
    discovery_method: str
    discovery_source: str
    recorded_at: datetime
