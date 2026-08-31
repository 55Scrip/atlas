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
    distinction, preserved end to end.

    `kind` (Automatic Enrichment Coverage, Implementation Phase 1)
    is the raised exception's own class name (e.g. `"CompanyNotFound"`,
    `"MissingRequiredField"`, `"ProviderUnavailable"`) -- the one piece
    of information `refresh_company_data`'s own `except Exception as
    exc:` handlers already have in scope but, before this field
    existed, discarded down to `str(exc)` alone.
    `completion.classify_provider_failure` reads this to distinguish a
    genuinely unsupported ticker/filer from a transient, retry-worthy
    failure -- a distinction `error`'s free-text message alone cannot
    make reliably. Defaults to `""` so every pre-existing direct
    construction of this type (tests, older call sites) stays valid;
    `""` classifies the same as an unrecognized kind (transient)."""

    provider_id: str
    error: str
    kind: str = ""


class EnrichmentDepth(str, Enum):
    """How far one `refresh_company_data` run is allowed to go
    (Calibration Phase 8B -- Minimal Enrichment Architecture).

    The measured cost of a full run is **4 Alpha Vantage calls** per
    company (`OVERVIEW`, `GLOBAL_QUOTE`, `TIME_SERIES_MONTHLY_ADJUSTED`,
    `EARNINGS_CALL_TRANSCRIPT`) plus SEC's own keyless, un-quota'd
    calls. Only the *first* of those four decides whether Atlas can
    analyse the company at all: `OVERVIEW` is the sole source of the
    identity candidates `CanonicalSecurityIdentityGate` needs, and the
    same single response also carries sector, industry, exchange,
    currency and company name -- the entire minimal coverage model.

    So "can this company be analysed?" costs exactly **one** provider
    call, and the existing pipeline already makes that call first. This
    enum exists to let a caller *stop there*, rather than to add a new
    fetch strategy.

    `FULL` is the default everywhere and reproduces the pre-8B
    behaviour byte-for-byte -- no existing caller changes.
    """

    #: Identity + company profile only. Establishes coverage
    #: (`SUPPORTED` / `UNSUPPORTED`) and nothing else. 1 Alpha Vantage
    #: call, 0 SEC calls.
    MINIMAL = "minimal"
    #: Everything `MINIMAL` does, plus the two stages that need no
    #: further Alpha Vantage budget beyond one quote: SEC fundamentals
    #: and the current market snapshot. Deliberately excludes the two
    #: purely-historical stages.
    STANDARD = "standard"
    #: Every stage, including historical market snapshots and earnings
    #: call transcripts. The default; unchanged behaviour.
    FULL = "full"


#: Which stages each depth is allowed to run, in pipeline order. Read by
#: `service.refresh_company_data` only -- a stage name here is never a
#: provider name, so adding a provider never touches this table.
_STAGES_BY_DEPTH: dict[EnrichmentDepth, frozenset[str]] = {
    EnrichmentDepth.MINIMAL: frozenset({"profile"}),
    EnrichmentDepth.STANDARD: frozenset({"profile", "fundamentals"}),
    EnrichmentDepth.FULL: frozenset({"profile", "fundamentals", "historical", "transcripts"}),
}


def stage_allowed(depth: EnrichmentDepth, stage: str) -> bool:
    """Pure and total: an unknown stage name is never allowed, rather
    than defaulting to permitted."""
    return stage in _STAGES_BY_DEPTH.get(depth, frozenset())


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
    #: Calibration Phase 8B. The depth this run was asked for --
    #: `FULL` for every pre-8B caller, so an existing `RefreshSummary`
    #: keeps meaning exactly what it meant before.
    depth: EnrichmentDepth = EnrichmentDepth.FULL
    #: Calibration Phase 8B. The stages this run actually completed, in
    #: order. A caller compares this against `depth` to tell "this run
    #: did everything it was asked to" from "this run stopped early" --
    #: without re-deriving it from record counts.
    completed_stages: tuple[str, ...] = field(default_factory=tuple)
    #: Calibration Phase 8B. `True` when this run stopped before
    #: finishing its requested depth because the provider budget was
    #: exhausted mid-company. Never an error and never a partial
    #: corruption: every stage that *did* run is fully ingested and
    #: persisted, and the untouched stages remain genuinely
    #: `NOT_YET_ATTEMPTED`, so a later run resumes them normally.
    stopped_for_budget: bool = False


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
    #: Zero-Effort Portfolio Onboarding: the shared Alpha Vantage daily
    #: quota was already exhausted before this ticker's turn, so it was
    #: never attempted -- an honest, calm deferral (retried once quota
    #: resets) rather than letting it hit a live provider rate-limit
    #: error and surface as a confusing `FAILED`/`UNSUPPORTED`.
    QUOTA_DEFERRED = "quota_deferred"


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

    @property
    def quota_deferred_count(self) -> int:
        return sum(1 for r in self.results if r.outcome is EnrichmentOutcome.QUOTA_DEFERRED)
