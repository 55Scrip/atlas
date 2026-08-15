"""Security Discovery (Sprint 19) -- the smallest read-only feasibility
seam proving that a human-entered company name can produce useful,
auditable security *candidates* without ever being treated as identity
proof.

Genesis: Sprint 16 found Atlas has no path from a free-text company
name ("NVIDIA") to a ticker. Sprint 17 found Atlas needs a Security
Identity ontology but has none. Sprint 18 found FIGI is share-class-safe
but only useful *after* a correct ticker is already known -- it does
not solve name discovery. This package is Sprint 19's answer to the
remaining gap: discovery, not resolution.

This package deliberately does NOT:

- resolve, confirm, or persist anything -- every `SecurityCandidate`
  it returns carries a fixed `status="candidate_only"`;
- fuzzy-match, rank, or score -- `canonicalize.py`'s transform is a
  fixed, symmetric, published rule set (strip common legal-entity
  suffixes and punctuation, case-fold) applied identically to the
  query and to every SEC title; two titles either produce the exact
  same canonical string or they do not match at all -- there is no
  "closest" result, no threshold, no similarity library;
- silently pick a single candidate when multiple securities share a
  canonical form (Berkshire Hathaway's BRK-A/BRK-B, Alphabet's
  GOOG/GOOGL/GOOGM/GOOGN) -- every match is returned, unranked;
- touch `Decision.subject`, `Case`, Pattern Recognition, or Observed
  Decision Properties -- none of those are imported here, and nothing
  in this package writes to any repository;
- call a provider from inside this package's own pure logic --
  `service.discover_security_candidates` takes an already-built
  `title_index` as a plain argument; fetching that index from SEC's
  real `company_tickers.json` is the caller's concern, exercised only
  at explicit enrichment time, never from Pattern Recognition, History,
  Decision Review, or Observed Decision Properties render paths.

Source: SEC's own `company_tickers.json` only (free, unlicensed U.S.
government data, already fetched by
`atlas.business_data_providers.sec_edgar` for CIK resolution) --
deliberately not Alpha Vantage `SYMBOL_SEARCH` (its terms of service
do not clearly establish that caching search results is permitted;
Sprint 19's own investigation could not resolve this from available
documentation) and not OpenFIGI (Sprint 18 already established that
tool belongs to *verification*, not name discovery).

Following the one-way boundary `test_core_does_not_import_atlas_alpha`
already enforces: this package (`atlas.alpha`) may import
`atlas.core.application`/`atlas.core.domain`; nothing in Core ever
imports this package. In practice this package imports neither --
it depends on nothing outside the Python standard library.
"""
from __future__ import annotations
