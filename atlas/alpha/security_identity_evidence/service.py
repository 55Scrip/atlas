"""`SecurityVerificationService` -- the one write path for Security
Identity Evidence. Never touches `ConfirmedSecuritySelection` or
`Decision` -- reads the current confirmation via
`security_confirmation`'s own repository (a read-only Alpha-to-Alpha
dependency, the same kind Daily Brief/History already have on
`investment_case_change`'s persisted state), calls the OpenFIGI
adapter, and writes exactly one new, immutable evidence event.

Verification is always an explicit call to `verify()` -- nothing in
this package, `security_confirmation`, or anywhere else calls it
automatically (Sprint 23 ground rule 8/9/14). `confirm()`, `correct()`,
and `revoke()` remain completely unaware this package exists.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from atlas.alpha.security_confirmation.repository import SqlAlchemySecurityConfirmationRepository
from atlas.alpha.security_discovery.canonicalize import canonicalize_company_text
from atlas.alpha.security_identity_evidence.exceptions import NoActiveConfirmationError
from atlas.alpha.security_identity_evidence.models import SecurityIdentityEvidence, SecurityVerificationStatus
from atlas.alpha.security_identity_evidence.openfigi_adapter import (
    OpenFigiMappingResult,
    OpenFigiProviderUnavailable,
    map_ticker,
)
from atlas.alpha.security_identity_evidence.repository import SqlAlchemySecurityIdentityEvidenceRepository

#: Closed allow-list of `discovery_source` values this package knows
#: how to verify against OpenFIGI -- declared independently of
#: `security_confirmation.service._SUPPORTED_DISCOVERY_SOURCES` rather
#: than importing it, so this package's own honesty boundary about what
#: it can verify never silently widens just because the confirmation
#: package's own allow-list grows for unrelated reasons. Currently
#: identical by coincidence, not by shared reference.
_VERIFIABLE_DISCOVERY_SOURCES = frozenset({"sec_company_tickers"})

_PROVIDER_NAME = "openfigi"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SecurityVerificationService:
    def __init__(
        self,
        confirmation_repository: SqlAlchemySecurityConfirmationRepository,
        evidence_repository: SqlAlchemySecurityIdentityEvidenceRepository,
        provider=map_ticker,
        clock=_utc_now,
    ) -> None:
        self._confirmations = confirmation_repository
        self._evidence = evidence_repository
        self._provider = provider
        self._clock = clock

    def verify(self, decision_id: str) -> SecurityIdentityEvidence:
        confirmation = self._confirmations.get_by_decision_id(decision_id)
        if confirmation is None:
            raise NoActiveConfirmationError(decision_id)

        if confirmation.discovery_source not in _VERIFIABLE_DISCOVERY_SOURCES:
            evidence = self._build_evidence(
                confirmation_id=confirmation.id,
                status="unsupported",
                provider_identifier=None,
                verified_ticker=None,
                verified_name=None,
                exchange=None,
                response_snapshot={},
            )
            self._evidence.add(evidence)
            return evidence

        try:
            result = self._provider(confirmation.confirmed_ticker)
        except OpenFigiProviderUnavailable:
            evidence = self._build_evidence(
                confirmation_id=confirmation.id,
                status="provider_unavailable",
                provider_identifier=None,
                verified_ticker=None,
                verified_name=None,
                exchange=None,
                response_snapshot={},
            )
            self._evidence.add(evidence)
            return evidence

        status, match = self._classify(result, confirmation.confirmed_display_name)
        evidence = self._build_evidence(
            confirmation_id=confirmation.id,
            status=status,
            provider_identifier=match.figi if match else None,
            verified_ticker=match.ticker if match else None,
            verified_name=match.name if match else None,
            exchange=match.exch_code if match else None,
            response_snapshot=_snapshot(result),
        )
        self._evidence.add(evidence)
        return evidence

    def get_latest(self, confirmation_id: str) -> SecurityIdentityEvidence | None:
        return self._evidence.get_latest(confirmation_id)

    def _classify(self, result: OpenFigiMappingResult, confirmed_display_name: str):
        if len(result.matches) == 0:
            return "not_verified", None
        if len(result.matches) > 1:
            return "ambiguous", None

        match = result.matches[0]
        if match.name is not None and canonicalize_company_text(match.name) == canonicalize_company_text(
            confirmed_display_name
        ):
            return "verified", match
        return "not_verified", match

    def _build_evidence(
        self,
        *,
        confirmation_id: str,
        status: SecurityVerificationStatus,
        provider_identifier: str | None,
        verified_ticker: str | None,
        verified_name: str | None,
        exchange: str | None,
        response_snapshot: dict,
    ) -> SecurityIdentityEvidence:
        return SecurityIdentityEvidence(
            id=str(uuid.uuid4()),
            confirmation_id=confirmation_id,
            provider=_PROVIDER_NAME,
            status=status,
            provider_identifier=provider_identifier,
            verified_ticker=verified_ticker,
            verified_name=verified_name,
            exchange=exchange,
            provider_response_json=json.dumps(response_snapshot, sort_keys=True),
            verified_at=self._clock(),
        )


def _snapshot(result: OpenFigiMappingResult) -> dict:
    """Exactly the fields this package actually reads -- never the
    entire raw HTTP payload (see `models.py`'s own docstring)."""
    return {
        "matches": [
            {
                "figi": m.figi,
                "ticker": m.ticker,
                "name": m.name,
                "exchCode": m.exch_code,
                "securityType": m.security_type,
                "marketSector": m.market_sector,
            }
            for m in result.matches
        ]
    }
