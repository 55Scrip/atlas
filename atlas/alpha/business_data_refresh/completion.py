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
    "CoverageClassification",
    "CoverageState",
    "classify_coverage",
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


class CoverageClassification(str, Enum):
    """Calibration Phase 8B, Phase 9 -- the one word Atlas uses to say
    what it can do with a company, and the whole point of separating
    coverage from depth.

    Deliberately derived from `EnrichmentCompletion` above rather than
    stored anywhere: this is a *view* of the provider states Atlas
    already tracks, not a second, independently-mutable lifecycle that
    could drift out of agreement with them (Phase 3's own "avoid
    introducing duplicate state systems").

    The four states answer four genuinely different questions, and no
    two of them may ever collapse into a shared "unknown":

    - `SUPPORTED` -- every required provider succeeded. Atlas has what
      it needs; nothing is outstanding.
    - `DEEP_ANALYSIS_PENDING` -- identity and profile resolved, so Atlas
      *can* analyse this company and every coverage-dependent surface
      may render immediately, but at least one deeper signal is still
      being collected. This is the state the Minimal Enrichment
      Architecture makes common and useful: coverage now, depth later.
    - `TEMPORARILY_INCOMPLETE` -- Atlas cannot yet say whether the
      company is supported, but the obstacle is retryable (never
      attempted, a transient provider failure, or an exhausted daily
      budget). Trying again later is genuinely worthwhile.
    - `UNSUPPORTED` -- identity itself failed in a way classified
      permanent for this ticker. Retrying cannot help; only a new
      provider could.
    """

    SUPPORTED = "supported"
    DEEP_ANALYSIS_PENDING = "deep_analysis_pending"
    TEMPORARILY_INCOMPLETE = "temporarily_incomplete"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class CoverageState:
    """A classification plus the reason for it, always together --
    `classification` alone would reintroduce exactly the "one word
    meaning several things" problem this sprint removes. `reason` names
    the *cause*, in Phase 8's own failure vocabulary, never a generic
    "missing"."""

    ticker: str
    classification: CoverageClassification
    reason: str
    completion: EnrichmentCompletion

    @property
    def can_analyse(self) -> bool:
        """`True` when coverage-dependent surfaces (Portfolio,
        Watchlist, Daily Brief, Investment Case) may render this
        company immediately. Deliberately `True` for
        `DEEP_ANALYSIS_PENDING` -- that is the entire point of the
        staged architecture."""
        return self.classification in (
            CoverageClassification.SUPPORTED,
            CoverageClassification.DEEP_ANALYSIS_PENDING,
        )


def classify_coverage(completion: EnrichmentCompletion) -> CoverageState:
    """Pure and deterministic. Reads only the already-computed
    per-provider states, so it can never disagree with them.

    Identity (`COMPANY_PROFILE`) is evaluated first and decides the
    branch, because it is the one signal that determines whether Atlas
    can say anything at all: it is the sole source of the candidates
    `CanonicalSecurityIdentityGate` needs, and the same single provider
    response carries the whole minimal coverage model (name, exchange,
    currency, country, sector, industry).
    """
    profile = completion.status_for(SourceKind.COMPANY_PROFILE)
    statements = completion.status_for(SourceKind.FINANCIAL_STATEMENT)

    if profile is ProviderCompletionStatus.FAILED_UNSUPPORTED:
        return CoverageState(
            ticker=completion.ticker,
            classification=CoverageClassification.UNSUPPORTED,
            reason="No configured provider recognises this ticker, and the failure is permanent for it.",
            completion=completion,
        )
    if profile is not ProviderCompletionStatus.SUCCEEDED:
        reason = (
            "Identity resolution has not been attempted yet."
            if profile is ProviderCompletionStatus.NOT_YET_ATTEMPTED
            else "Identity resolution failed for a retryable reason (provider or budget), not a permanent one."
        )
        return CoverageState(
            ticker=completion.ticker,
            classification=CoverageClassification.TEMPORARILY_INCOMPLETE,
            reason=reason,
            completion=completion,
        )

    if statements is ProviderCompletionStatus.SUCCEEDED:
        return CoverageState(
            ticker=completion.ticker,
            classification=CoverageClassification.SUPPORTED,
            reason="Identity, profile and financial statements are all present.",
            completion=completion,
        )
    if statements is ProviderCompletionStatus.FAILED_UNSUPPORTED:
        # Identity is known, so Atlas can analyse the company as far as
        # its data allows -- but no retry will ever add financials.
        # Named as such rather than left "pending" forever, which would
        # imply work still in progress that will never happen.
        return CoverageState(
            ticker=completion.ticker,
            classification=CoverageClassification.SUPPORTED,
            reason=(
                "Identity and profile resolved. No configured provider files financial statements "
                "for this company, permanently -- analysis proceeds without them."
            ),
            completion=completion,
        )
    return CoverageState(
        ticker=completion.ticker,
        classification=CoverageClassification.DEEP_ANALYSIS_PENDING,
        reason="Identity and profile resolved; financial statements are still being collected.",
        completion=completion,
    )
