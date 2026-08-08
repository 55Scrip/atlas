"""Business Data Ingestion (ATLAS-022) -- the canonical owner of
normalized business information: `atlas.analysis_engine.business_data`
is the one place a `BusinessRecord` is ever assembled anywhere in this
repository.

**Not a second analysis engine.** This package produces no findings, no
conclusions, no scores -- it answers exactly one question, "what
documents exist, and what do we structurally know about them," and
nothing else. `atlas.analysis_engine.business` (ATLAS-021) remains the
only place a business-quality judgment is ever made; this package feeds
it raw material, never a conclusion.

**Pipeline** (Phase 6): `providers.BusinessDataProvider.fetch` ->
`validation.validate_raw_document` -> `normalization.normalize` ->
`versioning.determine_version` -> `models.BusinessRecord`, orchestrated
by `pipeline.ingest`. Every stage is a pure, deterministic function;
nothing in this package reads a wall clock, calls a network, touches a
database, or invokes an LLM.

**Phase 10 -- exactly where a future data source plugs in.** Three
things, and nothing else, change when a real provider connects:

1. A new class implementing `providers.BusinessDataProvider`'s single
   `fetch` method -- e.g. `SecEdgarProvider`, `CompaniesHouseProvider`,
   `ManualUploadProvider` -- living in a future sibling module. It
   returns `RawBusinessDocument` tuples; nothing else in this package
   needs to know which real API or file format produced them.
2. If that provider surfaces a genuinely new kind of document, one new
   member on `sources.SourceKind` -- the same one-line addition every
   closed taxonomy in this codebase already expects when a real new
   case appears (see that enum's own docstring).
3. Whatever composition layer calls `pipeline.ingest` today with a
   `StaticBusinessDataProvider` instead calls it with the real
   provider, and passes the previous run's `existing_records` so
   versioning/duplicate-detection keeps working across runs.

**Nothing else changes.** `validation.py`, `normalization.py`,
`versioning.py`, `models.BusinessRecord`'s own shape, and every type in
`atlas.analysis_engine.business` (`BusinessFinding`, `BusinessCategory`,
`BusinessAnalysisResult`) are untouched by adding a provider --
`test_extensibility.py` proves this by adding a second, differently-shaped
provider mid-suite and confirming every downstream stage still behaves
identically. `BusinessFinding`, `BusinessAnalysisResult`, `Conviction`,
`RecommendationGateResult`, and `RiskSection` are entirely unaware this
package exists at all beyond the one field `business.py` gained this
sprint (`evaluate_business_analysis(..., business_records=...)`) -- no
other type anywhere in `atlas.analysis_engine` changed shape to make
this package possible.

**Architectural boundary**, identical to every sibling module in this
package (enforced by the same
`tests/test_architecture_boundaries.py::test_analysis_engine_only_reads_core_and_decision_engine`
that already covers all of `atlas.analysis_engine`, since this is a
subpackage of it, not a new top-level one): no `atlas.alpha`, no
`atlas.core.application`, no `atlas.core.infrastructure`, no
`.repository` imports, no database writes, no external API calls this
sprint.
"""
