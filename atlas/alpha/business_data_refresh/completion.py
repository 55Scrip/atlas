"""Provider-aware enrichment completion model (Automatic Enrichment
Coverage, Implementation Phase 1).

Replaces `ensure_company_enriched`'s own prior gate -- `assess_data
_completeness(existing).is_minimally_complete` (`has_profile or
has_statements`) -- which treats any one successful provider as
permanent, whole-ticker "done," with no way to tell "this specific
provider never got a chance to run" from "this specific provider ran
and will never succeed for this ticker." A ticker with only SEC
fundamentals stayed permanently unenriched for Alpha Vantage identity;
a ticker with only Alpha Vantage identity stayed permanently
unenriched for SEC fundamentals -- confirmed the actual, observed
shape of the real 32-case investigation this sprint acts on.

**Two required provider signals only, this sprint** -- exactly the two
the governing investigation named: Alpha Vantage's identity leg
(`COMPANY_PROFILE`) and SEC's fundamentals leg (`FINANCIAL_STATEMENT`).
Not a generic, arbitrary-provider-count model: asset-type-based
applicability (would a *third* provider, or *no* provider, genuinely
apply to a given ticker -- ETFs, crypto, private companies) is
explicitly out of this sprint's scope (see the investigation's own
"Explicitly out of scope" list). Both signals are therefore always
`REQUIRED` for every ticker this sprint evaluates; `_REQUIRED_PROVIDERS`
is the one place a future sprint narrows that per asset type.

**Reuses `atlas.alpha.ingestion.models.IngestionResult.provider_failures`
rather than inventing new persistence** -- this module never touches a
repository itself; `known_provider_failures` is a plain tuple its
caller (`business_data_refresh.service.ensure_company_enriched`,
threaded from `IngestionResult`) already resolved. Kept dependency-free
of `atlas.alpha.ingestion` on purpose: `atlas.alpha.ingestion` already
depends on `atlas.alpha.business_data_refresh` (for `RefreshSummary`),
so the reverse dependency would be circular; every caller that already
depends on both packages (`AlphaPortfolioService`/`AlphaWatchlistService`
`_trigger_enrichment`, `enrich_holdings`) is responsible for the one
`ingestion_result_repository.get_by_ticker(...)` lookup and passing its
`.provider_failures` through.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from atlas.alpha.business_data_refresh.models import ProviderFailure
from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind

__all__ = [
    "ProviderFailureClassification",
    "classify_provider_failure",
    "ProviderCompletionStatus",
    "ProviderCompletion",
    "EnrichmentCompletion",
    "assess_enrichment_completion",
]


class ProviderFailureClassification(str, Enum):
    """Whether a recorded `ProviderFailure` is worth retrying. Not part
    of `ProviderCompletionStatus` below -- that enum also needs
    `SUCCEEDED`/`NOT_YET_ATTEMPTED`, states this one has no opinion
    about."""

    TRANSIENT = "transient"
    UNSUPPORTED = "unsupported"


#: Every kind whose own name means "this provider genuinely has nothing
#: for this ticker, and never will" -- `atlas.business_data_providers
#: .errors`'s own taxonomy, read by class name only (never a raised
#: instance): the ticker/filer itself is the obstacle, not the provider
#: call. `RateLimited`/`ProviderUnavailable`/`ProviderTimeout` are
#: deliberately absent -- those name a *provider-call* problem, not a
#: *this-ticker* one, and belong in the transient default below.
_UNSUPPORTED_KINDS = frozenset({"CompanyNotFound", "AmbiguousSymbol", "UnsupportedUnit"})

#: The one provider_id this sprint's Alpha Vantage identity leg
#: (`fetch_company_profile`) can ever report a failure under --
#: `AlphaVantageMarketDataProvider._resolved_api_key` is the *only*
#: exception source in `fetch_company_profile`'s own body (confirmed by
#: reading it: a missing/unset ticker never raises there, it returns
#: `()`), and it always raises `MissingRequiredField` for exactly one
#: reason -- `ALPHA_VANTAGE_API_KEY` is not configured. That is a
#: deployment-config gap, not a per-ticker fact, so it must never
#: classify the same way SEC's own `MissingRequiredField` (no CIK
#: match, no us-gaap facts -- a genuine per-ticker absence) does.
_ALPHA_VANTAGE_PROFILE_PROVIDER_ID = "AlphaVantageMarketDataProvider.fetch_company_profile"


def classify_provider_failure(*, provider_id: str, kind: str) -> ProviderFailureClassification:
    """Pure, deterministic. `kind` is `ProviderFailure.kind` -- the
    raised exception's own class name, `""` for a `ProviderFailure`
    built before this field existed (classifies as `TRANSIENT`, the
    safe default: retry rather than silently give up on old data)."""
    if provider_id == _ALPHA_VANTAGE_PROFILE_PROVIDER_ID and kind == "MissingRequiredField":
        return ProviderFailureClassification.TRANSIENT
    if kind in _UNSUPPORTED_KINDS:
        return ProviderFailureClassification.UNSUPPORTED
    if kind == "MissingRequiredField":
        # Every other MissingRequiredField (SEC: no CIK match, or no
        # us-gaap facts for a foreign-private-issuer 20-F filer) is a
        # genuine, per-ticker structural absence.
        return ProviderFailureClassification.UNSUPPORTED
    # ProviderUnavailable/ProviderTimeout/RateLimited/
    # MalformedProviderResponse/an unrecognized or empty kind: none of
    # these say "this ticker can never be served" -- treated as
    # transient, retry-worthy.
    return ProviderFailureClassification.TRANSIENT


class ProviderCompletionStatus(str, Enum):
    """One required provider's own state for one ticker -- never
    collapsed into a whole-ticker boolean (that collapse is exactly
    what `is_minimally_complete` got wrong)."""

    SUCCEEDED = "succeeded"
    NOT_YET_ATTEMPTED = "not_yet_attempted"
    FAILED_TRANSIENT = "failed_transient"
    FAILED_UNSUPPORTED = "failed_unsupported"


@dataclass(frozen=True)
class ProviderCompletion:
    document_kind: SourceKind
    provider_id: str
    """The success-side identifier -- `BusinessRecord.provider_id`'s own
    value (e.g. `"alpha_vantage"`, `"sec_edgar"`), not the failure-side
    `TypeName.method_name` format `ProviderFailure.provider_id` uses --
    an existing inconsistency between the two vocabularies this module
    bridges internally, never exposed to a caller as something to
    reconcile itself."""
    status: ProviderCompletionStatus


@dataclass(frozen=True)
class _RequiredProvider:
    document_kind: SourceKind
    success_provider_id: str
    failure_provider_id: str


#: This sprint's exactly-two required signals -- see module docstring.
_REQUIRED_PROVIDERS: tuple[_RequiredProvider, ...] = (
    _RequiredProvider(
        document_kind=SourceKind.COMPANY_PROFILE,
        success_provider_id="alpha_vantage",
        failure_provider_id=_ALPHA_VANTAGE_PROFILE_PROVIDER_ID,
    ),
    _RequiredProvider(
        document_kind=SourceKind.FINANCIAL_STATEMENT,
        success_provider_id="sec_edgar",
        failure_provider_id="SecEdgarFundamentalsProvider",
    ),
)


@dataclass(frozen=True)
class EnrichmentCompletion:
    """One ticker's complete, provider-aware picture -- always names
    every required provider, satisfied or not (the same "always name
    every member" discipline `MandatoryCoreAssessment`/
    `BusinessAnalysisResult` already establish elsewhere in this
    codebase)."""

    ticker: str
    providers: tuple[ProviderCompletion, ...]

    def status_for(self, document_kind: SourceKind) -> ProviderCompletionStatus:
        return next(p.status for p in self.providers if p.document_kind is document_kind)

    @property
    def is_fully_complete(self) -> bool:
        return all(p.status is ProviderCompletionStatus.SUCCEEDED for p in self.providers)

    @property
    def has_retryable_work(self) -> bool:
        """`True` iff at least one required provider is either not yet
        attempted or failed transiently -- `ensure_company_enriched`'s
        own replacement gate: call `refresh_company_data` again exactly
        when this is `True`, never otherwise (an unsupported-classified
        provider is deliberately excluded here -- Requirement 8's own
        "not retried as though it were a transient failure")."""
        return any(
            p.status in (ProviderCompletionStatus.NOT_YET_ATTEMPTED, ProviderCompletionStatus.FAILED_TRANSIENT)
            for p in self.providers
        )


def assess_enrichment_completion(
    ticker: str,
    business_records: tuple[BusinessRecord, ...],
    known_provider_failures: tuple[ProviderFailure, ...] = (),
) -> EnrichmentCompletion:
    """Deterministic: identical inputs always produce an identical
    `EnrichmentCompletion`. `business_records` decides `SUCCEEDED`
    first and always -- a real, already-persisted record for a
    required `document_kind` outranks any failure history for that
    same provider (a later, out-of-band success -- e.g. a manual CLI
    run -- must never be shadowed by a stale recorded failure)."""
    completions = []
    for required in _REQUIRED_PROVIDERS:
        succeeded = any(record.document_type is required.document_kind for record in business_records)
        if succeeded:
            status = ProviderCompletionStatus.SUCCEEDED
        else:
            failure = next(
                (f for f in known_provider_failures if f.provider_id == required.failure_provider_id), None
            )
            if failure is None:
                status = ProviderCompletionStatus.NOT_YET_ATTEMPTED
            elif classify_provider_failure(provider_id=failure.provider_id, kind=failure.kind) is (
                ProviderFailureClassification.UNSUPPORTED
            ):
                status = ProviderCompletionStatus.FAILED_UNSUPPORTED
            else:
                status = ProviderCompletionStatus.FAILED_TRANSIENT
        completions.append(
            ProviderCompletion(
                document_kind=required.document_kind, provider_id=required.success_provider_id, status=status
            )
        )
    return EnrichmentCompletion(ticker=ticker, providers=tuple(completions))
