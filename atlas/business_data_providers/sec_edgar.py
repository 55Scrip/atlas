"""SEC EDGAR fundamentals provider (ATLAS-031, Phase 3/6).

Chosen after a live Phase 1 audit of the realistic alternatives: it is
official, free, requires no API key (only a descriptive `User-Agent`
per SEC's fair-access policy -- no signup, no secret to manage), has
no meaningful rate-limit risk for internal Alpha use, and its XBRL
`companyfacts` API was confirmed live to carry every fundamental this
sprint's evaluators need (Revenue, Operating Cash Flow, Capital
Expenditure, Buybacks, Issuance, Dividends, Debt Issuance/Repayment)
for at least one real internal holding (AAPL) before any code was
written here.

**Known, stated limitation, not fixed this sprint**: SEC EDGAR only
covers US SEC-registered filers. Of the real internal dev portfolio's
25 holdings, roughly half (the Swedish/Nordic tickers and foreign
private issuers) resolve to `CompanyNotFound` here, honestly, every
time -- there is no fallback guess. See the ATLAS-031 design record
for the full coverage map.

No market/price data of any kind -- see
`alpha_vantage.AlphaVantageMarketDataProvider` for that half of the
split this sprint's Phase 3 explicitly sanctions ("one provider for
fundamentals, one for market data").
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from typing import Any

from atlas.alpha.knowledge_coverage.models import KnowledgeDomain
from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.business_data_providers.errors import MalformedProviderResponse, MissingRequiredField
from atlas.business_data_providers.http import JsonFetcher
from atlas.business_data_providers.sec_edgar_identity import SecEdgarIdentity

__all__ = ["SecEdgarFundamentalsProvider", "SecEdgarFilingHistoryProvider"]

_COMPANYFACTS_URL_TEMPLATE = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json"
_FILING_INDEX_URL_TEMPLATE = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-K"
_SUBMISSIONS_URL_TEMPLATE = "https://data.sec.gov/submissions/CIK{cik10}.json"

#: Automatic Knowledge Ingestion Framework, Foundation Provider --
#: `SecEdgarFilingHistoryProvider` only reports these real filing types
#: (a genuine annual/quarterly/material-event/proxy report an investor
#: would actually want to know about), never every administrative SEC
#: form (e.g. Form 3/4/5, S-8) -- consistent with `KnowledgeDomain
#: .REGULATORY_FILINGS`'s own product intent ("regulatory filings," not
#: "every SEC EDGAR submission of any kind").
#: `"DEF 14A"` (Capability Expansion Sprint 12: Incentive Intelligence)
#: is the one, minimal, additive registry change that sprint made: it
#: lets Atlas discover *that* a proxy statement -- the real-world
#: document that discloses executive compensation -- was filed, and
#: when. It does not fetch or read that filing's own content (the same
#: "existence and metadata only" discipline every other tracked form
#: already follows); see `incentive_intelligence.py`'s own module
#: docstring for why that is a real, disclosed limitation, not an
#: oversight.
_TRACKED_FORM_TYPES = frozenset({"10-K", "10-Q", "8-K", "DEF 14A"})

_MIN_ANNUAL_DAYS = 300
_MAX_ANNUAL_DAYS = 400

#: canonical `business_facts` metadata key -> (candidate us-gaap tags in
#: priority order, the XBRL unit key those tags report under).
#: `_operating_cash_flow` is internal-only (never reaches a real
#: BusinessFactKind) -- used solely to derive `free_cash_flow` below,
#: the one canonical key SEC has no single matching tag for.
#:
#: **Duration concepts** -- a value that accumulates *over* a fiscal
#: year (income statement, cash flow statement). Extracted by
#: `_annual_entries`, which requires a real `start`/`end` span of
#: roughly a year.
#:
#: ATLAS-031A, Issue 3 -- fallback tags marked below were added after
#: the ATLAS-031 post-sprint audit found the single-tag mappings failed
#: for real, live-tested companies (confirmed by directly querying SEC
#: EDGAR, not assumed): NVDA's own CapEx is tagged
#: `PaymentsToAcquireProductiveAssets`, not `PaymentsToAcquireProperty
#: PlantAndEquipment` (which NVDA stopped using around 2012); MSFT's
#: debt activity is entirely commercial paper
#: (`RepaymentsOfCommercialPaper`), not `RepaymentsOfLongTermDebt`;
#: AMZN/NVDA/AVGO all lack `RepaymentsOfLongTermDebt` but do report the
#: broader one-sided `RepaymentsOfDebt`; AMZN/NVDA/META's issuance is
#: driven by employee stock plans
#: (`StockIssuedDuringPeriodValueStockOptionsExercised`), not
#: `ProceedsFromIssuanceOfCommonStock`. Each addition below is a
#: same-meaning alternative tag for the identical canonical concept --
#: never a different economic concept folded into an existing bucket.
#:
#: Company Data Foundation v1: `operating_income`/`net_income`/`eps`
#: added -- the three income-statement concepts the ATLAS-031 audit
#: never pursued. `eps` reports under XBRL unit `USD/shares`, not
#: `USD` -- the one duration concept here that is not a raw dollar
#: amount, which is exactly why `_annual_entries` now takes an explicit
#: `unit_key` rather than assuming `"USD"` everywhere.
_DURATION_CONCEPT_TAGS: dict[str, tuple[tuple[str, ...], str]] = {
    "revenue": (
        (
            "Revenues",
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "RevenueFromContractWithCustomerIncludingAssessedTax",
        ),
        "USD",
    ),
    "_operating_cash_flow": (
        (
            "NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        ),
        "USD",
    ),
    "operating_income": (("OperatingIncomeLoss",), "USD"),
    "net_income": (("NetIncomeLoss", "ProfitLoss"), "USD"),
    "eps": (("EarningsPerShareDiluted", "EarningsPerShareBasic"), "USD/shares"),
    # Capability Expansion Sprint 3 (Financial Statement Intelligence) --
    # `gross_profit` is a real, standard XBRL concept, but not every
    # filer reports it (e.g. many financial-sector companies do not
    # break out cost of revenue at all) -- `None`, never derived from a
    # guess, exactly like every other optional concept here.
    "gross_profit": (("GrossProfit",), "USD"),
    # Internal-only (never reaches `FinancialStatementFact` directly) --
    # used solely to derive `ebitda` below, the same "internal helper
    # key, popped before persistence" convention `_operating_cash_flow`
    # already establishes. SEC has no single "EBITDA" tag of its own;
    # EBITDA is *always* a derived figure, never a raw filed fact.
    "_depreciation_and_amortization": (
        ("DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet"),
        "USD",
    ),
    "investing_cash_flow": (("NetCashProvidedByUsedInInvestingActivities",), "USD"),
    "financing_cash_flow": (("NetCashProvidedByUsedInFinancingActivities",), "USD"),
    "capital_expenditure": (
        (
            "PaymentsToAcquirePropertyPlantAndEquipment",
            "PaymentsToAcquireProductiveAssets",  # ATLAS-031A: NVDA's real tag
        ),
        "USD",
    ),
    "share_buybacks": (("PaymentsForRepurchaseOfCommonStock",), "USD"),
    "share_issuance": (
        (
            "ProceedsFromIssuanceOfCommonStock",
            "StockIssuedDuringPeriodValueStockOptionsExercised",  # ATLAS-031A: AMZN/NVDA/META
        ),
        "USD",
    ),
    "dividends": (("PaymentsOfDividends", "PaymentsOfDividendsCommonStock"), "USD"),
    "debt_issuance": (
        (
            "ProceedsFromIssuanceOfLongTermDebt",
            "ProceedsFromIssuanceOfCommercialPaper",  # ATLAS-031A: AVGO
        ),
        "USD",
    ),
    "debt_repayment": (
        (
            "RepaymentsOfLongTermDebt",
            "RepaymentsOfDebt",  # ATLAS-031A: AMZN/NVDA/AVGO
            "RepaymentsOfCommercialPaper",  # ATLAS-031A: MSFT
        ),
        "USD",
    ),
    # Capability Expansion Sprint 4 (Capital Allocation Intelligence) --
    # the one genuinely missing acquisition per this sprint's own Phase
    # 2 audit: every other Capital Allocation raw fact (capex, buybacks,
    # issuance, dividends, debt issuance/repayment, shares outstanding)
    # was already fetched, by this same provider, before this sprint --
    # confirmed by reading this exact file, not assumed. Real, standard
    # XBRL concepts; not every filer reports M&A activity, so `None`
    # (never derived from a guess) is the honest default.
    "acquisitions": (("PaymentsToAcquireBusinessesNetOfCashAcquired",), "USD"),
    "disposals": (("ProceedsFromDivestitureOfBusinesses",), "USD"),
    "treasury_shares_acquired": (("TreasuryStockSharesAcquired",), "shares"),
}

#: **Instant concepts** (Company Data Foundation v1) -- a balance-sheet
#: value reported *as of* one point in time, not accumulated over a
#: year. SEC's own JSON omits the `start` key entirely for these
#: (`_instant_entries` below relies on exactly that), so they need a
#: distinct extraction path from `_DURATION_CONCEPT_TAGS` above. Each
#: value is attached only to a fiscal period `_DURATION_CONCEPT_TAGS`
#: already discovered for this company (matched by `end` date) --
#: never used to fabricate a new period whose own `start` date is
#: unknown; see `fetch`'s own comment at the merge point.
#:
#: `_debt_current`/`_debt_noncurrent`/`_debt_total_single` are
#: internal-only (never reach a real `BusinessFactKind`) -- combined
#: into the single canonical `total_debt` key per the documented v1
#: debt policy: current + non-current interest-bearing debt when both
#: are available; the single robust total-debt concept as a fallback
#: when the split is not reported; `None` (never fabricated from one
#: side alone) when neither is available. This never double-counts:
#: the current+noncurrent sum and the single-total fallback are
#: mutually exclusive branches, not summed together.
_INSTANT_CONCEPT_TAGS: dict[str, tuple[tuple[str, ...], str]] = {
    "cash": (
        (
            "CashAndCashEquivalentsAtCarryingValue",
            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        ),
        "USD",
    ),
    "_debt_current": (("LongTermDebtCurrent", "ShortTermBorrowings"), "USD"),
    "_debt_noncurrent": (("LongTermDebtNoncurrent",), "USD"),
    "_debt_total_single": (("LongTermDebt",), "USD"),
    # `CommonStockSharesOutstanding` reports under XBRL unit "shares",
    # never "USD" -- deliberately distinct from ValuationFactKind
    # .SHARES_OUTSTANDING (Alpha Vantage's *current*, today-only
    # figure): this one is a real per-fiscal-period historical count,
    # letting Capital Allocation see genuine share-count movement
    # (dilution or retirement) across years, not just today's snapshot.
    "shares_outstanding": (("CommonStockSharesOutstanding",), "shares"),
    # Capability Expansion Sprint 3 (Financial Statement Intelligence).
    # `equity`/`current_assets`/`current_liabilities`/`total_assets`/
    # `goodwill`/`intangible_assets` are all real, standalone concepts,
    # exposed directly the same as `cash`/`total_debt` already are.
    # `tangible_assets` (derived: `total_assets - goodwill - intangible
    # _assets`, see `fetch`'s own comment at the merge point) is the
    # one figure here with no XBRL tag of its own -- always derived,
    # never a raw filed fact, the same "no single source tag" reasoning
    # `ebitda`'s own comment above already applies to EBITDA.
    "equity": (("StockholdersEquity",), "USD"),
    "current_assets": (("AssetsCurrent",), "USD"),
    "current_liabilities": (("LiabilitiesCurrent",), "USD"),
    "total_assets": (("Assets",), "USD"),
    "goodwill": (("Goodwill",), "USD"),
    "intangible_assets": (("IntangibleAssetsNetExcludingGoodwill", "FiniteLivedIntangibleAssetsNet"), "USD"),
}


def _is_annual_span(start: str | None, end: str | None) -> bool:
    if not start or not end:
        return False
    try:
        span_days = (date.fromisoformat(end) - date.fromisoformat(start)).days
    except ValueError:
        return False
    return _MIN_ANNUAL_DAYS <= span_days <= _MAX_ANNUAL_DAYS


def _annual_entries(fact_node: dict[str, Any] | None, *, unit_key: str = "USD") -> list[dict[str, Any]]:
    """Every `unit_key`-unit entry for one us-gaap concept that is a
    real 10-K, full-fiscal-year ("FY") duration fact. Quarterly facts
    and stub/transition periods are excluded on purpose: Growth's own
    period-over-period comparison assumes consistent annual cadence,
    and mixing quarterly and annual values would misrepresent growth,
    not just under-cover it. `unit_key` defaults to `"USD"` for every
    dollar-denominated concept; `eps` is the one duration concept that
    reports under `"USD/shares"` instead (Company Data Foundation v1)."""
    if not fact_node:
        return []
    unit_entries = fact_node.get("units", {}).get(unit_key, [])
    return [
        entry
        for entry in unit_entries
        if entry.get("form") == "10-K"
        and entry.get("fp") == "FY"
        and _is_annual_span(entry.get("start"), entry.get("end"))
        and isinstance(entry.get("val"), (int, float))
        and not isinstance(entry.get("val"), bool)
    ]


def _latest_value_per_period(entries: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    """Groups by (start, end); where SEC's own data already carries
    more than one filing for the same period (an amendment or
    restatement), keeps whichever was filed most recently -- so a
    refresh always reflects SEC's latest known value, and a genuine
    later restatement naturally changes that period's contribution to
    the resulting record's content_hash on the next refresh (Phase 27)."""
    by_period: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in entries:
        key = (entry["start"], entry["end"])
        current = by_period.get(key)
        if current is None or entry.get("filed", "") >= current.get("filed", ""):
            by_period[key] = entry
    return by_period


def _instant_entries(fact_node: dict[str, Any] | None, *, unit_key: str = "USD") -> list[dict[str, Any]]:
    """(Company Data Foundation v1) Every `unit_key`-unit entry for one
    us-gaap concept that is a real 10-K, point-in-time ("instant")
    fact -- a balance-sheet value as of one date, not accumulated over
    a year. SEC's own JSON omits the `start` key entirely for an
    instant-context fact (confirmed shape of the real API, not
    assumed) -- `entry.get("start") is None` is exactly how this is
    distinguished from a duration fact, which always carries both
    `start` and `end`."""
    if not fact_node:
        return []
    unit_entries = fact_node.get("units", {}).get(unit_key, [])
    return [
        entry
        for entry in unit_entries
        if entry.get("form") == "10-K"
        and entry.get("start") is None
        and isinstance(entry.get("val"), (int, float))
        and not isinstance(entry.get("val"), bool)
    ]


def _latest_value_by_end(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """The instant-fact counterpart of `_latest_value_per_period` --
    groups by `end` date alone (an instant fact has no `start`),
    keeping the most recently filed value for any date SEC reports
    more than once (an amendment or restatement), for the identical
    reason that function documents."""
    by_end: dict[str, dict[str, Any]] = {}
    for entry in entries:
        key = entry["end"]
        current = by_end.get(key)
        if current is None or entry.get("filed", "") >= current.get("filed", ""):
            by_end[key] = entry
    return by_end


class SecEdgarFundamentalsProvider:
    """One `RawBusinessDocument` per discovered annual period, tagged
    `SourceKind.FINANCIAL_STATEMENT` (a derived structured fact set,
    not the filing document itself). `free_cash_flow` is computed as
    Operating Cash Flow minus Capital Expenditure -- the standard,
    unambiguous definition -- only when both source values exist for
    the same period; never invented from one side alone.

    A `company_identifier` with no SEC filer match raises
    `CompanyNotFound` -- Phase 5's "fail explicitly, do not guess,"
    never a fallback identity.
    """

    def __init__(
        self,
        fetch_json_fn: JsonFetcher | None = None,
        *,
        ticker_cik_map: dict[str, str] | None = None,
    ) -> None:
        self._identity = SecEdgarIdentity(fetch_json_fn, ticker_cik_map=ticker_cik_map)
        self._companyfacts_cache: dict[str, Any] = {}

    def _companyfacts(self, cik10: str) -> dict[str, Any]:
        if cik10 in self._companyfacts_cache:
            return self._companyfacts_cache[cik10]
        payload = self._identity.fetch_json(_COMPANYFACTS_URL_TEMPLATE.format(cik10=cik10))
        if not isinstance(payload, dict) or "facts" not in payload:
            raise MalformedProviderResponse(f"SEC companyfacts response for CIK {cik10} was not the expected shape")
        self._companyfacts_cache[cik10] = payload
        return payload

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        del evaluated_at  # every timestamp here comes from SEC's own filing data, never a wall-clock read
        cik10 = self._identity.resolve_cik(company_identifier)
        payload = self._companyfacts(cik10)
        us_gaap = payload.get("facts", {}).get("us-gaap", {})
        if not us_gaap:
            raise MissingRequiredField(
                f"SEC companyfacts for CIK {cik10} ({company_identifier}) has no us-gaap facts at all"
            )

        periods: dict[tuple[str, str], dict[str, float]] = {}
        filed_by_period: dict[tuple[str, str], str] = {}
        accn_by_period: dict[tuple[str, str], str] = {}

        for metadata_key, (tags, unit_key) in _DURATION_CONCEPT_TAGS.items():
            resolved: dict[tuple[str, str], dict[str, Any]] = {}
            for tag in tags:
                entries = _latest_value_per_period(_annual_entries(us_gaap.get(tag), unit_key=unit_key))
                for period_key, entry in entries.items():
                    resolved.setdefault(period_key, entry)  # first tag in priority order wins per period
            for period_key, entry in resolved.items():
                periods.setdefault(period_key, {})[metadata_key] = float(entry["val"])
                filed = entry.get("filed", "")
                if filed > filed_by_period.get(period_key, ""):
                    filed_by_period[period_key] = filed
                    accn_by_period[period_key] = entry.get("accn", "")

        if not periods:
            raise MissingRequiredField(f"No annual 10-K fundamentals found for {company_identifier} (CIK {cik10})")

        # Company Data Foundation v1: instant (balance-sheet) concepts,
        # keyed by their own `end` date only -- merged onto a duration
        # period below strictly by matching that same `end` date, never
        # used to invent a period whose `start` date only a duration
        # concept could ever establish (see `_INSTANT_CONCEPT_TAGS`'s
        # own docstring).
        instant_by_end: dict[str, dict[str, float]] = {}
        for metadata_key, (tags, unit_key) in _INSTANT_CONCEPT_TAGS.items():
            resolved_instant: dict[str, dict[str, Any]] = {}
            for tag in tags:
                entries = _latest_value_by_end(_instant_entries(us_gaap.get(tag), unit_key=unit_key))
                for end_date, entry in entries.items():
                    resolved_instant.setdefault(end_date, entry)
            for end_date, entry in resolved_instant.items():
                instant_by_end.setdefault(end_date, {})[metadata_key] = float(entry["val"])

        documents: list[RawBusinessDocument] = []
        for (start, end), values in sorted(periods.items()):
            operating_cash_flow = values.pop("_operating_cash_flow", None)
            if operating_cash_flow is not None:
                values["operating_cash_flow"] = operating_cash_flow
            capital_expenditure = values.get("capital_expenditure")

            # Capability Expansion Sprint 3: EBITDA is always derived
            # (Operating Income + Depreciation & Amortization), never a
            # raw filed tag -- only computed when both real inputs are
            # known for this exact period, never from one side alone.
            depreciation_and_amortization = values.pop("_depreciation_and_amortization", None)
            operating_income = values.get("operating_income")
            if operating_income is not None and depreciation_and_amortization is not None:
                values["ebitda"] = operating_income + depreciation_and_amortization

            # Sign validation (ATLAS-031A, Issue 4). "Payments to
            # Acquire..." concepts represent a cash outflow and are
            # reported as a positive magnitude by GAAP/XBRL convention
            # -- a negative value is a real, observed data-quality
            # signal (a tagging error, or a genuinely different
            # concept than intended), never something to silently
            # subtract. The fact is dropped, not "corrected" -- FCF
            # is then honestly left undetermined for this period
            # rather than derived from an unvalidated value.
            # Operating cash flow has no equivalent check: a company
            # genuinely burning cash reports it negative, and that is
            # a real, legitimate state, not a sign error.
            if capital_expenditure is not None and capital_expenditure < 0:
                values.pop("capital_expenditure", None)
                capital_expenditure = None

            if operating_cash_flow is not None and capital_expenditure is not None:
                values["free_cash_flow"] = operating_cash_flow - capital_expenditure

            # Company Data Foundation v1: cash/debt/shares policy.
            # `cash` and `shares_outstanding` pass through directly
            # when SEC reported them for this exact fiscal year-end.
            # `total_debt` follows the documented v1 policy: current +
            # non-current interest-bearing debt when both are known;
            # the single robust total-debt concept as a fallback when
            # the split is not reported; left undetermined (never
            # fabricated from one side alone) when neither is
            # available.
            period_instant = instant_by_end.get(end, {})
            cash = period_instant.get("cash")
            if cash is not None:
                values["cash"] = cash
            debt_current = period_instant.get("_debt_current")
            debt_noncurrent = period_instant.get("_debt_noncurrent")
            debt_total_single = period_instant.get("_debt_total_single")
            if debt_current is not None and debt_noncurrent is not None:
                values["total_debt"] = debt_current + debt_noncurrent
            elif debt_total_single is not None:
                values["total_debt"] = debt_total_single
            shares_outstanding = period_instant.get("shares_outstanding")
            if shares_outstanding is not None:
                values["shares_outstanding"] = shares_outstanding

            # Capability Expansion Sprint 3: `equity`/`current_assets`/
            # `current_liabilities`/`total_assets`/`goodwill`/
            # `intangible_assets` pass through directly, the same as
            # `cash` above. `working_capital`/`tangible_assets` are
            # always derived, never a raw filed tag -- `working_capital`
            # only when both sides are known; `tangible_assets` only
            # when `total_assets` is known (a company genuinely
            # reporting no goodwill/intangibles is a real zero for
            # those two, not a missing value, so their own absence does
            # not block the subtraction).
            equity = period_instant.get("equity")
            if equity is not None:
                values["equity"] = equity
            current_assets = period_instant.get("current_assets")
            if current_assets is not None:
                values["current_assets"] = current_assets
            current_liabilities = period_instant.get("current_liabilities")
            if current_liabilities is not None:
                values["current_liabilities"] = current_liabilities
            if current_assets is not None and current_liabilities is not None:
                values["working_capital"] = current_assets - current_liabilities
            total_assets = period_instant.get("total_assets")
            if total_assets is not None:
                values["total_assets"] = total_assets
            goodwill = period_instant.get("goodwill")
            if goodwill is not None:
                values["goodwill"] = goodwill
            intangible_assets = period_instant.get("intangible_assets")
            if intangible_assets is not None:
                values["intangible_assets"] = intangible_assets
            if total_assets is not None:
                values["tangible_assets"] = total_assets - (goodwill or 0.0) - (intangible_assets or 0.0)

            filed = filed_by_period.get((start, end), end)
            try:
                published_at = datetime.fromisoformat(filed).replace(tzinfo=timezone.utc)
            except ValueError:
                published_at = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)

            accn = accn_by_period.get((start, end), "")
            metadata: dict[str, Any] = {**values, "currency": "USD", "sec_cik": cik10, "sec_form": "10-K"}
            if accn:
                metadata["sec_accession"] = accn

            content_hash = hashlib.sha256(
                json.dumps({"start": start, "end": end, **values}, sort_keys=True).encode("utf-8")
            ).hexdigest()

            documents.append(
                RawBusinessDocument(
                    identifier=f"{company_identifier.upper()}:FY:{end}",
                    company=company_identifier.upper(),
                    source_kind=SourceKind.FINANCIAL_STATEMENT.value,
                    published_at=published_at,
                    provider_id="sec_edgar",
                    raw_reference=(
                        f"https://www.sec.gov/Archives/edgar/data/{int(cik10)}/{accn.replace('-', '')}/"
                        if accn
                        else _FILING_INDEX_URL_TEMPLATE.format(cik=int(cik10))
                    ),
                    content_hash=content_hash,
                    period_start=date.fromisoformat(start),
                    period_end=date.fromisoformat(end),
                    language="en",
                    metadata=metadata,
                )
            )
        return tuple(documents)


class SecEdgarFilingHistoryProvider:
    """Automatic Knowledge Ingestion Framework, Foundation Provider
    (`KnowledgeDomain.REGULATORY_FILINGS`). One `RawBusinessDocument`
    per real, investor-relevant filing (10-K/10-Q/8-K) SEC's own public
    `submissions` endpoint reports for a company -- the filing's own
    existence and metadata (form type, filing date, accession number),
    never the filing's own content (this provider does not fetch or
    read the filing document itself, the same "a `BusinessRecord` says
    a document exists, never what it says" discipline
    `SecEdgarFundamentalsProvider` already follows for `companyfacts`).

    Reuses `SecEdgarIdentity` for ticker->CIK resolution -- the exact
    same cached, live, keyless resolution `SecEdgarFundamentalsProvider`
    already uses, never a second, independent implementation.
    """

    provider_id = "sec_edgar_filings"
    supported_domains = (KnowledgeDomain.REGULATORY_FILINGS,)
    supported_source_kinds = (SourceKind.COMPANY_FILING,)

    def __init__(self, fetch_json_fn: JsonFetcher | None = None, *, ticker_cik_map: dict[str, str] | None = None) -> None:
        self._identity = SecEdgarIdentity(fetch_json_fn, ticker_cik_map=ticker_cik_map)

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        del evaluated_at  # every timestamp here comes from SEC's own filing data, never a wall-clock read
        cik10 = self._identity.resolve_cik(company_identifier)
        payload = self._identity.fetch_json(_SUBMISSIONS_URL_TEMPLATE.format(cik10=cik10))
        if not isinstance(payload, dict):
            raise MalformedProviderResponse(f"SEC submissions response for CIK {cik10} was not a JSON object")

        recent = payload.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accession_numbers = recent.get("accessionNumber", [])
        filing_dates = recent.get("filingDate", [])
        report_dates = recent.get("reportDate", [])
        primary_documents = recent.get("primaryDocument", [])
        if not (forms and accession_numbers and filing_dates):
            raise MissingRequiredField(
                f"SEC submissions for CIK {cik10} ({company_identifier}) has no recent filings array"
            )
        if not (len(forms) == len(accession_numbers) == len(filing_dates)):
            raise MalformedProviderResponse(
                f"SEC submissions for CIK {cik10} ({company_identifier}) has mismatched parallel filing arrays"
            )

        documents: list[RawBusinessDocument] = []
        for index, form in enumerate(forms):
            if form not in _TRACKED_FORM_TYPES:
                continue
            accession = accession_numbers[index]
            filing_date = filing_dates[index]
            report_date = report_dates[index] if index < len(report_dates) else None
            primary_document = primary_documents[index] if index < len(primary_documents) else None

            try:
                published_at = datetime.fromisoformat(filing_date).replace(tzinfo=timezone.utc)
            except (TypeError, ValueError):
                continue  # a filing with no parseable date is skipped, never fabricated
            period_end = None
            if report_date:
                try:
                    period_end = date.fromisoformat(report_date)
                except ValueError:
                    period_end = None

            accession_no_dashes = accession.replace("-", "")
            filing_url = (
                f"https://www.sec.gov/Archives/edgar/data/{int(cik10)}/{accession_no_dashes}/{primary_document}"
                if primary_document
                else f"https://www.sec.gov/Archives/edgar/data/{int(cik10)}/{accession_no_dashes}/"
            )
            content_hash = hashlib.sha256(
                json.dumps({"accn": accession, "form": form, "filed": filing_date}, sort_keys=True).encode("utf-8")
            ).hexdigest()

            documents.append(
                RawBusinessDocument(
                    identifier=f"{company_identifier.upper()}:FILING:{accession}",
                    company=company_identifier.upper(),
                    source_kind=SourceKind.COMPANY_FILING.value,
                    published_at=published_at,
                    provider_id=self.provider_id,
                    raw_reference=filing_url,
                    content_hash=content_hash,
                    period_start=None,
                    period_end=period_end,
                    language="en",
                    metadata={
                        "form_type": form,
                        "accession_number": accession,
                        "sec_cik": cik10,
                        "filing_url": filing_url,
                    },
                )
            )
        return tuple(documents)
