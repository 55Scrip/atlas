"""Discovery Context (ATLAS-018).

The single canonical composition point Discovery consumes -- not a
fourth reasoning engine. `DiscoveryContextService.build()` assembles one
`DiscoveryContext` from `atlas.alpha.portfolio_intelligence
.PortfolioIntelligenceService` and `atlas.alpha.case_intelligence
.CaseIntelligenceService`, both reused verbatim (the exact same report
objects the Portfolio and Investment Case pages themselves render, via
the exact same `build_report()` calls) -- never a second computation of
anything either already produces.

This package also performs the one piece of assembly logic that did not
already exist anywhere: deterministic instrument/Case identity
resolution (`models.ResolvedIdentity`) -- see that type's own docstring
for why "InstrumentId" is deliberately absent (no such domain concept
exists in this codebase) and why a malformed or nonexistent `caseId`
degrades to an honest `UNRESOLVED` state rather than a crash or a
guess.

`diff.py` implements the deterministic comparison Phase 5 ("what
changed?") requires, but it is **not wired into the live chat flow**:
no snapshot/history store for past `PortfolioIntelligenceReport`/
`CaseIntelligenceReport` values exists yet in this codebase, so there is
no real "previous" object to compare against without fabricating one.
See `diff.py`'s own module docstring.
"""
