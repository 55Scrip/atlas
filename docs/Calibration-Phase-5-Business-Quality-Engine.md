# Calibration Phase 5 — Business Quality Engine

Atlas is stronger at evaluating financial evidence than business quality. This
document is Phase 1–2's required "document before implementing." Part A is the
research synthesis; Part B is the confirmed architecture; Parts C–F design the
four deliverables (Moat, Management, Reinvestment, integrated Score); Part G
is the recommendation-integration design; Part H is the file/package plan.

## Part A — Business Quality Research (Phase 1)

Reviewed the recurring analytical content behind long-horizon quality/
compounder investing (Buffett/Munger's moat-and-rationality framework, Nick
Sleep's "scale economics shared" and duration-of-compounding lens, Terry
Smith's "buy good companies, don't overpay, do nothing" ROCE-and-cash-
conversion discipline, Chuck Akre's three-legged stool, Mark Leonard's
decentralized serial-acquirer capital-allocation discipline, and general
quality-investing literature). Per the brief, no single philosophy is
adopted — the themes below are what multiple independent frameworks converge
on, stripped of any one investor's own vocabulary.

**Eleven recurring themes**, not tied to any one investor: (1) durable
competitive advantage — brand, switching costs, network effects, cost
leadership, regulatory/IP barriers, distribution, efficient scale, never
inferred from size or market cap alone; (2) sustained high returns on
capital — the most common *quantitative* proxy that a moat is real; (3)
reinvestment runway at high incremental returns — a business with nowhere
left to deploy capital well stops compounding, a separate question from
whether it is *currently* good; (4) management as capital allocators and
operators, judged on decisions made, never personality or communication
style; (5) revenue quality — recurring vs. one-off, mission-criticality as a
real switching-cost proxy, customer concentration risk; (6) margin structure
as the externally-visible trace pricing power leaves in financial
statements; (7) capital intensity — asset-light models convert more profit
into distributable, reinvestable cash; (8) industry structure as a context
modifier, not a standalone score; (9) growth durability (secular) vs.
cyclicality (mean-reverting); (10) balance-sheet resilience as a
survivability precondition for compounding through a downturn; (11)
simplicity/understandability — a confidence modifier on every other
assessment, not a dimension of its own.

**How the brief's 21 suggested dimensions map onto these themes**: most are
facets, not independent axes. Competitive Advantage, Market Position,
Pricing Power, Customer Stickiness, Switching Costs, Network Effects, Brand
Strength, Scale Advantages, Cost Advantages → all facets of theme 1, which is
exactly why the brief's own Phase 3 asks for one integrated **Moat Engine**,
not nine scores. Recurring Revenue, Mission Critical Products, Customer
Concentration, Supplier Dependence → theme 5, folded into Moat evidence where
Atlas has data, otherwise disclosed as unassessed. Capital Intensity,
Reinvestment Opportunity, Growth Durability → themes 3+7, the **Reinvestment
Engine**. Industry Structure, Cyclicality, Business Complexity, Operational
Stability, Geographic Diversification → themes 8/9/11, context modifiers with
no current Atlas data source — disclosed as unassessed throughout, never
approximated.

## Part B — Architecture investigation (confirms where this can and cannot live)

`atlas.analysis_engine`'s `BusinessCategory` is a **closed six-member enum**
(`BUSINESS_MODEL`, `COMPETITIVE_POSITION`, `MANAGEMENT`, `CAPITAL_ALLOCATION`,
`GROWTH`, `DURABILITY`). Four members are **permanently locked** at
`INSUFFICIENT_INPUT` by explicit, repeated, multi-file doctrine — this layer
categorically refuses to parse qualitative/free-text content. This is not
incidental: `atlas.decision_engine.contracts.py` **structurally forbids** a
`moat`/`competitive_position`/`management`/`business_quality` field from ever
existing on a Core object at all (`__post_init__` locks Durability to
`INSUFFICIENT_INPUT` unconditionally). **This engine cannot live in
`analysis_engine` or write into any Core/decision_engine contract.**

A separate, mature system already exists in `atlas/alpha/investment_case/`
that reads real filing/transcript content deterministically (keyword/
structure matching, never NLP). Of its modules:

- **Structurally dormant today** (no production path fetches real DEF
  14A/10-K HTML into `FilingContent` anywhere in Atlas — a prior sprint's own
  deliberate, disclosed decision): `governance_intelligence.py`,
  `executive_compensation_intelligence.py`, `incentive_intelligence.py`
  (permanently framework-only regardless of input), and the ownership/equity
  half of `insider_alignment_intelligence.py`. These read `UNKNOWN`, always,
  this sprint — a real, disclosed gap, not an oversight.
- **Genuinely live and populated** (real transcripts + real financials,
  already wired in `service.py`, already flowing to real companies):
  `management_credibility_intelligence.py` (`execution_consistency`,
  `communication_consistency`, `guidance_reliability`),
  `management_guidance_intelligence.py`, `capital_allocation_intelligence.py`
  (`ManagementCapitalAllocationKnowledge` — shareholder return policy,
  financing strategy, acquisition behavior, debt discipline, buyback
  consistency, reinvestment discipline), and
  `business_quality_intelligence.py` (a pure third-order aggregation over
  Growth/Capital-Allocation/Financial-Quality into `BusinessStability`,
  `BusinessDurability`, `BusinessEfficiency`, `BusinessConsistency`,
  `BusinessEvolution` — already exactly the quantitative moat-proxy evidence
  Part A's research calls for: margin stability as a pricing-power proxy,
  capital-efficiency trend as a returns-on-capital proxy, growth-durability
  count as a secular-advantage proxy).

**Design consequence**: this engine is a new alpha-layer package,
`atlas/alpha/business_quality_assessment/` (not `business_quality` — that
name is already taken by the narrower, purely-numeric module above; reusing
it would collide both as an import path and a schema field), synthesizing
(a) `analysis_engine`'s real Growth/Capital Allocation findings, (b) the
already-live alpha-layer intelligence modules above, into Moat/Management/
Reinvestment assessments and one integrated score — mirroring the exact
pattern `atlas/alpha/recommendation_conviction/` already establishes (pure
engine function + thin `Service` + reused, never-recomputed sibling inputs).
It reuses substantial existing, tested capability rather than reinventing
financial ratios from scratch, and never touches `analysis_engine`'s locked
`BusinessCategory` enum.

**Recommendation integration boundary**: "Recommendation Drivers"
(`strengths`/`risks` in the API response) is `CaseHighlightView`, sourced
purely from `analysis_engine.investment_case_synthesis`'s `HighlightKind`
mechanism — a Core concept that cannot read alpha-layer signals, the same
one-way boundary that already keeps `is_thesis_stale` a caller-supplied
parameter in Conviction. This engine's drivers are therefore surfaced as a
**separate, clearly-labeled, independently-traceable field** at the API
layer (never blended into `strengths`/`risks`), exactly matching this
codebase's own established discipline of never conflating two distinct
concepts under one name (the `ConvictionLevel`/`RecommendationConvictionLevel`
precedent).

## Part C — Moat Engine (Phase 3)

**Output**: `MoatLevel` — `EXCEPTIONAL` / `STRONG` / `MODERATE` / `WEAK` /
`UNKNOWN`.

**Evidence, all real, all reused, never recomputed** — five independent
signals, each `POSITIVE`/`NEGATIVE`/`UNKNOWN`:

1. `pricing_power` — `BusinessQualityKnowledge.stability.profitability_
   stability` (`StabilityLevel`): `STABLE` → `POSITIVE` (margins hold up
   through varying conditions — the only externally-visible trace pricing
   power leaves in financial statements); `VOLATILE` → `NEGATIVE`;
   `MODERATE`/`INSUFFICIENT_DATA` → `UNKNOWN`.
2. `capital_efficiency` — `BusinessQualityKnowledge.efficiency
   .capital_efficiency.return_on_assets_trend` (`TrendDirection`): `RISING`
   → `POSITIVE`; `FALLING` → `NEGATIVE`; else `UNKNOWN`.
3. `growth_durability` — `len(BusinessQualityKnowledge.durability
   .growth_durability.metrics_with_consistent_growth) >= 3` → `POSITIVE`
   (the identical threshold `business_quality_intelligence.py` itself uses
   for its own `DURABLE_GROWTH` finding — reused, not reinvented).
4. `consistent_value_creation` — presence of
   `BusinessQualityFindingKind.CONSISTENT_VALUE_CREATION` in
   `BusinessQualityKnowledge.findings` → `POSITIVE`.
5. `capital_allocation_corroboration` — `analysis_engine`'s own, Calibration
   Phase 4 Capital Allocation `BusinessFinding.status`: `STRONG` →
   `POSITIVE`; `WEAK` → `NEGATIVE`; else `UNKNOWN`.

**Combination** (same style as Capital Allocation v2 — negatives must
outweigh positives, the top tier needs broad corroboration):
```
if computable_count == 0:                          UNKNOWN
elif negative_count > positive_count:               WEAK
elif positive_count >= 4 and negative_count == 0:   EXCEPTIONAL
elif positive_count >= 3 and negative_count == 0:   STRONG
else:                                               MODERATE
```

**Every assessment always discloses `unassessed_dimensions`** — a fixed
tuple naming the qualitative moat evidence Atlas structurally cannot measure
this sprint regardless of level reached: market share, brand strength,
network effects, switching costs (as directly observed), ecosystem,
regulatory barriers, distribution, technology leadership. This is not a
caveat added only when the level is uncertain — it is always present,
because even an `EXCEPTIONAL` read here is proxy-based, never a substitute
for genuine competitive analysis. **Never inferred from market cap** — no
signal above reads size, revenue scale, or market cap; every one reads a
trend or a stability classification.

## Part D — Management Engine (Phase 4)

**Output**: `ManagementQualityLevel` — `EXCEPTIONAL` / `STRONG` /
`MODERATE` / `WEAK` / `UNKNOWN`, plus one assessment per dimension.

Seven dimensions, evaluating **behavior only, never personality**:

| Dimension | Real source | Populability |
|---|---|---|
| Capital Allocation | `analysis_engine`'s own Capital Allocation `BusinessFinding` (primary) + `ManagementCapitalAllocationKnowledge.debt_discipline`/`.capital_allocation_consistency` (detail) | Live |
| Execution | `ManagementCredibilityKnowledge.execution_consistency` — did commitments get fulfilled | Live (needs transcripts) |
| Consistency | `ManagementCredibilityKnowledge.guidance_reliability` — fulfilled vs. withdrawn guidance counts | Live (needs transcripts) |
| Communication | `ManagementCredibilityKnowledge.communication_consistency.direction` — did messaging/emphasis shift materially | Live (needs transcripts) |
| Long-term Thinking | `ManagementCapitalAllocationKnowledge.reinvestment_discipline` trend | Live |
| Shareholder Alignment | `ManagementCapitalAllocationKnowledge.shareholder_return_policy` + `.debt_discipline` (real, partial); insider-ownership evidence is structurally dormant | Partial — disclosed |
| Governance | No live data source (filing-content fetch path does not exist in production) | **Always Unknown** |

Each dimension resolves independently to `STRONG`/`MODERATE`/`WEAK`/
`UNKNOWN` via a direct, named mapping from its real source enum (no numeric
scoring). The overall `ManagementQualityLevel` combines the *computable*
dimensions (Governance always excluded from the count, always listed in
`unassessed_dimensions`) with the identical positive/negative-count
combination rule as Moat.

## Part E — Reinvestment Engine (Phase 5)

**Output**: `ReinvestmentOpportunityLevel` — `EXCELLENT` / `GOOD` /
`MODERATE` / `LIMITED` / `UNKNOWN`.

Four signals: `growth_durability` (reused verbatim from Moat's own
computation — the same real evidence answers both "is the business
advantaged" and "does growth have real durability," never duplicated as two
different numbers); `capital_efficiency` (reused verbatim from Moat — rising
returns on capital means the business is reinvesting at attractive
returns, not just growing for growth's sake); `cash_generation_capacity`
(`BusinessQualityKnowledge.durability.financial_durability` — sustained cash
generation funds reinvestment without external capital); `reinvestment_
activity` (`ManagementCapitalAllocationKnowledge.reinvestment_discipline`:
`RISING` → `POSITIVE`, real ongoing capital deployment; `FALLING` is
deliberately **not** read as `NEGATIVE` — falling capex could mean either
harvesting a mature, saturated market or genuine capital discipline, and
Atlas cannot honestly distinguish the two without segment/TAM data it does
not have, so `FALLING` resolves to `UNKNOWN` rather than guessed).

Same combination rule as Moat/Management. **Always discloses
`unassessed_dimensions`**: addressable market size, market saturation,
adjacent-product opportunities, international expansion headroom, industry
maturity — none of these has a real Atlas data source (no TAM, no segment or
geographic revenue breakdown exists as a fact kind).

## Part F — Business Quality Score (Phase 6)

**`BusinessQualityAssessment`** integrates the three engines without
replacing them:
- `overall_level` — the same positive/negative-count rule applied one level
  up, over the three sub-assessment levels (`EXCEPTIONAL`/`STRONG` count as
  positive, `WEAK`/`LIMITED` as negative, `MODERATE`/`GOOD` neutral,
  `UNKNOWN` excluded).
- `strengths` / `weaknesses` — real, named labels drawn directly from
  whichever sub-assessment(s) reached a strong/weak read (e.g. "Exceptional
  competitive position" from Moat, "Excellent reinvestment runway" from
  Reinvestment, "Disciplined capital allocation" from Management) — never
  invented text, always traceable to one real sub-assessment field.
- `greatest_advantage` / `greatest_concern` — the single most extreme
  positive/negative reading among the three, deterministic tie-break by a
  fixed Moat > Management > Reinvestment priority order (disclosed, not
  hidden).
- `unknowns` — the deduplicated union of all three engines' own
  `unassessed_dimensions`, so the reader sees, in one place, exactly what
  Atlas could not evaluate and why.

## Part G — Recommendation integration (Phase 7–8)

Business Quality **influences without dominating**: it is exposed as an
additive, separately-labeled driver set at the API layer (a new
`business_quality_drivers` field alongside, never merged into, the existing
Core-sourced `strengths`/`risks`), the same non-conflation discipline this
codebase already applies to Conviction vs. Recommendation Conviction. It does
not write into `analysis_engine.recommendation.ChangeTriggerKind` or
`_derive_what_would_change` — doing so would require Core to read an alpha
signal, the exact boundary violation this whole design avoids. It naturally
interacts with Valuation/Growth/Risk/Coverage/Conviction because it is
computed from real findings those engines already produced (Growth, Capital
Allocation, business-quality intelligence derived from the same financial
history) — never a second, independent read of raw data that could disagree
with them for no reason. No weight is hard-coded: the driver labels are
presence-only (a dimension either reached a strong/weak read or it didn't),
never summed into the recommendation's own gate.

## Part H — Files

New package `atlas/alpha/business_quality_assessment/`:
`models.py`, `moat.py`, `management.py`, `reinvestment.py`, `engine.py`,
`service.py`. Modified: `atlas/alpha/investment_case/api/schemas.py` (new
view types + two new response fields), `atlas/alpha/investment_case/api/
router.py` (wire the new service into `get_investment_case_analysis`), plus
`atlas/alpha/investment_case/api/dependencies.py` if a new provider function
is needed. New test files mirroring the package layout under
`tests/unit/alpha/business_quality_assessment/`.
