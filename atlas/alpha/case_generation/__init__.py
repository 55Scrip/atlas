"""Automatic canonical Investment Case existence (ATLAS-027, Phase 20).

**One canonical owner.** `CaseGenerationService.ensure_cases` is the
only place in this codebase that decides "does this holding need a new
Case" -- never duplicated into Portfolio Import, Portfolio Intelligence,
Case Intelligence, Discovery, a router, or the frontend. Every one of
those either consumes `AlphaHolding.case_id` after the fact, or (in the
frontend's manual "Open Investment Case" flow) keeps using
`AlphaPortfolioService.link_case_to_holding`'s own pre-existing,
independent idempotent path -- untouched by this module.

**Write-side only, never a read path.** Per explicit design confirmation
this sprint: called from `atlas.alpha.portfolio.AlphaPortfolioService`
at the exact points where a complete holdings list is known and about
to be persisted (`import_portfolio`, `reconcile_replace_allocation`,
`apply_confirmed_trade`) -- never from `get_state`/`get_view`, and never
from `analysis_engine` (ATLAS-020's `lifecycle.py` already established,
six sprints ago, that automatic Case-creation is a write-side,
event-triggered concern that belongs in a Core/Alpha use-case layer, not
inside the read-only, pure-function `analysis_engine` package).

**Idempotent by construction.** A holding that already carries a
`case_id` is returned completely unchanged -- its Case, and everything
ever recorded against it, is never touched, never re-created, never
re-linked. Only a holding with `case_id is None` gets a brand-new Case.

**Creates a Case, nothing else.** `Case.create()` (via
`atlas.core.application.case.create_case.CaseService`, the exact same
entrypoint the manual "Open Investment Case" button already uses) never
creates a Decision, Observation, Outcome, or Recommendation. See
`atlas.core.domain.case.entity.Case`'s own docstring: creating a Case
establishes only an ownership boundary.
"""
