"""`SecurityIdentityEvidence` -- one append-only, externally-sourced
observation about a specific confirmation event. See this package's
own `__init__.py` for the full ontology.

`status` is a closed, explicit set (Sprint 23 Phase 10) -- never a
free-text field, never a fuzzy score:

- `"verified"`: the provider returned data for the confirmed ticker
  whose name plausibly corroborates `confirmed_display_name` (compared
  via `security_discovery.canonicalize_company_text`, the same fixed
  transform Sprint 19 already proved -- never a second, invented
  similarity heuristic).
- `"not_verified"`: the provider returned data for the ticker, but the
  name does not plausibly corroborate the confirmation -- an honest
  negative signal, never treated the same as "the provider had
  nothing to say."
- `"provider_unavailable"`: a network/timeout/HTTP-server failure
  talking to the provider -- an infrastructure fact, never a judgment
  about the security.
- `"ambiguous"`: the provider returned zero or more than one match for
  the ticker query -- Atlas cannot honestly pick one, so it says so
  rather than silently choosing.
- `"unsupported"`: the confirmation's own `discovery_source` is not one
  this package knows how to verify against any provider it actually
  integrates (mirrors the closed allow-list guard
  `security_confirmation.service._SUPPORTED_DISCOVERY_SOURCES` already
  established).

Field-naming discipline mirrors `ConfirmedSecuritySelection`'s own
(Sprint 20 ground rule 32): every name here reads as "what the
provider returned," never as "what Atlas has determined to be true."
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

SecurityVerificationStatus = Literal[
    "verified", "not_verified", "provider_unavailable", "ambiguous", "unsupported"
]


@dataclass(frozen=True)
class SecurityIdentityEvidence:
    """`confirmation_id` is the entire scope of this record -- see
    this package's own `__init__.py` for why evidence is scoped to one
    confirmation event, never to a Decision or a provider directly.
    `provider_response_json` is a compact snapshot of exactly the
    fields this package actually reads from the provider's response
    (never the entire raw HTTP payload, and never a field the provider
    did not actually return) -- present for auditability, so a later
    reader can see precisely what was observed rather than trusting
    the derived `status` alone."""

    id: str
    confirmation_id: str
    provider: str
    status: SecurityVerificationStatus
    provider_identifier: str | None
    verified_ticker: str | None
    verified_name: str | None
    exchange: str | None
    provider_response_json: str
    verified_at: datetime
