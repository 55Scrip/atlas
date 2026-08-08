"""The canonical `ValuationFact` model and its extraction (ATLAS-024,
Phase 4/5) -- the market-data half of the fundamental/market boundary
Phase 5 requires.

**Two members, not a speculative ontology.** Only `SHARE_PRICE` and
`SHARES_OUTSTANDING` exist -- the minimum needed to derive a market
capitalization ourselves (`value` × `count`, a real traceable
multiplication) for the one real v1 method
(`atlas.analysis_engine.valuation.cash_flow`). `NET_DEBT`, `EBITDA`,
and `EPS` are deliberately not named here even as reserved members --
per `atlas.analysis_engine.business_facts.contracts`'s own precedent,
fact taxonomies are exactly the place this codebase refuses to
speculatively reserve members; a future EV/EBITDA or P/E method adds
what it genuinely needs when it exists, not before.

**Reuses `atlas.analysis_engine.business_data`'s existing canonical
data layer -- not a second "MarketRecord" ingestion system.** A market
snapshot is ingested through the identical `validate` -> `normalize` ->
`version` pipeline every other `BusinessRecord` uses, tagged
`SourceKind.MARKET_DATA_SNAPSHOT`. Phase 5's boundary between
fundamental and market data lives entirely in *which fact taxonomy
reads a record's `metadata`* -- this module only ever reads records
tagged `MARKET_DATA_SNAPSHOT`, and
`atlas.analysis_engine.business_facts.extraction` is untouched by this
sprint and still reads whatever document types it always has.

Otherwise identical discipline to `business_facts.extraction`: no LLM,
no NLP, exact well-known key lookup only, a missing key means the fact
does not exist, a document with no declared period contributes nothing.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind as DocumentSourceKind
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger

__all__ = ["ValuationFactKind", "ValuationFact", "extract_valuation_facts", "extract_valuation_facts_from_records"]


class ValuationFactKind(str, Enum):
    """A closed, two-member set for ATLAS-024 v1. See module docstring
    for why no further members are reserved speculatively."""

    SHARE_PRICE = "share_price"
    SHARES_OUTSTANDING = "shares_outstanding"


@dataclass(frozen=True)
class ValuationFact:
    """One atomic, structured market-data observation -- deliberately
    the same shape as `business_facts.models.BusinessFact` (Phase 4's
    own "reuse BusinessFact conventions" instruction), including the
    same deliberate absence of a `confidence` field for the identical
    reason: exact deterministic extraction has no partial-success state
    for one atomic value to grade. Confidence is computed at the
    `ValuationFinding` level instead (see `cash_flow.py`)."""

    id: str
    company: str
    kind: ValuationFactKind
    value: float
    unit: str
    period: str
    source_record_id: str
    provenance: Provenance
    extracted_at: datetime


_METADATA_KEYS: dict[ValuationFactKind, str] = {
    ValuationFactKind.SHARE_PRICE: "share_price",
    ValuationFactKind.SHARES_OUTSTANDING: "shares_outstanding",
}

_UNSPECIFIED_UNIT = "unspecified"

_ALL_CONSUMERS = (
    Consumer.PORTFOLIO_PAGE,
    Consumer.INVESTMENT_CASE_PAGE,
    Consumer.DISCOVERY,
    Consumer.HISTORY,
)


def _record_period(record: BusinessRecord) -> str | None:
    if record.period_end is not None:
        return record.period_end.isoformat()
    if record.period_start is not None:
        return record.period_start.isoformat()
    return None


def _numeric_value(raw: object) -> float | None:
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    return None


def extract_valuation_facts(record: BusinessRecord, *, evaluated_at: datetime) -> tuple[ValuationFact, ...]:
    """Deterministic: identical `record` always produces a deeply equal
    result. Only reads records tagged `SourceKind.MARKET_DATA_SNAPSHOT`
    -- a stray `"share_price"` metadata key on, say, an annual report is
    never treated as authoritative market data (see module docstring).
    """
    if record.document_type is not DocumentSourceKind.MARKET_DATA_SNAPSHOT:
        return ()

    period = _record_period(record)
    if period is None:
        return ()

    unit = record.metadata.get("currency")
    unit = unit if isinstance(unit, str) and unit.strip() else _UNSPECIFIED_UNIT

    facts: list[ValuationFact] = []
    for kind, key in _METADATA_KEYS.items():
        value = _numeric_value(record.metadata.get(key))
        if value is None:
            continue
        facts.append(
            ValuationFact(
                id=f"{record.id}:{kind.value}:{period}",
                company=record.company,
                kind=kind,
                value=value,
                unit=unit,
                period=period,
                source_record_id=record.id,
                provenance=Provenance(
                    source_kind=SourceKind.ANALYSIS_ENGINE_STAGE,
                    source_references=(record.source_reference,),
                    dependencies=(record.id,),
                    update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
                    consumers=_ALL_CONSUMERS,
                    computed_at=evaluated_at,
                ),
                extracted_at=evaluated_at,
            )
        )
    return tuple(facts)


def extract_valuation_facts_from_records(
    records: tuple[BusinessRecord, ...], *, evaluated_at: datetime
) -> tuple[ValuationFact, ...]:
    """Flat-maps `extract_valuation_facts` over every record, then --
    identical policy to
    `business_facts.extraction.extract_facts_from_records` -- drops any
    `(company, kind, period)` group with more than one distinct value
    rather than guessing which source is authoritative."""
    all_facts = [
        fact for record in records for fact in extract_valuation_facts(record, evaluated_at=evaluated_at)
    ]

    values_by_group: dict[tuple[str, ValuationFactKind, str], set[float]] = {}
    for fact in all_facts:
        group = (fact.company, fact.kind, fact.period)
        values_by_group.setdefault(group, set()).add(fact.value)

    conflicting_groups = {group for group, values in values_by_group.items() if len(values) > 1}

    seen_groups: set[tuple[str, ValuationFactKind, str]] = set()
    resolved: list[ValuationFact] = []
    for fact in all_facts:
        group = (fact.company, fact.kind, fact.period)
        if group in conflicting_groups or group in seen_groups:
            continue
        seen_groups.add(group)
        resolved.append(fact)

    return tuple(resolved)
