"""Finding the facts that link an action to a strategy -- and reporting
honestly that there usually are none.

An audit of every record in the corpus decided the shape of this module,
and most of the outcome was subtraction. There is **no dimensional data
of any kind**: no segment, axis, member, geography or reportable-unit key
on any record. The European ESEF records carry `esef_concepts`, which
maps a consolidated measure to the IFRS concept it came from rather than
to a dimension, and none of the four benchmark companies has even that.
So structural attribution -- narrowing a filed figure by the breakdown it
was filed with -- has nothing to run on.

What remains is what management says. Across the four benchmarks there
are sixteen sentences naming an amount and a purpose together, and most
of them describe money that *will* be spent. Named projects appear for
one company. That is the whole of the evidence, and this module's job is
to read it exactly and to say "no attribution evidence" everywhere else.

**A linking fact is required.** Nothing here builds an attribution from
the existence of a strategy and the existence of an action; factor
equality and period overlap produce a candidate, and a candidate is
never published as a fact.
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import datetime

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.strategy import CompanyStrategy, StrategyNode
from atlas.analysis_engine.strategy.factors import resolve_factors
from atlas.analysis_engine.strategy_attribution.contracts import (
    ActionTense,
    AttributionBasis,
    AttributionResolution,
    AttributionStatus,
    EvidenceRole,
)
from atlas.analysis_engine.strategy_attribution.models import (
    ActionAttribution,
    AttributedAmount,
    CompanyAttribution,
    EvidenceRef,
    LinkingFact,
)

__all__ = [
    "ATTRIBUTOR_VERSION",
    "UNAVAILABLE_CHANNELS",
    "SEARCHED_CHANNELS",
    "company_attribution",
    "extract_linking_facts",
]

ATTRIBUTOR_VERSION = "strategy-attribution-1"

#: Audited across every record in the corpus and found absent. Named on
#: every result, because "Atlas cannot narrow this" and "Atlas did not
#: try" are different statements and only one of them is true.
UNAVAILABLE_CHANNELS = (
    "reported_segment_data -- no segment, axis or member key exists on any record",
    "esef_dimensions -- `esef_concepts` maps measures to IFRS concepts, not to dimensions, "
    "and covers eight European holdings, none of them a benchmark",
    "sec_dimensions -- filings are stored as accession references without content",
    "business_line_data -- no line-level measure is persisted",
    "customer_contracts -- zero customer commitments corpus-wide",
    "headcount_and_rnd_allocation -- no such line exists in BusinessFact",
)

SEARCHED_CHANNELS = (
    "explicit_management_quantification",
    "management_named_link",
    "reported_financial_statement_action",
)

#: An amount, in management's own words. Kept verbatim: "more than",
#: "approximately" and "up to" are part of the claim, and parsing them
#: into a number would discard the hedge management chose.
_AMOUNT = (
    r"(?:(?:more\s+than|approximately|about|around|up\s+to|over|at\s+least|nearly)\s+)?"
    r"(?:\$\s?\d[\d,.]*\s*(?:billion|million|bn|mm)?"
    r"|\d[\d,.]*\s*(?:billion|million)(?:\s+dollars)?"
    r"|\d[\d,.]*\s*(?:MW|megawatts?|GW|gigawatts?))"
)
_ALLOCATION_VERB = (
    r"(?:invest(?:ed|ing|s)?|spend|spent|spending|allocat(?:e|ed|ing)|commit(?:ted|ting)?"
    r"|deploy(?:ed|ing)?|put|add(?:ed|ing)?|contract(?:ed|ing)?)"
)
_PURPOSE = r"(?:for|on|to|into|toward|towards|in|at)"

#: Amount + allocation verb + purpose, all in one clause. The conjunction
#: is the whole rule: an amount alone is a figure, a verb alone is an
#: action, and a purpose alone is a topic.
_QUANTIFIED_PURPOSE = re.compile(
    rf"\b{_ALLOCATION_VERB}\b[^.]{{0,40}}?({_AMOUNT})[^.]{{0,30}}?\b{_PURPOSE}\b\s+([^.]{{3,70}})",
    re.I,
)

#: Past tense, and nothing that turns it back into a plan. Checked
#: against the whole sentence, because "we have invested ... and expect
#: to invest more" is both.
_PAST = re.compile(
    r"\b(?:invested|spent|allocated|committed|deployed|added|built|completed|contracted"
    r"|placed\s+in\s+service|returned\s+to\s+service)\b",
    re.I,
)
_FORWARD = re.compile(
    r"\b(?:will|expect|expects|expected|plan|plans|intend|intends|anticipat\w+|going\s+to"
    r"|target\w*|would|could|to\s+be\s+invested)\b",
    re.I,
)

#: A named asset. Requires capitalised words before the asset noun, so
#: "our data center" does not become a project and "Comanche Peak
#: nuclear plant" does.
_NAMED_PROJECT = re.compile(
    r"\b((?:[A-Z][\w'-]+\s+){1,3})(?:facility|plant|site|project|campus|fab|unit)\b"
)
#: A named counterparty to an agreement.
_NAMED_COUNTERPARTY = re.compile(
    r"\b(?:contract|agreement|partnership|deal|PPA)\s+with\s+([A-Z][\w'-]+(?:\s+[A-Z][\w'-]+)?)"
)
#: A named place. A specific place, never the category -- Sprint 7 found
#: that the geographic factor class groups Arizona with China, so a
#: resolution claim cannot be built on it.
_NAMED_PLACE = re.compile(
    r"\b(?:in|at|into)\s+((?:the\s+)?(?:U\.?S\.?|U\.?K\.?|UAE|China|India|Mexico|Brazil|Japan"
    r"|Korea|Germany|France|Texas|Arizona|Europe|Asia|Africa|Ohio|Pennsylvania|Illinois))\b"
)
#: A quantified physical capability.
_CAPACITY = re.compile(r"\b(\d[\d,.]*\s*(?:MW|megawatts?|GW|gigawatts?))\b", re.I)

_SENTENCE = re.compile(r"(?<=[.!?])\s+")
_ANALYST = re.compile(r"\banalyst\b", re.I)
_OPERATOR = re.compile(r"\boperator\b", re.I)
_EXECUTIVE = re.compile(
    r"\b(chief\s+[\w\s&]*officer|C[A-Z]{1,2}O\b|president|chair(?:man|woman|person)?"
    r"|founder|treasurer|senior\s+executive|(?:executive\s+|senior\s+)?(?:vice\s+president|VP)\b"
    r"|head\s+of\s+[\w\s&]+)\b",
    re.I,
)


def _is_executive(title: str | None) -> bool:
    if not title:
        return False
    if _ANALYST.search(title) or _OPERATOR.search(title):
        return False
    return bool(_EXECUTIVE.search(title))


def _tense(sentence: str) -> ActionTense:
    """Past only when nothing in the sentence turns it back into a plan."""
    if _FORWARD.search(sentence):
        return ActionTense.STATED_INTENT
    if _PAST.search(sentence):
        return ActionTense.OBSERVED_PAST
    return ActionTense.UNKNOWN


def _resolution_for(sentence: str) -> tuple[AttributionResolution, str]:
    """The finest resolution the sentence itself names.

    Order matters and reflects specificity: a named asset beats a named
    counterparty, which beats a quantified capability, which beats a
    place. When the sentence names nothing, the resolution is the
    company -- which is where the observation already was."""
    project = _NAMED_PROJECT.search(sentence)
    if project:
        return AttributionResolution.PROJECT, project.group(1).strip()
    counterparty = _NAMED_COUNTERPARTY.search(sentence)
    if counterparty:
        return AttributionResolution.COUNTERPARTY, counterparty.group(1).strip()
    capacity = _CAPACITY.search(sentence)
    if capacity:
        return AttributionResolution.CAPACITY_ASSET, capacity.group(1).strip()
    place = _NAMED_PLACE.search(sentence)
    if place:
        return AttributionResolution.GEOGRAPHY, place.group(1).strip()
    return AttributionResolution.COMPANY, ""


def extract_linking_facts(record: BusinessRecord) -> tuple[LinkingFact, ...]:
    """Linking facts stated in one transcript record.

    Only transcripts: filings are stored in this corpus as accession
    references without content, so there is no filed text to read."""
    if record.document_type is not SourceKind.TRANSCRIPT:
        return ()
    content = record.metadata.get("content")
    if not isinstance(content, str) or not content.strip():
        return ()
    title = record.metadata.get("title")
    title = title if isinstance(title, str) else None
    if not _is_executive(title):
        return ()
    quarter = record.metadata.get("quarter")
    period = quarter if isinstance(quarter, str) else None

    facts: list[LinkingFact] = []
    for raw in _SENTENCE.split(content):
        sentence = raw.strip()
        if not sentence or len(sentence) > 420:
            continue

        def ref(text: str) -> EvidenceRef:
            return EvidenceRef(
                role=EvidenceRole.LINKING,
                source_record_id=record.id,
                source_kind=record.document_type.value,
                period=period,
                published_at=record.published_at,
                semantic_owner="strategy_attribution",
                text=text,
                speaker_title=title,
            )

        quantified = _QUANTIFIED_PURPOSE.search(sentence)
        resolution, target = _resolution_for(sentence)
        tense = _tense(sentence)

        if quantified:
            facts.append(
                LinkingFact(
                    basis=AttributionBasis.EXPLICIT_MANAGEMENT_QUANTIFICATION,
                    resolution=resolution,
                    target_name=target,
                    evidence=ref(sentence),
                    tense=tense,
                    amount=AttributedAmount(
                        value_text=quantified.group(1).strip(),
                        total_context_text="",
                        residual_is_unallocated=True,
                    ),
                )
            )
            continue

        # A named link with no amount is still attribution -- "a 20-year
        # contract with Amazon at our Comanche Peak nuclear plant" places
        # an agreement at an asset without saying what it cost.
        if resolution is not AttributionResolution.COMPANY and _PAST.search(sentence):
            facts.append(
                LinkingFact(
                    basis=AttributionBasis.MANAGEMENT_NAMED_LINK,
                    resolution=resolution,
                    target_name=target,
                    evidence=ref(sentence),
                    tense=tense,
                )
            )
    return tuple(facts)


def _links_for_node(
    node: StrategyNode, facts: Iterable[LinkingFact]
) -> tuple[list[LinkingFact], list[LinkingFact]]:
    """Split linking facts into ones that attribute to *this* node and
    ones that are merely candidates.

    Factor equality finds candidates and cannot assert anything, which
    the first run of this module demonstrated at some cost: matching on
    the factor alone gave VST's `nuclear uprates`, `megawatts` and
    `PPAs` nodes the *same six* linking facts, because all three are
    about electric power and so was every passage. Six strategies
    cannot each own the same 4,500 megawatts.

    What connects a linking fact to a particular node is the **passage
    itself**: the node was read out of a sentence, and the linking fact
    has to be that same sentence. Management naming the strategy and the
    allocation in one breath is the connection; anything looser is not.

    Shared *record* was tried first and is too coarse. A speaker turn
    runs for paragraphs and changes subject: matching on the record
    attributed "5,500 megawatts" from an announced acquisition of a
    natural-gas fleet to VST's *nuclear uprate* dependency, because both
    sat in one answer and both concern electric power. Same turn is not
    same subject.

    The cost is recall, and it is the correct trade. An attribution that
    could belong to any of six strategies has not attributed
    anything."""
    if node.factor is None:
        return [], []
    node_passages = {item.source_text.strip() for item in node.evidence}
    supported: list[LinkingFact] = []
    candidates: list[LinkingFact] = []
    for fact in facts:
        mentions = resolve_factors(fact.evidence.text)
        if not any(m.factor is node.factor for m in mentions):
            continue
        if fact.evidence.text.strip() in node_passages:
            supported.append(fact)
        else:
            candidates.append(fact)
    return supported, candidates


def _status(links: list[LinkingFact], candidates: list[LinkingFact]) -> AttributionStatus:
    if not links:
        return (
            AttributionStatus.CANDIDATE_ONLY
            if candidates
            else AttributionStatus.NO_ATTRIBUTION_EVIDENCE
        )
    resolutions = {link.resolution for link in links}
    targets = {link.target_name for link in links if link.target_name}
    if len(targets) > 1:
        # Two named targets for one strategy: Atlas does not choose.
        return AttributionStatus.CONFLICTING
    if resolutions == {AttributionResolution.COMPANY}:
        # A linking fact that resolves no further than the company has
        # not narrowed anything.
        return AttributionStatus.AMBIGUOUS
    return AttributionStatus.ATTRIBUTED


def company_attribution(
    strategy: CompanyStrategy,
    records: Iterable[BusinessRecord],
    *,
    evaluated_at: datetime,
) -> CompanyAttribution:
    """What Atlas can place against each node of one company's strategy.

    Reads the strategy graph and the records directly. It does **not**
    read Strategic Corroboration: attribution asks what an action was
    for, corroboration asks whether it happened, and chaining them would
    make the second a precondition of the first for no reason."""
    records = list(records)
    facts = [fact for record in records for fact in extract_linking_facts(record)]

    results: list[ActionAttribution] = []
    for node in strategy.nodes:
        matched, candidates = _links_for_node(node, facts)
        # One passage stating one allocation is one linking fact, however
        # many times it is repeated across the call or the corpus.
        unique: list[LinkingFact] = []
        seen: set[tuple] = set()
        for fact in matched:
            key = (fact.basis, fact.resolution, fact.target_name, fact.evidence.text)
            if key in seen:
                continue
            seen.add(key)
            unique.append(fact)

        results.append(
            ActionAttribution(
                node_id=node.node_id,
                company=strategy.company,
                node_kind=node.kind.value,
                subject_text=node.subject_text,
                status=_status(unique, candidates),
                links=tuple(unique),
                searched_channels=SEARCHED_CHANNELS,
                unavailable_channels=UNAVAILABLE_CHANNELS,
                derivation_rule="linking-fact-sharing-the-nodes-canonical-factor",
            )
        )

    return CompanyAttribution(
        company=strategy.company,
        nodes=tuple(results),
        attributor_version=ATTRIBUTOR_VERSION,
        evaluated_at=evaluated_at,
        unavailable_channels=UNAVAILABLE_CHANNELS,
    )
