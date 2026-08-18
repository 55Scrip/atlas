"""`BusinessRecordIdentityProvenance` -- Sprint O Phase 8.

The four facts every gate-allowed `BusinessRecord` must carry: which
`CanonicalSecurity` its identity was resolved to, which algorithm
version performed that resolution, when, and a reference back to the
full shadow evidence trail (Sprint N's `SqlAlchemyResolutionRepository`
row id) that explains why.

Deliberately a plain value object, not imported by
`atlas.analysis_engine.business_data` -- `pipeline.ingest()` accepts
these same four facts as plain primitives (`str | None`/`datetime |
None`) rather than importing this type, so that foundational package
never depends on `canonical_security_gate` at all. This dataclass
exists for callers *above* `pipeline.ingest()` --
`business_data_refresh.service.refresh_company_data` and this
package's own `gate.py` -- to pass those four facts around as one
unit instead of four loose arguments.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

__all__ = ["BusinessRecordIdentityProvenance"]


@dataclass(frozen=True)
class BusinessRecordIdentityProvenance:
    canonical_security_id: str
    resolution_version: str
    resolved_at: datetime
    provider_evidence_reference: str
