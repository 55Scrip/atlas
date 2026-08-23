"""Daily Brief Agenda (Product Sprint 6) -- the Priority Engine that
turns Atlas's existing signals into one unified, prioritized agenda.

**Owns almost no business logic of its own.** Every signal below is a
direct, disclosed read of an already-computed fact:

- Workflow items (Decision without Outcome, awaiting reconciliation,
  missing Case, very old Case) <- `atlas.alpha.portfolio_status`
  (`PortfolioStatusReport.review_queue`/`.attention_items`), the exact
  severity taxonomy `frontend/src/portfolio/derivePortfolioActions.ts`
  already established -- ported here, not reinvented, because this
  sprint's own Deliverable 13 requires Portfolio to consume the same
  backend agenda instead of a second, client-only derivation.
- Portfolio-level risk/allocation findings <- `atlas.alpha
  .portfolio_intelligence` (`KeyFinding`), unmodified.
- Thesis change <- `atlas.alpha.daily_brief`/`atlas.analysis_engine
  .investment_case_change` (`ChangeIntelligence.thesis_impact`),
  unmodified.
- Portfolio Fit rating and trend <- `atlas.alpha.portfolio_fit`
  (`PortfolioFitAssessment.overall`/`.trend`), unmodified -- see that
  package's own `__init__.py`.
- Case Condition / Assumption state <- `atlas.core.application
  .reasoning_workspace.read_models` (`list_active_case_conditions`/
  `list_active_assumptions`), unmodified.

**No new domain object, no new persistence.** `engine.py` is pure
(a deterministic function of already-fetched signals to one
`AgendaItem` per ticker/portfolio-level concern); `service.py` is the
only part that performs I/O, and it does so by calling four existing
services' own public methods -- never by re-querying a repository
those services already own.

**Why a new package, not code added to `atlas.alpha.daily_brief`.**
Every signal source here belongs to a *different* existing package
(`portfolio_status`, `portfolio_intelligence`, `portfolio_fit`,
`case_condition`, `assumption`), none of which `daily_brief` itself
already depends on. Composing five siblings into a new capability is
exactly the same "new orchestration package, existing services
untouched" shape `atlas.alpha.portfolio_fit` and `atlas.alpha
.reasoning_workspace` already established -- `atlas.alpha.daily_brief`
itself is not modified by this sprint at all.
"""
