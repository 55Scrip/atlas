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

**Frozen, not refreshed.** A history entry shows the evidence persisted
with that snapshot (`valuation_evidence_snapshot`), read from the same row
as the snapshot itself. Current prices, current filings and the current
Case are never consulted for its content: a later filing or a new method
changes what Atlas says now, never what a stored entry reports it had
then. Snapshots taken before evidence persistence existed carry none, and
that absence is reported as an absence -- never reconstructed from today's
data, which would be a fabricated history.

**The Core/Alpha boundary is kept at the join.** `AnalyticalHistory` and
`HistoricalAnalysisEntry` are Core contracts that know nothing about how
Atlas persists evidence; hanging an Alpha persistence type on them would
invert the dependency the architecture tests police. So Core computes and
orders the history, `AnalyticalHistoryWithEvidence` carries the frozen
evidence beside it, and the API schema joins the two by snapshot identity
-- the same `snapshotId` a client sees, never by ticker.

**Bounded, by construction.** A request returns one page, newest first,
never the whole corpus: absence of `limit` means the default page, and a
ceiling makes the unbounded response unaskable. The boundary between pages
is an opaque cursor carrying the three values the history is ordered by
(`captured_at`, `case_id`, `content_hash`) -- a total order, since a row's
identity is `case_id:captured_at`. An offset would have been wrong here:
history is append-only *and* rows can be retracted, so "skip 25" stops
meaning the same thing the moment the visible set changes.

Three things happen strictly before a page is cut, all of them in the
database: scope is narrowed to the Cases live membership allows, retracted
rows are excluded, and only then are the cursor and limit applied. A row a
reader may not see therefore cannot consume a page slot or move a boundary.
The cursor narrows; it never widens -- scope is re-derived on every request,
so a cursor cannot reach a Case the request could not already see. One
consequence is honest and deliberate: a multi-page traversal is not a
transactional snapshot of membership, because scope means "now".

**Read-only, by construction.** `InvestmentCaseHistoryService
.build_analytical_history` calls only `SqlAlchemyInvestmentCaseSnapshotRepository
.get_history_with_evidence` -- never `.add`, never
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
