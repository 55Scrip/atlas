"""The deterministic per-refresh report (ATLAS-031, Phase 17)."""
from __future__ import annotations

from dataclasses import dataclass

__all__ = ["ProviderFailure", "RefreshSummary"]


@dataclass(frozen=True)
class ProviderFailure:
    """One provider's fetch failing never blocks another provider, and
    is always reported here -- never silently converted into "no data,"
    Phase 13's "we checked and it's missing" vs. "the provider failed"
    distinction, preserved end to end."""

    provider_id: str
    error: str


@dataclass(frozen=True)
class RefreshSummary:
    """Exactly the fields Phase 17 requires. `new_records` counts
    brand-new lineages (`version.version_number == 1`); `new_versions`
    counts a genuine new version of an already-known lineage (a
    restatement) -- kept distinct so a caller can tell "we learned
    about this company for the first time" from "something we already
    had changed."""

    ticker: str
    providers_attempted: tuple[str, ...]
    fetched_documents: int
    new_records: int
    new_versions: int
    duplicates_skipped: int
    rejected_documents: int
    provider_errors: tuple[ProviderFailure, ...]
