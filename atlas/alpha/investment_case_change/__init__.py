"""Persistence for Investment Case Monitoring & Change Intelligence v1.

`atlas.analysis_engine.investment_case_change` computes everything
analytical (what a snapshot is, how two snapshots compare) as pure
functions with no store of their own -- the exact same "Core computes,
Alpha persists" split `atlas.analysis_engine.business_data`/
`atlas.alpha.business_data_refresh` already establish for
`BusinessRecord`s. This package is the "Alpha persists" half for
`AnalyticalSnapshot`: a table, a repository, and the composition wiring
that decides *when* a new snapshot is worth writing.

**Idempotency lives here, not in the pure comparison function.**
`atlas.analysis_engine.investment_case_change.compare_snapshots` will
happily compare two snapshots with an identical `content_hash` (it just
produces zero changes) -- but this package's own repository is what
actually prevents a duplicate row from ever being written for
unchanged analytical state, via a plain `content_hash` equality check
against the current head before any `add`. See `repository.py`'s own
`SqlAlchemyInvestmentCaseSnapshotRepository.add` for the exact
contract callers must follow.

**Architectural boundary**, identical to every other Alpha module: no
LLM, no NLP, no direct provider/network calls. May read
`atlas.core.domain`, `atlas.decision_engine`, and `atlas.analysis_engine`
freely, and other `atlas.alpha` packages for their own repository types,
the same pattern `atlas.alpha.investment_case` already follows for
`atlas.alpha.business_data_refresh.repository
.SqlAlchemyBusinessRecordRepository`.
"""
