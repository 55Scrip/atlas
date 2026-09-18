"""Computing salience signals from records Atlas already holds.

Nothing here fetches, stores, or decides. It reads a company's strategy
graph and the same transcript records that graph was built from, and
counts -- attaching the passage behind every count.

**Two rules shape the whole module.** Management signals and analyst
signals are computed by separate functions into separate fields and are
never summed. And every count is a count of `PassageRef`s, so there is
no number in the output that cannot be expanded back into sentences.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Sequence

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.strategy import (
    CompanyStrategy,
    FactorClass,
    StrategyNode,
    StrategyNodeKind,
)
from atlas.analysis_engine.strategy.factors import resolve_factors
from atlas.analysis_engine.strategy_salience.contracts import CallSection, SpeakerRole
from atlas.analysis_engine.strategy_salience.models import (
    AnalystAttention,
    GraphLinkage,
    PassageRef,
    PriorityLanguage,
    SalienceEvidence,
    SpeakerMention,
)

__all__ = ["SALIENCE_VERSION", "classify_role", "company_salience", "speaker_identity"]

SALIENCE_VERSION = "strategy-salience-1"

_ANALYST = re.compile(r"\banalyst\b", re.I)
_OPERATOR = re.compile(r"\boperator\b", re.I)
_IR = re.compile(r"investor\s+relations|\bIR\b", re.I)
_CEO = re.compile(r"\bCEO\b|chief\s+executive\s+officer", re.I)
_CFO = re.compile(r"\bCFO\b|chief\s+financial\s+officer", re.I)
_EXECUTIVE = re.compile(
    r"\b(chief\s+[\w\s&]*officer|C[A-Z]{1,2}O\b|president|chair(?:man|woman|person)?"
    r"|founder|treasurer|senior\s+executive|(?:executive\s+|senior\s+)?(?:vice\s+president|VP)\b"
    r"|head\s+of\s+[\w\s&]+)\b",
    re.I,
)

#: Management naming something a priority in words that commit to it.
#:
#: Fifteen sentences across four benchmark companies match this. 277
#: match "important", "excited", "opportunity" or "well positioned",
#: which are absent here on purpose: at eighteen to one they would drown
#: every real priority statement in enthusiasm, and enthusiasm is what
#: earnings calls are made of.
_PRIORITY_LANGUAGE = re.compile(
    r"\b(?:top|key|highest|number\s+one|#1|biggest|main|primary|overriding)\s+priorit\w+"
    r"|\bstrategic\s+priorit\w+"
    r"|\bour\s+priorit(?:y|ies)\s+(?:is|are|remain\w*|include\w*)"
    r"|\bcentral\s+to\s+our\s+strateg\w+"
    r"|\bcore\s+(?:to|of)\s+our\s+strateg\w+"
    r"|\bone\s+of\s+our\s+(?:biggest|largest|most\s+important)\s+(?:investments?|priorities|bets?)"
    r"|\bsingle\s+biggest\b",
    re.I,
)

_SENTENCE = re.compile(r"(?<=[.!?])\s+")


def classify_role(title: str | None) -> SpeakerRole:
    """Normalise a title. Analyst and operator are checked first and
    cannot be overturned, the same precedence the extraction layer
    uses -- a sell-side title routinely contains an executive word."""
    if not title:
        return SpeakerRole.UNKNOWN
    if _ANALYST.search(title):
        return SpeakerRole.ANALYST
    if _OPERATOR.search(title):
        return SpeakerRole.OPERATOR
    if _IR.search(title):
        return SpeakerRole.INVESTOR_RELATIONS
    if _CEO.search(title):
        return SpeakerRole.CHIEF_EXECUTIVE
    if _CFO.search(title):
        return SpeakerRole.CHIEF_FINANCIAL
    if _EXECUTIVE.search(title):
        return SpeakerRole.OTHER_EXECUTIVE
    return SpeakerRole.UNKNOWN


def speaker_identity(speaker: str | None, title: str | None) -> tuple[str, str]:
    """One person, however the provider spelled them this quarter.

    Neither field is stable on its own. Titles vary -- VST's CEO appears
    as "President and CEO", "President and Chief Executive Officer" and
    "President & Chief Executive Officer" across four calls -- and so do
    names: the same man is "Jim Burke" and "James Burke", and AMAT's IR
    lead is both "Michael Sullivan" and "Mike Sullivan". Keying on
    either alone counted one voice as two, which inflated the speaker
    breadth of VST's capital-allocation node from two to four.

    Surname plus normalised role is stable across every benchmark call.
    Role is included so that two people who share a surname stay
    separate; the residual risk is two same-surname speakers in the same
    role on one call, which does not occur in this corpus and would
    under-count rather than invent.
    """
    surname = (speaker or "").strip().split()[-1].lower() if (speaker or "").strip() else ""
    return (surname, classify_role(title).value)


def _period_key(period: str | None) -> tuple[int, int]:
    if not period or "Q" not in period:
        return (0, 0)
    year, _, quarter = period.partition("Q")
    try:
        return (int(year), int(quarter))
    except ValueError:
        return (0, 0)


def _statement_index(record: BusinessRecord) -> int:
    raw = record.metadata.get("statement_index")
    try:
        return int(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return -1


def _quarter(record: BusinessRecord) -> str | None:
    value = record.metadata.get("quarter")
    return value if isinstance(value, str) else None


def _content(record: BusinessRecord) -> str:
    value = record.metadata.get("content")
    return value if isinstance(value, str) else ""


def _title(record: BusinessRecord) -> str | None:
    value = record.metadata.get("title")
    return value if isinstance(value, str) else None


def _speaker(record: BusinessRecord) -> str | None:
    value = record.metadata.get("speaker")
    return value if isinstance(value, str) else None


def _section_boundaries(records: Sequence[BusinessRecord]) -> dict[str, int]:
    """The first analyst statement index per period.

    This is the whole of the prepared-remarks/Q&A split, and it is
    derived from role metadata and statement order -- never from what a
    sentence says. Across sixteen benchmark calls it lands at index 4,
    5 or 6 every time."""
    first_analyst: dict[str, int] = {}
    for record in records:
        quarter = _quarter(record)
        if quarter is None:
            continue
        if classify_role(_title(record)) is not SpeakerRole.ANALYST:
            continue
        index = _statement_index(record)
        if index < 0:
            continue
        if quarter not in first_analyst or index < first_analyst[quarter]:
            first_analyst[quarter] = index
    return first_analyst


def _section(record: BusinessRecord, boundaries: dict[str, int]) -> CallSection:
    quarter = _quarter(record)
    if quarter is None or quarter not in boundaries:
        return CallSection.UNKNOWN
    index = _statement_index(record)
    if index < 0:
        return CallSection.UNKNOWN
    return (
        CallSection.PREPARED_REMARKS
        if index < boundaries[quarter]
        else CallSection.QUESTION_AND_ANSWER
    )


def _ref(record: BusinessRecord, text: str, boundaries: dict[str, int]) -> PassageRef:
    title = _title(record)
    return PassageRef(
        source_record_id=record.id,
        period=_quarter(record),
        speaker=_speaker(record),
        speaker_title=title,
        role=classify_role(title),
        section=_section(record, boundaries),
        text=text,
    )


def _node_records(node: StrategyNode, by_id: dict[str, BusinessRecord]) -> list[tuple[BusinessRecord, str]]:
    """The records behind a node's own evidence, in a stable order."""
    found: list[tuple[BusinessRecord, str]] = []
    for item in node.evidence:
        record = by_id.get(item.source_record_id)
        if record is not None:
            found.append((record, item.source_text))
    return found


def _analyst_attention(
    node: StrategyNode, records: Sequence[BusinessRecord], boundaries: dict[str, int]
) -> AnalystAttention:
    """Analyst turns whose text resolves this node's canonical factor.

    Matched on the factor, not on the node's wording: an analyst asks
    about interconnection in their own words, and the question is
    whether the market is pressing on the same *thing*. Nodes with no
    factor -- objectives stated as an outcome, economic engines -- get
    no analyst attention rather than a guess, because there is no
    canonical subject to match on."""
    if node.factor is None:
        return AnalystAttention((), (), ())
    # Geography is excluded, because for this one class the canonical
    # factor is a *category* rather than a subject. Every other class
    # names one thing -- electric power is electric power in whoever's
    # mouth -- but GEOGRAPHIC_MARKET covers Arizona and China alike, so
    # factor-level matching credited an analyst asking about China as
    # attention on AMAT's Arizona facility, and produced eight analysts
    # for a node nobody had asked about. Matching geography properly
    # needs place-level identity, which this sprint does not build.
    if node.factor is FactorClass.GEOGRAPHIC_MARKET:
        return AnalystAttention((), (), ())
    analysts: list[str] = []
    periods: list[str] = []
    refs: list[PassageRef] = []
    for record in records:
        if classify_role(_title(record)) is not SpeakerRole.ANALYST:
            continue
        content = _content(record)
        for sentence in _SENTENCE.split(content):
            mentions = resolve_factors(sentence)
            if not any(m.factor is node.factor for m in mentions):
                continue
            refs.append(_ref(record, sentence.strip(), boundaries))
            name = _speaker(record)
            if name and name not in analysts:
                analysts.append(name)
            quarter = _quarter(record)
            if quarter and quarter not in periods:
                periods.append(quarter)
            break
    return AnalystAttention(
        distinct_analysts=tuple(sorted(analysts)),
        periods=tuple(sorted(periods, key=_period_key)),
        refs=tuple(refs),
    )


def _priority_language(
    evidence_records: list[tuple[BusinessRecord, str]], boundaries: dict[str, int]
) -> PriorityLanguage:
    """Priority language *in the node's own passages*, not anywhere in
    the call. A company calling something a strategic priority three
    paragraphs away is not calling this node one."""
    refs = [
        _ref(record, text, boundaries)
        for record, text in evidence_records
        if _PRIORITY_LANGUAGE.search(text)
    ]
    return PriorityLanguage(refs=tuple(refs))


def _graph_linkage(node: StrategyNode, strategy: CompanyStrategy) -> GraphLinkage:
    by_relation: dict[str, int] = {}
    linked: list[str] = []
    for edge in strategy.edges:
        other = None
        if edge.source_id == node.node_id:
            other = edge.target_id
        elif edge.target_id == node.node_id:
            other = edge.source_id
        if other is None:
            continue
        by_relation[edge.relation.value] = by_relation.get(edge.relation.value, 0) + 1
        if other not in linked:
            linked.append(other)
    return GraphLinkage(by_relation=dict(sorted(by_relation.items())), linked_node_ids=tuple(sorted(linked)))


def _resource_links(
    node: StrategyNode,
    resource_nodes: Sequence[StrategyNode],
    by_id: dict[str, BusinessRecord],
) -> tuple[str, ...]:
    """Resource commitments whose own passage names this node's factor.

    Not matched on the commitment's factor: a RESOURCE_COMMITMENT node
    carries a `resource`, and its `factor` is always None, so comparing
    the two fields linked nothing at all and the benchmark run reported
    zero resource linkage for every node in every company. The
    commitment's *passage* is what says which part of the business the
    money is going to, so that is what is read."""
    if node.factor is None:
        return ()
    linked: list[str] = []
    for commitment in resource_nodes:
        if commitment.node_id == node.node_id:
            continue
        for item in commitment.evidence:
            if any(m.factor is node.factor for m in resolve_factors(item.source_text)):
                linked.append(commitment.node_id)
                break
    return tuple(sorted(linked))


def company_salience(
    strategy: CompanyStrategy,
    records: Iterable[BusinessRecord],
    *,
    forward_links: dict[str, tuple] | None = None,
) -> tuple[SalienceEvidence, ...]:
    """Salience evidence for every node in one company's strategy.

    `forward_links` is how guidance and customer-commitment evidence
    reaches this layer when a caller has it: supplied, never fetched.
    The forward-evidence layer owns those objects, and importing it here
    would create a second interpretation path into the same evidence."""
    records = [r for r in records if r.document_type is SourceKind.TRANSCRIPT]
    by_id = {r.id: r for r in records}
    boundaries = _section_boundaries(records)
    corpus_latest = max((q for q in (_quarter(r) for r in records) if q), key=_period_key, default=None)
    forward_links = forward_links or {}

    resource_nodes = [
        n for n in strategy.nodes if n.kind is StrategyNodeKind.RESOURCE_COMMITMENT
    ]

    out: list[SalienceEvidence] = []
    for node in strategy.nodes:
        evidence_records = _node_records(node, by_id)

        # Management voices, keyed by the person's name.
        #
        # Not by (name, title): the provider spells the same office
        # differently from quarter to quarter -- "President and Chief
        # Executive Officer" in one call, "President & Chief Executive
        # Officer" in the next -- and keying on the pair counted one
        # person as two voices, turning a two-speaker node into a
        # four-speaker one. A person is a person; the title is how the
        # provider wrote their role that quarter.
        mentions: dict[tuple[str, str], list[tuple[BusinessRecord, str]]] = {}
        for record, text in evidence_records:
            role = classify_role(_title(record))
            if not role.is_management:
                continue
            mentions.setdefault(speaker_identity(_speaker(record), _title(record)), []).append(
                (record, text)
            )

        speakers = tuple(
            SpeakerMention(
                speaker=_speaker(items[0][0]),
                title=_title(items[0][0]),
                role=classify_role(_title(items[0][0])),
                periods=tuple(sorted({q for r, _ in items if (q := _quarter(r))}, key=_period_key)),
                refs=tuple(_ref(r, t, boundaries) for r, t in items),
            )
            for identity, items in sorted(mentions.items())
        )

        prepared = tuple(
            _ref(r, t, boundaries)
            for r, t in evidence_records
            if _section(r, boundaries) is CallSection.PREPARED_REMARKS
        )
        qa = tuple(
            _ref(r, t, boundaries)
            for r, t in evidence_records
            if _section(r, boundaries) is CallSection.QUESTION_AND_ANSWER
            and classify_role(_title(r)).is_management
        )

        out.append(
            SalienceEvidence(
                node_id=node.node_id,
                company=strategy.company,
                node_kind=node.kind.value,
                subject_text=node.subject_text,
                periods=node.observed_periods,
                speakers=speakers,
                prepared_remark_refs=prepared,
                qa_refs=qa,
                priority_language=_priority_language(evidence_records, boundaries),
                analyst_attention=_analyst_attention(node, records, boundaries),
                graph_linkage=_graph_linkage(node, strategy),
                resource_commitment_links=_resource_links(node, resource_nodes, by_id),
                forward_links=tuple(forward_links.get(node.node_id, ())),
                continuity=node.continuity.value,
                latest_period=node.observed_periods[-1] if node.observed_periods else None,
                corpus_latest_period=corpus_latest,
            )
        )
    return tuple(out)
