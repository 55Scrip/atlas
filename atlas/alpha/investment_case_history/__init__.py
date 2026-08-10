"""History v1 -- the Alpha-layer retrieval half of
`atlas.analysis_engine.investment_case_history`.

**Deliberately distinct from `atlas.history`.** That package is
unrelated legacy infrastructure (a weekly-review, numeric-score-based
change engine -- `ChangeType.QUALITY_SCORE_CHANGED`/`RISK_SCORE_CHANGED`,
`atlas.memory.MemoryStore`), never wired into this codebase's real
Case/Portfolio/Watchlist/Investment-Case architecture and never touched
by any of the sprints that built it. Reusing it, or importing from it,
would smuggle a numeric-scoring model into a product line that has
consistently and deliberately forbidden one (`ChangeIntelligence`'s own
categorical `ThesisImpact`). This package's own name
(`investment_case_history`, mirroring `investment_case_change`'s own
naming) is chosen specifically to avoid the collision the word "history"
alone would invite.

**Read-only, by construction.** `InvestmentCaseHistoryService
.build_analytical_history` calls only `SqlAlchemyInvestmentCaseSnapshotRepository
.get_history` -- never `.add`, never
`InvestmentCaseCompositionService.build`/`build_many` (which *would*
have the side effect of persisting a new snapshot). Opening History can
never create analytical state; it can only read what already exists.

**Architectural boundary**, identical to every other Alpha module: no
LLM, no NLP, no direct provider/network calls, no
`atlas.business_data_providers`. May read `atlas.core.domain`,
`atlas.decision_engine`, `atlas.analysis_engine`, and other `atlas.alpha`
packages for their own repository/service types -- the same pattern
`atlas.alpha.daily_brief` already follows.
"""
