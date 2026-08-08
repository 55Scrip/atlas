"""Business Facts (ATLAS-023) -- the structured layer between
`atlas.analysis_engine.business_data` (raw documents) and
`atlas.analysis_engine.business` (category judgments).

`BusinessRecord` (ATLAS-022) is deliberately structural-only -- no
parsed metric ever lived on it. This package is the smallest
deterministic fact-extraction layer the Phase 1 audit found necessary
to give `atlas.analysis_engine.growth` and `.capital_allocation`
something real to reason about: `extraction.extract_facts_from_records`
reads a closed set of well-known `BusinessRecord.metadata` keys and
produces atomic, structured `BusinessFact`s -- never interpreting,
scoring, or inferring from document content itself.

**Not a second Business Analysis owner.** This package produces no
findings, no conclusions, no `WEAK`/`MODERATE`/`STRONG` classification
-- it answers exactly one question, "what numeric facts were
deterministically extractable from the documents Atlas has," and
nothing else. `atlas.analysis_engine.business` remains the sole owner
of every category judgment; the evaluators in `atlas.analysis_engine
.growth`/`.capital_allocation` are the only readers of `BusinessFact`.

Reusable by design: `REVENUE` and `FREE_CASH_FLOW` are generic enough
that a future Valuation stage can read the identical facts Growth
already extracts, without this package or its taxonomy needing to
change, and without a second extraction pass over the same
`BusinessRecord`s.
"""
