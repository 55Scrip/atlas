"""Linking strategy nodes to what the company actually reported.

Three rules decide everything here.

**Which measure.** A node is mapped to observable measures only where the
mapping is defensible: an initiative adding production capacity implies
capital expenditure; an expected outcome of cost reduction implies
operating income. Node kinds with no honest mapping get
`SEMANTIC_LINK_UNAVAILABLE`, and measures Atlas has no line for -- research
spending, headcount, physical capacity -- are named as unavailable rather
than silently skipped.

**When.** A fact may only corroborate *executing* a statement if the
period it measures does not end before the statement was made. The corpus
makes this bite hard: strategy statements run 2025Q3-2026Q2 and the newest
financial fact for every benchmark is fiscal 2025, so an initiative first
stated in 2026Q2 has nothing measuring any time after it. That is reported
as nothing observed, never as nothing done.

**How many.** Support is counted in underlying events, not links. One
fiscal year's capital expenditure is one observation however many nodes it
touches and however many executives discussed it.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import UTC, date, datetime

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_facts.contracts import BusinessFactKind
from atlas.analysis_engine.business_facts.extraction import extract_facts_from_records
from atlas.analysis_engine.strategy import (
    CompanyStrategy,
    FactorClass,
    OutcomeKind,
    ResourceKind,
    StrategyNode,
    StrategyNodeKind,
)
from atlas.analysis_engine.strategy_corroboration.contracts import (
    CorroborationRelation,
    EvidenceClass,
    IndependenceChannel,
    TemporalRelation,
)
from atlas.analysis_engine.strategy_corroboration.models import (
    CompanyCorroboration,
    CorroborationItem,
    NodeCorroboration,
    ObservedEvidence,
)

__all__ = [
    "CORROBORATOR_VERSION",
    "EXCLUDED_CHANNELS",
    "company_corroboration",
    "temporal_relation",
]

CORROBORATOR_VERSION = "strategy-corroboration-1"

#: Named in every result. Share price is excluded on principle, not for
#: want of data: Atlas holds price snapshots for all four benchmarks, and
#: a share price moving after an announcement is the market's opinion of
#: a strategy rather than evidence the company executed one. Admitting it
#: would let sentiment corroborate what produced the sentiment.
EXCLUDED_CHANNELS = (
    "market_price -- the market's opinion of a strategy, not evidence of executing it",
)

#: Measures the strategy vocabulary implies that Atlas has no line for.
#: Named on the result so their absence is visible. `BusinessFactKind`
#: has no research-spending, headcount or physical-capacity member, so
#: Atlas can never observe these move -- and reporting that as "not
#: corroborated" would be honest while reporting it as "weakened" would
#: be a lie told by an absence.
_UNOBSERVABLE = {
    ResourceKind.RESEARCH_AND_DEVELOPMENT: "research_and_development",
    ResourceKind.HEADCOUNT: "headcount",
    ResourceKind.INVENTORY: "inventory",
    ResourceKind.PRODUCTION_CAPACITY: "physical_capacity",
}

#: Resource commitments to reported lines. Only where the money the
#: company says it is deploying is the money a filed statement reports.
_RESOURCE_MEASURE: dict[ResourceKind, BusinessFactKind] = {
    ResourceKind.CAPITAL: BusinessFactKind.CAPITAL_EXPENDITURE,
    ResourceKind.CAPITAL_EXPENDITURE: BusinessFactKind.CAPITAL_EXPENDITURE,
    ResourceKind.SHARE_REPURCHASE: BusinessFactKind.SHARE_BUYBACKS,
    ResourceKind.ACQUISITION: BusinessFactKind.CAPITAL_EXPENDITURE,
}

#: Factors whose pursuit shows up as capital spending. Deliberately
#: short: a dependency on regulatory approval or customer adoption is
#: real and moves no filed number, and inventing a proxy for it would be
#: worse than reporting that none exists.
_FACTOR_MEASURE: dict[FactorClass, BusinessFactKind] = {
    FactorClass.COMPUTE_CAPACITY: BusinessFactKind.CAPITAL_EXPENDITURE,
    FactorClass.PRODUCTION_CAPACITY: BusinessFactKind.CAPITAL_EXPENDITURE,
    FactorClass.ELECTRIC_POWER: BusinessFactKind.CAPITAL_EXPENDITURE,
    FactorClass.LAND_AND_SITES: BusinessFactKind.CAPITAL_EXPENDITURE,
}

#: Intended outcomes to reported results, with the direction management's
#: own word implies.
_OUTCOME_MEASURE: dict[OutcomeKind, tuple[BusinessFactKind, str]] = {
    OutcomeKind.REVENUE_GROWTH: (BusinessFactKind.REVENUE, "increased"),
    OutcomeKind.MARGIN_EXPANSION: (BusinessFactKind.OPERATING_INCOME, "increased"),
    OutcomeKind.COST_REDUCTION: (BusinessFactKind.OPERATING_INCOME, "increased"),
    OutcomeKind.CASH_GENERATION: (BusinessFactKind.FREE_CASH_FLOW, "increased"),
    OutcomeKind.MONETIZATION: (BusinessFactKind.REVENUE, "increased"),
}

RESOURCE_RULE = "reported-line-for-stated-resource"
FACTOR_RULE = "capital-spending-for-capacity-factor"
OUTCOME_RULE = "reported-result-for-stated-outcome"
GUIDANCE_RULE = "guidance-revision-as-commitment-event"


def _quarter_end(period: str | None) -> date | None:
    """The calendar end of a "2026Q2" label. Fiscal years differ from
    calendar ones, so this is an approximation used only for ordering
    against a fiscal period end -- never for arithmetic."""
    if not period or "Q" not in period:
        return None
    year, _, quarter = period.partition("Q")
    try:
        year_i, quarter_i = int(year), int(quarter)
    except ValueError:
        return None
    month, day = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}.get(quarter_i, (12, 31))
    return date(year_i, month, day)


def _as_date(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    return value if isinstance(value, date) else None


def temporal_relation(statement_period: str | None, fact_period: str | None) -> TemporalRelation:
    """Where an observation sits against the statement it might support.

    The rule is one-directional and has no window to tune: a fact whose
    period ends before the statement cannot be evidence of executing it.
    Everything else is contemporaneous or subsequent, and staleness is
    reported through the periods themselves rather than a decay curve
    nobody can justify."""
    statement_end = _quarter_end(statement_period)
    try:
        fact_end = date.fromisoformat(fact_period) if fact_period else None
    except (TypeError, ValueError):
        fact_end = None
    if statement_end is None or fact_end is None:
        return TemporalRelation.UNKNOWN
    if fact_end < statement_end:
        return TemporalRelation.PRECEDES_STRATEGY
    if (fact_end - statement_end).days <= 366:
        return TemporalRelation.CONTEMPORANEOUS
    return TemporalRelation.SUBSEQUENT


def _fact_evidence(fact, prior) -> ObservedEvidence:
    outcome = fact.kind in {
        BusinessFactKind.REVENUE,
        BusinessFactKind.OPERATING_INCOME,
        BusinessFactKind.FREE_CASH_FLOW,
        BusinessFactKind.NET_INCOME,
        BusinessFactKind.EPS,
    }
    return ObservedEvidence(
        evidence_id=f"{fact.source_record_id}:{fact.kind.value}:{fact.period}",
        evidence_class=(
            EvidenceClass.FINANCIAL_OUTCOME if outcome else EvidenceClass.RESOURCE_DEPLOYMENT
        ),
        channel=IndependenceChannel.REPORTED_FINANCIAL_STATEMENT,
        measure=fact.kind.value,
        period=fact.period,
        published_at=fact.published_at,
        value=fact.value,
        prior_value=prior.value if prior is not None else None,
        unit=fact.unit,
        currency=fact.unit,
        source_record_id=fact.source_record_id,
        semantic_owner="business_facts",
    )


def _comparable(fact, prior) -> bool:
    """Two facts may be compared only when they are the same measure in
    the same unit. Periods must differ, or a fact would be compared with
    itself and report `unchanged` as though something had been
    observed."""
    return (
        prior is not None
        and fact.kind is prior.kind
        and fact.unit == prior.unit
        and fact.period != prior.period
    )


def _latest_pair(facts: Sequence, kind: BusinessFactKind):
    """The most recent value of a measure and the one before it, by
    fiscal period."""
    matching = sorted((f for f in facts if f.kind is kind), key=lambda f: f.period)
    if not matching:
        return None, None
    return matching[-1], (matching[-2] if len(matching) > 1 else None)


def _implied_measures(node: StrategyNode) -> tuple[list[BusinessFactKind], list[str], list[str]]:
    """What a node implies Atlas should look at: observable measures,
    and measures it implies that Atlas cannot observe."""
    observable: list[BusinessFactKind] = []
    unavailable: list[str] = []
    if node.resource is not None:
        if node.resource in _UNOBSERVABLE:
            unavailable.append(_UNOBSERVABLE[node.resource])
        elif node.resource in _RESOURCE_MEASURE:
            observable.append(_RESOURCE_MEASURE[node.resource])
    if node.outcome is not None and node.outcome in _OUTCOME_MEASURE:
        observable.append(_OUTCOME_MEASURE[node.outcome][0])
    if node.factor is not None and node.kind in {
        StrategyNodeKind.INITIATIVE,
        StrategyNodeKind.OBJECTIVE,
    }:
        if node.factor in _FACTOR_MEASURE:
            observable.append(_FACTOR_MEASURE[node.factor])
        elif node.factor in {FactorClass.SUPPLY_CHAIN_INPUTS, FactorClass.LABOR_CAPABILITY}:
            unavailable.append("physical_capacity")
    return observable, unavailable, sorted({m.value for m in observable})


def _relation_for(node: StrategyNode, evidence: ObservedEvidence) -> CorroborationRelation | None:
    """What this observation corroborates, if anything.

    An expected outcome is judged against the direction management's own
    word implies; everything else is judged as execution. An unchanged
    measure supports nothing in either direction -- it is context."""
    direction = evidence.direction
    if direction is None or direction == "unchanged":
        return CorroborationRelation.CONTEXT_ONLY
    if node.outcome is not None and node.outcome in _OUTCOME_MEASURE:
        measure, intended = _OUTCOME_MEASURE[node.outcome]
        if measure.value == evidence.measure:
            return (
                CorroborationRelation.SUPPORTS_OUTCOME
                if direction == intended
                else CorroborationRelation.WEAKENS_OUTCOME
            )
    if evidence.evidence_class is EvidenceClass.RESOURCE_DEPLOYMENT:
        return (
            CorroborationRelation.SUPPORTS_EXECUTION
            if direction == "increased"
            else CorroborationRelation.WEAKENS_EXECUTION
        )
    return CorroborationRelation.CONTEXT_ONLY


def company_corroboration(
    strategy: CompanyStrategy,
    records: Iterable[BusinessRecord],
    *,
    evaluated_at: datetime,
    guidance: Iterable | None = None,
) -> CompanyCorroboration:
    """Corroboration for every node in one company's strategy.

    `guidance` is supplied by the caller -- `forward_claims` owns
    guidance revisions and this package does not import it, so there is
    no second interpretation path into that evidence."""
    records = list(records)
    facts = extract_facts_from_records(tuple(records), evaluated_at=evaluated_at)
    guidance = list(guidance or ())

    results: list[NodeCorroboration] = []
    for node in strategy.nodes:
        observable, unavailable, searched = _implied_measures(node)
        supporting: list[CorroborationItem] = []
        weakening: list[CorroborationItem] = []
        context: list[CorroborationItem] = []
        seen_events: set[tuple] = set()

        # The clock starts when the strategy was *first* stated, not when
        # it was last repeated. Using the latest mention inverted the
        # rule: Alphabet's data-centre initiative, stated in 2025Q3 and
        # restated twice, was measured against its 2026Q1 restatement,
        # which made fiscal-2025 capital expenditure look like backwards
        # leakage -- so a strategy repeated every quarter could never be
        # corroborated, while one mentioned once could. Repetition is a
        # salience signal; it does not move the announcement.
        statement_period = node.observed_periods[0] if node.observed_periods else None

        for kind in observable:
            fact, prior = _latest_pair(facts, kind)
            if fact is None:
                continue
            evidence = _fact_evidence(fact, prior if _comparable(fact, prior) else None)
            if evidence.event_key in seen_events:
                continue  # one fiscal year's measure is one observation
            seen_events.add(evidence.event_key)

            temporal = temporal_relation(statement_period, fact.period)
            relation = _relation_for(node, evidence)
            if temporal is TemporalRelation.PRECEDES_STRATEGY:
                # Cannot be evidence of executing something not yet said.
                relation = CorroborationRelation.CONTEXT_ONLY
            item = CorroborationItem(
                node_id=node.node_id,
                evidence=evidence,
                relation=relation,
                temporal=temporal,
                derivation_rule=(
                    OUTCOME_RULE
                    if relation
                    in {CorroborationRelation.SUPPORTS_OUTCOME, CorroborationRelation.WEAKENS_OUTCOME}
                    else RESOURCE_RULE
                    if node.resource is not None
                    else FACTOR_RULE
                ),
                explanation=(
                    f"reported {evidence.measure} for {evidence.period} "
                    f"{evidence.direction or 'has no comparable prior period'}"
                ),
            )
            if relation in {
                CorroborationRelation.SUPPORTS_EXECUTION,
                CorroborationRelation.SUPPORTS_OUTCOME,
            }:
                supporting.append(item)
            elif relation in {
                CorroborationRelation.WEAKENS_EXECUTION,
                CorroborationRelation.WEAKENS_OUTCOME,
            }:
                weakening.append(item)
            else:
                context.append(item)

        # Guidance revisions, by reference. A commitment event, never
        # evidence that anything was done.
        for item in guidance:
            measure = getattr(getattr(item, "subject", None), "value", None)
            if measure is None or measure not in searched:
                continue
            evidence = ObservedEvidence(
                evidence_id=getattr(item, "signal_id", ""),
                evidence_class=EvidenceClass.GUIDANCE_COMMITMENT,
                channel=IndependenceChannel.MANAGEMENT_GUIDANCE,
                measure=measure,
                period=getattr(item, "source_period", "") or "",
                published_at=None,
                semantic_owner="forward_claims",
            )
            if evidence.event_key in seen_events:
                continue
            seen_events.add(evidence.event_key)
            supporting.append(
                CorroborationItem(
                    node_id=node.node_id,
                    evidence=evidence,
                    relation=CorroborationRelation.SUPPORTS_COMMITMENT,
                    temporal=TemporalRelation.CONTEMPORANEOUS,
                    derivation_rule=GUIDANCE_RULE,
                    explanation=f"management revised its own {measure} guidance",
                )
            )

        results.append(
            NodeCorroboration(
                node_id=node.node_id,
                company=strategy.company,
                node_kind=node.kind.value,
                subject_text=node.subject_text,
                supporting=tuple(supporting),
                weakening=tuple(weakening),
                context=tuple(context),
                searched_measures=tuple(searched),
                unavailable_measures=tuple(sorted(set(unavailable))),
            )
        )

    return CompanyCorroboration(
        company=strategy.company,
        nodes=tuple(results),
        corroborator_version=CORROBORATOR_VERSION,
        evaluated_at=evaluated_at,
        excluded_channels=EXCLUDED_CHANNELS,
    )
