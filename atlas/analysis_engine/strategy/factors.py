"""Canonical factor identity -- the join key, and the semantic gate.

**Why this exists twice over.** A dependency is only useful if two
companies can express the same one without either naming the other, so
dependency targets need canonical identities. And a strategy sentence is
only an assertion if it names something: "our strategy is clear, and
we're executing against it" carries every strategy marker in the
language and asserts nothing. Requiring a canonical factor or resource
solves both problems with one rule, and rejects marketing prose as a
side effect rather than by a blocklist of adjectives.

**Identity is by explicit mapping, never by string similarity.** "AI
compute", "computing infrastructure" and "accelerator capacity" may or
may not be the same factor, and no edit distance can tell. Each surface
phrase is listed under exactly one class by a decision recorded here,
with the corpus evidence that motivated it. Two phrases that merely look
alike are two factors until someone decides otherwise -- see
`test_conservative_non_merge`.

**Bare ambiguous words are never factors.** The corpus is emphatic
about this: in MA's calls "power" is almost always a verb ("ways to
power payments", "will now power Mastercard Global"), and in GOOGL's it
is usually figurative ("the power of conversational AI"). A single word
that common cannot carry a dependency, so every pattern here requires a
compound noun phrase. The cost is recall -- Atlas will miss real
dependencies stated in one word -- and that is the correct trade for a
layer whose whole value is that its edges mean something.

**"AI" is deliberately not a factor.** It appears 266-446 times per
benchmark company. A factor that universal would join every company to
every other and carry no information; it names a topic, not a thing one
company needs and another supplies.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from atlas.analysis_engine.strategy.contracts import FactorClass, ResourceKind

__all__ = [
    "FACTOR_RESOLVER_VERSION",
    "FactorMention",
    "ResourceMention",
    "resolve_factors",
    "resolve_resources",
    "surface_forms",
]

#: Bumped whenever a pattern below changes in a way that could alter
#: which factors resolve. Stamped onto every node so an older node stays
#: distinguishable from a newer one without re-reading the source.
FACTOR_RESOLVER_VERSION = "strategy-factors-1"


#: Surface phrases by canonical class. Every entry is a phrase at least
#: one benchmark company actually used; the comment on each class names
#: the companies that motivated it, so a future editor can see whether a
#: proposed addition has the same kind of backing.
_PATTERNS: dict[FactorClass, tuple[str, ...]] = {
    # VST (generation fleet, PJM/ERCOT capacity), GOOGL and AMAT (both
    # speak about powering data centres as a constraint, not a verb).
    FactorClass.ELECTRIC_POWER: (
        r"electric(?:al|ity)?\s+power",
        r"power\s+(?:generation|capacity|markets?|supply|prices?|demand|plants?|purchase\s+agreements?)",
        r"generation\s+(?:capacity|fleet|assets)",
        r"megawatts?\b",
        r"\bMW\b",
        r"(?:the\s+)?(?:electric(?:ity)?\s+)?grid\b",
        r"transmission\s+(?:capacity|infrastructure|lines?)",
        r"interconnection(?:\s+queue)?",
        r"nuclear\s+(?:generation|capacity|fleet|plants?|units?|uprates?)",
        r"natural\s+gas\s+(?:supply|plants?|generation|capacity)",
        # VST says "customer PPAs" far more often than it spells the
        # phrase out; the acronym was invisible to the first pass.
        r"\bPPAs?\b",
    ),
    # GOOGL (TPU/third-party capacity), AMAT (customers' compute build).
    FactorClass.COMPUTE_CAPACITY: (
        r"compute\s+(?:capacity|resources|infrastructure|supply|demand)",
        r"computing\s+(?:capacity|infrastructure|power)",
        r"data\s?cent(?:er|re)s?\b",
        r"accelerator\s+(?:capacity|supply)",
        r"(?:server|cloud)\s+capacity",
        r"\bTPUs?\b",
        r"\bGPUs?\b",
    ),
    # AMAT (fab and clean-room capacity pacing industry investment), VST.
    FactorClass.PRODUCTION_CAPACITY: (
        r"manufacturing\s+capacity",
        r"production\s+capacity",
        r"clean\s?room(?:\s+(?:space|capacity))?",
        r"\bfabs?\b",
        r"wafer\s+(?:capacity|starts?|fab\w*)",
        r"capacity\s+(?:expansions?|additions?|constraints?)",
    ),
    # AMAT and GOOGL (component availability, supply constraints).
    FactorClass.SUPPLY_CHAIN_INPUTS: (
        r"supply\s+chains?\b",
        r"(?:availability|supply)\s+of\s+(?:supply|components?|parts?|materials?|equipment|chips?|memory)",
        r"component\s+(?:supply|availability|pricing|shortages?)",
        r"(?:semiconductor|memory|DRAM|NAND)\s+supply",
        r"supplier\s+(?:capacity|base)",
        r"supply[- ]constrained",
        # "The loss of access to DRAM has significantly affected us"
        # (AMAT) is a dependency statement that named the input without
        # the word "supply" anywhere near it.
        r"access\s+to\s+(?:DRAM|NAND|memory|components?|equipment|materials?|chips?)",
        r"high[- ]voltage\s+equipment",
    ),
    # All four; the one factor every business model has an opinion about.
    FactorClass.CUSTOMER_DEMAND: (
        r"customer\s+demand",
        r"end[- ]market\s+demand",
        r"demand\s+(?:environment|from\s+customers?|for\s+our\s+\w+)",
        r"(?:large\s+)?load\s+growth",
        r"consumer\s+spending",
    ),
    # VST (project financing), MA and GOOGL (capital for investment).
    FactorClass.CAPITAL_FINANCING: (
        r"(?:project|debt|external)\s+financing",
        r"access\s+to\s+capital",
        r"cost\s+of\s+capital",
        r"capital\s+markets?\b",
        r"credit\s+(?:markets?|facilit\w+)",
        # VST: "we plan to make a final decision on financing". The
        # first pass required the word to be qualified.
        r"\bfinancing\b",
    ),
    # AMAT, MA, VST -- skilled labour named as a constraint.
    FactorClass.LABOR_CAPABILITY: (
        r"(?:skilled|technical|engineering)\s+(?:labor|labour|talent|workforce)",
        r"labor\s+(?:availability|markets?|costs?|shortages?)",
        r"(?:hiring|talent)\s+(?:pipeline|constraints?)",
    ),
    # VST (plant permits, PJM rules), AMAT (export controls).
    FactorClass.REGULATORY_APPROVAL: (
        r"regulatory\s+(?:approvals?|framework|environment|clarity)",
        r"(?:construction|environmental|operating)\s+permits?",
        r"export\s+(?:controls?|licen[cs]es?)",
        r"license\s+(?:renewals?|extensions?)",
        r"market\s+rules?\b",
    ),
    # VST (sites and land for new generation), MA (merchant locations).
    FactorClass.LAND_AND_SITES: (
        r"\bland\s+(?:acquisitions?|positions?|parcels?)\b",
        r"\bsites?\s+(?:for|selection|development)",
        r"(?:brownfield|greenfield)\s+sites?",
        # "our Permian gas site, which we are expanding by adding
        # turbines" -- a site named by possession rather than purpose.
        r"(?:our|existing)\s+(?:[\w-]+\s+){0,3}sites?\b",
    ),
    # MA (network, merchants, issuers), GOOGL (distribution partners).
    FactorClass.DISTRIBUTION_NETWORK: (
        r"(?:payment|acceptance|merchant|distribution)\s+networks?",
        r"merchant\s+(?:acceptance|base|network)",
        r"issuer\s+(?:relationships?|partners?)",
        r"distribution\s+(?:partners?|agreements?|channels?)",
    ),
    # MA names counterparties constantly; AMAT named eight of them in
    # one sentence. A partner is a firm whose participation the strategy
    # needs, which is not a channel and not a customer.
    FactorClass.PARTNER_ECOSYSTEM: (
        r"(?:our|the)\s+partners?\b",
        r"partnerships?\b",
        r"co[- ]innovation\s+\w+",
        r"(?:issuer|fintech|bank|ecosystem)\s+partners?",
        r"partner\s+(?:ecosystems?|networks?|base)",
        r"(?:working|work)\s+with\s+partners",
    ),
    # Adoption is a behaviour change the strategy requires, and is not
    # demand. MA: "essential for merchant adoption and ease of use".
    FactorClass.CUSTOMER_ADOPTION: (
        r"(?:customer|merchant|issuer|consumer|user|developer)\s+adoption",
        r"adoption\s+(?:of|by|rates?|curves?)",
        r"(?:customers?|merchants?|issuers?|users?)\s+(?:to\s+)?(?:adopt|participate)\w*",
        r"enable\s+our\s+(?:global\s+)?(?:issuer|merchant|customer)\s*\w*\s*base",
    ),
    # A named market the strategy moves into. Requires a real place --
    # a country, region or "new markets" -- never a bare "market",
    # which every call says a hundred times about nothing in particular.
    FactorClass.GEOGRAPHIC_MARKET: (
        r"\bin\s+(?:the\s+)?(?:U\.?S\.?|U\.?K\.?|UAE|EU|China|India|Mexico|Brazil|Japan|Korea"
        r"|Germany|France|Texas|Arizona|Europe|Asia|Africa|Latin\s+America|North\s+America)\b",
        r"(?:new|additional|more\s+than\s+a\s+dozen)\s+(?:countries|markets|geographies|regions)",
        r"(?:global|international|geographic)\s+(?:expansion|footprint|rollout)",
        r"\bglobally\b",
    ),
}

#: Resource kinds, by the phrase management uses when committing one.
#: Narrower than the factor patterns on purpose: a resource commitment
#: needs a first-person commitment verb around it (see `extraction`), so
#: these patterns only have to name the resource.
_RESOURCE_PATTERNS: dict[ResourceKind, tuple[str, ...]] = {
    ResourceKind.CAPITAL_EXPENDITURE: (r"capital\s+expenditures?", r"\bcapex\b"),
    # Negative lookaheads earned on the first benchmark run: "capital
    # markets" is a factor the world supplies, not a resource this
    # company allocates, and "investment-grade credit ratings" is a
    # rating, not an investment. Both matched a bare \binvestments?\b
    # and produced a resource commitment out of a balance-sheet remark.
    ResourceKind.CAPITAL: (
        r"\bcapital\b(?!\s*(?:markets?|structure|grade))",
        r"\binvestments?\b(?!\s*[-\u2011\u2013]\s*grade)(?!-grade)",
        # The bare verb forms. AMAT's "we plan to invest more than $200
        # million in Arizona" and VST's "$1 billion to be invested over
        # time" both matched nothing, because the first pass listed the
        # gerund and the noun and forgot the verb.
        r"\binvest(?:ing|ed|s)?\b",
    ),
    ResourceKind.RESEARCH_AND_DEVELOPMENT: (r"\bR\s?&\s?D\b", r"research\s+and\s+development"),
    ResourceKind.HEADCOUNT: (
        r"\bheadcount\b", r"\bhiring\b", r"\bemployees\b",
        # VST: "we're adding people"; AMAT: "adding to our customer
        # engineers". Both are headcount commitments in plain words.
        r"adding\s+(?:to\s+our\s+)?(?:people|staff|engineers|teams?)",
        r"\bworkforce\b",
    ),
    ResourceKind.PRODUCTION_CAPACITY: (r"manufacturing\s+capacity", r"production\s+capacity", r"new\s+capacity"),
    ResourceKind.INVENTORY: (r"\binventor(?:y|ies)\b",),
    ResourceKind.ACQUISITION: (r"\bacquisitions?\b", r"\bacquired?\b", r"\bacquiring\b"),
    ResourceKind.SHARE_REPURCHASE: (r"(?:share|stock)\s+repurchases?", r"\brepurchased?\b", r"\bbuybacks?\b"),
}


def _compile(patterns: dict) -> dict:
    return {key: tuple(re.compile(p, re.I) for p in pats) for key, pats in patterns.items()}


_COMPILED_FACTORS = _compile(_PATTERNS)
_COMPILED_RESOURCES = _compile(_RESOURCE_PATTERNS)


@dataclass(frozen=True)
class FactorMention:
    """One canonical factor, and the exact words that resolved it. The
    surface form travels because two companies meeting at
    `ELECTRIC_POWER` should be inspectable down to "power markets" and
    "generation capacity" -- a reader has to be able to disagree with
    the merge."""

    factor: FactorClass
    surface: str
    resolver_version: str = FACTOR_RESOLVER_VERSION


@dataclass(frozen=True)
class ResourceMention:
    resource: ResourceKind
    surface: str
    resolver_version: str = FACTOR_RESOLVER_VERSION


def resolve_factors(text: str) -> tuple[FactorMention, ...]:
    """Every canonical factor named in `text`, in class order, each once.

    A phrase resolving to two classes is a mapping error, not a runtime
    ambiguity: the patterns are disjoint by construction and a test
    holds them so."""
    found: list[FactorMention] = []
    seen: set[FactorClass] = set()
    for factor, patterns in _COMPILED_FACTORS.items():
        for pattern in patterns:
            match = pattern.search(text)
            if match is not None and factor not in seen:
                seen.add(factor)
                found.append(FactorMention(factor=factor, surface=match.group(0).strip()))
                break
    return tuple(found)


def resolve_resources(text: str) -> tuple[ResourceMention, ...]:
    """Resource kinds named in `text`.

    Order matters here and does not for factors: `CAPITAL_EXPENDITURE`
    is checked before `CAPITAL`, because "capital expenditure" contains
    "capital" and the narrower reading is the true one. The dict is
    ordered accordingly and a test pins that ordering."""
    found: list[ResourceMention] = []
    seen: set[ResourceKind] = set()
    matched_spans: list[tuple[int, int]] = []
    for resource, patterns in _COMPILED_RESOURCES.items():
        for pattern in patterns:
            match = pattern.search(text)
            if match is None or resource in seen:
                continue
            # A narrower resource already claimed these characters --
            # "capital" inside "capital expenditure" is not a second
            # commitment.
            if any(start <= match.start() < end for start, end in matched_spans):
                continue
            seen.add(resource)
            matched_spans.append((match.start(), match.end()))
            found.append(ResourceMention(resource=resource, surface=match.group(0).strip()))
            break
    return tuple(found)


def surface_forms(factor: FactorClass) -> tuple[str, ...]:
    """The raw patterns behind a class, for the diagnostic renderer and
    for anyone auditing what Atlas considers the same thing."""
    return _PATTERNS[factor]
