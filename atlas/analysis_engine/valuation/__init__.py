"""Valuation Engine v1 (ATLAS-024) -- the canonical owner of every
valuation conclusion Atlas produces: what the market is currently
asking to pay for a business, relative to its own recorded history.

**Not a second Business Analysis.** This package never reads a Growth
or Capital Allocation finding, and `atlas.analysis_engine.business`
never reads a Valuation finding -- per this sprint's own explicit rule,
"a great company can be expensive, a weak company can be cheap," the
two dimensions coexist in `CanonicalAnalysis` without either overriding
or agreeing with the other.

**One real method, three honest placeholders.**
`ValuationMethodKind.FCF_YIELD_RELATIVE` (`cash_flow.py`) is real: FCF
yield vs. this company's own historical range, chosen because it needs
the fewest unsupported assumptions of any method the Phase 1 audit
considered. The three scenario methods (`scenarios.py`) are real,
tested structure that honestly returns `INSUFFICIENT_INPUT` -- Atlas
has no canonical source for a forward growth/discount-rate assumption
yet, and fabricating one would violate this sprint's own "no fabricated
assumptions" rule.

**Market data reuses `atlas.analysis_engine.business_data`'s existing
canonical ingestion layer, not a second one.** A market snapshot is a
`BusinessRecord` tagged `SourceKind.MARKET_DATA_SNAPSHOT`; `facts.py`
extracts `ValuationFact`s from it the same deterministic, well-known-key
way `atlas.analysis_engine.business_facts` already does for
fundamentals -- Phase 5's fundamental/market boundary lives in which
fact taxonomy reads a record, not in a second ingestion system.

**Provider-independent by the same structural guarantee ATLAS-023
established**: `cash_flow.py`/`scenarios.py` never import
`business_data.providers` or any provider-specific type -- only
`BusinessFact`/`ValuationFact`. A future market-data provider only
needs to populate the same well-known metadata keys `facts.py` already
reads; no evaluator changes.

**Architectural boundary**, identical to every sibling subpackage
(enforced by the same repository-wide
`test_analysis_engine_only_reads_core_and_decision_engine`, since this
is a subpackage of `atlas.analysis_engine`, not a new top-level one):
no `atlas.alpha`, no `atlas.core.application`, no
`atlas.core.infrastructure`, no external API calls, no LLM, no NLP.
"""
