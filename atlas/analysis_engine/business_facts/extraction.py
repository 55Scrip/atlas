"""Structured, deterministic Business Fact extraction (ATLAS-023,
Phase 4).

**No LLM. No NLP. No semantic interpretation of document content.**
`extract_facts` reads exactly one `BusinessRecord` and looks up a
closed set of well-known `metadata` keys -- the same keys a real,
future structured-data provider (an XBRL/EDGAR adapter, a
Financial-Modeling-Prep connector, a manual entry form) would populate
deterministically at ingestion time, per
`atlas.analysis_engine.business_data`'s own Phase 6 pipeline. This
module never reads `source_reference`'s target, never guesses a value
from a document's free-text content, and never converts "a document of
this type exists" into a fact by itself -- a report existing is not
evidence of anything numeric.

**If a value cannot be extracted deterministically, the fact does not
exist.** No key -> no fact. Wrong type (a string where a number is
expected, or a bare `bool`, which Python's `int` subclassing would
otherwise silently accept as `0`/`1`) -> no fact. No period on the
source record (`period_start`/`period_end` both `None`) -> no facts
extracted from that record at all, since nothing here invents a period
a document didn't declare.

**Conflicting facts are excluded, not guessed.** If two source records
report a different value for the same `(company, kind, period)`,
`extract_facts_from_records` drops that fact entirely rather than
picking one arbitrarily -- silently preferring one provider's number
over another's would be exactly the "hidden heuristic" this sprint
forbids.
"""
from __future__ import annotations

from datetime import datetime

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.models import BusinessFact
from atlas.analysis_engine.provenance import Consumer, Provenance, SourceKind, UpdateTrigger

__all__ = ["extract_facts", "extract_facts_from_records"]

#: The one closed mapping from a fact kind to the `BusinessRecord
#: .metadata` key a structured provider is expected to populate.
#: Extending this sprint's fact taxonomy always means adding one entry
#: here alongside the new `BusinessFactKind` member -- never a second,
#: parallel lookup table.
_METADATA_KEYS: dict[BusinessFactKind, str] = {
    BusinessFactKind.REVENUE: "revenue",
    BusinessFactKind.FREE_CASH_FLOW: "free_cash_flow",
    BusinessFactKind.CAPITAL_EXPENDITURE: "capital_expenditure",
    BusinessFactKind.SHARE_BUYBACKS: "share_buybacks",
    BusinessFactKind.SHARE_ISSUANCE: "share_issuance",
    BusinessFactKind.DIVIDENDS: "dividends",
    BusinessFactKind.DEBT_ISSUANCE: "debt_issuance",
    BusinessFactKind.DEBT_REPAYMENT: "debt_repayment",
    # -- Company Data Foundation v1 --
    BusinessFactKind.OPERATING_INCOME: "operating_income",
    BusinessFactKind.NET_INCOME: "net_income",
    BusinessFactKind.EPS: "eps",
    BusinessFactKind.CASH: "cash",
    BusinessFactKind.TOTAL_DEBT: "total_debt",
    BusinessFactKind.SHARES_OUTSTANDING: "shares_outstanding",
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


def extract_facts(record: BusinessRecord, *, evaluated_at: datetime) -> tuple[BusinessFact, ...]:
    """Deterministic: identical `record` always produces a deeply equal
    result. Never reads a wall clock -- `evaluated_at` is the only
    timestamp source.
    """
    period = _record_period(record)
    if period is None:
        return ()

    unit = record.metadata.get("currency")
    unit = unit if isinstance(unit, str) and unit.strip() else _UNSPECIFIED_UNIT

    facts: list[BusinessFact] = []
    for kind, key in _METADATA_KEYS.items():
        value = _numeric_value(record.metadata.get(key))
        if value is None:
            continue
        facts.append(
            BusinessFact(
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
                    # `dependencies` names the source BusinessRecord's id
                    # here, not a Finding.id -- a deliberate broadening of
                    # this field's original scope (see module docstring),
                    # since a BusinessFact's real dependency is a document,
                    # not another Finding.
                    dependencies=(record.id,),
                    update_trigger=UpdateTrigger.EXTERNAL_BUSINESS_DATA_INGESTED,
                    consumers=_ALL_CONSUMERS,
                    computed_at=evaluated_at,
                ),
                extracted_at=evaluated_at,
                published_at=record.published_at,
            )
        )
    return tuple(facts)


def extract_facts_from_records(
    records: tuple[BusinessRecord, ...], *, evaluated_at: datetime
) -> tuple[BusinessFact, ...]:
    """Flat-maps `extract_facts` over every record, then drops any
    `(company, kind, period)` group with more than one distinct value
    -- see module docstring. Callers are expected to pass only the
    current head of each document lineage
    (`business_data.versioning.latest_versions`); this function does
    not deduplicate versions itself, only genuinely conflicting values.
    """
    all_facts = [fact for record in records for fact in extract_facts(record, evaluated_at=evaluated_at)]

    values_by_group: dict[tuple[str, BusinessFactKind, str], set[float]] = {}
    for fact in all_facts:
        group = (fact.company, fact.kind, fact.period)
        values_by_group.setdefault(group, set()).add(fact.value)

    conflicting_groups = {group for group, values in values_by_group.items() if len(values) > 1}

    seen_groups: set[tuple[str, BusinessFactKind, str]] = set()
    resolved: list[BusinessFact] = []
    for fact in all_facts:
        group = (fact.company, fact.kind, fact.period)
        if group in conflicting_groups or group in seen_groups:
            continue
        seen_groups.add(group)
        resolved.append(fact)

    return tuple(resolved)
