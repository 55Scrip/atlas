"""Reading strategy out of what management actually said.

**Keywords find candidates; they never accept one.** The corpus settles
this beyond argument. Searching four benchmark companies' executive
statements for the obvious dependency markers -- "depends on",
"requires", "subject to", "availability of" -- returns 37 sentences, of
which the most common single form is "today's call includes
forward-looking statements which are subject to risks and
uncertainties", and the second is an executive saying "Depends on what
you're measuring off of." A layer that accepted keyword hits would be
asserting that Alphabet's strategy depends on risks and uncertainties.

So every rule here is a conjunction: a marker, **and** a canonical
object from `factors`, **and** a first-person subject, **and** no
disqualifying frame. The object requirement does most of the work. It is
why "our strategy is clear, and we're executing against it" produces
nothing -- it names no thing -- and why no blocklist of adjectives is
needed to reject enthusiasm.

**Only OBSERVED comes out of this module.** Extraction reads; it does
not compose. Anything Atlas concludes by putting two readings together
is built in `composition`, carries a named rule, and is DERIVED or
HYPOTHESIS. That separation is what makes the status field mean
something, and a test pins it.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime

from atlas.analysis_engine.business_data.models import BusinessRecord
from atlas.analysis_engine.business_data.sources import SourceKind
from atlas.analysis_engine.strategy.contracts import (
    EvidenceStatus,
    FactorClass,
    OutcomeKind,
    RelationKind,
    StrategyNodeKind,
    StrategyRejectionReason,
    SupportPolarity,
)
from atlas.analysis_engine.strategy.factors import (
    FACTOR_RESOLVER_VERSION,
    resolve_factors,
    resolve_resources,
)
from atlas.analysis_engine.strategy.models import (
    RejectedStrategyCandidate,
    StrategyEdge,
    StrategyEvidence,
    StrategyNode,
)

__all__ = ["EXTRACTOR_VERSION", "extract_strategy"]

#: Bumped whenever a rule below changes in a way that could alter which
#: nodes are produced.
EXTRACTOR_VERSION = f"strategy-extraction-1+{FACTOR_RESOLVER_VERSION}"

_SENTENCE = re.compile(r"(?<=[.!?])\s+")

# --- who is speaking ---------------------------------------------------
# Same three-way reading `forward_claims.classify_claimant` performs, and
# for the same reason: an analyst asking "what does that depend on?" and
# a CFO saying "that depends on" are the same words and opposite
# evidence. Checked in this order -- analyst and operator first, so a
# deliberately broad executive pattern can never reclassify either.
_ANALYST = re.compile(r"\banalyst\b", re.I)
_OPERATOR = re.compile(r"\boperator\b", re.I)
#: Deliberately broad, because the analyst and operator checks run
#: first and cannot be overturned by it. The first pass spelled out
#: `C[EFOT]O` and silently discarded eleven Alphabet statements from
#: its CBO and CRO -- among them the clearest description of the
#: company's economic engine in the whole corpus. An enumeration of
#: C-level letters is a guess about org charts; the shape is the rule.
_EXECUTIVE = re.compile(
    r"\b(chief\s+[\w\s&]*officer|C[A-Z]{1,2}O\b|president|chair(?:man|woman|person)?"
    r"|founder|treasurer|senior\s+executive"
    r"|(?:executive\s+|senior\s+)?(?:vice\s+president|VP)\b"
    r"|head\s+of\s+[\w\s&]+)\b",
    re.I,
)

# --- frames that disqualify a sentence outright ------------------------
#: Safe-harbour recitation. The single most frequent dependency-marker
#: sentence in the corpus and never a dependency.
_SAFE_HARBOUR = re.compile(
    r"forward[- ]looking\s+statements?|safe\s+harbou?r|risks?\s+and\s+uncertainties"
    r"|actual\s+results?\s+(?:to\s+)?(?:may\s+)?differ",
    re.I,
)
#: Filing risk-factor boilerplate. A risk factor is a disclosure that a
#: thing could go wrong; a failure mode is a thing that threatens a
#: strategy Atlas has evidence the company is pursuing.
_GENERIC_RISK = re.compile(
    r"could\s+(?:materially\s+and\s+)?adversely\s+affect\s+our\s+business"
    r"|business,?\s+financial\s+condition,?\s+(?:and\s+|or\s+)?results\s+of\s+operations"
    r"|no\s+assurance\s+(?:can\s+be\s+given|that)",
    re.I,
)
#: Sentiment about a strategy. Listed for the rejection *reason* -- the
#: object requirement already rejects most of these -- so an auditor can
#: see that Atlas saw the sentence and declined it.
_MARKETING = re.compile(
    r"\b(excited|thrilled|pleased|proud|delighted|encouraged)\b"
    r"|well[- ]positioned|best[- ]in[- ]class|world[- ]class|market[- ]leading"
    r"|(?:our\s+)?strategy\s+is\s+clear|remain\s+confident|strong\s+momentum",
    re.I,
)
#: Somebody else's strategy. "Our customers are investing in capacity"
#: is evidence about customers, and recording it as this company's
#: dependency would put the whole industry's plans on one balance sheet.
_THIRD_PARTY = re.compile(
    r"^\s*(?:our\s+)?(?:customers?|competitors?|suppliers?|partners?|the\s+industry|they)\b"
    r"|\b(?:customers?|competitors?|the\s+industry)\s+(?:are|is|will|have|has)\s+\w+ing\b",
    re.I,
)
#: Completed and reported, not pursued. Checked before the initiative
#: rules so "we acquired the land" in a results recital does not become
#: a live initiative.
_HISTORICAL = re.compile(
    r"\b(?:in\s+the\s+(?:quarter|year)|last\s+(?:quarter|year)|during\s+the\s+quarter"
    r"|delivered|reported|recorded|posted)\b.*\b(?:of|was|were)\b.*\$",
    re.I,
)
#: An anaphor with no antecedent Atlas carries. "We will persist with
#: this initiative" names nothing a graph can hold.
_ANAPHOR_OBJECT = re.compile(
    r"\b(?:that|this|those|these|it|them|the\s+same)\s+"
    r"(?:initiative|portfolio|program|effort|strategy|business|area|investment|one)s?\b",
    re.I,
)

# --- first person ------------------------------------------------------
_FIRST_PERSON = re.compile(r"\b(?:we|we'(?:re|ve|ll)|our|us)\b", re.I)

# --- predicates --------------------------------------------------------
_OBJECTIVE = re.compile(
    r"\bour\s+(?:goal|objective|aim|strategy|priority|priorities|focus|ambition)\s+(?:is|are|remains?|include)"
    # "we expect to" is deliberately absent. An expectation is a
    # forecast, and `ForwardClaim` already owns forecasts -- VST's "the
    # premium above market we expect to receive under the long-term
    # power purchase agreements" is guidance about a range, not a
    # statement of what management is trying to achieve. Admitting it
    # turned two guidance sentences into objectives on the first run.
    r"|\bwe\s+(?:aim|intend|plan|seek)\s+to\b"
    r"|\bwe(?:'re|\s+are)\s+(?:focused\s+on|targeting|working\s+to(?:ward)?)\b",
    re.I,
)
_INITIATIVE = re.compile(
    r"\bwe(?:'ve|'re|\s+are|\s+have\s+been|\s+will\s+be)?\s*"
    r"(?:been\s+)?(?:building|constructing|investing|expanding|adding|launching|deploying"
    r"|developing|acquiring|signing|contracting|converting|upgrading|scaling|commissioning)\b"
    r"|\bwe\s+(?:will|plan\s+to)\s+(?:build|construct|invest|expand|add|deploy|develop|acquire)\b",
    re.I,
)
_DEPENDENCY = re.compile(
    r"\b(?:depends?|depend|dependent|depending)\s+(?:on|upon)\b"
    r"|\brequires?\b|\brequired\s+(?:for|to|by)\b"
    r"|\bsubject\s+to\b|\bcontingent\s+(?:on|upon)\b|\bconstrained\s+by\b|\blimited\s+by\b"
    r"|\breli(?:es|ant|y)\s+(?:on|upon)\b"
    r"|\bavailability\s+of\b|\baccess\s+to\b"
    r"|\bkey\s+factor\b|\bpacing\b|\bbottleneck\b|\bgating\b"
    # Necessity, stated without the word "depends". The corpus puts 23
    # of these in front of the four benchmarks and most of them are
    # product marketing -- "eBeam metrology is critical for 3D devices"
    # -- which is precisely why they are safe to admit: none of those
    # names a canonical factor, so the object gate rejects them, while
    # "Switching is critical to a virtuous cycle" survives.
    r"|\b(?:essential|critical|necessary|fundamental)\s+(?:for|to)\b"
    r"|\bkey\s+to\b|\bhinges?\s+on\b|\bpredicated\s+on\b|\bunderpin\w*\b",
    re.I,
)
_COMMITMENT = re.compile(
    r"\bwe\s+(?:will\s+)?(?:commit|committed|are\s+committing|allocate|allocated|spend|spent"
    r"|are\s+spending|invest|invested|are\s+investing|deploy|deployed|repurchased?)\b"
    r"|\bwe(?:'ve|\s+have)\s+(?:committed|allocated|invested|spent|repurchased)\b",
    re.I,
)
#: Conditional constructions -- what must hold for an outcome to arrive.
_CONDITION = re.compile(
    r"\b(?:as\s+long\s+as|so\s+long\s+as|provided\s+that|once\s+we|in\s+order\s+to|subject\s+to\s+the"
    r"|assuming|to\s+the\s+extent\s+that|if\s+we\s+(?:can|are\s+able))\b",
    re.I,
)
#: A negative conditional or an explicit, company-specific threat.
_THREAT = re.compile(
    r"\b(?:if\s+(?:we\s+(?:do\s+not|don't|cannot|can't|fail)|(?:that|this|it)\s+(?:does\s+not|doesn't))"
    r"|unless\s+we|the\s+risk\s+(?:is|that)|challenge\s+(?:is|will\s+be)|conundrum|headwind)\b",
    re.I,
)

_OUTCOME_PATTERNS: tuple[tuple[OutcomeKind, re.Pattern[str]], ...] = (
    (OutcomeKind.MARGIN_EXPANSION, re.compile(r"\b(?:margins?|operating\s+leverage|profitability)\b", re.I)),
    (OutcomeKind.COST_REDUCTION, re.compile(r"\b(?:lower|reduce|reducing|down)\s+(?:unit\s+)?costs?\b|\bproductivity\b", re.I)),
    (OutcomeKind.CASH_GENERATION, re.compile(r"\b(?:free\s+cash\s+flow|cash\s+generation)\b", re.I)),
    (OutcomeKind.CAPACITY_GROWTH, re.compile(r"\b(?:capacity\s+(?:growth|additions?)|more\s+capacity|new\s+capacity)\b", re.I)),
    (OutcomeKind.CUSTOMER_GROWTH, re.compile(r"\b(?:new\s+customers?|customer\s+(?:growth|additions?)|market\s+share)\b", re.I)),
    (OutcomeKind.MONETIZATION, re.compile(r"\b(?:monetiz|advertis\w+\s+(?:revenue|value)|pricing\s+power)\w*\b", re.I)),
    (OutcomeKind.REVENUE_GROWTH, re.compile(r"\b(?:revenue\s+growth|grow\s+revenue|top[- ]line\s+growth)\b", re.I)),
)

#: How the business turns something it has into money.
#:
#: This is the correction Phase 4 asked for. The first definition of an
#: economic engine was "an initiative plus an expected outcome", which
#: describes a *strategy* -- a thing the company is doing and hopes will
#: work -- and returned UNKNOWN for all four benchmarks. An engine is
#: not a plan. It is how the business that already exists converts
#: something it holds into revenue, and management describes it in a
#: recognisable grammar:
#:
#:   "we can get access to more transactions, which fuel our virtuous
#:    cycle"                                                   (MA)
#:   "the core engine of our search ads relies on a dual prediction,
#:    delivering immediate utility for the user while maximizing
#:    measurable value for the advertiser"                  (GOOGL)
#:
#: Both name a conversion. Neither is an initiative, and no composition
#: over initiatives would have found either.
_ENGINE = re.compile(
    r"\b(?:core\s+)?engine\s+of\b|\bvirtuous\s+cycle\b|\bflywheel\b"
    r"|\bhow\s+we\s+(?:make|generate)\s+money\b"
    r"|\b(?:which|that)\s+(?:fuels?|drives?|powers?)\s+our\b"
    r"|\bmonetiz\w+\b|\btranslates?\s+into\b|\bconverts?\s+\w+\s+into\b",
    re.I,
)
#: An engine has to end in economics. Without an output term the
#: sentence is a metaphor -- "flywheel" on its own is a slogan.
_ENGINE_OUTPUT = re.compile(
    r"\b(?:revenue|fees?|transactions?|cash\s+flow|earnings|margins?"
    r"|advertising|inventory|monetiz\w+|volumes?|spend)\b",
    re.I,
)

#: A dependency that is being *denied*, not asserted. VST: "So we do not
#: see equipment or EPC as the gating items to building new generation".
#: AMAT: "the customers we are currently serving and our outlook do not
#: depend on those licenses." Recording either as a dependency states
#: the opposite of what management said -- the most damaging error this
#: layer can make, because it is confidently wrong rather than merely
#: absent.
_NEGATED_DEPENDENCY = re.compile(
    r"\b(?:do\s+not|don't|does\s+not|doesn't|did\s+not|didn't|never|no\s+longer|not)\b"
    r"[^.]{0,60}?\b(?:see|depend|depends|require|requires|need|needs|gating|constrain\w*|rely|relies)\b",
    re.I,
)

#: The company *holding* or *supplying* a factor, rather than needing
#: it. "we also have ample access to high-voltage equipment" is a
#: statement of sufficiency; "our co-innovation model provides chip
#: makers much earlier access to next-generation process technology" is
#: the company being somebody else's supply. The first pass read both as
#: dependencies because both contain "access to".
_HOLDS_OR_SUPPLIES = re.compile(
    r"\b(?:we|our(?:\s+[\w-]+){1,4})\s+"
    r"(?:also\s+)?(?:have|has|had|provides?|provide|gives?|give|offers?|offer|supply|supplies|enable\w*)\b"
    r"[^.]{0,80}?\baccess\s+to\b"
    # "we have the breadth of solutions and partnerships required for
    # end-to-end leadership" (AMD) is the same claim in the other
    # grammar: the company saying it already holds the thing, with
    # "required" as an adjective rather than a verb about its strategy.
    r"|\bwe\s+have\s+(?:the\s+)?[^.]{0,70}?\brequired\b",
    re.I,
)

#: A general activity, not this company's strategy. "Building modern AI
#: platforms requires not only GPUs but also CPUs" (NVDA) and "deploying
#: AI at large scale requires significant innovation at every level of
#: the technology stack" (AMAT) are statements about what the work takes
#: for anyone who does it. The subject is a gerund phrase naming an
#: activity, not the company or anything it owns, and the turn-level
#: first-person check cannot catch them because the surrounding turn is
#: full of "we".
_GENERAL_ACTIVITY_SUBJECT = re.compile(
    r"(?<!our\s)(?<!we\sare\s)(?<!we're\s)\b(?:building|deploying|running|operating"
    r"|scaling|training|developing|manufacturing)\s+[\w\s,-]{0,45}?\brequires?\b",
    re.I,
)

#: A product specification, not a strategy. "Just 64 Blackwell GPUs are
#: required to run the GPT-3 benchmark compared to 256 H100s" is a claim
#: about how efficient the company's product is; read as a dependency it
#: says NVIDIA's strategy depends on GPUs.
_PRODUCT_SPECIFICATION = re.compile(
    r"\b\d[\d,.]*\s+[\w-]+(?:\s+[\w-]+){0,2}\s+(?:are|is)\s+(?:required|needed)\s+to\b"
    r"|\brequired\s+to\s+run\b|\bcompared\s+to\s+\d",
    re.I,
)

#: A reported figure explaining its own variability. The subject of
#: such a sentence is an accounting line, not a strategy:
#:
#:   "revenues from TPU hardware sales will fluctuate from quarter to
#:    quarter depending on when TPUs are shipped to customers"
#:   "the availability of supply, pricing of components, and timing of
#:    cash payments can cause some variability in the reported CapEx
#:    number"
#:
#: Both contain a dependency predicate and a real canonical factor, and
#: both became DEPENDENCY nodes in the coverage pass. Neither asserts
#: that the company's strategy depends on anything -- they assert that a
#: number moves around -- and a layer that cannot tell those apart would
#: let every revenue-recognition remark become a strategic dependency.
_REPORTED_VARIABILITY = re.compile(
    r"\b(?:fluctuate|variability|vary)\w*\b.{0,80}\b(?:quarter|revenue|capex|number|margin)\b"
    r"|\b(?:revenue|capex|margin|number)\w*\b.{0,80}\b(?:fluctuate|variability|vary)\w*\b",
    re.I,
)

#: A forward-looking figure with a horizon. Owned by `ForwardClaim`; a
#: number is not an objective, and this layer must never become a second
#: place where guidance lives.
_GUIDANCE_SHAPE = re.compile(
    r"(?:\$\s?\d|\d+(?:\.\d+)?\s*(?:%|percent|billion|million|basis\s+points))", re.I
)
_FORWARD_MARKER = re.compile(r"\b(?:expect|guidance|outlook|forecast|will\s+be|anticipate)\w*\b", re.I)


def _speaker_is_executive(title: str | None) -> bool:
    if not title:
        return False
    if _ANALYST.search(title) or _OPERATOR.search(title):
        return False
    return bool(_EXECUTIVE.search(title))


def _node_id(company: str, kind: StrategyNodeKind, subject: str, record_id: str) -> str:
    """Stable and content-addressed: the same sentence in the same
    record always produces the same id, which is what makes composition
    idempotent without a registry."""
    digest = hashlib.sha256(f"{company}|{kind.value}|{subject}|{record_id}".encode()).hexdigest()[:12]
    return f"{kind.value}:{company}:{digest}"


def _outcome_in(text: str) -> OutcomeKind | None:
    for kind, pattern in _OUTCOME_PATTERNS:
        if pattern.search(text):
            return kind
    return None


def extract_strategy(
    record: BusinessRecord, *, extracted_at: datetime
) -> tuple[tuple[StrategyNode, ...], tuple[StrategyEdge, ...], tuple[RejectedStrategyCandidate, ...]]:
    """Read one `BusinessRecord`. Never opens a URL, never calls a
    provider, never reads `source_reference`.

    Returns only OBSERVED nodes and the edges whose relation one
    sentence states outright."""
    nodes: list[StrategyNode] = []
    edges: list[StrategyEdge] = []
    rejected: list[RejectedStrategyCandidate] = []

    if record.document_type is not SourceKind.TRANSCRIPT:
        return (), (), ()
    content = record.metadata.get("content")
    if not isinstance(content, str) or not content.strip():
        return (), (), ()

    title = record.metadata.get("title")
    title = title if isinstance(title, str) else None
    # Phase 5, bounded deliberately. A transcript record is one speaker's
    # uninterrupted turn, so "is this speaker talking about their own
    # company?" is a property of the turn, not of each sentence in it.
    #
    # Sentence-level first person was too strict in one direction and
    # too loose in the other. It threw away VST's "The PJM nuclear
    # uprates will require growth capital over an 8-year period" -- a
    # dependency on VST's own assets, stated without a pronoun -- and it
    # admitted AMAT's "deploying AI at large scale requires significant
    # innovation at every level of the technology stack", which is about
    # the industry and sits in a turn that never says "we".
    #
    # The turn is the smallest context that answers the question, it is
    # already a stored record, and provenance is untouched: the evidence
    # is still the sentence, and the turn is only what licensed reading
    # it as this company's.
    speaker_is_self_referential = bool(_FIRST_PERSON.search(content))
    quarter = record.metadata.get("quarter")
    source_period = quarter if isinstance(quarter, str) else None

    def evidence(text: str, polarity: SupportPolarity = SupportPolarity.SUPPORTS) -> StrategyEvidence:
        return StrategyEvidence(
            source_record_id=record.id,
            source_text=text,
            source_kind=record.document_type.value,
            company=record.company,
            source_period=source_period,
            statement_at=None,
            speaker_title=title,
            polarity=polarity,
            extractor_version=EXTRACTOR_VERSION,
        )

    for raw in _SENTENCE.split(content):
        sentence = raw.strip()
        if not sentence or len(sentence) > 600:
            continue

        has_marker = bool(
            _OBJECTIVE.search(sentence)
            or _INITIATIVE.search(sentence)
            or _DEPENDENCY.search(sentence)
            or _COMMITMENT.search(sentence)
            or _THREAT.search(sentence)
            or _ENGINE.search(sentence)
        )
        if not has_marker:
            continue  # not a candidate; not worth a rejection record

        def reject(reason: StrategyRejectionReason) -> None:
            rejected.append(
                RejectedStrategyCandidate(
                    company=record.company, source_record_id=record.id, text=sentence, reason=reason
                )
            )

        if not _speaker_is_executive(title):
            reject(StrategyRejectionReason.NOT_A_COMPANY_INSIDER)
            continue
        if _SAFE_HARBOUR.search(sentence):
            reject(StrategyRejectionReason.SAFE_HARBOUR_BOILERPLATE)
            continue
        if _GENERIC_RISK.search(sentence):
            reject(StrategyRejectionReason.GENERIC_RISK_FACTOR)
            continue
        # An engine is read before the canonical-object requirement,
        # not after it. An engine's terms are economic -- transactions,
        # advertising inventory, fee revenue -- and none of them is a
        # thing the world must supply, so the factor gate rejected every
        # engine sentence in the corpus before it could be read. Its own
        # output requirement is the gate that applies here.
        if _ENGINE.search(sentence) and _ENGINE_OUTPUT.search(sentence):
            engine_factors = resolve_factors(sentence)
            outcome = _outcome_in(sentence)
            node_id = _node_id(record.company, StrategyNodeKind.ECONOMIC_ENGINE, sentence[:60], record.id)
            nodes.append(
                StrategyNode(
                    node_id=node_id,
                    company=record.company,
                    kind=StrategyNodeKind.ECONOMIC_ENGINE,
                    status=EvidenceStatus.OBSERVED,
                    factor=engine_factors[0].factor if engine_factors else None,
                    outcome=outcome,
                    subject_text=sentence[:160],
                    evidence=(evidence(sentence),),
                    observed_periods=(source_period,) if source_period else (),
                )
            )
            continue

        factors = resolve_factors(sentence)
        resources = resolve_resources(sentence)

        # The object check runs before the subject check on purpose. A
        # sentence naming nothing has no assertion in it for anybody --
        # VST's "Depends on what you're measuring off of" is not a third
        # party's strategy, it is no strategy -- and the rejection
        # reason should say which of the two Atlas found.
        if not factors and not resources:
            if _MARKETING.search(sentence):
                reject(StrategyRejectionReason.MARKETING_LANGUAGE)
            elif _GUIDANCE_SHAPE.search(sentence):
                # A marker, a figure, and no strategic object: a number.
                # `ForwardClaim` owns numbers, and holding guidance in a
                # second place is how two layers start disagreeing.
                reject(StrategyRejectionReason.GUIDANCE_NOT_STRATEGY)
            elif _ANAPHOR_OBJECT.search(sentence):
                reject(StrategyRejectionReason.UNRESOLVED_REFERENT)
            else:
                reject(StrategyRejectionReason.NO_CANONICAL_FACTOR)
            continue

        # Whose strategy is this? The first pass answered it with a
        # first-person pronoun, which is a proxy, and the proxy cost
        # real evidence: VST's "The PJM nuclear uprates will require
        # growth capital over an 8-year period" is a dependency
        # statement about VST's own assets, made by a VST executive on
        # VST's own earnings call, and it contains no "we".
        #
        # The direct test is the right one. On a company's own call an
        # executive is speaking about that company unless they name
        # somebody else, so the burden belongs on the third-party
        # frame -- which is checked here, and is the only thing between
        # this layer and recording the whole industry's plans against
        # one issuer.
        if _THIRD_PARTY.search(sentence):
            reject(StrategyRejectionReason.THIRD_PARTY_SUBJECT)
            continue

        # A dependency predicate governing a canonical factor is the
        # strongest reading available, so it is tried first: "the
        # availability of clean room space was a key factor pacing the
        # rate of industry investment" is a dependency, not an
        # initiative, even though the sentence also mentions investment.
        # A geography is not a dependency target. The coverage pass
        # added GEOGRAPHIC_MARKET so that entering a market could be
        # represented, and the dependency rule immediately read "we're
        # running part of the switch in the UAE, and it gives us access
        # to transactions" as a dependency on the UAE -- then derived
        # "availability of in the UAE" as a success condition from it.
        # A market is somewhere a company operates; it is not something
        # the world supplies to it, and the two must not share a rule.
        supplied = tuple(m for m in factors if m.factor is not FactorClass.GEOGRAPHIC_MARKET)
        if _DEPENDENCY.search(sentence) and supplied and not speaker_is_self_referential:
            reject(StrategyRejectionReason.THIRD_PARTY_SUBJECT)
            continue
        if _DEPENDENCY.search(sentence) and supplied and _REPORTED_VARIABILITY.search(sentence):
            reject(StrategyRejectionReason.GUIDANCE_NOT_STRATEGY)
            continue
        if _DEPENDENCY.search(sentence) and supplied and _GENERAL_ACTIVITY_SUBJECT.search(sentence):
            reject(StrategyRejectionReason.THIRD_PARTY_SUBJECT)
            continue
        if _DEPENDENCY.search(sentence) and supplied and _PRODUCT_SPECIFICATION.search(sentence):
            reject(StrategyRejectionReason.NO_STRATEGIC_PREDICATE)
            continue
        if _DEPENDENCY.search(sentence) and supplied and _NEGATED_DEPENDENCY.search(sentence):
            reject(StrategyRejectionReason.DEPENDENCY_DENIED)
            continue
        if _DEPENDENCY.search(sentence) and supplied and _HOLDS_OR_SUPPLIES.search(sentence):
            reject(StrategyRejectionReason.HOLDS_OR_SUPPLIES_FACTOR)
            continue
        if _DEPENDENCY.search(sentence) and supplied:
            for mention in supplied:
                node_id = _node_id(record.company, StrategyNodeKind.DEPENDENCY, mention.factor.value, record.id)
                nodes.append(
                    StrategyNode(
                        node_id=node_id,
                        company=record.company,
                        kind=StrategyNodeKind.DEPENDENCY,
                        status=EvidenceStatus.OBSERVED,
                        factor=mention.factor,
                        subject_text=mention.surface,
                        evidence=(evidence(sentence),),
                        observed_periods=(source_period,) if source_period else (),
                    )
                )
            continue

        # A completed action reported as a result is not a strategy
        # being pursued -- unless it names a resource the company
        # allocates. MA reported the same buyback sentence in four
        # consecutive quarters; that is a capital-allocation policy
        # observed four times, and the first pass threw all four away
        # as history.
        if _HISTORICAL.search(sentence) and not resources:
            reject(StrategyRejectionReason.HISTORICAL_STATEMENT)
            continue

        if _OBJECTIVE.search(sentence):
            outcome = _outcome_in(sentence)
            subject = factors[0].surface if factors else (outcome.value if outcome else resources[0].surface)
            node_id = _node_id(record.company, StrategyNodeKind.OBJECTIVE, subject, record.id)
            nodes.append(
                StrategyNode(
                    node_id=node_id,
                    company=record.company,
                    kind=StrategyNodeKind.OBJECTIVE,
                    status=EvidenceStatus.OBSERVED,
                    factor=factors[0].factor if factors else None,
                    outcome=outcome,
                    subject_text=subject,
                    evidence=(evidence(sentence),),
                    observed_periods=(source_period,) if source_period else (),
                )
            )
            continue

        if _INITIATIVE.search(sentence) and factors:
            mention = factors[0]
            node_id = _node_id(record.company, StrategyNodeKind.INITIATIVE, mention.factor.value, record.id)
            nodes.append(
                StrategyNode(
                    node_id=node_id,
                    company=record.company,
                    kind=StrategyNodeKind.INITIATIVE,
                    status=EvidenceStatus.OBSERVED,
                    factor=mention.factor,
                    subject_text=mention.surface,
                    evidence=(evidence(sentence),),
                    observed_periods=(source_period,) if source_period else (),
                )
            )
            # An outcome named in the same sentence as the initiative is
            # management linking the two, so the edge is OBSERVED. An
            # outcome merely present elsewhere in the call is not.
            outcome = _outcome_in(sentence)
            if outcome is not None:
                outcome_id = _node_id(record.company, StrategyNodeKind.EXPECTED_OUTCOME, outcome.value, record.id)
                nodes.append(
                    StrategyNode(
                        node_id=outcome_id,
                        company=record.company,
                        kind=StrategyNodeKind.EXPECTED_OUTCOME,
                        status=EvidenceStatus.OBSERVED,
                        outcome=outcome,
                        subject_text=outcome.value,
                        evidence=(evidence(sentence),),
                        observed_periods=(source_period,) if source_period else (),
                    )
                )
                edges.append(
                    StrategyEdge(
                        source_id=node_id,
                        target_id=outcome_id,
                        relation=RelationKind.INTENDED_TO_PRODUCE,
                        status=EvidenceStatus.OBSERVED,
                        evidence=(evidence(sentence),),
                    )
                )
            if _CONDITION.search(sentence):
                condition_id = _node_id(
                    record.company, StrategyNodeKind.SUCCESS_CONDITION, mention.factor.value, record.id
                )
                nodes.append(
                    StrategyNode(
                        node_id=condition_id,
                        company=record.company,
                        kind=StrategyNodeKind.SUCCESS_CONDITION,
                        status=EvidenceStatus.OBSERVED,
                        factor=mention.factor,
                        subject_text=mention.surface,
                        evidence=(evidence(sentence),),
                        observed_periods=(source_period,) if source_period else (),
                    )
                )
            continue

        if _COMMITMENT.search(sentence) and resources:
            mention = resources[0]
            node_id = _node_id(record.company, StrategyNodeKind.RESOURCE_COMMITMENT, mention.resource.value, record.id)
            nodes.append(
                StrategyNode(
                    node_id=node_id,
                    company=record.company,
                    kind=StrategyNodeKind.RESOURCE_COMMITMENT,
                    status=EvidenceStatus.OBSERVED,
                    resource=mention.resource,
                    subject_text=mention.surface,
                    evidence=(evidence(sentence),),
                    observed_periods=(source_period,) if source_period else (),
                )
            )
            continue

        if _THREAT.search(sentence) and factors:
            mention = factors[0]
            node_id = _node_id(record.company, StrategyNodeKind.FAILURE_MODE, mention.factor.value, record.id)
            nodes.append(
                StrategyNode(
                    node_id=node_id,
                    company=record.company,
                    kind=StrategyNodeKind.FAILURE_MODE,
                    status=EvidenceStatus.OBSERVED,
                    factor=mention.factor,
                    subject_text=mention.surface,
                    evidence=(evidence(sentence),),
                    observed_periods=(source_period,) if source_period else (),
                )
            )
            continue

        reject(StrategyRejectionReason.NO_STRATEGIC_PREDICATE)

    return tuple(nodes), tuple(edges), tuple(rejected)
