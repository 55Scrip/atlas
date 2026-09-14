"""Backfill historical market-data provenance onto the observations Atlas
already holds (Historical Market-Data Backfill).

Monthly price snapshots written before Historical Market-Data Provenance
carry only the adjusted close; statements carry a period-end share count
without the filing it came from. This fills in what the providers can now
say about those same observations -- and nothing else:

- **Prices** (`--prices`): each stored month is re-fetched and gains its
  raw close, dividend and explicit price basis. Only months Atlas already
  holds are touched -- the command asks the provider for exactly those
  months, and a month the provider maps elsewhere is held, never added --
  so no new observation, and therefore no new valuation epoch, can appear.
  A month whose adjusted close the provider has since revised (a dividend
  after it was fetched) is **held**, not written: accepting a revision is
  a data refresh, not provenance, and it would move historical yields.
  `--accept-price-revisions` (named `--tickers` only) is the operator's
  explicit decision to take such a revision after reviewing it; it is
  honoured only when a company's revision is one uniform, dividend-sized
  rescale of every revised month, and the stored versions stay.
- **SEC share counts** (`--sec`): a statement gains the filing its stored
  count came from and what the first filing reported, through
  `pipeline.enrich_provenance` -- a new version with the same content
  hash, refused if anything but provenance would change. A statement
  whose stored content no longer matches what the SEC now returns (a
  restatement, or concepts a later adapter captures) is held: bringing that
  content in is a data refresh, not provenance.

**One provider request per company, and only for work that is pending.**
Completion is read from the stored records before any request is planned
(`is_price_complete`), so a finished company costs nothing and a re-run
resumes. Prices use the currency and share count Atlas already holds --
the same carry-forward `fetch_price_only` uses -- so `OVERVIEW` is never
called: one `TIME_SERIES_MONTHLY_ADJUSTED` request, not two, and each new
version differs from the stored one only in what the monthly bar says.

**No new path to the network.** Providers come from `business_data_refresh`'s
own composition (`get_default_business_data_providers`), whose Alpha
Vantage client counts every request in the persisted daily counter; the
same counter, behind `ProviderBudgetGate`, is checked before each request,
`--max-calls` caps the run below the daily allowance, and
`DailyQuotaExhausted` stops it. SEC requests are keyless and uncounted;
the plan states how many there will be.

**Which companies.** Only a company whose Case can later support a
historical market capitalisation: an applicable FCF-yield valuation, a
domestic (10-K) filer, one priced security per issuer, and at least
`_MINIMUM_SHARE_COUNTS` stored period-end counts (`classify`). Foreign
listings and banks are refused outright; a company with prices but no share
counts is refused unless `--allow-price-only`. A security of a multi-class
issuer is refused unless `--allow-multi-class` names it (`--tickers`, prices
only): its monthly bars are its own, but its issuer-level share count fits
no single price -- only security-level class counts
(`backfill_security_share_evidence`) can pair with them.

Creates no Case, no decision and no methodology change; valuation keeps
reading `share_price`, which no version written here changes.

    python -m atlas.dev.backfill_market_data_provenance [--database PATH]
        [--tickers AAPL,MSFT] [--prices] [--sec] [--max-calls N]
        [--allow-price-only] [--allow-multi-class] [--dry-run]
        [--save-fetched FILE | --from-fetched FILE]

`--save-fetched`/`--from-fetched` split one run's requests from its writes:
fetch once (applying to a database copy for rehearsal), then apply the
same saved documents to the live database with no further request.
"""
from __future__ import annotations

import argparse
import json
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path

from sqlalchemy import create_engine, select

from atlas.alpha.business_data_refresh.api.dependencies import get_default_business_data_providers
from atlas.alpha.business_data_refresh.provider_state import (
    ALPHA_VANTAGE_PROVIDER_NAME,
    ProviderAvailabilityStore,
    ProviderBudgetGate,
)
from atlas.alpha.business_data_refresh.quota import AlphaVantageQuotaTracker
from atlas.alpha.business_data_refresh.repository import SqlAlchemyBusinessRecordRepository
from atlas.alpha.business_data_refresh.table import business_record_table, create_business_record_table
from atlas.analysis_engine.business_data.models import BusinessRecord, RawBusinessDocument
from atlas.analysis_engine.business_data.pipeline import (
    SHARE_COUNT_PROVENANCE_KEYS,
    IngestedRecord,
    ProvenanceEnrichmentRefused,
    enrich_provenance,
    ingest,
)
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.business_data.versioning import compute_lineage_id, latest_versions
from atlas.analysis_engine.valuation.applicability import fcf_yield_applies
from atlas.analysis_engine.valuation.facts import PriceBasis, market_price_provenance
from atlas.core.infrastructure.api.decision.dependencies import get_decision_engine
from atlas.core.infrastructure.config.database import resolve_database_path
from atlas.dev.guard import ensure_development_environment

__all__ = [
    "CORE",
    "classify",
    "is_price_complete",
    "plan_prices",
    "apply_prices",
    "plan_sec",
    "apply_sec",
    "classify_price_revision",
    "select_companies",
    "fetch",
    "apply",
    "save_fetched",
    "load_fetched",
    "main",
]

#: Stored period-end share counts below which a company has no plausible
#: path to a historical market capitalisation; its prices alone are
#: `price_only`.
_MINIMUM_SHARE_COUNTS = 3

CORE = "core"
PRICE_ONLY = "price_only"
MULTI_CLASS = "multi_class"
REFUSED = (MULTI_CLASS, "foreign_listing", "not_applicable", "no_price_history", "no_statements")

_MONTHLY_ENDPOINT = "function=TIME_SERIES_MONTHLY_ADJUSTED"
#: What a monthly bar adds on top of the price valuation reads; everything
#: else in a re-fetched month must repeat the stored version exactly.
PRICE_PROVENANCE_KEYS = frozenset({"raw_close", "dividend_amount", "price_basis"})


def _redacted(error: Exception) -> str:
    """An error as printable text: never a key, even inside a quoted URL."""
    return re.sub(r"apikey=[^&\s'\"]+", "apikey=***", str(error))[:120]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _monthly(records: Iterable[BusinessRecord]) -> list[BusinessRecord]:
    return [
        r for r in records
        if r.document_type is SourceKind.MARKET_DATA_SNAPSHOT and _MONTHLY_ENDPOINT in (r.source_reference or "")
    ]


def _statements(records: Iterable[BusinessRecord]) -> list[BusinessRecord]:
    return [r for r in records if r.document_type is SourceKind.FINANCIAL_STATEMENT]


def classify(ticker: str, records: tuple[BusinessRecord, ...], *, issuer_companies: Callable[[str], set[str]]) -> str:
    """Generic, from the company's own stored records -- never a list of
    names. `issuer_companies(issuer_id)` names every company Atlas files
    under that issuer: more than one is a multi-class (or multi-listing)
    issuer whose issuer-level share count fits no single price."""
    heads = latest_versions(records)
    statements = _statements(heads)
    if not statements:
        return "no_statements"
    # Every version, not only the latest: a later version of a statement
    # need not repeat the issuer an earlier one was filed under.
    issuers = {r.canonical_issuer_id for r in records if r.canonical_issuer_id}
    if any(issuer_companies(issuer) - {ticker} for issuer in issuers):
        return MULTI_CLASS
    if any(r.metadata.get("sec_form") != "10-K" for r in statements):
        return "foreign_listing"
    industry = next((r.metadata.get("industry") for r in heads if r.document_type is SourceKind.COMPANY_PROFILE), None)
    if fcf_yield_applies(industry) is False:
        return "not_applicable"
    if not _monthly(heads):
        return "no_price_history"
    if sum(1 for r in statements if r.metadata.get("shares_outstanding")) < _MINIMUM_SHARE_COUNTS:
        return PRICE_ONLY
    return CORE


def is_price_complete(record: BusinessRecord) -> bool:
    """A monthly snapshot carrying everything the provider now reports:
    a recorded adjusted basis, the raw close, and the dividend field
    (an explicit provider zero counts; a missing field does not)."""
    provenance = market_price_provenance(record)
    return (
        provenance is not None
        and provenance.basis_recorded
        and provenance.basis is PriceBasis.SPLIT_AND_DIVIDEND_ADJUSTED
        and provenance.raw_close is not None
        and provenance.dividend_amount is not None
    )


@dataclass(frozen=True)
class PricePlan:
    ticker: str
    category: str
    months: int
    complete: int
    pending: tuple[date, ...]
    known_currency: str | None = None
    known_shares_outstanding: float | None = None
    refusal: str | None = None

    @property
    def calls(self) -> int:
        return 1 if self.pending and self.refusal is None else 0


def plan_prices(
    ticker: str,
    records: tuple[BusinessRecord, ...],
    *,
    category: str,
    allow_price_only: bool = False,
    allow_multi_class: bool = False,
) -> PricePlan:
    heads = _monthly(latest_versions(records))
    complete = [r for r in heads if is_price_complete(r)]
    pending = tuple(sorted(r.period_end for r in heads if not is_price_complete(r)))
    base = PricePlan(ticker=ticker, category=category, months=len(heads), complete=len(complete), pending=pending)
    if category == MULTI_CLASS and not allow_multi_class:
        return replace(base, refusal="multi_class (name it with --allow-multi-class)")
    if category in REFUSED and category != MULTI_CLASS:
        return replace(base, refusal=category)
    if category == PRICE_ONLY and not allow_price_only:
        return replace(base, refusal="price_only (pass --allow-price-only)")
    currencies = {r.metadata.get("currency") for r in heads}
    shares = {r.metadata.get("shares_outstanding") for r in heads}
    if len(currencies) != 1 or len(shares) != 1 or None in currencies:
        return replace(base, refusal="stored months disagree on currency or share count")
    return replace(base, known_currency=currencies.pop(), known_shares_outstanding=shares.pop())


@dataclass
class PriceOutcome:
    new_versions: int = 0
    already_complete: int = 0
    held_revisions: list[tuple[str, float, float]] = field(default_factory=list)
    held_new_observations: list[str] = field(default_factory=list)
    #: Months written because the provider's revised adjusted close was
    #: explicitly accepted (`accept_revisions`): (month, stored, accepted).
    accepted_revisions: list[tuple[str, float, float]] = field(default_factory=list)
    revision: "PriceRevision | None" = None


#: The provider quotes adjusted closes to four decimals: two independently
#: rounded quotes of one rescaled price differ from the exact rescale by at
#: most half a unit in the fourth decimal each.
_QUOTE_ROUNDING = 0.5e-4
#: The largest one-year dividend-drift step of the adjusted series -- the
#: same band `alpha.investment_case.historical_market_cap.SMALL_STEP` draws
#: (pinned equal by a test; not imported, so the descriptive module keeps
#: its closed set of importers).
DIVIDEND_DRIFT_STEP = 1.06
#: A revision with every month within this of one factor is near-uniform:
#: economically one rescale, but beyond what quote rounding explains.
NEAR_UNIFORM_TOLERANCE = 0.001


class RevisionKind(str, Enum):
    UNIFORM_RESCALE = "uniform_rescale"
    NEAR_UNIFORM_RESCALE = "near_uniform_rescale"
    NON_UNIFORM_REVISION = "non_uniform_revision"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class PriceRevision:
    """How one company's revised adjusted closes relate to the stored ones.
    A later dividend rescales every earlier adjusted close by one factor
    below 1; nothing else about the stored months changes."""

    kind: RevisionKind
    months: int
    factor: float | None
    min_ratio: float | None
    max_ratio: float | None
    max_residual: float | None
    dividend_consistent: bool

    @property
    def acceptable(self) -> bool:
        return self.kind is RevisionKind.UNIFORM_RESCALE and self.dividend_consistent


def classify_price_revision(pairs: list[tuple[float, float]]) -> PriceRevision:
    """`pairs` are (stored, revised) adjusted closes for every revised month
    of one company. Uniform when each revised quote equals one factor times
    the stored quote within quote rounding. `dividend_consistent` says only
    that the factor has the direction and size a later dividend adjustment
    can have -- it lowers the history by no more than one dividend-drift
    step (`DIVIDEND_DRIFT_STEP`); a split-sized or upward
    rescale never passes. It does not attribute the cause."""
    pairs = [(old, new) for old, new in pairs if old > 0 and new > 0]
    if len(pairs) < 2:
        return PriceRevision(RevisionKind.AMBIGUOUS, len(pairs), None, None, None, None, False)
    ratios = sorted(new / old for old, new in pairs)
    # Least squares on the quotes themselves: rounding is absolute (four
    # decimals), so a $0.30 quote's ratio is hundreds of times noisier than
    # a $170 one's -- a median of ratios would let the noisy ones decide.
    factor = sum(old * new for old, new in pairs) / sum(old * old for old, _ in pairs)
    residuals = [abs(new - factor * old) - _QUOTE_ROUNDING * (1 + factor) for old, new in pairs]
    if max(residuals) <= 1e-12:
        kind = RevisionKind.UNIFORM_RESCALE
    elif max(abs(r / factor - 1) for r in ratios) <= NEAR_UNIFORM_TOLERANCE:
        kind = RevisionKind.NEAR_UNIFORM_RESCALE
    else:
        kind = RevisionKind.NON_UNIFORM_REVISION
    return PriceRevision(
        kind=kind, months=len(pairs), factor=factor, min_ratio=ratios[0], max_ratio=ratios[-1],
        max_residual=max(abs(new - factor * old) for old, new in pairs),
        dividend_consistent=1 / DIVIDEND_DRIFT_STEP <= factor < 1,
    )


def _lineage(document: RawBusinessDocument) -> str:
    return compute_lineage_id(
        provider_id=document.provider_id,
        source_kind=SourceKind(document.source_kind),
        company=document.company,
        identifier=document.identifier,
    )


def _without(metadata, keys: frozenset[str]) -> dict:
    return {k: v for k, v in metadata.items() if k not in keys}


def apply_prices(
    documents: tuple[RawBusinessDocument, ...],
    records: tuple[BusinessRecord, ...],
    *,
    add: Callable[[BusinessRecord], None],
    evaluated_at: datetime,
    accept_revisions: bool = False,
) -> PriceOutcome:
    """Writes a new version only for a month Atlas already holds, whose
    stored metadata the fetched bar repeats exactly apart from
    `PRICE_PROVENANCE_KEYS`; everything the provider would change is held.

    `accept_revisions` (Held Historical Price Revision Acceptance) is the
    operator's explicit decision to take the provider's revised adjusted
    close as well -- a real valuation-data revision, not provenance. It is
    honoured only for a revision that changes nothing but `share_price` and
    is, across every revised month of the company, one uniform dividend-
    sized rescale (`classify_price_revision`); any other revision stays
    held. The stored version is kept: the accepted one supersedes it."""
    outcome = PriceOutcome()
    known = list(records)
    heads = {r.lineage_id: r for r in _monthly(latest_versions(records))}
    pending: list[tuple[RawBusinessDocument, BusinessRecord]] = []
    revised: list[tuple[RawBusinessDocument, BusinessRecord]] = []
    for document in documents:
        head = heads.get(_lineage(document))
        if head is None:
            outcome.held_new_observations.append(document.identifier)
            continue
        if is_price_complete(head):
            outcome.already_complete += 1
            continue
        stored = _without(head.metadata, PRICE_PROVENANCE_KEYS)
        fetched = _without(document.metadata, PRICE_PROVENANCE_KEYS)
        if fetched == stored:
            pending.append((document, head))
            continue
        if _without(fetched, {"share_price"}) == _without(stored, {"share_price"}):
            revised.append((document, head))
            continue
        outcome.held_revisions.append(
            (head.period_end.isoformat(), head.metadata.get("share_price"), document.metadata.get("share_price"))
        )
    if revised:
        outcome.revision = classify_price_revision(
            [(h.metadata["share_price"], d.metadata["share_price"]) for d, h in revised]
        )
        if accept_revisions and outcome.revision.acceptable:
            outcome.accepted_revisions.extend(
                (h.period_end.isoformat(), h.metadata["share_price"], d.metadata["share_price"]) for d, h in revised
            )
            pending.extend(revised)
        else:
            outcome.held_revisions.extend(
                (h.period_end.isoformat(), h.metadata["share_price"], d.metadata["share_price"]) for d, h in revised
            )
    for document, head in sorted(pending, key=lambda pair: pair[1].period_end):
        result = ingest(
            document,
            existing_records=tuple(known),
            evaluated_at=evaluated_at,
            canonical_security_id=head.canonical_security_id,
            resolution_version=head.resolution_version,
            identity_resolved_at=head.identity_resolved_at,
            provider_evidence_reference=head.provider_evidence_reference,
        )
        if isinstance(result, IngestedRecord):
            record = replace(result.record, canonical_issuer_id=head.canonical_issuer_id)
            add(record)
            known.append(record)
            outcome.new_versions += 1
    return outcome


@dataclass(frozen=True)
class SecPlan:
    ticker: str
    category: str
    statements: int
    with_count: int
    with_provenance: int
    refusal: str | None = None

    @property
    def pending(self) -> int:
        return self.with_count - self.with_provenance

    @property
    def calls(self) -> int:
        return 1 if self.pending and self.refusal is None else 0


def plan_sec(ticker: str, records: tuple[BusinessRecord, ...], *, category: str) -> SecPlan:
    statements = _statements(latest_versions(records))
    counted = [r for r in statements if r.metadata.get("shares_outstanding")]
    enriched = [r for r in counted if "shares_outstanding_filed" in r.metadata]
    return SecPlan(
        ticker=ticker, category=category, statements=len(statements), with_count=len(counted),
        with_provenance=len(enriched), refusal=category if category != CORE else None,
    )


@dataclass
class SecOutcome:
    enriched: int = 0
    already_complete: int = 0
    no_count: int = 0
    held_content_changed: list[str] = field(default_factory=list)
    held_new_periods: list[str] = field(default_factory=list)


def apply_sec(
    documents: tuple[RawBusinessDocument, ...],
    records: tuple[BusinessRecord, ...],
    *,
    add: Callable[[BusinessRecord], None],
    evaluated_at: datetime,
) -> SecOutcome:
    outcome = SecOutcome()
    heads = {r.lineage_id: r for r in _statements(latest_versions(records))}
    for document in documents:
        if not document.metadata.get("shares_outstanding"):
            outcome.no_count += 1
            continue
        head = heads.get(_lineage(document))
        if head is None:
            outcome.held_new_periods.append(document.identifier)
            continue
        try:
            record = enrich_provenance(
                document, head=head, provenance_keys=SHARE_COUNT_PROVENANCE_KEYS, evaluated_at=evaluated_at
            )
        except ProvenanceEnrichmentRefused:
            outcome.held_content_changed.append(document.identifier)
            continue
        if record is None:
            outcome.already_complete += 1
            continue
        add(record)
        outcome.enriched += 1
    return outcome


def select_companies(named: list[str] | None, categories: dict[str, str], *, allow_price_only: bool) -> list[str]:
    """Named tickers exactly as given (each refused later if ineligible);
    otherwise every core company (and price-only ones only when asked)."""
    if named:
        return list(named)
    wanted = {CORE, PRICE_ONLY} if allow_price_only else {CORE}
    return [t for t in sorted(categories) if categories[t] in wanted]


def _provider(providers, predicate):
    return next((p for p in providers if predicate(p)), None)


def _issuer_companies(engine) -> Callable[[str], set[str]]:
    with engine.connect() as connection:
        rows = connection.execute(
            select(business_record_table.c.canonical_issuer_id, business_record_table.c.company)
            .where(business_record_table.c.canonical_issuer_id.is_not(None))
            .distinct()
        ).all()
    by_issuer: dict[str, set[str]] = {}
    for issuer, company in rows:
        by_issuer.setdefault(issuer, set()).add(company)
    return lambda issuer: by_issuer.get(issuer, set())


def _stored_companies(engine) -> list[str]:
    with engine.connect() as connection:
        rows = connection.execute(select(business_record_table.c.company).distinct()).all()
    return sorted(row[0] for row in rows)


@dataclass
class Fetched:
    """What one run's requests returned, kept apart from where it is
    written: a rehearsal applies it to a database copy and the operator
    applies the very same documents to the live database, so the
    provider is asked once."""

    fetched_at: datetime
    prices: dict[str, tuple[RawBusinessDocument, ...]] = field(default_factory=dict)
    sec: dict[str, tuple[RawBusinessDocument, ...]] = field(default_factory=dict)
    av_requests: int = 0
    stopped: str | None = None


def fetch(
    price_plans: list[PricePlan],
    sec_plans: list[SecPlan],
    *,
    providers,
    gate: ProviderBudgetGate,
    max_calls: int,
    fetched_at: datetime,
) -> Fetched:
    fetched = Fetched(fetched_at=fetched_at)
    prices = _provider(providers, lambda p: hasattr(p, "fetch_historical_snapshots"))
    for plan in price_plans:
        if not plan.calls:
            continue
        if fetched.av_requests >= max_calls:
            fetched.stopped = "max-calls reached"
            break
        if not gate.has_budget():
            fetched.stopped = f"budget gate: {gate.current_state().value}"
            break
        fetched.av_requests += 1
        try:
            fetched.prices[plan.ticker] = prices.fetch_historical_snapshots(
                company_identifier=plan.ticker,
                filing_dates=plan.pending,
                evaluated_at=fetched_at,
                known_currency=plan.known_currency,
                known_shares_outstanding=plan.known_shares_outstanding,
            )
        except Exception as exc:  # noqa: BLE001 -- reported, never silently swallowed
            # Read by exception class name, never by importing the provider
            # package's own error types (the boundary `backfill_transcript_quarters` keeps).
            kind = type(exc).__name__
            print(f"  {plan.ticker:6} {kind}: {_redacted(exc)}")
            if kind == "DailyQuotaExhausted":
                gate.record_daily_exhausted(_redacted(exc))
                fetched.stopped = "provider daily quota exhausted"
                break
    sec = _provider(providers, lambda p: type(p).__name__ == "SecEdgarFundamentalsProvider")
    for plan in sec_plans:
        if not plan.calls:
            continue
        try:
            fetched.sec[plan.ticker] = sec.fetch(company_identifier=plan.ticker, evaluated_at=fetched_at)
        except Exception as exc:  # noqa: BLE001 -- reported, never silently swallowed
            print(f"  {plan.ticker:6} SEC {type(exc).__name__}: {_redacted(exc)}")
    return fetched


def apply(fetched: Fetched, repository: SqlAlchemyBusinessRecordRepository, *, accept_revisions: bool = False) -> None:
    """Every write goes through `repository.add`, with the stored records
    re-read per company, so applying the same documents twice is a no-op."""
    if fetched.prices:
        print("\nprices:")
    for ticker, documents in fetched.prices.items():
        outcome = apply_prices(
            documents, repository.get_by_company(ticker), add=repository.add, evaluated_at=fetched.fetched_at,
            accept_revisions=accept_revisions,
        )
        print(f"  {ticker:6} new versions {outcome.new_versions:3}  already complete {outcome.already_complete:3}  "
              f"accepted revisions {len(outcome.accepted_revisions):3}  held revisions {len(outcome.held_revisions):3}  "
              f"held new {len(outcome.held_new_observations):3}")
        if outcome.revision is not None:
            r = outcome.revision
            print(f"         revision: {r.kind.value}, {r.months} months, factor {r.factor:.6f} "
                  f"(ratios {r.min_ratio:.6f}..{r.max_ratio:.6f}, max residual {r.max_residual:.6f}), "
                  f"{'direction and size of a dividend adjustment (cause not attributed)' if r.dividend_consistent else 'not a dividend-sized downward rescale'}"
                  if r.factor is not None else f"         revision: {r.kind.value}, {r.months} months")
        for month, stored, now in outcome.held_revisions[:3]:
            print(f"         held {month}: stored {stored} -> provider now {now}")
    if fetched.sec:
        print("\nSEC:")
    for ticker, documents in fetched.sec.items():
        outcome = apply_sec(
            documents, repository.get_by_company(ticker), add=repository.add, evaluated_at=fetched.fetched_at
        )
        print(f"  {ticker:6} enriched {outcome.enriched:3}  already complete {outcome.already_complete:3}  "
              f"held (content differs) {len(outcome.held_content_changed):3}  held new periods {len(outcome.held_new_periods):3}")


def _document_json(document: RawBusinessDocument) -> dict:
    return {
        "identifier": document.identifier,
        "company": document.company,
        "source_kind": document.source_kind,
        "published_at": document.published_at.isoformat() if document.published_at else None,
        "provider_id": document.provider_id,
        "raw_reference": document.raw_reference,
        "content_hash": document.content_hash,
        "period_start": document.period_start.isoformat() if document.period_start else None,
        "period_end": document.period_end.isoformat() if document.period_end else None,
        "language": document.language,
        "metadata": dict(document.metadata),
    }


def _document(payload: dict) -> RawBusinessDocument:
    def day(value):
        return date.fromisoformat(value) if value else None

    return RawBusinessDocument(
        identifier=payload["identifier"],
        company=payload["company"],
        source_kind=payload["source_kind"],
        published_at=datetime.fromisoformat(payload["published_at"]) if payload["published_at"] else None,
        provider_id=payload["provider_id"],
        raw_reference=payload["raw_reference"],
        content_hash=payload["content_hash"],
        period_start=day(payload["period_start"]),
        period_end=day(payload["period_end"]),
        language=payload["language"],
        metadata=payload["metadata"],
    )


def save_fetched(fetched: Fetched, path: str) -> None:
    payload = {
        "fetched_at": fetched.fetched_at.isoformat(),
        "av_requests": fetched.av_requests,
        "stopped": fetched.stopped,
        "prices": {t: [_document_json(d) for d in docs] for t, docs in fetched.prices.items()},
        "sec": {t: [_document_json(d) for d in docs] for t, docs in fetched.sec.items()},
    }
    Path(path).write_text(json.dumps(payload, indent=1, sort_keys=True))


def load_fetched(path: str) -> Fetched:
    payload = json.loads(Path(path).read_text())
    return Fetched(
        fetched_at=datetime.fromisoformat(payload["fetched_at"]),
        prices={t: tuple(_document(d) for d in docs) for t, docs in payload["prices"].items()},
        sec={t: tuple(_document(d) for d in docs) for t, docs in payload["sec"].items()},
        # Applying a saved fetch asks the provider nothing.
        av_requests=0,
    )


def main() -> int:
    ensure_development_environment()

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database", default=None, help="Path to the Atlas database (default: the resolved one).")
    parser.add_argument("--tickers", default=None, help="Comma-separated subset; default: every core company.")
    parser.add_argument("--prices", action="store_true", help="Backfill monthly price provenance.")
    parser.add_argument("--sec", action="store_true", help="Backfill SEC share-count provenance.")
    parser.add_argument("--max-calls", type=int, default=13, help="Alpha Vantage requests this run may make.")
    parser.add_argument("--allow-price-only", action="store_true", help="Also backfill prices without share counts.")
    parser.add_argument(
        "--allow-multi-class", action="store_true",
        help="Also backfill prices of the named --tickers' securities of multi-class issuers (prices only).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report the plan and the request cost, fetch nothing.")
    parser.add_argument("--save-fetched", default=None, help="Also write the fetched documents to this JSON file.")
    parser.add_argument("--from-fetched", default=None, help="Apply documents saved by --save-fetched; no provider call.")
    parser.add_argument(
        "--accept-price-revisions", action="store_true",
        help="Also accept the provider's revised adjusted closes for the named --tickers, when each company's "
             "revision is one uniform dividend-sized rescale. A valuation-data revision; off by default.",
    )
    arguments = parser.parse_args()
    if not (arguments.prices or arguments.sec):
        parser.error("choose --prices, --sec or both")
    if arguments.accept_price_revisions and not (arguments.tickers and arguments.prices):
        parser.error("--accept-price-revisions needs --prices and explicit --tickers")
    if arguments.allow_multi_class and not (arguments.tickers and arguments.prices and not arguments.sec):
        parser.error("--allow-multi-class needs --prices (without --sec) and explicit --tickers")

    path = arguments.database or resolve_database_path()
    engine = create_engine(f"sqlite:///{path}", future=True)
    create_business_record_table(engine)
    repository = SqlAlchemyBusinessRecordRepository(engine)
    issuer_companies = _issuer_companies(engine)

    named = [t.strip().upper() for t in arguments.tickers.split(",") if t.strip()] if arguments.tickers else None
    everyone = named or _stored_companies(engine)
    records = {t: repository.get_by_company(t) for t in everyone}
    categories = {t: classify(t, records[t], issuer_companies=issuer_companies) for t in everyone}
    candidates = select_companies(named, categories, allow_price_only=arguments.allow_price_only)

    # The counter the provider's own request hook writes, behind the gate
    # every enrichment path reads -- never the database being backfilled.
    counter_engine = get_decision_engine()
    quota = AlphaVantageQuotaTracker(counter_engine)
    gate = ProviderBudgetGate(quota, ProviderAvailabilityStore(counter_engine), provider_name=ALPHA_VANTAGE_PROVIDER_NAME)

    print(f"database        : {path}")
    print(f"companies       : {len(candidates)} ({', '.join(candidates)})")
    price_plans = [
        plan_prices(t, records[t], category=categories[t], allow_price_only=arguments.allow_price_only,
                    allow_multi_class=arguments.allow_multi_class) for t in candidates
    ] if arguments.prices else []
    sec_plans = [plan_sec(t, records[t], category=categories[t]) for t in candidates] if arguments.sec else []
    if price_plans:
        print("\nprices (monthly snapshots):")
        for p in price_plans:
            note = f"REFUSED: {p.refusal}" if p.refusal else f"{p.calls} request, at most {len(p.pending)} new versions"
            print(f"  {p.ticker:6} {p.category:16} months {p.months:3}  complete {p.complete:3}  pending {len(p.pending):3}  {note}")
    if sec_plans:
        print("\nSEC share-count provenance:")
        for p in sec_plans:
            note = f"REFUSED: {p.refusal}" if p.refusal else f"{p.calls} request, at most {p.pending} new versions"
            print(f"  {p.ticker:6} statements {p.statements:3}  with count {p.with_count:3}  with provenance {p.with_provenance:3}  {note}")
    if price_plans:
        print(f"  total  months {sum(p.months for p in price_plans)}  complete {sum(p.complete for p in price_plans)}  "
              f"pending {sum(len(p.pending) for p in price_plans if not p.refusal)} (refused companies excluded)")
    if sec_plans:
        print(f"  total  with count {sum(p.with_count for p in sec_plans)}  with provenance "
              f"{sum(p.with_provenance for p in sec_plans)}  pending {sum(p.pending for p in sec_plans if not p.refusal)}")
    av_planned = sum(p.calls for p in price_plans)
    sec_planned = sum(p.calls for p in sec_plans)
    print(f"\nAlpha Vantage   : {av_planned} planned (cap {arguments.max_calls}; used today {quota.calls_used_today()}, "
          f"gate {gate.current_state().value})")
    print(f"SEC EDGAR       : {sec_planned} companyfacts + {1 if sec_planned else 0} ticker map (keyless, uncounted)")
    if arguments.dry_run:
        print("\n[dry run] no provider call made, nothing written.")
        return 0

    if arguments.from_fetched:
        fetched = load_fetched(arguments.from_fetched)
        print(f"\napplying documents fetched at {fetched.fetched_at.isoformat()} from {arguments.from_fetched} "
              "-- no provider call")
    else:
        fetched = fetch(
            price_plans, sec_plans, providers=get_default_business_data_providers(), gate=gate,
            max_calls=arguments.max_calls, fetched_at=_utc_now(),
        )
        if arguments.save_fetched:
            save_fetched(fetched, arguments.save_fetched)
            print(f"\nfetched documents saved to {arguments.save_fetched}")
    apply(fetched, repository, accept_revisions=arguments.accept_price_revisions)
    print(f"\nAlpha Vantage requests made: {fetched.av_requests}" + (f" -- stopped: {fetched.stopped}" if fetched.stopped else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
