"""Atlas Alpha's provisional Watchlist state (Investment Case Engine v1 slice).

This module is explicitly provisional Alpha application state, mirroring
`atlas/alpha/portfolio/__init__.py`'s own boundary exactly:

- NOT a Core Domain Object (`OE-002` §4's Domain Object Set is closed and
  includes no Watchlist primitive).
- NOT a canonical Product aggregate. `atlas.domains.watchlist.Watchlist`
  (a thin re-export of `atlas.shared.Watchlist`) already names the
  product concept of "a list of tickers" -- this package does not
  replace or duplicate that. It exists only to answer one narrow
  question: "does this ticker already have a Case, and how does the
  investor add one," so that a Watchlist company gets the exact same
  Investment Case knowledge a Portfolio holding already gets.
- NOT a permanent Watchlist architecture. It may be replaced, migrated,
  or deleted once a formal Watchlist product architecture is authorized.

`AlphaWatchlistEntry` (ticker + linked Case id) is the one thing this
package adds. Unlike `AlphaPortfolioState`'s singleton-with-embedded-
holdings shape, Watchlist entries are stored one row per ticker
(`table.py`) -- there is no cash, no allocation, no entry mode to bundle
alongside them, so a normalized table is the natural shape here, not an
imitation of Portfolio's own JSON-blob singleton.

Case linkage reuses `atlas.alpha.case_generation.CaseGenerationService`
exactly -- the one canonical owner of automatic Case existence
(`tests/unit/alpha/case_generation/test_boundaries.py`) -- via its
single-ticker `ensure_case_id` entrypoint, never a second, parallel
Case-creation implementation. Adding a ticker already linked to a Case
in the *other* membership context (Portfolio) reuses that same Case,
never creating a second one for the same company (see `service.py`).
"""
