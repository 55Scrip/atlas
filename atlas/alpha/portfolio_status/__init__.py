"""ATLAS-015 — Portfolio Status: workflow-completeness summary for Alpha.

Explicitly provisional Alpha application state, the same boundary
`atlas/alpha/portfolio/__init__.py` already establishes for the rest of
this package: may read `atlas.core` (Decision, Outcome, Observation, all
read-only), must never be read by `atlas.core` in return (enforced by
`tests/test_architecture_boundaries.py::test_core_does_not_import_atlas_alpha`,
which already scans this whole directory).

Naming note, read this before reusing the term "Portfolio Intelligence"
anywhere near this module: that name is already an established doctrine
term in this codebase for a different concept —
`docs/atlas_decision_engine/DE-003-Portfolio-Intelligence.md` and
`atlas/capabilities/portfolio_intelligence/` (`PortfolioIntelligenceCapability`)
score how well a *candidate position* fits the existing portfolio (seven
factors: allocation, concentration, diversification, correlation,
opportunity cost, existing thesis, previous decisions) to inform a
recommendation. This module does none of that — no scoring, no fit
analysis, no recommendation. It only counts and cross-references records
that already exist (holdings, Decisions, Outcomes, Observations, trade
log entries) to answer "what's incomplete, what's stale, what should be
looked at next" — a workflow-completeness summary, not an evaluation.
The Python module and service class are named `portfolio_status` /
`PortfolioStatusService` specifically to avoid colliding with
`PortfolioIntelligenceCapability`; the product-facing UI may still call
this feature "Portfolio Intelligence" (ATLAS-015's own vocabulary) since
that's a UI/product naming choice, not a code identifier.
"""
