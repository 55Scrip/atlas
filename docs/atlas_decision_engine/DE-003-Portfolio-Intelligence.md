# DE-003 — Atlas Portfolio Intelligence

**Status:** Draft v0.1. Companion specification to
`docs/ATLAS_DECISION_ENGINE_DOCTRINE.md` §3. Governed by, and subordinate to,
that Doctrine and to `APP-000`. Documentation only — no code accompanies this
specification.

## 1. Principle

Atlas SHALL NOT evaluate a company in isolation from the portfolio it would
join or already belongs to. This is `ATLAS_CONSTITUTION.md`'s Non-Negotiable
Principle "Portfolio before position," applied concretely: every Atlas
Recommendation (`DE-001`) SHALL state which of the seven factors below
actually informed its direction, per `DE-002` §2.4 (Portfolio Context).

This specification is also, directly, an application of `APS-006`
`PFINV-004` (Single Priority Model): *"Portfolio SHALL NOT create an
independent priority or ranking model separate from the Atlas Priority
Model."* The seven factors below are not a competing ranking system — they
are the inputs this Doctrine's own Recommendation Framework (`DE-001`) uses;
Portfolio's own product surface continues to read, not compute, any
resulting priority, exactly as `PFINV-004` and `PFINV-003` ("No Deep
Reasoning Ownership") already require.

## 2. Grounding in What Is Already Implemented

Two of the seven factors already have a live, deterministic data model this
specification builds directly on, rather than inventing a parallel one:

- **Allocation** — `atlas/domains/portfolio/models.py`'s `Allocation`
  dataclass (name, market value, weight, holdings count per category).
- **Concentration** — the same module's `Concentration` dataclass and its
  `ConcentrationLevel` enum: `LOW`, `MODERATE`, `ELEVATED`, `HIGH` — already
  computed, already surfaced (in English and Swedish) on the Portfolio page.

The remaining five factors — Diversification, Correlation, Opportunity Cost,
Existing Thesis, and Previous Decisions — have no equivalent computed data
model in the codebase today. This specification states honestly, per
`ATLAS_CONSTITUTION.md`'s Trust Principles, that these are new doctrine, not
descriptions of something already running: they define what a future
implementation phase must compute, not what it currently computes.

## 3. The Seven Factors

### Current Allocation

What share of the portfolio this position represents (or would represent),
by market value and by category (sector, geography, or another dimension
already meaningful to this Investor's portfolio). Sourced from the existing
`Allocation` dataclass.

### Concentration

Whether this position, existing or proposed, pushes the portfolio's
concentration — largest single holding, top-five weight — toward a level
this specification treats as a genuine input to Trim and Exit reasoning
(`DE-001`). Sourced from the existing `Concentration`/`ConcentrationLevel`
data. A `HIGH` or `ELEVATED` concentration level is not, by itself, a
recommendation — it is one factor `DE-002` §2.4 requires be named when it
bears on the direction reached.

### Diversification

Whether this position adds exposure the portfolio does not already have, or
duplicates exposure it already holds in depth — a sector, a business model,
a geographic dependency, or a specific risk factor already well-represented
elsewhere in the portfolio. Not yet computed anywhere in the codebase; this
specification states the factor Atlas SHALL consider, leaving the specific
computation method to the implementation phase.

### Correlation

Whether this position tends to move with, or independently of, the
portfolio's existing holdings — relevant specifically to Buy and Add
reasoning, where a position that is highly correlated with existing large
holdings adds less genuine diversification than its allocation weight alone
would suggest. Not yet computed anywhere in the codebase; stated here as a
required factor, not a required algorithm.

### Opportunity Cost

What the capital committed to this position could otherwise be doing —
whether another candidate, or simply an existing position with a stronger
current thesis, would make better use of the same capital. This is the
direct portfolio-level counterpart to `DE-001`'s Business Evaluation and
Valuation Philosophy content: a Buy recommendation is not just "is this a
good business at a fair price" but "is this the best use of the capital
this Investor has available to commit." `UX-012B`'s own "Comparison"
component (`UX-012B` — comparison to alternatives, qualitative prose, no
numeric scores or rankings) is the existing product-surface precedent for
presenting this factor to the Investor; this specification does not alter
that component, only states that Atlas's own reasoning SHALL consider
opportunity cost as a distinct factor.

### Existing Thesis

For a position already held, what the original or most recently updated
thesis actually claimed, and whether the recommendation being reasoned
toward is consistent with, or a revision of, that thesis. Sourced from
Decision Memory (`DE-005`) — this factor is where `DE-003` and `DE-005`
meet: Portfolio Intelligence asks whether the thesis still holds; Decision
Memory is where that thesis and its history are actually recorded.

### Previous Decisions

What the Investor has already decided about this position — prior Buy,
Add, Trim, or Exit decisions, and prior Outcomes reported against them.
Sourced from the same recorded Decision and Outcome history `DE-005`
specifies. A recommendation SHALL NOT be reasoned as though a position's
history began at the moment of the current recommendation.

## 4. Application Rule

Not every recommendation requires all seven factors stated explicitly.
`DE-002` §2.4 requires that a recommendation name the factors that actually
informed its direction — a Buy recommendation for a new position necessarily
engages Allocation, Concentration, Diversification, Correlation, and
Opportunity Cost, but has no Existing Thesis or Previous Decisions to draw
on; a Hold recommendation may turn almost entirely on Existing Thesis. The
requirement is relevance, not exhaustive recitation — per `APP-000` PP-004,
complexity disclosed progressively, withheld by default.
