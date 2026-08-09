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
import os
from datetime import date, datetime, timezone
from typing import Any

from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.business_data_providers.errors import (
    CompanyNotFound,
    MalformedProviderResponse,
    MissingRequiredField,
)
from atlas.business_data_providers.http import JsonFetcher, fetch_json

__all__ = ["SecEdgarFundamentalsProvider"]

_TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
_COMPANYFACTS_URL_TEMPLATE = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json"
_FILING_INDEX_URL_TEMPLATE = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-K"

#: SEC's fair-access policy requires every automated caller to
#: identify itself as "company name + contact email" -- not a secret,
#: not authentication, but confirmed live (Phase 1 audit) to be
#: strictly enforced: a `User-Agent` without an email-shaped contact
#: gets a genuine `403`, not just a polite warning. Override with a
#: real contact via `ATLAS_SEC_EDGAR_USER_AGENT` (`atlas.ai.provider`'s
#: own `os.environ.get(...)`-only convention -- see that module for the
#: precedent this follows).
_DEFAULT_USER_AGENT = "Atlas Investment OS admin@atlas-investment-os.local (set ATLAS_SEC_EDGAR_USER_AGENT)"

_MIN_ANNUAL_DAYS = 300
_MAX_ANNUAL_DAYS = 400

#: canonical `business_facts` metadata key -> candidate us-gaap tags,
#: in priority order. `_operating_cash_flow` is internal-only (never
#: reaches a real BusinessFactKind) -- used solely to derive
#: `free_cash_flow` below, the one canonical key SEC has no single
#: matching tag for.
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
_CONCEPT_TAGS: dict[str, tuple[str, ...]] = {
    "revenue": (
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
    ),
    "_operating_cash_flow": (
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    ),
    "capital_expenditure": (
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",  # ATLAS-031A: NVDA's real tag
    ),
    "share_buybacks": ("PaymentsForRepurchaseOfCommonStock",),
    "share_issuance": (
        "ProceedsFromIssuanceOfCommonStock",
        "StockIssuedDuringPeriodValueStockOptionsExercised",  # ATLAS-031A: AMZN/NVDA/META
    ),
    "dividends": ("PaymentsOfDividends", "PaymentsOfDividendsCommonStock"),
    "debt_issuance": (
        "ProceedsFromIssuanceOfLongTermDebt",
        "ProceedsFromIssuanceOfCommercialPaper",  # ATLAS-031A: AVGO
    ),
    "debt_repayment": (
        "RepaymentsOfLongTermDebt",
        "RepaymentsOfDebt",  # ATLAS-031A: AMZN/NVDA/AVGO
        "RepaymentsOfCommercialPaper",  # ATLAS-031A: MSFT
    ),
}


def _user_agent() -> str:
    return os.environ.get("ATLAS_SEC_EDGAR_USER_AGENT", _DEFAULT_USER_AGENT)


def _is_annual_span(start: str | None, end: str | None) -> bool:
    if not start or not end:
        return False
    try:
        span_days = (date.fromisoformat(end) - date.fromisoformat(start)).days
    except ValueError:
        return False
    return _MIN_ANNUAL_DAYS <= span_days <= _MAX_ANNUAL_DAYS


def _annual_entries(fact_node: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Every USD-unit entry for one us-gaap concept that is a real
    10-K, full-fiscal-year ("FY") duration fact. Quarterly facts and
    stub/transition periods are excluded on purpose: Growth's own
    period-over-period comparison assumes consistent annual cadence,
    and mixing quarterly and annual values would misrepresent growth,
    not just under-cover it."""
    if not fact_node:
        return []
    usd_entries = fact_node.get("units", {}).get("USD", [])
    return [
        entry
        for entry in usd_entries
        if entry.get("form") == "10-K"
        and entry.get("fp") == "FY"
        and _is_annual_span(entry.get("start"), entry.get("end"))
        and isinstance(entry.get("val"), (int, float))
        and not isinstance(entry.get("val"), bool)
    ]


def _sec_ticker_candidates(ticker: str) -> tuple[str, ...]:
    """Provider-local normalization only (ATLAS-031A, Issue 2) -- Atlas's
    own ticker identity is never changed by this; only the candidate
    strings tried against SEC's own ticker map. SEC's `company_tickers
    .json` commonly uses a hyphen where Atlas (and most retail-facing
    data) uses a dot for multi-class tickers -- confirmed live: Atlas's
    `BRK.B` has no entry in SEC's map, but `BRK-B` does. Tried in
    order; the exact ticker always wins first so an already-SEC-format
    ticker never pays for a wasted lookup or behaves differently."""
    upper = ticker.upper()
    candidates = [upper]
    if "." in upper:
        candidates.append(upper.replace(".", "-"))
    return tuple(candidates)


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
        self._fetch_json = fetch_json_fn or fetch_json
        self._ticker_cik_cache: dict[str, str] | None = ticker_cik_map
        self._companyfacts_cache: dict[str, Any] = {}

    def _headers(self) -> dict[str, str]:
        return {"User-Agent": _user_agent()}

    def _ticker_to_cik(self) -> dict[str, str]:
        if self._ticker_cik_cache is not None:
            return self._ticker_cik_cache
        payload = self._fetch_json(_TICKER_MAP_URL, self._headers())
        if not isinstance(payload, dict):
            raise MalformedProviderResponse("SEC ticker map response was not a JSON object")
        mapping: dict[str, str] = {}
        for entry in payload.values():
            ticker = entry.get("ticker") if isinstance(entry, dict) else None
            cik = entry.get("cik_str") if isinstance(entry, dict) else None
            if isinstance(ticker, str) and cik is not None:
                mapping[ticker.upper()] = f"{int(cik):010d}"
        self._ticker_cik_cache = mapping
        return mapping

    def _resolve_cik(self, company_identifier: str) -> str:
        mapping = self._ticker_to_cik()
        for candidate in _sec_ticker_candidates(company_identifier):
            cik = mapping.get(candidate)
            if cik is not None:
                return cik
        raise CompanyNotFound(f"{company_identifier!r} did not resolve to any SEC-registered filer")

    def _companyfacts(self, cik10: str) -> dict[str, Any]:
        if cik10 in self._companyfacts_cache:
            return self._companyfacts_cache[cik10]
        payload = self._fetch_json(_COMPANYFACTS_URL_TEMPLATE.format(cik10=cik10), self._headers())
        if not isinstance(payload, dict) or "facts" not in payload:
            raise MalformedProviderResponse(f"SEC companyfacts response for CIK {cik10} was not the expected shape")
        self._companyfacts_cache[cik10] = payload
        return payload

    def fetch(self, *, company_identifier: str, evaluated_at: datetime) -> tuple[RawBusinessDocument, ...]:
        del evaluated_at  # every timestamp here comes from SEC's own filing data, never a wall-clock read
        cik10 = self._resolve_cik(company_identifier)
        payload = self._companyfacts(cik10)
        us_gaap = payload.get("facts", {}).get("us-gaap", {})
        if not us_gaap:
            raise MissingRequiredField(
                f"SEC companyfacts for CIK {cik10} ({company_identifier}) has no us-gaap facts at all"
            )

        periods: dict[tuple[str, str], dict[str, float]] = {}
        filed_by_period: dict[tuple[str, str], str] = {}
        accn_by_period: dict[tuple[str, str], str] = {}

        for metadata_key, tags in _CONCEPT_TAGS.items():
            resolved: dict[tuple[str, str], dict[str, Any]] = {}
            for tag in tags:
                for period_key, entry in _latest_value_per_period(_annual_entries(us_gaap.get(tag))).items():
                    resolved.setdefault(period_key, entry)  # first tag in priority order wins per period
            for period_key, entry in resolved.items():
                periods.setdefault(period_key, {})[metadata_key] = float(entry["val"])
                filed = entry.get("filed", "")
                if filed > filed_by_period.get(period_key, ""):
                    filed_by_period[period_key] = filed
                    accn_by_period[period_key] = entry.get("accn", "")

        if not periods:
            raise MissingRequiredField(f"No annual 10-K fundamentals found for {company_identifier} (CIK {cik10})")

        documents: list[RawBusinessDocument] = []
        for (start, end), values in sorted(periods.items()):
            operating_cash_flow = values.pop("_operating_cash_flow", None)
            capital_expenditure = values.get("capital_expenditure")

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
