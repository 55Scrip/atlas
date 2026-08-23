"""The deterministic per-refresh report (ATLAS-031, Phase 17)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from atlas.analysis_engine.business_data.models import BusinessRecord

__all__ = [
    "ProviderFailure",
    "RefreshSummary",
    "EnrichmentOutcome",
    "HoldingEnrichmentResult",
    "BulkEnrichmentSummary",
]


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
    #: Sprint O Phase 7 -- always populated: the Identity Gate's own
    #: resolution outcome for this run (`"AUTO_ACCEPT"`,
    #: `"MANUAL_CONFIRMATION"`, `"LOW_CONFIDENCE"`, `"AMBIGUOUS"`,
    #: `"NO_MATCH"`, or `"REJECT"`), so a caller can distinguish "no
    #: BusinessRecord created because every provider failed" from "no
    #: BusinessRecord created because the gate blocked it," never
    #: silently conflating the two. `identity_gate_reason` is the
    #: gate's own human-readable explanation, `None` only when the
    #: outcome is `AUTO_ACCEPT` (nothing to explain).
    identity_gate_outcome: str = "AUTO_ACCEPT"
    identity_gate_reason: str | None = None
    #: Atlas Intelligence Sprint 9 (Data Ingestion & Automatic Refresh).
    #: Every `BusinessRecord` this run actually wrote (`new_records` +
    #: `new_versions` combined, in the order ingested) -- `()` by
    #: default so every pre-Sprint-9 caller/test keeps constructing a
    #: valid `RefreshSummary` unchanged. The one real per-document
    #: detail this dataclass previously discarded down to counts only;
    #: `atlas.alpha.ingestion` reads this to classify exactly which
    #: `SourceKind`/lineage changed, never re-deriving it by diffing
    #: the repository a second time.
    changed_records: tuple[BusinessRecord, ...] = field(default_factory=tuple)
    #: The one real wall-clock timestamp this refresh run used for
    #: every document it touched (`atlas.analysis_engine.business_data
    #: .pipeline.ingest`'s own `evaluated_at`) -- `None` only for a
    #: `RefreshSummary` built before this field existed.
    evaluated_at: datetime | None = None


class EnrichmentOutcome(str, Enum):
    """One ticker's outcome within a `BulkEnrichmentSummary` (Internal
    Alpha Fix Sprint 1, IA-001). Deliberately not a numeric score or a
    pass/fail boolean -- four honest, mutually exclusive states, the
    same "categorical, never invented" discipline `RiskStatus`/
    `ConvictionLevel` already establish elsewhere in this codebase."""

    #: `ensure_company_enriched` ran and produced at least one new
    #: record or version -- real progress happened, even if some
    #: providers also failed (provider isolation is unchanged; partial
    #: real data is still real data, matching this codebase's existing
    #: "one provider's failure never blocks another's success"
    #: doctrine).
    ENRICHED = "enriched"
    #: `ensure_company_enriched` returned `None` -- the ticker was
    #: already `assess_data_completeness.is_minimally_complete`; no
    #: provider was called at all.
    SKIPPED_ALREADY_ENRICHED = "skipped_already_enriched"
    #: Every provider ran without raising, but none produced a single
    #: new record -- an honest "no provider can serve this ticker"
    #: result (e.g. a non-US-filer ticker SEC does not cover and Alpha
    #: Vantage has no quote for), never silently retried into a fake
    #: success.
    UNSUPPORTED = "unsupported"
    #: An unexpected exception escaped `ensure_company_enriched` itself
    #: (not a provider-reported failure -- those already surface as
    #: `RefreshSummary.provider_errors` and still count as `ENRICHED`/
    #: `UNSUPPORTED` above). Isolated per-ticker so one broken ticker
    #: can never abort the rest of the batch.
    FAILED = "failed"


@dataclass(frozen=True)
class HoldingEnrichmentResult:
    """One ticker's result within a bulk enrichment run. `detail` is
    the human-readable reason for `UNSUPPORTED`/`FAILED` (provider
    error text or exception message); always `None` for `ENRICHED`/
    `SKIPPED_ALREADY_ENRICHED`, where there is nothing to explain."""

    ticker: str
    outcome: EnrichmentOutcome
    detail: str | None


@dataclass(frozen=True)
class BulkEnrichmentSummary:
    """The deterministic report for one bulk-enrichment run across many
    tickers (Internal Alpha Fix Sprint 1, Part 1). Every ticker given
    to `enrich_holdings` appears here exactly once, in the same order
    it was given -- no ticker is ever silently dropped."""

    results: tuple[HoldingEnrichmentResult, ...]

    @property
    def enriched_count(self) -> int:
        return sum(1 for r in self.results if r.outcome is EnrichmentOutcome.ENRICHED)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.results if r.outcome is EnrichmentOutcome.SKIPPED_ALREADY_ENRICHED)

    @property
    def unsupported_count(self) -> int:
        return sum(1 for r in self.results if r.outcome is EnrichmentOutcome.UNSUPPORTED)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.outcome is EnrichmentOutcome.FAILED)
