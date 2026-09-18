"""Strategy & Dependency Intelligence, v1 -- the vocabulary.

**What this layer is for.** Atlas can already say that FCF yield is low,
that financial risk is high, that management raised guidance and that two
contracted-volume claims exist. What it could not say is what the company
is *trying to do*, what it is *committing* to that attempt, and what that
attempt *materially depends on*. Those are different questions from every
question Atlas already answers, and none of the existing objects can be
stretched to answer them without destroying what they mean.

**The five layers, kept apart.** A source observation ("2027 capital
expenditure is expected to increase materially") is not a structured
strategic interpretation ("the company is committing capital to
infrastructure"), which is not a causal hypothesis ("that depends on
converting capacity into monetization"), which is not an investment
consequence ("higher capex may be value-creating"), which is not a
recommendation. This package builds the first three and stops. Nothing
here is imported by anything that decides -- pinned by
`tests/unit/analysis_engine/strategy/test_integration_safety.py`, the
same way `forward_claims` is pinned.

**Not a narrative machine.** Every object here is a structured,
falsifiable record with a verbatim passage behind it. Prose exists only
in the diagnostic renderer, over the structure, never instead of it.
"""
from __future__ import annotations

from enum import Enum

__all__ = [
    "EvidenceStatus",
    "StrategyNodeKind",
    "RelationKind",
    "SupportPolarity",
    "FactorClass",
    "ResourceKind",
    "OutcomeKind",
    "StrategyRejectionReason",
    "ContinuityState",
]


class EvidenceStatus(str, Enum):
    """How Atlas came to hold an assertion. Four states, never collapsed
    into "Atlas knows", because the difference between them is the
    difference between reading a company and guessing about one."""

    OBSERVED = "observed"
    """A company insider said it, and the verbatim passage says it. The
    assertion adds no proposition the passage does not contain. This is
    the only status extraction can produce."""

    DERIVED = "derived"
    """Atlas composed it from two or more OBSERVED records by a named,
    deterministic rule, and the rule's inputs travel with it. Not found
    in any single passage; reproducible from the passages that are."""

    HYPOTHESIS = "hypothesis"
    """The evidence makes a relation plausible and does not establish
    it. A cross-company factor match is the canonical case: two
    companies naming the same canonical factor is a structural
    adjacency, not a commercial relationship. A hypothesis is a question
    Atlas has earned the right to ask, never an answer."""

    UNKNOWN = "unknown"
    """Atlas cannot currently determine it. Carried explicitly -- an
    `EconomicEngine` with UNKNOWN mechanism is a different and more
    honest object than no engine at all, and than a fabricated one."""


class StrategyNodeKind(str, Enum):
    """The node types v1 can represent. Each exists because the
    benchmark corpus actually produced instances of it; a kind Atlas
    cannot extract would read as a capability."""

    ECONOMIC_ENGINE = "economic_engine"
    OBJECTIVE = "objective"
    INITIATIVE = "initiative"
    RESOURCE_COMMITMENT = "resource_commitment"
    DEPENDENCY = "dependency"
    EXPECTED_OUTCOME = "expected_outcome"
    SUCCESS_CONDITION = "success_condition"
    FAILURE_MODE = "failure_mode"


class RelationKind(str, Enum):
    """Typed edges. The graph is compositional on purpose: A requires
    factor X and B provides factor X are two independent edges, and the
    composition of the two is a third object with its own weaker status
    -- never a fourth edge asserting that B benefits from A."""

    PURSUED_BY = "pursued_by"
    """OBJECTIVE -> INITIATIVE."""
    REQUIRES = "requires"
    """INITIATIVE -> RESOURCE_COMMITMENT."""
    DEPENDS_ON = "depends_on"
    """INITIATIVE | OBJECTIVE -> DEPENDENCY."""
    INTENDED_TO_PRODUCE = "intended_to_produce"
    """INITIATIVE -> EXPECTED_OUTCOME."""
    CONDITIONED_ON = "conditioned_on"
    """EXPECTED_OUTCOME -> SUCCESS_CONDITION."""
    THREATENED_BY = "threatened_by"
    """DEPENDENCY | INITIATIVE -> FAILURE_MODE."""
    EXPANDS_IN = "expands_in"
    """INITIATIVE -> GEOGRAPHIC_MARKET. Named separately from
    BUILDS_CAPACITY_IN because entering a market is not adding capacity
    to a factor, and joining the two would put MA's UAE switch and
    Alphabet's data centres in the same bucket."""

    CONVERTS = "converts"
    """ECONOMIC_ENGINE -> the inputs and outputs it names. See
    `EconomicMechanism`: an engine is a conversion, and the edge has to
    be able to say so."""

    BUILDS_CAPACITY_IN = "builds_capacity_in"
    """INITIATIVE -> canonical factor.

    **Not "provides".** The first benchmark run named this PROVIDES and
    it was wrong: an initiative naming a factor is a company *adding to*
    that factor, and nothing in the sentence says who gets the output.
    Alphabet building data centres is building compute capacity for
    Alphabet. Reading that as supply would have produced "GOOGL provides
    compute capacity to NVDA" from two unrelated sentences -- a
    commercial relationship invented by a join.

    What the edge supports is weaker and real: this company is exposed
    to this factor from the building side, and another company may be
    exposed to it from the needing side."""


class SupportPolarity(str, Enum):
    """What a piece of evidence does to an assertion.

    There are three members, not two, and the absence of a member is a
    fourth thing again: **no supporting evidence is not contradiction.**
    An initiative nobody mentioned this quarter is unmentioned, not
    abandoned, and an outcome nobody confirmed is unconfirmed, not
    refuted. Collapsing those would let silence argue."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    CONTEXT = "context"
    """Relevant, and neither confirming nor denying."""


class FactorClass(str, Enum):
    """Canonical dependency targets -- the smallest normalization the
    benchmark evidence justifies, and the join key that lets two
    companies meet without either one naming the other.

    Derived from the corpus, not from an ontology: each member is a
    concrete thing at least two benchmark companies actually talk about
    needing. Deliberately absent is a class for "AI", which appears
    266-446 times per benchmark company and denotes a topic rather than
    a factor -- see `test_over_inference`. A topic that frequent would
    connect every company to every other one and mean nothing."""

    ELECTRIC_POWER = "electric_power"
    COMPUTE_CAPACITY = "compute_capacity"
    PRODUCTION_CAPACITY = "production_capacity"
    SUPPLY_CHAIN_INPUTS = "supply_chain_inputs"
    CUSTOMER_DEMAND = "customer_demand"
    CAPITAL_FINANCING = "capital_financing"
    LABOR_CAPABILITY = "labor_capability"
    REGULATORY_APPROVAL = "regulatory_approval"
    LAND_AND_SITES = "land_and_sites"
    DISTRIBUTION_NETWORK = "distribution_network"

    # --- added in the coverage pass, from the MA falsification -------
    # The first four classes above are things the physical world must
    # supply. Run against a capital-light network business they
    # recovered one objective and one initiative from 188 statements,
    # while MA spent those statements describing exactly what it
    # depends on -- in a vocabulary the ontology could not hold. These
    # three are what that corpus actually names.

    PARTNER_ECOSYSTEM = "partner_ecosystem"
    """Other firms whose participation the strategy needs: MA's issuers
    and fintech partners, AMAT's eight named co-innovation partners.
    Distinct from DISTRIBUTION_NETWORK, which is the channel itself --
    a partner is a counterparty, a channel is a route to a customer."""

    CUSTOMER_ADOPTION = "customer_adoption"
    """Whether customers actually take the thing up. Distinct from
    CUSTOMER_DEMAND, and the distinction is the point: demand is
    appetite for what already exists, adoption is a behaviour change
    the strategy requires. MA's "essential for merchant adoption" is a
    dependency on adoption; it says nothing about demand."""

    GEOGRAPHIC_MARKET = "geographic_market"
    """A named market the strategy moves into or scales within. MA's
    UAE switch, Mexico partnership and South African deals; GOOGL's
    "more than a dozen new countries"; AMAT's Arizona facility.
    Geographic expansion was invisible to the first ontology, which had
    no way to say that entering a market is a strategic act."""


class ResourceKind(str, Enum):
    """What management is committing. Kept separate from `FactorClass`:
    a resource is something the company spends or allocates, a factor is
    something the world must supply. Capital is both, in two different
    sentences, and the two must not be silently merged."""

    CAPITAL = "capital"
    CAPITAL_EXPENDITURE = "capital_expenditure"
    RESEARCH_AND_DEVELOPMENT = "research_and_development"
    HEADCOUNT = "headcount"
    PRODUCTION_CAPACITY = "production_capacity"
    INVENTORY = "inventory"
    ACQUISITION = "acquisition"
    SHARE_REPURCHASE = "share_repurchase"


class OutcomeKind(str, Enum):
    """Intended economic outcomes, in Atlas's existing economic
    vocabulary wherever one exists. `REVENUE_GROWTH`, `MARGIN_EXPANSION`
    and `CASH_GENERATION` deliberately echo `EconomicDimension` so the
    two layers can later be compared; they are not the same objects and
    are not interchangeable."""

    REVENUE_GROWTH = "revenue_growth"
    MARGIN_EXPANSION = "margin_expansion"
    COST_REDUCTION = "cost_reduction"
    CASH_GENERATION = "cash_generation"
    CAPACITY_GROWTH = "capacity_growth"
    CUSTOMER_GROWTH = "customer_growth"
    MONETIZATION = "monetization"


class EngineElementRole(str, Enum):
    """Where an element sits in an economic engine.

    The coverage pass replaced the first definition of an engine --
    "an initiative plus an outcome" -- which described *strategy*, not
    economics, and returned UNKNOWN for all four benchmarks. An engine
    is how the business that already exists turns something it has into
    money: MA's "we can get access to more transactions, which fuel our
    virtuous cycle", GOOGL's "the core engine of our search ads relies
    on a dual prediction, delivering immediate utility for the user
    while maximizing measurable value for the advertiser". Both name a
    conversion. Neither is an initiative."""

    INPUT = "input"
    """What the business puts in, or already holds: network
    participation, user engagement, installed capacity, installed
    base."""
    MECHANISM = "mechanism"
    """The conversion itself, in management's own words."""
    OUTPUT = "output"
    """What comes out, economically: transaction activity, advertising
    inventory, generated electricity, equipment demand."""


class ContinuityState(str, Enum):
    """What a strategy node is doing across periods. v1 supports the
    first three honestly and refuses the fourth: ABANDONED cannot be
    read from silence, and the corpus contains no statement in which
    management says it stopped doing something it previously said it
    was doing."""

    NEW = "new"
    """First observed in this period, with no matching earlier node."""
    CONTINUING = "continuing"
    """The same assertion, restated in a later period. One node, several
    observations -- never several nodes."""
    MODIFIED = "modified"
    """The same subject, with a materially different object or resource
    in a later period."""


class StrategyRejectionReason(str, Enum):
    """Why a candidate sentence produced no node. Real, inspectable
    output: "Atlas found no strategy in this call" and "Atlas rejected
    eleven candidates for these reasons" are materially different
    answers, and the second is the one that can be audited."""

    NOT_A_COMPANY_INSIDER = "not_a_company_insider"
    """An analyst asking what the strategy is, or the operator."""
    MARKETING_LANGUAGE = "marketing_language"
    """"We are excited about", "we are well positioned", "our strategy
    is clear". Sentiment about a strategy is not a strategy."""
    NO_CANONICAL_FACTOR = "no_canonical_factor"
    """The sentence carries a strategy marker and names nothing Atlas
    can identify -- so there is no assertion to record, only a mood."""
    UNRESOLVED_REFERENT = "unresolved_referent"
    """The object is anaphoric: "we're expanding that portfolio", "we
    will persist with this initiative". The referent is in a previous
    sentence Atlas does not carry, so the node would name nothing."""
    SAFE_HARBOUR_BOILERPLATE = "safe_harbour_boilerplate"
    """"Today's call includes forward-looking statements which are
    subject to risks and uncertainties." The single most common
    dependency-marker sentence in the corpus, and never a dependency."""
    GENERIC_RISK_FACTOR = "generic_risk_factor"
    """Filing boilerplate -- "could adversely affect our business,
    financial condition and results of operations" -- with no named
    dependency and no materiality. A risk factor is not a failure
    mode."""
    GUIDANCE_NOT_STRATEGY = "guidance_not_strategy"
    """A forward-looking figure for a company-level measure, with no
    strategic object attached. `ForwardClaim` already owns this, and a
    number is not an objective."""
    THIRD_PARTY_SUBJECT = "third_party_subject"
    """The sentence is about what a customer, competitor or the industry
    depends on, not about this company's own strategy."""
    HISTORICAL_STATEMENT = "historical_statement"
    """A completed past action reported as a result, not a strategy
    being pursued."""
    DEPENDENCY_DENIED = "dependency_denied"
    """Management said the opposite: "we do not see equipment or EPC as
    the gating items". Recording this as a dependency would make Atlas
    confidently wrong, which is worse than silent."""
    HOLDS_OR_SUPPLIES_FACTOR = "holds_or_supplies_factor"
    """"We also have ample access to high-voltage equipment" is
    sufficiency, and "our co-innovation model provides chip makers
    earlier access to process technology" is the company being someone
    else's supply. Neither is a dependency, and both contain "access
    to"."""
    NO_STRATEGIC_PREDICATE = "no_strategic_predicate"
    """A factor is named, with no objective, initiative or dependency
    predicate governing it -- a mention, not a commitment."""
