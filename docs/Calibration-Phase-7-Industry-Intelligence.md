# Calibration Phase 7 — Industry Intelligence

## Part A — Industry Taxonomy Audit (Phase 1)

**No GICS/NAICS/SIC or any industry taxonomy exists anywhere in this codebase**
— confirmed by exhaustive, case-insensitive search. Industry classification
today is a thin, unvalidated **free-text passthrough**: `CompanyProfile.sector`/
`.industry` (`atlas/alpha/investment_case/company_profile.py`) are `str | None`,
populated verbatim from Alpha Vantage's `OVERVIEW` endpoint
(`atlas/business_data_providers/alpha_vantage.py`'s `_IDENTITY_FIELD_MAP`), with
the type's own docstring stating plainly: *"No sector/industry taxonomy is
normalized or validated here."* The only two production reads of this field
are a null-presence check (`knowledge_coverage/engine.py`, feeding coverage
completeness, never branching on content) and raw display
(`CompanyProfileView`). **No evaluator anywhere branches on the sector/industry
string's content.**

A named-but-empty slot already exists for exactly this gap:
`KnowledgeDomain.INDUSTRY` in the live Knowledge Coverage taxonomy has zero
extractor wired, permanently `NOT_APPLICABLE`. A real, substantial legacy
engine (`atlas/capabilities/portfolio_intelligence/engine.py`, 356 lines,
sector/country/market-cap concentration) already exists but is explicitly,
deliberately disowned from the live FastAPI app — confirmed dead code, not a
capability to resurrect (its own package docstring states this).

**The pattern to mirror already exists**: `SecurityType`
(`atlas.alpha.canonical_security.value_objects`) is a closed `Literal` +
frozenset + `validate_*` function, fed by a closed translation table
(`_ASSET_TYPE_TRANSLATION` in `canonical_security_gate/candidate_mapping.py`)
that maps Alpha Vantage's own raw `AssetType` string ("Common Stock" → `
COMMON_STOCK`) into the closed vocabulary, falling through to `OTHER` for
anything unrecognized. **Industry Intelligence follows this exact, already-
adopted pattern** — a closed `IndustryFamily` enum fed by a closed translation
table over Alpha Vantage's real `sector`/`industry` strings, never a free-text
field promoted directly into decision logic.

**Confirmed real string values** (live dev database, 8 of 25 benchmark
companies have a populated `CompanyProfile`): `MSFT` → `TECHNOLOGY` /
`SOFTWARE - INFRASTRUCTURE`; `AMZN` → `CONSUMER CYCLICAL` / `INTERNET RETAIL`;
`GOOG`/`META` → `COMMUNICATION SERVICES` / `INTERNET CONTENT & INFORMATION`;
`AZN` → `HEALTHCARE` / `DRUG MANUFACTURERS - GENERAL`; `MA` → `FINANCIAL
SERVICES` / `CREDIT SERVICES`; `SKHY` → `TECHNOLOGY` / `SEMICONDUCTORS`; `AMAT`
→ `TECHNOLOGY` / `SEMICONDUCTOR EQUIPMENT & MATERIALS`. The other 17 have no
`CompanyProfile` ingested at all (13 of these are the same zero-company-data
set every prior Calibration phase has found; the remaining 4 — NVDA, AVGO,
BRK.B, VST, VRT — have real financial data but no profile/identity data,
a distinct, disclosed gap: profile and fundamentals come from different
provider calls and were not both ingested).

**Disclosed limitation carried into Part B**: Alpha Vantage's own
classification reflects a company's *largest reported operating segment*, not
economic structure — a true capital-allocation holding company (Berkshire
Hathaway, Investor, Industrivärden, Latour) may be classified by its largest
subsidiary's industry (e.g. insurance) rather than as a holding company at
all. This is a real property of the external data source, not something a
translation table can correct without fabricating a classification Atlas
cannot verify — disclosed explicitly, not silently mis-mapped.

## Part B — Industry Family Model (Phase 2)

18 families, derived from the brief's own suggested list, cross-checked
against the real strings above and the standard Alpha-Vantage/Yahoo sector-
industry vocabulary those 8 real companies confirm Atlas actually receives:
`SOFTWARE`, `SEMICONDUCTORS`, `INTERNET_PLATFORMS`, `BANKS`, `INSURANCE`,
`ASSET_MANAGERS`, `INDUSTRIALS`, `CONSUMER_STAPLES`, `CONSUMER_DISCRETIONARY`,
`LUXURY`, `PHARMA_BIOTECH`, `MEDICAL_DEVICES`, `UTILITIES`, `ENERGY`,
`REAL_ESTATE`, `TELECOM`, `PAYMENTS`, `HOLDING_COMPANIES`, plus
`UNCLASSIFIED` (a real, mapped-but-unrecognized string) and the honest
`UNKNOWN` (no `CompanyProfile` at all — the 17-of-25 case above).

## Part C — Industry Economics (Phase 3)

Documented in full, per family, in this document's own companion research
(value drivers, value destroyers, metrics that matter, metrics that can
mislead, structurally normal vs. abnormal risk) — see the Business Quality/
Capital Allocation/Valuation/Risk integration parts below for exactly which
of these become executable interpretation rules vs. remain reference-only
documentation. **Not every economic principle documented becomes code this
sprint** — only the ones with a real, already-computed Atlas signal to attach
to (per the brief's own "industry context determines what to look for... it
does not replace company-specific evidence").

## Part D — Interpretation Architecture (Phase 4, Phase 15)

New alpha-layer package `atlas/alpha/industry_intelligence/` — mirrors
`business_quality_assessment`'s own shape exactly (pure engine modules + thin
service, reused-not-recomputed sibling inputs). Cannot live in
`analysis_engine`/`canonical_security` (Core, deliberately identity-only) or
be added to any Core contract, the same boundary already established.

**Never overrides, never hides, always attaches.** Every interpretation
function takes an already-computed generic signal (a `BusinessCategoryStatus`,
`MoatLevel`, `ValuationStatus`, a `MetricTrend`) plus an `IndustryFamily`, and
returns a closed-vocabulary annotation *alongside* it — the original signal is
always still present, unmodified, on the API response. This directly
implements the conceptual model the brief itself gives: `Generic Signal +
Industry Context → Industry-Adjusted Interpretation`, where "interpretation"
means a new, additional, named annotation, never a replacement value.

## Part E — Industry-Specific Materiality (Phase 5)

Implemented as **semantic rules, not numeric weights** — a closed mapping from
(signal kind, industry family) to a materiality note, e.g. `(CUSTOMER_
CONCENTRATION, SEMICONDUCTORS) → HEIGHTENED`, `(CUSTOMER_CONCENTRATION,
CONSUMER_STAPLES) → ORDINARY`. Every rule is a named, disclosed mapping table
entry — never an invented numeric multiplier, per the brief's own explicit
preference.

## Part F — Business Quality Integration (Phase 6)

Reuses Calibration Phase 5's real `MoatAssessment`/`ReinvestmentAssessment`
output directly — never recomputed. Industry Intelligence adds one further,
honest layer: for each family, which qualitative moat-evidence *types* would
be most relevant (network effects/acceptance density for Payments; brand
scarcity for Luxury; technology leadership for Semiconductors; installed-
base/aftermarket for Industrials; pipeline/patent-cliff exposure for Pharma)
— always phrased as "this is the evidence type that would matter here," never
"this company has it," since Atlas has no direct data source for any of
these (the identical disclosed gap Phase 5's own `unassessed_dimensions`
already names generically; Phase 7 makes it industry-specific rather than
generic).

## Part G — Capital Allocation Integration (Phase 7)

The one, clear, repeated pattern across the brief's own examples: **leverage
means something different for a regulated/contracted-cash-flow business than
for an industrial company, and something structurally different again for a
bank** (whose entire balance sheet *is* the business). Implemented as a
narrow `interpret_leverage(family, debt_trend) → LeverageInterpretation`:
`STRUCTURALLY_NORMAL` (Utilities, Telecom, Real Estate — debt-funded capex
against a regulated/contracted base), `METRIC_NOT_APPROPRIATE` (Banks,
Insurance — the whole leverage concept doesn't transfer), `GENERIC_INTERPRETATION_
APPLIES` (Industrials, Software, most families — the existing Capital
Allocation/Risk read stands unadjusted), `UNKNOWN` (no classification).
**Never weakens the underlying signal** — Capital Allocation's own
`BusinessCategoryStatus`/Financial Risk's own `RiskStatus` are unchanged;
this only adds context for how to read them.

## Part H — Valuation Applicability (Phase 8)

The single most valuable, lowest-risk addition this sprint makes. A closed
`assess_valuation_applicability(family) → ValuationApplicability`:
`APPROPRIATE` (most operating companies — Software, Semiconductors,
Industrials, Consumer, Pharma, Payments, Telecom, Energy), `USEFUL_WITH_
CAVEATS` (Utilities — FCF is real but capex-heavy regulated reinvestment
cycles make the historical range noisier than a typical industrial), `POOR_
FIT` (Banks, Insurance, Real Estate, Holding Companies — FCF Yield Relative's
own model, current FCF ÷ market cap, does not fit a balance-sheet-is-the-
business institution, a GAAP-depreciation-distorted REIT, or a capital-
allocation holding company with no single consolidated operating P&L). **No
alternative valuation model is built this sprint** — for `POOR_FIT` families,
Atlas surfaces the honest disclosure directly, per the brief's own
instruction: "Unknown is better than false precision."

## Part I — Risk Interpretation (Phase 9)

Reuses Part G's `interpret_leverage` for the debt-trend-driven half of
Financial Risk. No other Risk-category adjustment is implemented this sprint
— Business Risk (Growth-derived) and Valuation Risk (FCF-Yield-derived) do
not have an equally clear, single, repeated industry-normalcy pattern across
the brief's own examples, and inventing one without a clear, evidence-backed
economic principle would risk exactly the "convert stereotypes into facts"
outcome the brief explicitly forbids.

## Part J — Recommendation Driver Integration (Phase 10)

Mirrors Calibration Phase 6's own pattern exactly: Industry Intelligence's
real, evidence-backed notes (Valuation Applicability when `POOR_FIT`/`USEFUL_
WITH_CAVEATS`; Leverage Interpretation when it changes the read) become new,
additive, alpha-layer-computed entries — never generated boilerplate, never
constructed when the underlying evidence is `UNKNOWN`.

## Part K — Coverage-Support Matrix (Phase 14)

Every family gets an honest `IndustrySupportLevel`: `STRONG` (the family has
a real classification path AND at least one real interpretation rule — e.g.
Utilities, Banks, Software, Semiconductors, REITs), `PARTIAL` (classification
exists but no dedicated interpretation rule beyond generic — most other
families this sprint), `UNSUPPORTED` implicitly for `UNCLASSIFIED`/`UNKNOWN`.
No family is ever marked `STRONG` without a real, implemented rule backing
it — this table is generated from the actual rule tables, not asserted
separately (so it cannot silently drift out of sync with the code).

## Part L — What this sprint deliberately does not do

No numeric industry-adjustment weights anywhere. No alternative valuation
model for `POOR_FIT` families. No industry-specific Business Risk/Valuation
Risk rule beyond the shared leverage interpretation. No attempt to correct
Alpha Vantage's own segment-based misclassification of holding companies —
disclosed, not fabricated around. No change to any Core `analysis_engine`
contract, Growth/Capital Allocation/Risk/Valuation's own computation, or the
Conviction/Recommendation gates.
