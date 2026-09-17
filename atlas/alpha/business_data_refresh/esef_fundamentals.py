"""The one sanctioned route from a European filing to a Business Record.

`atlas.business_data_providers` has exactly one caller in the application,
this package, so that every path to a real network call is visible in one
place. This module is the ESEF half of that boundary, the same shape
`sec_statement_content` already gives the SEC half: it owns the composition --
find an issuer's filings, read each one, turn a fiscal year into a document the
ingestion pipeline accepts -- and leaves the parsing to the provider package.

It decides nothing. A fiscal year whose gross debt cannot be established
safely arrives here without one, and Financial Risk withholds on its own
terms rather than being told what to conclude.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from atlas.analysis_engine.business_data.models import RawBusinessDocument
from atlas.business_data_providers.esef.debt import DebtResolution, resolve_gross_debt
from atlas.business_data_providers.esef.normalization import (
    NormalizedPeriod,
    instant_facts,
    normalize_filing,
)
from atlas.business_data_providers.esef.source import (
    EsefFiling,
    EsefSourceError,
    annual_filings,
    fetch_facts,
    fetch_package,
    index_filings,
    lei_for_isin,
)
from atlas.business_data_providers.esef.taxonomy import read_taxonomy, to_qname

__all__ = ["PROVIDER_ID", "EsefPeriodEvidence", "EsefSourceError", "esef_filing_index",
           "issuer_lei", "annual_evidence", "newest_per_period", "document_for"]

PROVIDER_ID = "esef"

# Re-exported so callers reach the provider package only through here.
esef_filing_index = index_filings
issuer_lei = lei_for_isin


@dataclass(frozen=True)
class EsefPeriodEvidence:
    """One fiscal year of one issuer, read and interpreted but not yet stored."""

    filing: EsefFiling
    period: NormalizedPeriod
    debt: DebtResolution


def newest_per_period(filings: tuple[EsefFiling, ...]) -> list[EsefFiling]:
    """One filing per fiscal year.

    An issuer files the same annual report in more than one language, and the
    index lists each separately. They are one piece of evidence; ingesting both
    would duplicate every fact in it.
    """
    chosen: dict[date, EsefFiling] = {}
    for filing in filings:
        seen = chosen.get(filing.period_end)
        if seen is None or (filing.facts_path and not seen.facts_path):
            chosen[filing.period_end] = filing
    return [chosen[period] for period in sorted(chosen, reverse=True)]


def annual_evidence(lei: str, cache: Path, *, years: int = 4, index=None) -> list[EsefPeriodEvidence]:
    """Read this issuer's most recent annual filings.

    Raises `EsefSourceError` for one filing only when that filing cannot be
    retrieved; the caller decides whether one issuer's failure should stop a
    batch, and in Atlas it never does.
    """
    evidence: list[EsefPeriodEvidence] = []
    for filing in newest_per_period(annual_filings(lei, index=index))[:years]:
        facts = fetch_facts(filing, cache)
        taxonomy = read_taxonomy(zipfile.ZipFile(fetch_package(filing, cache)))
        period_end = filing.period_end.isoformat()
        evidence.append(EsefPeriodEvidence(
            filing=filing,
            period=normalize_filing(facts, taxonomy, period_end),
            debt=resolve_gross_debt(
                taxonomy,
                lambda concept: (instant_facts(facts, to_qname(concept)).get(period_end) or (None, None))[0],
            ),
        ))
    return evidence


def document_for(ticker: str, evidence: EsefPeriodEvidence, lei: str) -> RawBusinessDocument:
    """One fiscal year, shaped as the ingestion pipeline expects.

    `published_at` is when the filing became publicly retrievable, never the
    period end -- it is what stops a figure being used before it existed. It is
    an *upper* bound rather than the issuer's own publication date: the only
    authorisation date an ESEF report carries is free prose (Volvo's reads
    "Goteborg, February 28, 2024" inside a narrative block; Schneider's is
    French wrapped in HTML), so nothing machine-readable states it, and parsing
    prose for a date is the kind of guess this whole path refuses. Erring late
    can only make Atlas withhold; it can never let it look ahead.
    """
    period, filing, debt = evidence.period, evidence.filing, evidence.debt
    values = dict(period.values)
    if period.free_cash_flow is not None:
        values["free_cash_flow"] = period.free_cash_flow
    if debt.resolved:
        values["total_debt"] = debt.gross_debt

    metadata: dict[str, object] = {k: v for k, v in values.items() if v is not None}
    if period.currency:
        metadata["currency"] = period.currency
    # Which tag produced which field, so a figure can be traced to its concept
    # years later -- and, for the fields that are absent, why.
    metadata["esef_lei"] = lei
    metadata["esef_filing"] = filing.filing_id
    metadata["esef_concepts"] = json.dumps(
        {name: list(concepts) for name, concepts in sorted(period.concepts.items())})
    metadata["esef_withheld"] = json.dumps(sorted(period.withheld))
    # Fields the filing tagged and then failed to carry a value for, as
    # distinct from fields the company does not report. Only the first is a
    # defect in the filing, and only the first might be fixed by a later one.
    metadata["esef_reported_but_unusable"] = json.dumps(sorted(period.reported_but_unusable))
    metadata["esef_debt_outcome"] = debt.outcome.value
    metadata["esef_debt_reason"] = debt.reason

    body = json.dumps(metadata, sort_keys=True, default=str)
    published = filing.published_at
    return RawBusinessDocument(
        identifier=f"{ticker}:FY:{period.period_end}",
        company=ticker,
        source_kind="financial_statement",
        published_at=datetime(published.year, published.month, published.day, tzinfo=timezone.utc),
        provider_id=PROVIDER_ID,
        raw_reference=filing.source_reference,
        content_hash=hashlib.sha256(body.encode()).hexdigest(),
        period_end=filing.period_end,
        language="en",
        metadata=metadata,
    )
